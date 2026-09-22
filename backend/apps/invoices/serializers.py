from rest_framework import serializers

from apps.invoices.models import (
    Invoice,
    InvoiceDocument,
    InvoiceException,
    InvoiceExtractedField,
    InvoiceLineItem,
)
from apps.purchase_orders.models import PurchaseOrder
from apps.vendors.models import Vendor


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = ["id", "line_no", "description", "quantity", "unit_price", "tax_amount", "amount"]


class InvoiceDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceDocument
        fields = ["id", "file_url", "file_name", "file_type", "file_size", "page_count", "is_primary", "created_at"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url


class InvoiceExtractedFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceExtractedField
        fields = ["id", "field_name", "value", "confidence", "is_mandatory", "is_edited", "validation_status"]


class InvoiceExceptionSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.display_name", read_only=True, default=None)
    resolved_by_name = serializers.CharField(source="resolved_by.display_name", read_only=True, default=None)
    exception_type_display = serializers.CharField(source="get_exception_type_display", read_only=True)

    class Meta:
        model = InvoiceException
        fields = [
            "id",
            "exception_type",
            "exception_type_display",
            "severity",
            "description",
            "status",
            "assigned_to",
            "assigned_to_name",
            "resolved_by",
            "resolved_by_name",
            "resolution_comment",
            "resolved_at",
            "created_at",
        ]
        read_only_fields = ["resolved_by", "resolved_at"]


class ExceptionCenterSerializer(InvoiceExceptionSerializer):
    """Flattened, cross-invoice view used by the Exception Center table."""

    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    vendor_name = serializers.CharField(source="invoice.vendor.name", read_only=True, default=None)
    invoice_total = serializers.DecimalField(source="invoice.total_amount", max_digits=14, decimal_places=2, read_only=True, default=None)

    class Meta(InvoiceExceptionSerializer.Meta):
        fields = InvoiceExceptionSerializer.Meta.fields + ["invoice", "invoice_number", "vendor_name", "invoice_total"]


class InvoiceListSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True, default=None)
    open_exception_count = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "vendor",
            "vendor_name",
            "purchase_order",
            "invoice_date",
            "due_date",
            "total_amount",
            "currency",
            "status",
            "ocr_confidence",
            "ocr_confidence_level",
            "po_match_status",
            "department",
            "open_exception_count",
            "created_at",
        ]

    def get_open_exception_count(self, obj):
        return obj.exceptions.filter(status="OPEN").count()


class InvoiceDetailSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True, default=None)
    po_number = serializers.CharField(source="purchase_order.po_number", read_only=True, default=None)
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    documents = InvoiceDocumentSerializer(many=True, read_only=True, context={})
    extracted_fields = InvoiceExtractedFieldSerializer(many=True, read_only=True)
    exceptions = InvoiceExceptionSerializer(many=True, read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.display_name", read_only=True, default=None)
    has_payment_request = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "has_payment_request",
            "invoice_number",
            "vendor",
            "vendor_name",
            "vendor_name_raw",
            "purchase_order",
            "po_number",
            "po_number_raw",
            "gstin",
            "invoice_date",
            "due_date",
            "currency",
            "subtotal",
            "tax_amount",
            "cgst",
            "sgst",
            "igst",
            "discount",
            "total_amount",
            "payment_terms",
            "department",
            "status",
            "ocr_provider",
            "ocr_confidence",
            "ocr_confidence_level",
            "po_match_status",
            "line_items",
            "documents",
            "extracted_fields",
            "exceptions",
            "uploaded_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "ocr_provider",
            "ocr_confidence",
            "ocr_confidence_level",
            "po_match_status",
        ]

    def to_representation(self, instance):
        request = self.context.get("request")
        self.fields["documents"] = InvoiceDocumentSerializer(many=True, read_only=True, context={"request": request})
        return super().to_representation(instance)

    def get_has_payment_request(self, obj):
        return hasattr(obj, "payment_request")


class InvoiceUpdateSerializer(serializers.ModelSerializer):
    """Used for manual correction of header fields after OCR review."""

    class Meta:
        model = Invoice
        fields = [
            "invoice_number",
            "vendor",
            "purchase_order",
            "gstin",
            "invoice_date",
            "due_date",
            "currency",
            "subtotal",
            "tax_amount",
            "cgst",
            "sgst",
            "igst",
            "discount",
            "total_amount",
            "payment_terms",
            "department",
        ]


class ExtractedFieldUpdateItemSerializer(serializers.Serializer):
    field_name = serializers.CharField()
    value = serializers.CharField(allow_blank=True)


class ExtractedFieldBulkUpdateSerializer(serializers.Serializer):
    fields = ExtractedFieldUpdateItemSerializer(many=True)
