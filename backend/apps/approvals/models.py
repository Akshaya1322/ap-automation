from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel
from apps.invoices.models import Invoice


class WorkflowStatus(models.TextChoices):
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CHANGES_REQUESTED = "CHANGES_REQUESTED", "Changes Requested"


class StepStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    SKIPPED = "SKIPPED", "Skipped"
    CHANGES_REQUESTED = "CHANGES_REQUESTED", "Changes Requested"


class ApprovalWorkflow(UUIDTimeStampedModel):
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="approval_workflow")
    status = models.CharField(max_length=20, choices=WorkflowStatus.choices, default=WorkflowStatus.IN_PROGRESS)
    current_step_number = models.PositiveIntegerField(default=1)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "approval_workflows"

    def __str__(self):
        return f"Workflow for {self.invoice}"


class ApprovalStep(UUIDTimeStampedModel):
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE, related_name="steps")
    step_number = models.PositiveIntegerField()
    role_required = models.CharField(max_length=32)
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approval_steps"
    )
    is_parallel = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=StepStatus.choices, default=StepStatus.PENDING)
    due_at = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "approval_steps"
        ordering = ["step_number"]

    def __str__(self):
        return f"Step {self.step_number} ({self.role_required}) - {self.workflow_id}"


class ApprovalActionType(models.TextChoices):
    APPROVE = "APPROVE", "Approve"
    REJECT = "REJECT", "Reject"
    REQUEST_CHANGES = "REQUEST_CHANGES", "Request Changes"


class ApprovalAction(UUIDTimeStampedModel):
    step = models.ForeignKey(ApprovalStep, on_delete=models.CASCADE, related_name="actions")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=20, choices=ApprovalActionType.choices)
    comment = models.CharField(max_length=1000, blank=True, default="")

    class Meta:
        db_table = "approval_actions"
        ordering = ["-created_at"]


class ApprovalMatrixRule(UUIDTimeStampedModel):
    """Configurable approval matrix: amount band -> required approver roles."""

    min_amount = models.DecimalField(max_digits=14, decimal_places=2)
    max_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)  # null = unbounded
    required_roles = models.JSONField(default=list)  # ordered list of role codes
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "approval_matrix_rules"
        ordering = ["min_amount"]

    def __str__(self):
        upper = self.max_amount if self.max_amount is not None else "∞"
        return f"{self.min_amount} - {upper}: {self.required_roles}"
