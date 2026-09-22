from django.conf import settings
from django.db import models

from apps.common.models import UUIDTimeStampedModel
from apps.vendors.models import Vendor


class PurchaseOrderStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Partially Received"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


class PurchaseOrder(UUIDTimeStampedModel):
    po_number = models.CharField(max_length=50, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="purchase_orders")
    order_date = models.DateField()
    department = models.CharField(max_length=100, blank=True, default="")
    currency = models.CharField(max_length=6, default="INR")
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=PurchaseOrderStatus.choices, default=PurchaseOrderStatus.OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "purchase_orders"
        ordering = ["-order_date"]
        indexes = [
            models.Index(fields=["po_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.po_number


class PurchaseOrderLineItem(UUIDTimeStampedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="line_items")
    line_no = models.PositiveIntegerField()
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "purchase_order_line_items"
        ordering = ["line_no"]

    def __str__(self):
        return f"{self.purchase_order.po_number} - line {self.line_no}"


class GoodsReceiptStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    COMPLETED = "COMPLETED", "Completed"


class GoodsReceipt(UUIDTimeStampedModel):
    grn_number = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="goods_receipts")
    received_date = models.DateField()
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=GoodsReceiptStatus.choices, default=GoodsReceiptStatus.COMPLETED)
    remarks = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "goods_receipts"
        ordering = ["-received_date"]

    def __str__(self):
        return self.grn_number


class GoodsReceiptLineItem(UUIDTimeStampedModel):
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="line_items")
    po_line_item = models.ForeignKey(PurchaseOrderLineItem, on_delete=models.CASCADE, related_name="receipt_lines")
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "goods_receipt_line_items"
