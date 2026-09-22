import io
from decimal import Decimal

from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.approvals.models import ApprovalMatrixRule, StepStatus, WorkflowStatus
from apps.approvals.services import create_workflow
from apps.authentication.models import Role
from apps.common.test_utils import make_user, make_vendor, setup_approval_matrix
from apps.invoices.models import Invoice, InvoiceStatus
from apps.notifications.models import Notification


class ApprovalWorkflowTests(APITestCase):
    def setUp(self):
        setup_approval_matrix()
        self.vendor = make_vendor()
        self.processor = make_user(Role.AP_PROCESSOR, username="proc_ap1")
        self.ap_manager = make_user(Role.AP_MANAGER, username="mgr_ap1")
        self.finance_manager = make_user(Role.FINANCE_MANAGER, username="fin_ap1")
        self.other_manager = make_user(Role.AP_MANAGER, username="mgr_ap2")

    def _invoice(self, amount):
        return Invoice.objects.create(
            invoice_number=f"INV-{amount}",
            vendor=self.vendor,
            total_amount=Decimal(amount),
            currency="INR",
            status=InvoiceStatus.VALIDATED,
            uploaded_by=self.processor,
        )

    def test_small_invoice_needs_only_ap_manager(self):
        invoice = self._invoice("20000.00")
        workflow = create_workflow(invoice, notify=False)
        self.assertEqual(workflow.steps.count(), 1)
        self.assertEqual(workflow.steps.first().role_required, Role.AP_MANAGER)

    def test_large_invoice_needs_three_approvers_in_order(self):
        invoice = self._invoice("600000.00")
        workflow = create_workflow(invoice, notify=False)
        roles = list(workflow.steps.order_by("step_number").values_list("role_required", flat=True))
        self.assertEqual(roles, [Role.AP_MANAGER, Role.FINANCE_MANAGER, Role.ADMIN])

    def test_full_approval_sequence_moves_invoice_to_approved(self):
        invoice = self._invoice("200000.00")  # AP_MANAGER + FINANCE_MANAGER
        create_workflow(invoice, notify=False)

        self.client.force_authenticate(self.ap_manager)
        first_step = invoice.approval_workflow.steps.get(step_number=1)
        response = self.client.post(reverse("approval-approve", args=[first_step.id]), {"comment": "ok"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, InvoiceStatus.PENDING_APPROVAL)  # still waiting on step 2

        self.client.force_authenticate(self.finance_manager)
        second_step = invoice.approval_workflow.steps.get(step_number=2)
        response = self.client.post(reverse("approval-approve", args=[second_step.id]), {"comment": "ok"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, InvoiceStatus.APPROVED)
        self.assertEqual(invoice.approval_workflow.status, WorkflowStatus.APPROVED)

    def test_reject_requires_a_comment(self):
        invoice = self._invoice("20000.00")
        create_workflow(invoice, notify=False)
        step = invoice.approval_workflow.steps.get(step_number=1)

        self.client.force_authenticate(self.ap_manager)
        response = self.client.post(reverse("approval-reject", args=[step.id]), {"comment": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(reverse("approval-reject", args=[step.id]), {"comment": "Wrong rate"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, InvoiceStatus.REJECTED)

    def test_only_assigned_approver_can_act(self):
        invoice = self._invoice("20000.00")
        create_workflow(invoice, notify=False)
        step = invoice.approval_workflow.steps.get(step_number=1)

        self.client.force_authenticate(self.other_manager)  # not the assigned approver
        response = self.client.post(reverse("approval-approve", args=[step.id]), {"comment": "ok"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_act_on_a_step_that_is_not_yet_current(self):
        invoice = self._invoice("200000.00")
        create_workflow(invoice, notify=False)
        second_step = invoice.approval_workflow.steps.get(step_number=2)

        self.client.force_authenticate(self.finance_manager)
        response = self.client.post(reverse("approval-approve", args=[second_step.id]), {"comment": "ok"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ParallelApprovalTests(APITestCase):
    """A required_roles entry that's itself a list -- e.g.
    [AP_MANAGER, [FINANCE_MANAGER, ADMIN]] -- means those roles approve in
    parallel (same step_number, either order) rather than one after another."""

    def setUp(self):
        ApprovalMatrixRule.objects.all().delete()
        ApprovalMatrixRule.objects.create(
            min_amount=Decimal("0"),
            max_amount=None,
            required_roles=[Role.AP_MANAGER, [Role.FINANCE_MANAGER, Role.ADMIN]],
        )
        self.vendor = make_vendor()
        self.processor = make_user(Role.AP_PROCESSOR, username="proc_par1")
        self.ap_manager = make_user(Role.AP_MANAGER, username="mgr_par1")
        self.finance_manager = make_user(Role.FINANCE_MANAGER, username="fin_par1")
        self.admin = make_user(Role.ADMIN, username="admin_par1")

    def _invoice(self):
        return Invoice.objects.create(
            invoice_number="INV-PARALLEL-1",
            vendor=self.vendor,
            total_amount=Decimal("999999.00"),
            currency="INR",
            status=InvoiceStatus.VALIDATED,
            uploaded_by=self.processor,
        )

    def test_parallel_step_creates_two_steps_sharing_one_step_number(self):
        invoice = self._invoice()
        workflow = create_workflow(invoice, notify=False)
        parallel_steps = workflow.steps.filter(step_number=2)
        self.assertEqual(parallel_steps.count(), 2)
        self.assertTrue(all(s.is_parallel for s in parallel_steps))
        self.assertEqual({s.role_required for s in parallel_steps}, {Role.FINANCE_MANAGER, Role.ADMIN})

    def test_workflow_waits_for_both_parallel_approvers(self):
        invoice = self._invoice()
        create_workflow(invoice, notify=False)

        self.client.force_authenticate(self.ap_manager)
        first_step = invoice.approval_workflow.steps.get(step_number=1)
        self.client.post(reverse("approval-approve", args=[first_step.id]), {"comment": "ok"})

        finance_step = invoice.approval_workflow.steps.get(step_number=2, role_required=Role.FINANCE_MANAGER)
        admin_step = invoice.approval_workflow.steps.get(step_number=2, role_required=Role.ADMIN)

        # First parallel approver: invoice must NOT be fully approved yet.
        self.client.force_authenticate(self.finance_manager)
        response = self.client.post(reverse("approval-approve", args=[finance_step.id]), {"comment": "ok"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, InvoiceStatus.PENDING_APPROVAL)
        self.assertEqual(invoice.approval_workflow.status, WorkflowStatus.IN_PROGRESS)

        # Second (last) parallel approver: now it completes.
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("approval-approve", args=[admin_step.id]), {"comment": "ok"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, InvoiceStatus.APPROVED)
        self.assertEqual(invoice.approval_workflow.status, WorkflowStatus.APPROVED)

    def test_parallel_approvers_can_act_in_either_order(self):
        invoice = self._invoice()
        create_workflow(invoice, notify=False)
        self.client.force_authenticate(self.ap_manager)
        first_step = invoice.approval_workflow.steps.get(step_number=1)
        self.client.post(reverse("approval-approve", args=[first_step.id]), {"comment": "ok"})

        admin_step = invoice.approval_workflow.steps.get(step_number=2, role_required=Role.ADMIN)
        finance_step = invoice.approval_workflow.steps.get(step_number=2, role_required=Role.FINANCE_MANAGER)

        # Admin acts first this time (opposite order from the other test).
        self.client.force_authenticate(self.admin)
        self.client.post(reverse("approval-approve", args=[admin_step.id]), {"comment": "ok"})
        self.client.force_authenticate(self.finance_manager)
        response = self.client.post(reverse("approval-approve", args=[finance_step.id]), {"comment": "ok"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, InvoiceStatus.APPROVED)


class EscalationCommandTests(APITestCase):
    def setUp(self):
        setup_approval_matrix()
        self.vendor = make_vendor()
        self.processor = make_user(Role.AP_PROCESSOR, username="proc_esc1")
        self.ap_manager = make_user(Role.AP_MANAGER, username="mgr_esc1")
        self.admin = make_user(Role.ADMIN, username="admin_esc1")
        self.invoice = Invoice.objects.create(
            invoice_number="INV-ESCALATE-1",
            vendor=self.vendor,
            total_amount=Decimal("20000.00"),  # AP_MANAGER-only band
            currency="INR",
            status=InvoiceStatus.VALIDATED,
            uploaded_by=self.processor,
        )
        self.workflow = create_workflow(self.invoice, notify=False)
        self.step = self.workflow.steps.get(step_number=1)

    def _run(self):
        out = io.StringIO()
        call_command("check_approval_escalations", stdout=out)
        return out.getvalue()

    def test_step_not_yet_due_gets_no_reminder(self):
        output = self._run()
        self.step.refresh_from_db()
        self.assertIsNone(self.step.reminder_sent_at)
        self.assertIn("0 reminder(s) sent, 0 escalation(s) sent", output)

    def test_step_due_soon_gets_a_reminder_once(self):
        self.step.due_at = timezone.now() + timezone.timedelta(hours=2)
        self.step.save(update_fields=["due_at"])

        output = self._run()
        self.assertIn("1 reminder(s) sent", output)
        self.step.refresh_from_db()
        self.assertIsNotNone(self.step.reminder_sent_at)
        self.assertTrue(
            Notification.objects.filter(user=self.ap_manager, type="APPROVAL_REMINDER").exists()
        )

        # Running it again shouldn't send a second reminder for the same step.
        output_again = self._run()
        self.assertIn("0 reminder(s) sent", output_again)

    def test_overdue_step_is_escalated_to_admins(self):
        self.step.due_at = timezone.now() - timezone.timedelta(hours=5)
        self.step.save(update_fields=["due_at"])

        output = self._run()
        self.assertIn("1 escalation(s) sent", output)
        self.assertTrue(
            Notification.objects.filter(user=self.admin, type="APPROVAL_ESCALATED").exists()
        )

        # Re-running shouldn't escalate the same still-pending step twice.
        output_again = self._run()
        self.assertIn("0 escalation(s) sent", output_again)

    def test_completed_step_is_never_escalated(self):
        self.step.status = StepStatus.APPROVED
        self.step.due_at = timezone.now() - timezone.timedelta(hours=5)
        self.step.save(update_fields=["status", "due_at"])

        output = self._run()
        self.assertIn("0 escalation(s) sent", output)
        self.assertFalse(Notification.objects.filter(user=self.admin, type="APPROVAL_ESCALATED").exists())
