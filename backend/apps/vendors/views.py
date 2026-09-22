from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit_logs.services import log_action
from apps.authentication.permissions import IsAdminOrManager
from apps.vendors.models import Vendor, VendorStatus
from apps.vendors.serializers import VendorDetailSerializer, VendorListSerializer, VendorWriteSerializer

# Onboarding: Draft -> Submitted -> Under Review -> Approved -> Active
TRANSITIONS = {
    "submit": (VendorStatus.DRAFT, VendorStatus.SUBMITTED),
    "start_review": (VendorStatus.SUBMITTED, VendorStatus.UNDER_REVIEW),
    "approve": (VendorStatus.UNDER_REVIEW, VendorStatus.APPROVED),
    "activate": (VendorStatus.APPROVED, VendorStatus.ACTIVE),
}
WRITE_ACTIONS = {"create", "update", "partial_update", "deactivate", *TRANSITIONS.keys()}


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.select_related("bank_details", "created_by").prefetch_related("documents")
    filterset_fields = ["status", "category", "is_active"]
    search_fields = ["name", "code", "gstin", "email"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return VendorListSerializer
        if self.action in ("update", "partial_update", "create"):
            return VendorWriteSerializer
        return VendorDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            qs = VendorListSerializer.annotate_queryset(qs)
        return qs

    def get_permissions(self):
        if self.action in WRITE_ACTIONS:
            return [IsAuthenticated(), IsAdminOrManager()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor = serializer.save(created_by=request.user, status=VendorStatus.DRAFT, is_active=False)
        log_action(action="VENDOR_CREATE", entity_type="Vendor", entity_id=vendor.id, description=f"Vendor '{vendor.name}' created")
        return Response(VendorDetailSerializer(vendor, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        vendor = serializer.save()
        log_action(action="VENDOR_UPDATE", entity_type="Vendor", entity_id=vendor.id, description=f"Vendor '{vendor.name}' updated")

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(VendorDetailSerializer(self.get_object(), context=self.get_serializer_context()).data)

    def _transition(self, key):
        from_status, to_status = TRANSITIONS[key]
        vendor = self.get_object()
        if vendor.status != from_status:
            return Response(
                {"detail": f"Vendor must be in '{from_status}' status to perform this action (currently '{vendor.status}')."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        vendor.status = to_status
        if to_status == VendorStatus.ACTIVE:
            vendor.is_active = True
        vendor.save(update_fields=["status", "is_active"])
        log_action(
            action="VENDOR_UPDATE",
            entity_type="Vendor",
            entity_id=vendor.id,
            description=f"Vendor '{vendor.name}' onboarding: {from_status} -> {to_status}",
        )
        return Response(VendorDetailSerializer(vendor, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        return self._transition("submit")

    @action(detail=True, methods=["post"], url_path="start-review")
    def start_review(self, request, pk=None):
        return self._transition("start_review")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._transition("approve")

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        return self._transition("activate")

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        vendor = self.get_object()
        vendor.status = VendorStatus.INACTIVE
        vendor.is_active = False
        vendor.save(update_fields=["status", "is_active"])
        log_action(action="VENDOR_UPDATE", entity_type="Vendor", entity_id=vendor.id, description=f"Vendor '{vendor.name}' deactivated")
        return Response(VendorDetailSerializer(vendor, context=self.get_serializer_context()).data)
