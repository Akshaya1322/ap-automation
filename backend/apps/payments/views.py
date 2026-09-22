from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit_logs.services import log_action
from apps.authentication.permissions import IsFinance
from apps.invoices.models import Invoice, InvoiceStatus
from apps.notifications.services import notify_user
from apps.payments.advice import generate_payment_advice
from apps.payments.gateway import get_banking_gateway
from apps.payments.models import Payment, PaymentRequest, PaymentStatus
from apps.payments.serializers import (
    PaymentRequestCreateSerializer,
    PaymentRequestDetailSerializer,
    PaymentRequestListSerializer,
)


class PaymentRequestViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = PaymentRequest.objects.select_related("invoice", "vendor", "payment", "requested_by")
    filterset_fields = ["status", "vendor", "method"]
    search_fields = ["request_number", "invoice__invoice_number", "vendor__name"]
    ordering_fields = ["created_at", "due_date", "amount"]
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentRequestListSerializer
        if self.action == "create":
            return PaymentRequestCreateSerializer
        return PaymentRequestDetailSerializer

    def get_permissions(self):
        if self.action in ("create", "process", "cancel"):
            return [IsAuthenticated(), IsFinance()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = Invoice.objects.select_related("vendor").filter(id=serializer.validated_data["invoice"]).first()
        if not invoice:
            return Response({"detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
        if invoice.status != InvoiceStatus.APPROVED:
            return Response({"detail": "Only approved invoices can have a payment request raised."}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(invoice, "payment_request"):
            return Response({"detail": "A payment request already exists for this invoice."}, status=status.HTTP_400_BAD_REQUEST)
        if not invoice.vendor or not hasattr(invoice.vendor, "bank_details"):
            return Response({"detail": "Vendor bank details are required before raising a payment request."}, status=status.HTTP_400_BAD_REQUEST)

        count = PaymentRequest.objects.count() + 1
        pr = PaymentRequest.objects.create(
            request_number=f"PREQ-2026-{count:05d}",
            invoice=invoice,
            vendor=invoice.vendor,
            amount=invoice.total_amount,
            currency=invoice.currency,
            method=serializer.validated_data["method"],
            due_date=invoice.due_date,
            status=PaymentStatus.PAYMENT_PENDING,
            requested_by=request.user,
        )
        invoice.status = InvoiceStatus.PAYMENT_PENDING
        invoice.save(update_fields=["status"])

        log_action(
            action="PAYMENT_REQUEST",
            entity_type="PaymentRequest",
            entity_id=pr.id,
            description=f"Payment request {pr.request_number} raised for invoice {invoice.invoice_number} (₹{pr.amount})",
        )
        return Response(PaymentRequestDetailSerializer(pr, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        pr = self.get_object()
        if pr.status not in (PaymentStatus.PAYMENT_PENDING, PaymentStatus.FAILED):
            return Response({"detail": f"Payment request is already '{pr.status}'."}, status=status.HTTP_400_BAD_REQUEST)

        pr.status = PaymentStatus.PROCESSING
        pr.save(update_fields=["status"])

        result = get_banking_gateway().pay(pr)
        payment, _ = Payment.objects.update_or_create(
            payment_request=pr,
            defaults=dict(
                transaction_ref=result["transaction_ref"],
                payment_date=timezone.now(),
                status=PaymentStatus.PAID if result["success"] else PaymentStatus.FAILED,
                bank_response=result["response"],
                processed_by=request.user,
            ),
        )

        old_status = pr.status
        pr.status = PaymentStatus.PAID if result["success"] else PaymentStatus.FAILED
        pr.save(update_fields=["status"])

        if result["success"]:
            generate_payment_advice(payment)
            pr.invoice.status = InvoiceStatus.PAID
            pr.invoice.save(update_fields=["status"])
            if pr.requested_by:
                notify_user(
                    pr.requested_by,
                    "PAYMENT_COMPLETED",
                    f"Payment {pr.request_number} for invoice {pr.invoice.invoice_number} completed successfully.",
                    link=f"/payments/{pr.id}",
                )

        log_action(
            action="PAYMENT_STATUS_CHANGE",
            entity_type="PaymentRequest",
            entity_id=pr.id,
            description=f"Payment {pr.request_number}: {old_status} -> {pr.status} (simulated gateway)",
            previous_value=old_status,
            new_value=pr.status,
        )

        return Response(PaymentRequestDetailSerializer(pr, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        pr = self.get_object()
        if pr.status != PaymentStatus.PAYMENT_PENDING:
            return Response({"detail": "Only pending payment requests can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        pr.status = PaymentStatus.CANCELLED
        pr.save(update_fields=["status"])
        log_action(
            action="PAYMENT_STATUS_CHANGE",
            entity_type="PaymentRequest",
            entity_id=pr.id,
            description=f"Payment {pr.request_number} cancelled",
        )
        return Response(PaymentRequestDetailSerializer(pr, context=self.get_serializer_context()).data)
