from django.contrib import admin

from apps.invoices.models import (
    Invoice,
    InvoiceDocument,
    InvoiceException,
    InvoiceExtractedField,
    InvoiceLineItem,
)


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0


class InvoiceDocumentInline(admin.TabularInline):
    model = InvoiceDocument
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "vendor", "total_amount", "status", "ocr_confidence_level", "created_at")
    list_filter = ("status", "ocr_confidence_level")
    search_fields = ("invoice_number", "vendor__name", "gstin")
    inlines = [InvoiceLineItemInline, InvoiceDocumentInline]


@admin.register(InvoiceException)
class InvoiceExceptionAdmin(admin.ModelAdmin):
    list_display = ("invoice", "exception_type", "severity", "status", "created_at")
    list_filter = ("exception_type", "severity", "status")


@admin.register(InvoiceExtractedField)
class InvoiceExtractedFieldAdmin(admin.ModelAdmin):
    list_display = ("invoice", "field_name", "value", "confidence", "validation_status")
    list_filter = ("field_name", "validation_status")
