import django_filters
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from apps.audit_logs.services import log_action
from apps.authentication.permissions import CanProcessInvoices
from apps.invoices.models import ExceptionStatus, InvoiceException
from apps.invoices.serializers import ExceptionCenterSerializer
from apps.invoices.validation import run_validation
from apps.notifications.services import notify_user


class ExceptionFilter(django_filters.FilterSet):
    class Meta:
        model = InvoiceException
        fields = {
            "status": ["exact"],
            "severity": ["exact"],
            "exception_type": ["exact"],
            "assigned_to": ["exact"],
            "invoice": ["exact"],
        }


class ExceptionActionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=True, allow_blank=False, max_length=1000)


class ExceptionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = InvoiceException.objects.select_related("invoice", "invoice__vendor", "assigned_to", "resolved_by")
    serializer_class = ExceptionCenterSerializer
    filterset_class = ExceptionFilter
    search_fields = ["description", "invoice__invoice_number", "invoice__vendor__name"]
    ordering_fields = ["created_at", "severity"]
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticated]

    def _finalize(self, request, new_status, extra_description_prefix):
        exc = self.get_object()
        serializer = ExceptionActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.validated_data["comment"]

        exc.status = new_status
        exc.resolved_by = request.user
        exc.resolved_at = timezone.now()
        exc.resolution_comment = comment
        exc.save(update_fields=["status", "resolved_by", "resolved_at", "resolution_comment"])

        log_action(
            action="EXCEPTION_RESOLVE",
            entity_type="InvoiceException",
            entity_id=exc.id,
            description=f"{extra_description_prefix} exception '{exc.get_exception_type_display()}' on invoice {exc.invoice.invoice_number}: {comment}",
        )

        # Re-run validation: resolved exceptions whose root cause is gone
        # stay cleared; overridden ones are protected by _maybe_raise.
        run_validation(exc.invoice)

        if exc.invoice.uploaded_by:
            notify_user(
                exc.invoice.uploaded_by,
                "GENERAL",
                f"Exception on invoice {exc.invoice.invoice_number} was {new_status.lower()} by {request.user.display_name}.",
                link=f"/invoices/{exc.invoice_id}",
            )

        return Response(ExceptionCenterSerializer(exc).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, CanProcessInvoices])
    def resolve(self, request, pk=None):
        return self._finalize(request, ExceptionStatus.RESOLVED, "Resolved")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, CanProcessInvoices])
    def reject(self, request, pk=None):
        return self._finalize(request, ExceptionStatus.REJECTED, "Rejected")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, CanProcessInvoices])
    def override(self, request, pk=None):
        return self._finalize(request, ExceptionStatus.OVERRIDDEN, "Overrode")
