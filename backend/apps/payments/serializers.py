from rest_framework import serializers

from apps.payments.models import Payment, PaymentRequest


class PaymentSerializer(serializers.ModelSerializer):
    advice_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "transaction_ref",
            "payment_date",
            "status",
            "bank_response",
            "advice_generated",
            "advice_file_url",
        ]

    def get_advice_file_url(self, obj):
        request = self.context.get("request")
        if not obj.advice_file:
            return None
        return request.build_absolute_uri(obj.advice_file.url) if request else obj.advice_file.url


class PaymentRequestListSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    payment_status = serializers.CharField(source="payment.status", read_only=True, default=None)

    class Meta:
        model = PaymentRequest
        fields = [
            "id",
            "request_number",
            "invoice",
            "invoice_number",
            "vendor",
            "vendor_name",
            "amount",
            "currency",
            "method",
            "requested_date",
            "due_date",
            "status",
            "payment_status",
        ]


class PaymentRequestDetailSerializer(PaymentRequestListSerializer):
    payment = PaymentSerializer(read_only=True)
    requested_by_name = serializers.CharField(source="requested_by.display_name", read_only=True, default=None)

    class Meta(PaymentRequestListSerializer.Meta):
        fields = PaymentRequestListSerializer.Meta.fields + ["payment", "requested_by_name", "created_at"]


class PaymentRequestCreateSerializer(serializers.Serializer):
    invoice = serializers.UUIDField()
    method = serializers.ChoiceField(choices=["BANK_TRANSFER", "CHEQUE", "UPI", "CARD"], default="BANK_TRANSFER")
