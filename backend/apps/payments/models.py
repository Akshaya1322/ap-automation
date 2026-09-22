from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel
from apps.invoices.models import Invoice
from apps.vendors.models import Vendor


class PaymentMethod(models.TextChoices):
    BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer (NEFT/RTGS)"
    CHEQUE = "CHEQUE", "Cheque"
    UPI = "UPI", "UPI"
    CARD = "CARD", "Card"


class PaymentStatus(models.TextChoices):
    PAYMENT_PENDING = "PAYMENT_PENDING", "Payment Pending"
    PROCESSING = "PROCESSING", "Processing"
    PAID = "PAID", "Paid"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class PaymentRequest(UUIDTimeStampedModel):
    request_number = models.CharField(max_length=50, unique=True)
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="payment_request")
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="payment_requests")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=6, default="INR")
    method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.BANK_TRANSFER)
    requested_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PAYMENT_PENDING)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="payment_requests_made"
    )

    class Meta:
        db_table = "payment_requests"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return self.request_number


class Payment(UUIDTimeStampedModel):
    payment_request = models.OneToOneField(PaymentRequest, on_delete=models.CASCADE, related_name="payment")
    transaction_ref = models.CharField(max_length=100, blank=True, default="")
    payment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PROCESSING)
    bank_response = models.JSONField(null=True, blank=True)  # simulated gateway response
    advice_generated = models.BooleanField(default=False)
    advice_file = models.FileField(upload_to="payment_advice/", null=True, blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment for {self.payment_request.request_number}"
