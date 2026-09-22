from datetime import date

from django.db.models import Avg, Count, Sum

from apps.invoices.models import Invoice, InvoiceException
from apps.payments.models import PaymentRequest

OUTSTANDING_STATUSES = [
    "UPLOADED",
    "PROCESSING",
    "EXTRACTED",
    "VALIDATED",
    "EXCEPTION",
    "PENDING_APPROVAL",
    "APPROVED",
    "PAYMENT_PENDING",
]

AGING_BUCKETS = [
    ("0-30", 0, 30),
    ("31-60", 31, 60),
    ("61-90", 61, 90),
    ("91-120", 91, 120),
    ("120+", 121, None),
]


def ap_aging_report(invoice_qs):
    outstanding = invoice_qs.filter(status__in=OUTSTANDING_STATUSES, total_amount__isnull=False)
    today = date.today()
    buckets = {label: {"label": label, "count": 0, "amount": 0} for label, _, _ in AGING_BUCKETS}
    total_amount = 0

    for due_date_val, invoice_date_val, total_amount_val in outstanding.values_list("due_date", "invoice_date", "total_amount"):
        reference_date = due_date_val or invoice_date_val
        if not reference_date:
            continue
        days_overdue = max((today - reference_date).days, 0)
        for label, lo, hi in AGING_BUCKETS:
            if days_overdue >= lo and (hi is None or days_overdue <= hi):
                buckets[label]["count"] += 1
                buckets[label]["amount"] += float(total_amount_val)
                total_amount += float(total_amount_val)
                break

    result = []
    for label, _, _ in AGING_BUCKETS:
        b = buckets[label]
        b["percentage"] = round((b["amount"] / total_amount) * 100, 1) if total_amount else 0
        result.append(b)
    return {"buckets": result, "total_amount": total_amount}


def invoice_status_report(invoice_qs):
    rows = invoice_qs.values("status").annotate(count=Count("id"), amount=Sum("total_amount")).order_by("-count")
    return [{"status": r["status"], "count": r["count"], "amount": float(r["amount"] or 0)} for r in rows]


def exception_report(invoice_qs):
    exceptions = InvoiceException.objects.filter(invoice__in=invoice_qs).select_related("invoice", "invoice__vendor")
    by_type = exceptions.values("exception_type").annotate(count=Count("id")).order_by("-count")
    by_severity = exceptions.values("severity").annotate(count=Count("id")).order_by("-count")
    by_status = exceptions.values("status").annotate(count=Count("id")).order_by("-count")
    return {
        "by_type": list(by_type),
        "by_severity": list(by_severity),
        "by_status": list(by_status),
        "total": exceptions.count(),
    }


def vendor_report(invoice_qs):
    rows = (
        invoice_qs.exclude(vendor__isnull=True)
        .values("vendor__id", "vendor__name")
        .annotate(invoice_count=Count("id"), total_amount=Sum("total_amount"))
        .order_by("-total_amount")
    )
    return [
        {
            "vendor_id": str(r["vendor__id"]),
            "vendor_name": r["vendor__name"],
            "invoice_count": r["invoice_count"],
            "total_amount": float(r["total_amount"] or 0),
        }
        for r in rows
    ]


def payment_report(invoice_qs):
    prs = PaymentRequest.objects.filter(invoice__in=invoice_qs)
    rows = prs.values("status").annotate(count=Count("id"), amount=Sum("amount")).order_by("-count")
    return [{"status": r["status"], "count": r["count"], "amount": float(r["amount"] or 0)} for r in rows]


def gst_report(invoice_qs):
    agg = invoice_qs.aggregate(
        total_taxable=Sum("subtotal"),
        total_cgst=Sum("cgst"),
        total_sgst=Sum("sgst"),
        total_igst=Sum("igst"),
        total_tax=Sum("tax_amount"),
    )
    by_vendor = (
        invoice_qs.exclude(vendor__isnull=True)
        .values("vendor__name", "gstin")
        .annotate(taxable=Sum("subtotal"), tax=Sum("tax_amount"))
        .order_by("-tax")[:20]
    )
    return {
        "summary": {k: float(v or 0) for k, v in agg.items()},
        "by_vendor": [
            {"vendor_name": r["vendor__name"], "gstin": r["gstin"], "taxable": float(r["taxable"] or 0), "tax": float(r["tax"] or 0)}
            for r in by_vendor
        ],
    }


def dashboard_kpis(invoice_qs):
    today = date.today()
    total_invoices = invoice_qs.count()
    pending_approvals = invoice_qs.filter(status="PENDING_APPROVAL").count()
    open_exceptions = InvoiceException.objects.filter(invoice__in=invoice_qs, status="OPEN").count()
    approved = invoice_qs.filter(status__in=["APPROVED", "PAYMENT_PENDING", "PAID"]).count()
    total_payable = invoice_qs.filter(status__in=["APPROVED", "PAYMENT_PENDING"]).aggregate(s=Sum("total_amount"))["s"] or 0
    overdue = invoice_qs.filter(
        status__in=OUTSTANDING_STATUSES, due_date__lt=today, total_amount__isnull=False
    ).aggregate(s=Sum("total_amount"))["s"] or 0
    ocr_accuracy = invoice_qs.filter(ocr_confidence__isnull=False).aggregate(a=Avg("ocr_confidence"))["a"] or 0

    processed = invoice_qs.filter(status__in=["APPROVED", "PAID", "PAYMENT_PENDING", "REJECTED"])
    durations = [
        (updated - created).total_seconds() / 3600
        for created, updated in processed.values_list("created_at", "updated_at")
    ]
    avg_processing_hours = round(sum(durations) / len(durations), 1) if durations else 0

    return {
        "total_invoices": total_invoices,
        "pending_approvals": pending_approvals,
        "exceptions": open_exceptions,
        "approved_invoices": approved,
        "total_payable_amount": float(total_payable),
        "overdue_amount": float(overdue),
        "ocr_accuracy": round(ocr_accuracy, 1),
        "avg_processing_time_hours": avg_processing_hours,
    }
