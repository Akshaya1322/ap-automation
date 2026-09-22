"""Orchestrates the three OCR pipeline stages and persists the outcome:

  1. providers.py  -- raw text extraction (Tesseract or demo fallback)
  2. extraction.py -- field parsing (regex heuristics over raw text)
  3. (this module)  -- persistence + confidence aggregation

Validation of the parsed values (mandatory-field checks, GSTIN format,
amount arithmetic, duplicates) is intentionally NOT done here -- see
apps/invoices/validation.py, invoked separately by the /validate/ endpoint.
"""

import logging

from apps.invoices.utils import MANDATORY_FIELDS, confidence_level
from apps.ocr.extraction import parse_fields, parse_line_items
from apps.ocr.providers import get_ocr_provider

logger = logging.getLogger(__name__)

OPTIONAL_FIELDS = ["po_number", "subtotal", "tax_amount", "due_date"]
ALL_FIELDS = MANDATORY_FIELDS + OPTIONAL_FIELDS


def run_ocr_pipeline(invoice, file_path, content_type):
    from apps.invoices.models import InvoiceExtractedField, InvoiceLineItem, InvoiceStatus
    from apps.vendors.models import Vendor

    invoice.status = InvoiceStatus.PROCESSING
    invoice.save(update_fields=["status"])

    provider = get_ocr_provider()
    result = provider.extract(file_path, content_type)

    base_confidence = 15.0 if result.is_demo_fallback else (result.mean_confidence or 55.0)
    parsed = parse_fields(result.raw_text, base_confidence=base_confidence)

    invoice.ocr_provider = result.provider
    invoice.ocr_raw_text = result.raw_text

    InvoiceExtractedField.objects.filter(invoice=invoice).delete()
    mandatory_confidences = []

    for field_name in ALL_FIELDS:
        value, conf = parsed.get(field_name, ("", 0.0))
        conf = round(conf, 1)
        InvoiceExtractedField.objects.create(
            invoice=invoice,
            field_name=field_name,
            value=value,
            confidence=conf,
            is_mandatory=field_name in MANDATORY_FIELDS,
            validation_status="PENDING",
        )
        if field_name in MANDATORY_FIELDS and value:
            mandatory_confidences.append(conf)

    overall_confidence = round(sum(mandatory_confidences) / len(mandatory_confidences), 1) if mandatory_confidences else 0.0
    invoice.ocr_confidence = overall_confidence
    invoice.ocr_confidence_level = confidence_level(overall_confidence)

    # Prefill invoice header fields from parsed values (still editable by the user).
    if "invoice_number" in parsed:
        invoice.invoice_number = parsed["invoice_number"][0]
    if "gstin" in parsed:
        invoice.gstin = parsed["gstin"][0]
    if "invoice_date" in parsed:
        invoice.invoice_date = parsed["invoice_date"][0] or None
    if "due_date" in parsed:
        invoice.due_date = parsed["due_date"][0] or None
    if "total_amount" in parsed:
        invoice.total_amount = parsed["total_amount"][0] or None
    if "subtotal" in parsed:
        invoice.subtotal = parsed["subtotal"][0] or None
    if "tax_amount" in parsed:
        invoice.tax_amount = parsed["tax_amount"][0] or None
    if "po_number" in parsed:
        invoice.po_number_raw = parsed["po_number"][0]
    if "vendor_name" in parsed:
        invoice.vendor_name_raw = parsed["vendor_name"][0]
        vendor = Vendor.objects.filter(name__icontains=parsed["vendor_name"][0][:20]).first()
        if vendor:
            invoice.vendor = vendor

    if invoice.gstin:
        vendor_by_gstin = Vendor.objects.filter(gstin=invoice.gstin).first()
        if vendor_by_gstin:
            invoice.vendor = vendor_by_gstin

    invoice.status = InvoiceStatus.EXTRACTED
    invoice.save()

    InvoiceLineItem.objects.filter(invoice=invoice).delete()
    line_items = parse_line_items(result.raw_text)
    for item in line_items:
        InvoiceLineItem.objects.create(
            invoice=invoice,
            line_no=int(item["line_no"]),
            description=item["description"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            amount=item["amount"],
        )

    from apps.audit_logs.services import log_action

    log_action(
        action="OCR_PROCESS",
        entity_type="Invoice",
        entity_id=invoice.id,
        description=(
            f"OCR processed via {result.provider} "
            f"({'demo fallback' if result.is_demo_fallback else 'real OCR'}); "
            f"overall confidence {overall_confidence}%"
        ),
    )

    return invoice
