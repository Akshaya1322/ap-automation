from django.urls import path

from apps.reports.views import (
    AgingReportView,
    AuditSummaryReportView,
    ExceptionReportView,
    GstReportView,
    InvoiceStatusReportView,
    PaymentReportView,
    VendorReportView,
)

urlpatterns = [
    path("aging/", AgingReportView.as_view(), name="report-aging"),
    path("invoices/", InvoiceStatusReportView.as_view(), name="report-invoices"),
    path("exceptions/", ExceptionReportView.as_view(), name="report-exceptions"),
    path("vendors/", VendorReportView.as_view(), name="report-vendors"),
    path("payments/", PaymentReportView.as_view(), name="report-payments"),
    path("gst/", GstReportView.as_view(), name="report-gst"),
    path("audit/", AuditSummaryReportView.as_view(), name="report-audit"),
]
