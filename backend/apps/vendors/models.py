from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class VendorStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    APPROVED = "APPROVED", "Approved"
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class Vendor(UUIDTimeStampedModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32, unique=True)
    gstin = models.CharField(max_length=15, blank=True, default="")
    pan = models.CharField(max_length=10, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    contact_person = models.CharField(max_length=150, blank=True, default="")

    address_line1 = models.CharField(max_length=255, blank=True, default="")
    address_line2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    pincode = models.CharField(max_length=12, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="India")

    category = models.CharField(max_length=100, blank=True, default="")
    department = models.CharField(max_length=100, blank=True, default="")
    payment_terms_days = models.PositiveIntegerField(default=30)

    status = models.CharField(max_length=20, choices=VendorStatus.choices, default=VendorStatus.DRAFT)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="vendors_created"
    )

    class Meta:
        db_table = "vendors"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["gstin"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class VendorBankDetails(UUIDTimeStampedModel):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name="bank_details")
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=40)
    bank_name = models.CharField(max_length=150)
    ifsc_code = models.CharField(max_length=15)
    branch = models.CharField(max_length=150, blank=True, default="")
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "vendor_bank_details"

    def __str__(self):
        return f"Bank details for {self.vendor.name}"

    @property
    def masked_account_number(self):
        acc = self.account_number or ""
        if len(acc) <= 4:
            return acc
        return "*" * (len(acc) - 4) + acc[-4:]


class VendorDocument(UUIDTimeStampedModel):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="vendor_documents/")
    document_type = models.CharField(max_length=100, blank=True, default="")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "vendor_documents"
