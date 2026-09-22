"""Send reminder notifications for approval steps nearing their due date,
and escalate steps that are already overdue to every Admin.

This app has no background task queue (see README's "Known Limitations") --
consistent with that, this command is meant to be run periodically by an
external scheduler (cron, Windows Task Scheduler) rather than as a
long-running daemon:

    python manage.py check_approval_escalations
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.approvals.models import ApprovalStep, StepStatus
from apps.audit_logs.models import AuditLog
from apps.audit_logs.services import log_action
from apps.authentication.models import Role
from apps.notifications.services import notify_role, notify_user

# Send a reminder once a step is within this window of its due date.
REMINDER_LEAD = timedelta(hours=24)


class Command(BaseCommand):
    help = "Send reminders for approval steps nearing their due date and escalate overdue ones to Admins."

    def handle(self, *args, **options):
        now = timezone.now()
        candidates = ApprovalStep.objects.filter(
            status=StepStatus.PENDING, due_at__isnull=False
        ).select_related("workflow", "workflow__invoice", "assigned_user")

        # Only the step(s) that are actually current in their workflow are
        # "actionable" right now -- a step later in the sequence can't be
        # meaningfully overdue since nobody could have acted on it yet.
        actionable = [s for s in candidates if s.step_number == s.workflow.current_step_number]

        reminders_sent = 0
        escalations_sent = 0

        for step in actionable:
            invoice = step.workflow.invoice
            invoice_label = invoice.invoice_number or str(invoice.id)
            assignee_label = step.assigned_user.display_name if step.assigned_user else "nobody (unassigned)"

            if now > step.due_at:
                already_escalated = AuditLog.objects.filter(
                    entity_type="ApprovalStep", entity_id=str(step.id), action="APPROVAL_ESCALATED"
                ).exists()
                if already_escalated:
                    continue

                notify_role(
                    Role.ADMIN,
                    "APPROVAL_ESCALATED",
                    f"Escalation: the {step.role_required} approval step for invoice {invoice_label} "
                    f"is overdue (assigned to {assignee_label}).",
                    link=f"/approvals/{step.id}",
                )
                log_action(
                    action="APPROVAL_ESCALATED",
                    entity_type="ApprovalStep",
                    entity_id=step.id,
                    description=f"Escalated overdue approval step for invoice {invoice_label} to Admins.",
                )
                escalations_sent += 1
                self.stdout.write(self.style.WARNING(f"Escalated step {step.id} (invoice {invoice_label})."))
                continue

            due_soon = (step.due_at - now) <= REMINDER_LEAD
            if step.reminder_sent_at is None and due_soon:
                notify_user(
                    step.assigned_user,
                    "APPROVAL_REMINDER",
                    f"Reminder: invoice {invoice_label} is awaiting your approval, due {step.due_at:%d %b %Y}.",
                    link=f"/approvals/{step.id}",
                )
                step.reminder_sent_at = now
                step.save(update_fields=["reminder_sent_at"])
                log_action(
                    action="APPROVAL_REMINDER",
                    entity_type="ApprovalStep",
                    entity_id=step.id,
                    description=f"Reminder sent for approval step on invoice {invoice_label} (assigned to {assignee_label}).",
                )
                reminders_sent += 1
                self.stdout.write(f"Reminder sent for step {step.id} (invoice {invoice_label}).")

        self.stdout.write(
            self.style.SUCCESS(f"Done. {reminders_sent} reminder(s) sent, {escalations_sent} escalation(s) sent.")
        )
