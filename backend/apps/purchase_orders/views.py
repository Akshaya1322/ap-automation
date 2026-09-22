from rest_framework import viewsets

from apps.purchase_orders.models import PurchaseOrder
from apps.purchase_orders.serializers import PurchaseOrderDetailSerializer, PurchaseOrderListSerializer


class PurchaseOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PurchaseOrder.objects.select_related("vendor").prefetch_related(
        "line_items", "goods_receipts", "goods_receipts__line_items"
    )
    filterset_fields = ["status", "vendor", "department"]
    search_fields = ["po_number", "vendor__name"]
    ordering_fields = ["order_date", "total_amount", "po_number"]
    ordering = ["-order_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return PurchaseOrderListSerializer
        return PurchaseOrderDetailSerializer
