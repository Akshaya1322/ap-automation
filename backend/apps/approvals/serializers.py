from rest_framework import serializers

from apps.approvals.models import ApprovalAction, ApprovalStep, ApprovalWorkflow
from apps.invoices.serializers import InvoiceDetailSerializer


class ApprovalActionSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.display_name", read_only=True, default=None)

    class Meta:
        model = ApprovalAction
        fields = ["id", "action", "comment", "actor", "actor_name", "created_at"]


class ApprovalStepSerializer(serializers.ModelSerializer):
    assigned_user_name = serializers.CharField(source="assigned_user.display_name", read_only=True, default=None)
    invoice_id = serializers.UUIDField(source="workflow.invoice_id", read_only=True)
    invoice_number = serializers.CharField(source="workflow.invoice.invoice_number", read_only=True)
    vendor_name = serializers.CharField(source="workflow.invoice.vendor.name", read_only=True, default=None)
    amount = serializers.DecimalField(
        source="workflow.invoice.total_amount", max_digits=14, decimal_places=2, read_only=True, default=None
    )
    currency = serializers.CharField(source="workflow.invoice.currency", read_only=True)
    workflow_status = serializers.CharField(source="workflow.status", read_only=True)
    is_current_step = serializers.SerializerMethodField()
    actions = ApprovalActionSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalStep
        fields = [
            "id",
            "workflow",
            "workflow_status",
            "step_number",
            "role_required",
            "assigned_user",
            "assigned_user_name",
            "is_parallel",
            "status",
            "due_at",
            "invoice_id",
            "invoice_number",
            "vendor_name",
            "amount",
            "currency",
            "is_current_step",
            "actions",
        ]

    def get_is_current_step(self, obj):
        return obj.step_number == obj.workflow.current_step_number


class ApprovalStepDetailSerializer(ApprovalStepSerializer):
    invoice = serializers.SerializerMethodField()
    all_steps = serializers.SerializerMethodField()

    class Meta(ApprovalStepSerializer.Meta):
        fields = ApprovalStepSerializer.Meta.fields + ["invoice", "all_steps"]

    def get_invoice(self, obj):
        return InvoiceDetailSerializer(obj.workflow.invoice, context=self.context).data

    def get_all_steps(self, obj):
        steps = obj.workflow.steps.order_by("step_number")
        return ApprovalStepSerializer(steps, many=True, context=self.context).data


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    steps = ApprovalStepSerializer(many=True, read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)

    class Meta:
        model = ApprovalWorkflow
        fields = ["id", "invoice", "invoice_number", "status", "current_step_number", "created_at", "completed_at", "steps"]


class ApprovalDecisionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, default="")
