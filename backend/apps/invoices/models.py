from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel
from apps.purchase_orders.models import PurchaseOrder
from apps.vendors.models import Vendor


class InvoiceStatus(models.TextChoices):
    UPLOADED = "UPLOADED", "Uploaded"
    PROCESSING = "PROCESSING", "Processing"
    EXTRACTED = "EXTRACTED", "Extracted"
    VALIDATED = "VALIDATED", "Validated"
    EXCEPTION = "EXCEPTION", "Exception"
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    PAYMENT_PENDING = "PAYMENT_PENDING", "Payment Pending"
    PAID = "PAID", "Paid"


class OcrConfidenceLevel(models.TextChoices):
    HIGH = "HIGH", "High"
    MEDIUM = "MEDIUM", "Medium"
    LOW = "LOW", "Low"


class Invoice(UUIDTimeStampedModel):
    invoice_number = models.CharField(max_length=100, blank=True, default="")
    vendor = models.ForeignKey(
        Vendor, null=True, blank=True, on_delete=models.SET_NULL, related_name="invoices"
    )
    vendor_name_raw = models.CharField(max_length=255, blank=True, default="")
    purchase_order = models.ForeignKey(
        PurchaseOrder, null=True, blank=True, on_delete=models.SET_NULL, related_name="invoices"
    )
    po_number_raw = models.CharField(max_length=50, blank=True, default="")

    gstin = models.CharField(max_length=15, blank=True, default="")
    invoice_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=6, default="INR")

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    cgst = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    sgst = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    igst = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True, default="")

    department = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.UPLOADED)

    ocr_provider = models.CharField(max_length=30, blank=True, default="")
    ocr_confidence = models.FloatField(null=True, blank=True)  # 0-100
    ocr_confidence_level = models.CharField(
        max_length=10, choices=OcrConfidenceLevel.choices, null=True, blank=True
    )
    ocr_raw_text = models.TextField(blank=True, default="")

    po_match_status = models.CharField(max_length=20, blank=True, default="")

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="invoices_uploaded"
    )

    class Meta:
        db_table = "invoices"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["gstin"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.invoice_number or f"Invoice {self.id}"


class InvoiceLineItem(UUIDTimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="line_items")
    line_no = models.PositiveIntegerField(default=1)
    description = models.CharField(max_length=500, blank=True, default="")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "invoice_line_items"
        ordering = ["line_no"]


class InvoiceDocument(UUIDTimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="invoices/")
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20)
    file_size = models.PositiveIntegerField(default=0)
    page_count = models.PositiveIntegerField(default=1)
    is_primary = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "invoice_documents"
        ordering = ["-created_at"]


class InvoiceExtractedField(UUIDTimeStampedModel):
    """Per-field OCR result used to drive the review/edit screen."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="extracted_fields")
    field_name = models.CharField(max_length=60)
    value = models.CharField(max_length=500, blank=True, default="")
    confidence = models.FloatField(default=0)  # 0-100
    is_mandatory = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    validation_status = models.CharField(max_length=20, default="PENDING")  # PENDING/VALID/INVALID

    class Meta:
        db_table = "invoice_extracted_fields"
        unique_together = ("invoice", "field_name")


class ExceptionType(models.TextChoices):
    MISSING_VENDOR = "MISSING_VENDOR", "Missing Vendor"
    INVALID_GSTIN = "INVALID_GSTIN", "Invalid GSTIN"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE", "Duplicate Invoice"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH", "Amount Mismatch"
    MISSING_PO = "MISSING_PO", "Missing PO"
    OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE", "OCR Low Confidence"
    MISSING_MANDATORY_FIELD = "MISSING_MANDATORY_FIELD", "Missing Mandatory Field"
    PO_MISMATCH = "PO_MISMATCH", "PO Mismatch"


class ExceptionSeverity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class ExceptionStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    RESOLVED = "RESOLVED", "Resolved"
    REJECTED = "REJECTED", "Rejected"
    OVERRIDDEN = "OVERRIDDEN", "Overridden"


class InvoiceException(UUIDTimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="exceptions")
    exception_type = models.CharField(max_length=30, choices=ExceptionType.choices)
    severity = models.CharField(max_length=10, choices=ExceptionSeverity.choices, default=ExceptionSeverity.MEDIUM)
    description = models.CharField(max_length=500)
    status = models.CharField(max_length=15, choices=ExceptionStatus.choices, default=ExceptionStatus.OPEN)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="exceptions_assigned"
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="exceptions_resolved"
    )
    resolution_comment = models.CharField(max_length=1000, blank=True, default="")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "invoice_exceptions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self):
        return f"{self.exception_type} - {self.invoice_id}"
