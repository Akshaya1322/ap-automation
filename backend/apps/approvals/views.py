from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.approvals.models import ApprovalStep, StepStatus
from apps.approvals.serializers import (
    ApprovalDecisionSerializer,
    ApprovalStepDetailSerializer,
    ApprovalStepSerializer,
)
from apps.approvals.services import apply_action
from apps.authentication.models import Role

MANAGEMENT_ROLES = {Role.ADMIN, Role.AP_MANAGER}


class ApprovalStepViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = ApprovalStep.objects.select_related(
        "workflow", "workflow__invoice", "workflow__invoice__vendor", "assigned_user"
    ).prefetch_related("actions", "actions__actor")
    filterset_fields = ["status", "role_required", "workflow"]
    ordering_fields = ["created_at", "due_at", "step_number"]
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ApprovalStepDetailSerializer
        return ApprovalStepSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        show_all = self.request.query_params.get("all") == "true"
        if show_all and user.role in MANAGEMENT_ROLES:
            return qs
        if user.role in MANAGEMENT_ROLES:
            # Managers see everything by default too, but can narrow to their own queue.
            if self.request.query_params.get("mine") == "true":
                return qs.filter(assigned_user=user)
            return qs
        return qs.filter(assigned_user=user)

    def _get_step_for_action(self, request, pk):
        step = self.get_object()
        if step.assigned_user_id != request.user.id and request.user.role != Role.ADMIN:
            raise PermissionDenied("You are not the assigned approver for this step.")
        if step.status != StepStatus.PENDING:
            raise serializers.ValidationError("This approval step has already been actioned.")
        if step.step_number != step.workflow.current_step_number:
            raise serializers.ValidationError("This step is not yet active in the approval sequence.")
        return step

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        step = self._get_step_for_action(request, pk)
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        apply_action(step, request.user, "APPROVE", serializer.validated_data["comment"])
        step.refresh_from_db()
        return Response(ApprovalStepDetailSerializer(step, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        step = self._get_step_for_action(request, pk)
        comment = request.data.get("comment", "").strip()
        if not comment:
            raise serializers.ValidationError({"comment": "A reason is required to reject an invoice."})
        apply_action(step, request.user, "REJECT", comment)
        step.refresh_from_db()
        return Response(ApprovalStepDetailSerializer(step, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="request-changes")
    def request_changes(self, request, pk=None):
        step = self._get_step_for_action(request, pk)
        comment = request.data.get("comment", "").strip()
        if not comment:
            raise serializers.ValidationError({"comment": "Please describe what changes are needed."})
        apply_action(step, request.user, "REQUEST_CHANGES", comment)
        step.refresh_from_db()
        return Response(ApprovalStepDetailSerializer(step, context={"request": request}).data)
