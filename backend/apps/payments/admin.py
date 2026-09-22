from django.contrib import admin

from apps.payments.models import Payment, PaymentRequest


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ("request_number", "invoice", "vendor", "amount", "status", "due_date")
    list_filter = ("status", "method")
    search_fields = ("request_number", "vendor__name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_request", "status", "transaction_ref", "payment_date")
    list_filter = ("status",)
