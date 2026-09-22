from django.contrib import admin

from apps.purchase_orders.models import (
    GoodsReceipt,
    GoodsReceiptLineItem,
    PurchaseOrder,
    PurchaseOrderLineItem,
)


class PurchaseOrderLineItemInline(admin.TabularInline):
    model = PurchaseOrderLineItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("po_number", "vendor", "order_date", "total_amount", "status")
    list_filter = ("status",)
    search_fields = ("po_number", "vendor__name")
    inlines = [PurchaseOrderLineItemInline]


class GoodsReceiptLineItemInline(admin.TabularInline):
    model = GoodsReceiptLineItem
    extra = 0


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ("grn_number", "purchase_order", "received_date", "status")
    search_fields = ("grn_number", "purchase_order__po_number")
    inlines = [GoodsReceiptLineItemInline]
