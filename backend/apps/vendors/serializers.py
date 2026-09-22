from django.db.models import Count, Q, Sum
from rest_framework import serializers

from apps.vendors.models import Vendor, VendorBankDetails, VendorDocument

PAYABLE_STATUSES = ["PENDING_APPROVAL", "APPROVED", "PAYMENT_PENDING"]


class VendorBankDetailsSerializer(serializers.ModelSerializer):
    masked_account_number = serializers.CharField(read_only=True)

    class Meta:
        model = VendorBankDetails
        fields = ["id", "account_holder_name", "masked_account_number", "bank_name", "ifsc_code", "branch", "is_verified"]


class VendorBankDetailsWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorBankDetails
        fields = ["account_holder_name", "account_number", "bank_name", "ifsc_code", "branch"]


class VendorDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source="uploaded_by.display_name", read_only=True, default=None)

    class Meta:
        model = VendorDocument
        fields = ["id", "file_url", "document_type", "uploaded_by_name", "created_at"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url


class VendorListSerializer(serializers.ModelSerializer):
    total_invoices = serializers.IntegerField(read_only=True)
    total_payable = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "code",
            "gstin",
            "email",
            "phone",
            "status",
            "is_active",
            "category",
            "total_invoices",
            "total_payable",
        ]

    @staticmethod
    def annotate_queryset(qs):
        return qs.annotate(
            total_invoices=Count("invoices", distinct=True),
            total_payable=Sum("invoices__total_amount", filter=Q(invoices__status__in=PAYABLE_STATUSES)),
        )


class VendorDetailSerializer(serializers.ModelSerializer):
    bank_details = VendorBankDetailsSerializer(read_only=True)
    documents = VendorDocumentSerializer(many=True, read_only=True)
    total_invoices = serializers.SerializerMethodField()
    total_payable = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.display_name", read_only=True, default=None)

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "code",
            "gstin",
            "pan",
            "email",
            "phone",
            "contact_person",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "pincode",
            "country",
            "category",
            "department",
            "payment_terms_days",
            "status",
            "is_active",
            "bank_details",
            "documents",
            "total_invoices",
            "total_payable",
            "total_paid",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = ["status", "is_active"]

    def get_total_invoices(self, obj):
        return obj.invoices.count()

    def get_total_payable(self, obj):
        return obj.invoices.filter(status__in=PAYABLE_STATUSES).aggregate(s=Sum("total_amount"))["s"] or 0

    def get_total_paid(self, obj):
        return obj.invoices.filter(status="PAID").aggregate(s=Sum("total_amount"))["s"] or 0


class VendorWriteSerializer(serializers.ModelSerializer):
    bank_details = VendorBankDetailsWriteSerializer(required=False)

    class Meta:
        model = Vendor
        fields = [
            "name",
            "code",
            "gstin",
            "pan",
            "email",
            "phone",
            "contact_person",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "pincode",
            "country",
            "category",
            "department",
            "payment_terms_days",
            "bank_details",
        ]

    def create(self, validated_data):
        bank_data = validated_data.pop("bank_details", None)
        vendor = Vendor.objects.create(**validated_data)
        if bank_data:
            VendorBankDetails.objects.create(vendor=vendor, **bank_data)
        return vendor

    def update(self, instance, validated_data):
        bank_data = validated_data.pop("bank_details", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if bank_data:
            VendorBankDetails.objects.update_or_create(vendor=instance, defaults=bank_data)
        return instance
