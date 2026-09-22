"""Validation engine.

Runs independently of OCR extraction (apps/ocr) -- it only looks at the
current state of an Invoice record (whether those values came from OCR or
were manually corrected on the review screen) and raises/clears
InvoiceException rows accordingly. Nothing here talks to an OCR provider or
a parsing regex; it only enforces business rules.
"""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from apps.invoices.models import (
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    Invoice,
    InvoiceException,
    InvoiceExtractedField,
    InvoiceStatus,
)
from apps.ocr.extraction import GSTIN_PATTERN

AMOUNT_TOLERANCE = Decimal("1.00")
DUPLICATE_DATE_WINDOW_DAYS = 3
LOW_CONFIDENCE_THRESHOLD = 60

# Exception types this engine owns end-to-end: every run recomputes exactly
# this set (open ones it no longer finds are auto-cleared; user-resolved
# ones are left alone since their status won't be OPEN).
AUTO_MANAGED_TYPES = [
    ExceptionType.MISSING_VENDOR,
    ExceptionType.MISSING_MANDATORY_FIELD,
    ExceptionType.INVALID_GSTIN,
    ExceptionType.DUPLICATE_INVOICE,
    ExceptionType.AMOUNT_MISMATCH,
    ExceptionType.MISSING_PO,
    ExceptionType.OCR_LOW_CONFIDENCE,
]


def _upsert_exception(invoice, exception_type, severity, description, assignee):
    obj, created = InvoiceException.objects.get_or_create(
        invoice=invoice,
        exception_type=exception_type,
        status=ExceptionStatus.OPEN,
        defaults=dict(severity=severity, description=description, assigned_to=assignee),
    )
    if not created and (obj.description != description or obj.severity != severity):
        obj.description = description
        obj.severity = severity
        obj.save(update_fields=["description", "severity"])
    return obj


def _maybe_raise(invoice, exception_type, severity, description, assignee, still_open_types):
    """Create/refresh an exception unless a human has already made a
    terminal decision (resolved/rejected/overridden) on this exact
    exception type for this invoice -- re-validation must not silently
    reopen something a reviewer already disposed of."""
    still_open_types.add(exception_type)
    already_decided = InvoiceException.objects.filter(
        invoice=invoice,
        exception_type=exception_type,
        status__in=[ExceptionStatus.RESOLVED, ExceptionStatus.REJECTED, ExceptionStatus.OVERRIDDEN],
    ).exists()
    if already_decided:
        return None
    return _upsert_exception(invoice, exception_type, severity, description, assignee)


def _clear_stale(invoice, still_open_types):
    """Auto-resolve OPEN exceptions of auto-managed types that this run no
    longer finds a reason for (e.g. the user fixed the underlying field)."""
    stale = InvoiceException.objects.filter(
        invoice=invoice, status=ExceptionStatus.OPEN, exception_type__in=AUTO_MANAGED_TYPES
    ).exclude(exception_type__in=still_open_types)
    for exc in stale:
        exc.status = ExceptionStatus.RESOLVED
        exc.resolution_comment = "Automatically cleared: underlying condition no longer present."
        exc.resolved_at = timezone.now()
        exc.save(update_fields=["status", "resolution_comment", "resolved_at"])


def check_mandatory_fields(invoice):
    missing = []
    if not invoice.vendor_id and not invoice.vendor_name_raw:
        missing.append("vendor name")
    if not invoice.invoice_number:
        missing.append("invoice number")
    if not invoice.invoice_date:
        missing.append("invoice date")
    if invoice.total_amount is None:
        missing.append("total amount")
    if not invoice.gstin:
        missing.append("GSTIN")
    return missing


def check_gstin_format(invoice):
    if not invoice.gstin:
        return None  # handled as a missing-mandatory-field case instead
    if not GSTIN_PATTERN.fullmatch(invoice.gstin.strip().upper()):
        return f"'{invoice.gstin}' does not match the standard 15-character GSTIN format (e.g. 27AAACB1234C1Z5)."
    return None


def check_amount_consistency(invoice):
    if invoice.total_amount is None or invoice.subtotal is None:
        return None
    tax = invoice.tax_amount or Decimal("0")
    discount = invoice.discount or Decimal("0")
    expected = invoice.subtotal + tax - discount
    diff = abs(expected - invoice.total_amount)
    if diff > AMOUNT_TOLERANCE:
        return (
            f"Subtotal (₹{invoice.subtotal}) + tax (₹{tax}) − discount (₹{discount}) = ₹{expected}, "
            f"which does not match the extracted total of ₹{invoice.total_amount} (difference ₹{diff})."
        )
    return None


def check_duplicates(invoice):
    """Returns (severity, description) or None."""
    if not invoice.vendor_id:
        return None

    exact = (
        Invoice.objects.filter(vendor_id=invoice.vendor_id, invoice_number=invoice.invoice_number)
        .exclude(id=invoice.id)
        .exclude(invoice_number="")
        .first()
    )
    if exact and invoice.invoice_number:
        return (
            ExceptionSeverity.HIGH,
            f"Duplicate suspected: invoice number '{invoice.invoice_number}' already exists for this vendor "
            f"(invoice {exact.id}, uploaded {exact.created_at.date()}).",
        )

    if invoice.total_amount is not None and invoice.invoice_date:
        window_start = invoice.invoice_date - timedelta(days=DUPLICATE_DATE_WINDOW_DAYS)
        window_end = invoice.invoice_date + timedelta(days=DUPLICATE_DATE_WINDOW_DAYS)
        near = (
            Invoice.objects.filter(
                vendor_id=invoice.vendor_id,
                total_amount=invoice.total_amount,
                invoice_date__range=(window_start, window_end),
            )
            .exclude(id=invoice.id)
            .first()
        )
        if near:
            return (
                ExceptionSeverity.MEDIUM,
                f"Duplicate suspected: same vendor, same amount (₹{invoice.total_amount}), and invoice date "
                f"within {DUPLICATE_DATE_WINDOW_DAYS} days of invoice {near.id} ({near.invoice_date}).",
            )
    return None


def run_validation(invoice):
    still_open_types = set()

    missing = check_mandatory_fields(invoice)
    if missing:
        _maybe_raise(
            invoice,
            ExceptionType.MISSING_MANDATORY_FIELD,
            ExceptionSeverity.CRITICAL if "total amount" in missing or "vendor name" in missing else ExceptionSeverity.HIGH,
            f"Missing mandatory field(s): {', '.join(missing)}.",
            invoice.uploaded_by,
            still_open_types,
        )

    if not invoice.vendor_id and invoice.vendor_name_raw:
        _maybe_raise(
            invoice,
            ExceptionType.MISSING_VENDOR,
            ExceptionSeverity.HIGH,
            f"Extracted vendor name '{invoice.vendor_name_raw}' does not match any vendor in the vendor master.",
            invoice.uploaded_by,
            still_open_types,
        )

    gstin_error = check_gstin_format(invoice)
    if gstin_error:
        _maybe_raise(invoice, ExceptionType.INVALID_GSTIN, ExceptionSeverity.HIGH, gstin_error, invoice.uploaded_by, still_open_types)

    amount_error = check_amount_consistency(invoice)
    if amount_error:
        _maybe_raise(
            invoice, ExceptionType.AMOUNT_MISMATCH, ExceptionSeverity.MEDIUM, amount_error, invoice.uploaded_by, still_open_types
        )

    duplicate = check_duplicates(invoice)
    if duplicate:
        severity, description = duplicate
        _maybe_raise(invoice, ExceptionType.DUPLICATE_INVOICE, severity, description, invoice.uploaded_by, still_open_types)

    if not invoice.purchase_order_id and not invoice.po_number_raw:
        _maybe_raise(
            invoice,
            ExceptionType.MISSING_PO,
            ExceptionSeverity.LOW,
            "No purchase order number was found or linked for this invoice.",
            invoice.uploaded_by,
            still_open_types,
        )

    if invoice.ocr_confidence is not None and invoice.ocr_confidence < LOW_CONFIDENCE_THRESHOLD:
        _maybe_raise(
            invoice,
            ExceptionType.OCR_LOW_CONFIDENCE,
            ExceptionSeverity.MEDIUM,
            f"Overall OCR confidence ({invoice.ocr_confidence}%) is below the {LOW_CONFIDENCE_THRESHOLD}% acceptance threshold.",
            invoice.uploaded_by,
            still_open_types,
        )

    _clear_stale(invoice, still_open_types)

    # Reflect per-field validation status for the review screen.
    invalid_fields = set()
    if gstin_error:
        invalid_fields.add("gstin")
    if amount_error:
        invalid_fields.add("total_amount")
    for f in invoice.extracted_fields.all():
        if not f.value and f.is_mandatory:
            f.validation_status = "INVALID"
        elif f.field_name in invalid_fields:
            f.validation_status = "INVALID"
        else:
            f.validation_status = "VALID"
        f.save(update_fields=["validation_status"])

    has_open_exceptions = invoice.exceptions.filter(status=ExceptionStatus.OPEN).exists()
    invoice.status = InvoiceStatus.EXCEPTION if has_open_exceptions else InvoiceStatus.VALIDATED
    invoice.save(update_fields=["status"])

    from apps.audit_logs.services import log_action

    log_action(
        action="VALIDATE",
        entity_type="Invoice",
        entity_id=invoice.id,
        description=f"Validation run: {'exceptions raised' if has_open_exceptions else 'passed cleanly'}",
    )

    return invoice
