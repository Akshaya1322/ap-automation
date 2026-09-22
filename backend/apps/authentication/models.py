import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    AP_MANAGER = "AP_MANAGER", "AP Manager"
    AP_PROCESSOR = "AP_PROCESSOR", "AP Processor"
    APPROVER = "APPROVER", "Approver"
    FINANCE_MANAGER = "FINANCE_MANAGER", "Finance Manager"
    AUDITOR = "AUDITOR", "Auditor"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.AP_PROCESSOR)
    department = models.CharField(max_length=100, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    is_active_employee = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def display_name(self):
        return self.get_full_name() or self.username
