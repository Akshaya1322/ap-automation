from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.approvals.models import ApprovalMatrixRule
from apps.audit_logs.services import log_action
from apps.authentication.permissions import IsAdminOrManager


class ApprovalMatrixRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalMatrixRule
        fields = ["id", "min_amount", "max_amount", "required_roles", "is_active"]


class ApprovalMatrixRuleViewSet(viewsets.ModelViewSet):
    queryset = ApprovalMatrixRule.objects.all().order_by("min_amount")
    serializer_class = ApprovalMatrixRuleSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminOrManager()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        rule = serializer.save()
        log_action(action="CREATE", entity_type="ApprovalMatrixRule", entity_id=rule.id, description=str(rule))

    def perform_update(self, serializer):
        rule = serializer.save()
        log_action(action="UPDATE", entity_type="ApprovalMatrixRule", entity_id=rule.id, description=str(rule))

    def perform_destroy(self, instance):
        log_action(action="DELETE", entity_type="ApprovalMatrixRule", entity_id=instance.id, description=str(instance))
        instance.delete()
