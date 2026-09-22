from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel


class NotificationType(models.TextChoices):
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED", "Approval Required"
    APPROVAL_REMINDER = "APPROVAL_REMINDER", "Approval Reminder"
    APPROVAL_ESCALATED = "APPROVAL_ESCALATED", "Approval Escalated"
    DUPLICATE_WARNING = "DUPLICATE_WARNING", "Duplicate Warning"
    PAYMENT_DUE = "PAYMENT_DUE", "Payment Due"
    PROCESSING_COMPLETE = "PROCESSING_COMPLETE", "Processing Complete"
    EXCEPTION_RAISED = "EXCEPTION_RAISED", "Exception Raised"
    INVOICE_REJECTED = "INVOICE_REJECTED", "Invoice Rejected"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED", "Payment Completed"
    GENERAL = "GENERAL", "General"


class Notification(UUIDTimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.GENERAL)
    message = models.CharField(max_length=500)
    link = models.CharField(max_length=255, blank=True, default="")
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.type} -> {self.user_id}"
