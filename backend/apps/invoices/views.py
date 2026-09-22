import re
from datetime import datetime

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.services import log_action
from apps.authentication.permissions import CanProcessInvoices
from apps.invoices.filters import InvoiceFilter
from apps.invoices.models import Invoice, InvoiceExtractedField, InvoiceStatus
from apps.invoices.serializers import (
    ExtractedFieldBulkUpdateSerializer,
    InvoiceDetailSerializer,
    InvoiceListSerializer,
    InvoiceUpdateSerializer,
)
from apps.invoices.matching import match_invoice_to_po
from apps.invoices.services import ingest_invoice_file
from apps.invoices.validation import run_validation


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related("vendor", "purchase_order").prefetch_related(
        "line_items", "documents", "extracted_fields", "exceptions"
    )
    filterset_class = InvoiceFilter
    search_fields = ["invoice_number", "vendor__name", "po_number_raw", "gstin"]
    ordering_fields = ["created_at", "total_amount", "invoice_date", "due_date", "status"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return InvoiceListSerializer
        if self.action in ("update", "partial_update"):
            return InvoiceUpdateSerializer
        return InvoiceDetailSerializer

    def get_permissions(self):
        if self.action in (
            "update",
            "partial_update",
            "destroy",
            "update_extracted_fields",
            "validate_invoice",
            "match_po",
            "submit_for_approval",
        ):
            return [IsAuthenticated(), CanProcessInvoices()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Invoices are created via POST /api/invoices/upload/, not this endpoint."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def perform_update(self, serializer):
        previous = InvoiceDetailSerializer(self.get_object(), context=self.get_serializer_context()).data
        instance = serializer.save()
        run_validation(instance)
        log_action(
            action="FIELD_EDIT",
            entity_type="Invoice",
            entity_id=instance.id,
            description=f"Invoice {instance.invoice_number} header fields updated",
            previous_value={k: previous.get(k) for k in serializer.validated_data.keys()},
            new_value={k: str(v) for k, v in serializer.validated_data.items()},
        )

    @action(detail=True, methods=["post"], url_path="extracted-fields")
    def update_extracted_fields(self, request, pk=None):
        invoice = self.get_object()
        serializer = ExtractedFieldBulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = []
        for item in serializer.validated_data["fields"]:
            field_obj, _created = InvoiceExtractedField.objects.get_or_create(
                invoice=invoice, field_name=item["field_name"], defaults={"confidence": 100, "is_mandatory": False}
            )
            previous_value = field_obj.value
            field_obj.value = item["value"]
            field_obj.is_edited = True
            field_obj.confidence = 100  # human-confirmed
            field_obj.validation_status = "PENDING"
            field_obj.save(update_fields=["value", "is_edited", "confidence", "validation_status"])
            updated.append(field_obj.field_name)

            if previous_value != item["value"]:
                log_action(
                    action="FIELD_EDIT",
                    entity_type="InvoiceExtractedField",
                    entity_id=field_obj.id,
                    description=f"Field '{field_obj.field_name}' manually corrected on invoice {invoice.invoice_number}",
                    previous_value=previous_value,
                    new_value=item["value"],
                )

            self._sync_field_to_invoice(invoice, field_obj.field_name, item["value"])

        invoice.save()
        run_validation(invoice)
        invoice.refresh_from_db()
        return Response(InvoiceDetailSerializer(invoice, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="validate")
    def validate_invoice(self, request, pk=None):
        invoice = self.get_object()
        run_validation(invoice)
        invoice.refresh_from_db()
        return Response(InvoiceDetailSerializer(invoice, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="match-po")
    def match_po(self, request, pk=None):
        invoice = self.get_object()
        result = match_invoice_to_po(invoice)
        return Response(result)

    @action(detail=True, methods=["post"], url_path="submit-for-approval")
    def submit_for_approval(self, request, pk=None):
        from apps.approvals.services import create_workflow
        from apps.invoices.models import InvoiceStatus

        invoice = self.get_object()
        if invoice.status != InvoiceStatus.VALIDATED:
            return Response(
                {"detail": "Only validated invoices with no open exceptions can be submitted for approval."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if invoice.exceptions.filter(status="OPEN").exists():
            return Response(
                {"detail": "Resolve, reject, or override all open exceptions before submitting for approval."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        create_workflow(invoice)
        invoice.refresh_from_db()
        return Response(InvoiceDetailSerializer(invoice, context={"request": request}).data)

    DATE_FORMATS = (
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%d-%b-%Y", "%d %b %Y", "%d-%B-%Y", "%d %B %Y",
        "%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y",
    )

    @classmethod
    def _parse_amount(cls, value):
        cleaned = re.sub(r"[^\d.-]", "", value)
        if not cleaned:
            return None
        return float(cleaned)

    @classmethod
    def _parse_date(cls, value):
        value = value.strip()
        for fmt in cls.DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def _sync_field_to_invoice(self, invoice, field_name, value):
        mapping = {
            "invoice_number": "invoice_number",
            "gstin": "gstin",
            "vendor_name": "vendor_name_raw",
            "po_number": "po_number_raw",
            "payment_terms": "payment_terms",
        }
        decimal_fields = {"total_amount", "subtotal", "tax_amount"}
        date_fields = {"invoice_date", "due_date"}

        if field_name in mapping:
            setattr(invoice, mapping[field_name], value)
        elif field_name in decimal_fields:
            try:
                setattr(invoice, field_name, self._parse_amount(value) if value else None)
            except ValueError:
                pass
        elif field_name in date_fields:
            setattr(invoice, field_name, self._parse_date(value) if value else None)


class InvoiceUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, CanProcessInvoices]

    def post(self, request):
        files = request.FILES.getlist("files") or ([request.FILES["file"]] if "file" in request.FILES else [])
        if not files:
            return Response({"detail": "No files provided. Attach one or more files under 'files'."}, status=400)

        department = request.data.get("department", "")
        created_invoices = []
        errors = []

        for f in files:
            try:
                invoice = ingest_invoice_file(f, department=department, uploaded_by=request.user, source="Manual upload")
            except Exception as exc:
                errors.append({"file": f.name, "error": str(exc.detail[0]) if hasattr(exc, "detail") else str(exc)})
                continue

            created_invoices.append(invoice)

        serialized = InvoiceDetailSerializer(created_invoices, many=True, context={"request": request}).data
        response_status = status.HTTP_201_CREATED if created_invoices else status.HTTP_400_BAD_REQUEST
        return Response({"created": serialized, "errors": errors}, status=response_status)
