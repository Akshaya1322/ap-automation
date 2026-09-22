from rest_framework import serializers

from apps.purchase_orders.models import (
    GoodsReceipt,
    GoodsReceiptLineItem,
    PurchaseOrder,
    PurchaseOrderLineItem,
)


class PurchaseOrderLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderLineItem
        fields = ["id", "line_no", "description", "quantity", "unit_price", "tax_amount", "amount"]


class GoodsReceiptLineItemSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source="po_line_item.description", read_only=True)

    class Meta:
        model = GoodsReceiptLineItem
        fields = ["id", "po_line_item", "description", "quantity_received"]


class GoodsReceiptSerializer(serializers.ModelSerializer):
    line_items = GoodsReceiptLineItemSerializer(many=True, read_only=True)
    received_by_name = serializers.CharField(source="received_by.display_name", read_only=True, default=None)

    class Meta:
        model = GoodsReceipt
        fields = [
            "id",
            "grn_number",
            "purchase_order",
            "received_date",
            "received_by_name",
            "status",
            "remarks",
            "line_items",
        ]


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    invoice_count = serializers.IntegerField(source="invoices.count", read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "po_number",
            "vendor",
            "vendor_name",
            "order_date",
            "department",
            "currency",
            "total_amount",
            "status",
            "invoice_count",
        ]


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    line_items = PurchaseOrderLineItemSerializer(many=True, read_only=True)
    goods_receipts = GoodsReceiptSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "po_number",
            "vendor",
            "vendor_name",
            "order_date",
            "department",
            "currency",
            "subtotal",
            "tax_amount",
            "total_amount",
            "status",
            "line_items",
            "goods_receipts",
            "created_at",
        ]
