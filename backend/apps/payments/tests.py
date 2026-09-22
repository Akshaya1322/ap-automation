from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import Role
from apps.common.test_utils import make_user, make_vendor
from apps.invoices.models import Invoice, InvoiceStatus
from apps.payments.models import PaymentStatus


class PaymentWorkflowTests(APITestCase):
    def setUp(self):
        self.finance = make_user(Role.FINANCE_MANAGER, username="fin_pay1")
        self.processor = make_user(Role.AP_PROCESSOR, username="proc_pay1")
        self.vendor = make_vendor()
        self.invoice = Invoice.objects.create(
            invoice_number="INV-PAY-1",
            vendor=self.vendor,
            total_amount=Decimal("25000.00"),
            currency="INR",
            due_date="2026-02-01",
            status=InvoiceStatus.APPROVED,
            uploaded_by=self.processor,
        )

    def test_create_payment_request_requires_finance_role(self):
        self.client.force_authenticate(self.processor)
        response = self.client.post(reverse("payment-list"), {"invoice": str(self.invoice.id), "method": "BANK_TRANSFER"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_payment_request_requires_approved_invoice(self):
        self.invoice.status = InvoiceStatus.PENDING_APPROVAL
        self.invoice.save()
        self.client.force_authenticate(self.finance)
        response = self.client.post(reverse("payment-list"), {"invoice": str(self.invoice.id), "method": "BANK_TRANSFER"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_payment_request_moves_invoice_to_payment_pending(self):
        self.client.force_authenticate(self.finance)
        response = self.client.post(reverse("payment-list"), {"invoice": str(self.invoice.id), "method": "BANK_TRANSFER"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, InvoiceStatus.PAYMENT_PENDING)

    def test_duplicate_payment_request_rejected(self):
        self.client.force_authenticate(self.finance)
        self.client.post(reverse("payment-list"), {"invoice": str(self.invoice.id), "method": "BANK_TRANSFER"})
        self.invoice.status = InvoiceStatus.APPROVED  # simulate re-approval attempt
        self.invoice.save()
        response = self.client.post(reverse("payment-list"), {"invoice": str(self.invoice.id), "method": "BANK_TRANSFER"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.payments.gateway.random.random", return_value=0.01)  # force simulated success
    def test_process_payment_success_marks_invoice_paid(self, _mock_random):
        self.client.force_authenticate(self.finance)
        create_resp = self.client.post(reverse("payment-list"), {"invoice": str(self.invoice.id), "method": "BANK_TRANSFER"})
        pr_id = create_resp.data["id"]

        response = self.client.post(reverse("payment-process", args=[pr_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], PaymentStatus.PAID)
        self.assertTrue(response.data["payment"]["bank_response"]["simulated"])
        self.assertTrue(response.data["payment"]["advice_generated"])
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, InvoiceStatus.PAID)

    @patch("apps.payments.gateway.random.random", return_value=0.99)  # force simulated failure
    def test_process_payment_failure_allows_retry(self, _mock_random):
        self.client.force_authenticate(self.finance)
        create_resp = self.client.post(reverse("payment-list"), {"invoice": str(self.invoice.id), "method": "BANK_TRANSFER"})
        pr_id = create_resp.data["id"]

        response = self.client.post(reverse("payment-process", args=[pr_id]))
        self.assertEqual(response.data["status"], PaymentStatus.FAILED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, InvoiceStatus.PAYMENT_PENDING)  # can still be retried

        with patch("apps.payments.gateway.random.random", return_value=0.01):
            retry_response = self.client.post(reverse("payment-process", args=[pr_id]))
        self.assertEqual(retry_response.data["status"], PaymentStatus.PAID)
