"""Shared invoice-ingestion logic.

Both the manual upload endpoint (apps/invoices/views.py::InvoiceUploadView)
and the email-ingestion management command
(apps/invoices/management/commands/ingest_invoice_emails.py) create an
Invoice from a raw file the same way -- store it, run it through OCR,
validation, and PO matching. Keeping that in one function means both entry
points behave identically and a bug fix only needs to happen once.
"""

from django.core.files.storage import default_storage

from apps.audit_logs.services import log_action
from apps.invoices.matching import match_invoice_to_po
from apps.invoices.models import Invoice, InvoiceDocument, InvoiceStatus
from apps.invoices.uploads import validate_upload
from apps.invoices.validation import run_validation
from apps.ocr.service import run_ocr_pipeline


def ingest_invoice_file(uploaded_file, department="", uploaded_by=None, source="Upload"):
    """Create an Invoice from a single file and run the full OCR ->
    validation -> PO-matching pipeline against it. Raises the same
    ValidationError as validate_upload() for a rejected file type/size --
    callers are expected to catch that per-file, since one bad file
    shouldn't stop the rest of a batch."""
    ext, content_type = validate_upload(uploaded_file)

    invoice = Invoice.objects.create(
        status=InvoiceStatus.UPLOADED,
        department=department,
        uploaded_by=uploaded_by,
    )
    doc = InvoiceDocument.objects.create(
        invoice=invoice,
        file=uploaded_file,
        file_name=uploaded_file.name,
        file_type=ext.lstrip("."),
        file_size=uploaded_file.size,
        is_primary=True,
        uploaded_by=uploaded_by,
    )
    log_action(
        action="UPLOAD",
        entity_type="Invoice",
        entity_id=invoice.id,
        description=f"{source}: uploaded file '{uploaded_file.name}' ({uploaded_file.size} bytes)",
        user=uploaded_by,
    )

    try:
        file_path = doc.file.path
    except NotImplementedError:
        file_path = default_storage.path(doc.file.name)

    try:
        run_ocr_pipeline(invoice, file_path, content_type)
        run_validation(invoice)
        match_invoice_to_po(invoice)
    except Exception as exc:
        invoice.status = InvoiceStatus.EXCEPTION
        invoice.save(update_fields=["status"])
        log_action(
            action="OCR_PROCESS",
            entity_type="Invoice",
            entity_id=invoice.id,
            description=f"OCR processing failed: {exc}",
            user=uploaded_by,
        )

    return invoice
