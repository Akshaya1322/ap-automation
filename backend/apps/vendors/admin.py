from django.contrib import admin

from apps.vendors.models import Vendor, VendorBankDetails, VendorDocument


class VendorBankDetailsInline(admin.StackedInline):
    model = VendorBankDetails
    extra = 0


class VendorDocumentInline(admin.TabularInline):
    model = VendorDocument
    extra = 0


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "gstin", "status", "is_active", "created_at")
    list_filter = ("status", "is_active", "category")
    search_fields = ("name", "code", "gstin", "email")
    inlines = [VendorBankDetailsInline, VendorDocumentInline]


@admin.register(VendorBankDetails)
class VendorBankDetailsAdmin(admin.ModelAdmin):
    list_display = ("vendor", "bank_name", "masked_account_number", "is_verified")
