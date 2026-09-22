from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class AuditAction(models.TextChoices):
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"
    UPLOAD = "UPLOAD", "Invoice Upload"
    OCR_PROCESS = "OCR_PROCESS", "OCR Processing"
    FIELD_EDIT = "FIELD_EDIT", "Field Edit"
    VALIDATE = "VALIDATE", "Validation Run"
    EXCEPTION_CREATE = "EXCEPTION_CREATE", "Exception Created"
    EXCEPTION_RESOLVE = "EXCEPTION_RESOLVE", "Exception Resolved"
    PO_MATCH = "PO_MATCH", "PO Matching Run"
    APPROVAL = "APPROVAL", "Approved"
    REJECTION = "REJECTION", "Rejected"
    REQUEST_CHANGES = "REQUEST_CHANGES", "Changes Requested"
    APPROVAL_REMINDER = "APPROVAL_REMINDER", "Approval Reminder Sent"
    APPROVAL_ESCALATED = "APPROVAL_ESCALATED", "Approval Escalated"
    VENDOR_CREATE = "VENDOR_CREATE", "Vendor Created"
    VENDOR_UPDATE = "VENDOR_UPDATE", "Vendor Updated"
    PAYMENT_REQUEST = "PAYMENT_REQUEST", "Payment Request Created"
    PAYMENT_STATUS_CHANGE = "PAYMENT_STATUS_CHANGE", "Payment Status Changed"
    CREATE = "CREATE", "Created"
    UPDATE = "UPDATE", "Updated"
    DELETE = "DELETE", "Deleted"


class AuditLog(UUIDTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs"
    )
    action = models.CharField(max_length=32, choices=AuditAction.choices)
    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64, blank=True, default="")
    description = models.CharField(max_length=500, blank=True, default="")
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} on {self.entity_type}:{self.entity_id} by {self.user}"
