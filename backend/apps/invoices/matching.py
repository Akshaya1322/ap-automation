"""PO matching engine: 2-way (PO vs Invoice) and 3-way (PO vs GRN vs
Invoice) comparison. Runs as an explicit pipeline step after validation,
producing a structured comparison plus a MATCHED/PARTIAL_MATCH/MISMATCH
verdict that both the API and the InvoiceException engine can act on.
"""

from decimal import Decimal

from apps.purchase_orders.models import GoodsReceiptLineItem, PurchaseOrder

AMOUNT_TOLERANCE_PCT = Decimal("0.02")  # 2%
QTY_TOLERANCE = Decimal("0.01")


def _within_tolerance(a, b, pct=AMOUNT_TOLERANCE_PCT):
    if a is None or b is None:
        return False
    a, b = Decimal(a), Decimal(b)
    if a == 0 and b == 0:
        return True
    base = max(abs(a), abs(b), Decimal("1"))
    return abs(a - b) / base <= pct


def try_auto_link_po(invoice):
    """If the invoice wasn't matched to a PO during OCR, attempt a lookup by
    the raw extracted PO number (+ vendor, when known)."""
    if invoice.purchase_order_id or not invoice.po_number_raw:
        return invoice.purchase_order

    qs = PurchaseOrder.objects.filter(po_number__iexact=invoice.po_number_raw.strip())
    if invoice.vendor_id:
        qs = qs.filter(vendor_id=invoice.vendor_id)
    po = qs.first()
    if po:
        invoice.purchase_order = po
        invoice.save(update_fields=["purchase_order"])
    return po


def _received_qty_by_po_line(po):
    totals = {}
    for grn_line in GoodsReceiptLineItem.objects.filter(po_line_item__purchase_order=po).select_related("po_line_item"):
        totals[grn_line.po_line_item_id] = totals.get(grn_line.po_line_item_id, Decimal("0")) + grn_line.quantity_received
    return totals


def match_invoice_to_po(invoice):
    po = try_auto_link_po(invoice)

    if not po:
        return {
            "status": "NOT_LINKED",
            "po": None,
            "grn": None,
            "header_comparison": [],
            "line_comparison": [],
        }

    header_comparison = [
        {
            "field": "Vendor",
            "po_value": po.vendor.name,
            "invoice_value": invoice.vendor.name if invoice.vendor else invoice.vendor_name_raw,
            "match": bool(invoice.vendor_id and invoice.vendor_id == po.vendor_id),
        },
        {
            "field": "Total Amount",
            "po_value": str(po.total_amount),
            "invoice_value": str(invoice.total_amount) if invoice.total_amount is not None else None,
            "match": _within_tolerance(po.total_amount, invoice.total_amount),
        },
        {
            "field": "Currency",
            "po_value": po.currency,
            "invoice_value": invoice.currency,
            "match": po.currency == invoice.currency,
        },
    ]

    grns = po.goods_receipts.all()
    received_by_line = _received_qty_by_po_line(po) if grns.exists() else None

    po_lines = list(po.line_items.order_by("line_no"))
    invoice_lines = list(invoice.line_items.order_by("line_no"))

    line_comparison = []
    max_lines = max(len(po_lines), len(invoice_lines))
    for i in range(max_lines):
        po_line = po_lines[i] if i < len(po_lines) else None
        inv_line = invoice_lines[i] if i < len(invoice_lines) else None

        qty_match = _within_tolerance(po_line.quantity if po_line else None, inv_line.quantity if inv_line else None, QTY_TOLERANCE)
        price_match = _within_tolerance(po_line.unit_price if po_line else None, inv_line.unit_price if inv_line else None)

        received_qty = received_by_line.get(po_line.id) if (received_by_line and po_line) else None
        over_billed = (
            received_qty is not None
            and inv_line is not None
            and inv_line.quantity > received_qty + QTY_TOLERANCE
        )

        line_comparison.append(
            {
                "line_no": i + 1,
                "description": (po_line.description if po_line else None) or (inv_line.description if inv_line else None),
                "po_quantity": str(po_line.quantity) if po_line else None,
                "po_unit_price": str(po_line.unit_price) if po_line else None,
                "grn_quantity_received": str(received_qty) if received_qty is not None else None,
                "invoice_quantity": str(inv_line.quantity) if inv_line else None,
                "invoice_unit_price": str(inv_line.unit_price) if inv_line else None,
                "quantity_match": qty_match,
                "price_match": price_match,
                "over_billed_vs_grn": over_billed,
                "present_in_po": po_line is not None,
                "present_in_invoice": inv_line is not None,
            }
        )

    header_ok = all(c["match"] for c in header_comparison)
    line_results = [c["quantity_match"] and c["price_match"] and not c["over_billed_vs_grn"] for c in line_comparison]
    all_lines_ok = all(line_results) if line_results else True
    any_line_ok = any(line_results) if line_results else True

    if header_ok and all_lines_ok:
        status = "MATCHED"
    elif header_comparison[0]["match"] is False or (not any_line_ok and line_results):
        status = "MISMATCH"
    else:
        status = "PARTIAL_MATCH"

    invoice.po_match_status = status
    invoice.save(update_fields=["po_match_status"])

    from apps.invoices.models import ExceptionSeverity, ExceptionType
    from apps.invoices.validation import _maybe_raise

    if status == "MISMATCH":
        _maybe_raise(
            invoice,
            ExceptionType.PO_MISMATCH,
            ExceptionSeverity.HIGH,
            "PO matching found significant discrepancies between the invoice and its linked purchase order.",
            invoice.uploaded_by,
            set(),
        )

    from apps.audit_logs.services import log_action

    log_action(
        action="PO_MATCH",
        entity_type="Invoice",
        entity_id=invoice.id,
        description=f"PO match against {po.po_number}: {status}",
    )

    return {
        "status": status,
        "po": {
            "id": str(po.id),
            "po_number": po.po_number,
            "vendor_name": po.vendor.name,
            "order_date": str(po.order_date),
            "total_amount": str(po.total_amount),
            "currency": po.currency,
            "status": po.status,
        },
        "grn": [
            {
                "id": str(g.id),
                "grn_number": g.grn_number,
                "received_date": str(g.received_date),
                "status": g.status,
            }
            for g in grns
        ]
        or None,
        "header_comparison": header_comparison,
        "line_comparison": line_comparison,
    }
