from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports import services
from apps.reports.csv_utils import csv_response
from apps.reports.filters import filtered_invoices


class AgingReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = services.ap_aging_report(filtered_invoices(request))
        if request.query_params.get("export") == "csv":
            return csv_response(
                "ap_aging_report.csv",
                ["Bucket", "Invoice Count", "Amount", "Percentage"],
                [[b["label"], b["count"], b["amount"], b["percentage"]] for b in data["buckets"]],
            )
        return Response(data)


class InvoiceStatusReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = services.invoice_status_report(filtered_invoices(request))
        if request.query_params.get("export") == "csv":
            return csv_response(
                "invoice_status_report.csv",
                ["Status", "Count", "Amount"],
                [[r["status"], r["count"], r["amount"]] for r in data],
            )
        return Response(data)


class ExceptionReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = services.exception_report(filtered_invoices(request))
        if request.query_params.get("export") == "csv":
            return csv_response(
                "exception_report.csv",
                ["Type", "Count"],
                [[r["exception_type"], r["count"]] for r in data["by_type"]],
            )
        return Response(data)


class VendorReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = services.vendor_report(filtered_invoices(request))
        if request.query_params.get("export") == "csv":
            return csv_response(
                "vendor_report.csv",
                ["Vendor", "Invoice Count", "Total Amount"],
                [[r["vendor_name"], r["invoice_count"], r["total_amount"]] for r in data],
            )
        return Response(data)


class PaymentReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = services.payment_report(filtered_invoices(request))
        if request.query_params.get("export") == "csv":
            return csv_response(
                "payment_report.csv",
                ["Status", "Count", "Amount"],
                [[r["status"], r["count"], r["amount"]] for r in data],
            )
        return Response(data)


class GstReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = services.gst_report(filtered_invoices(request))
        if request.query_params.get("export") == "csv":
            return csv_response(
                "gst_report.csv",
                ["Vendor", "GSTIN", "Taxable Amount", "Tax"],
                [[r["vendor_name"], r["gstin"], r["taxable"], r["tax"]] for r in data["by_vendor"]],
            )
        return Response(data)


class AuditSummaryReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Count

        from apps.audit_logs.models import AuditLog

        rows = AuditLog.objects.values("action").annotate(count=Count("id")).order_by("-count")
        data = list(rows)
        if request.query_params.get("export") == "csv":
            return csv_response("audit_summary_report.csv", ["Action", "Count"], [[r["action"], r["count"]] for r in data])
        return Response(data)
