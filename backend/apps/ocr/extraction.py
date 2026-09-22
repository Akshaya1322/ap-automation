"""Field parsing layer.

Deliberately separate from `providers.py` (raw OCR) and `apps/invoices`
validation: this module's only job is turning raw OCR text into a dict of
{field_name: (value, confidence)} candidates using pattern matching. It
knows nothing about business rules (mandatory fields, GST format
correctness, duplicate detection, etc.) -- that lives in the validation
engine (apps/invoices/validation.py).
"""

import re
from datetime import datetime

GSTIN_PATTERN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")
# Keyword patterns are matched per-line (see parse_fields) so a label like
# "Tax Invoice" on one line can't bleed into a value on the next line.
INVOICE_NUMBER_PATTERN = re.compile(
    r"invoice[\s#:.-]*(?:no|number|num)[\s#:.-]*([A-Za-z0-9/\-]{3,25})", re.IGNORECASE
)
PO_NUMBER_PATTERN = re.compile(
    r"(?:p\.?o\.?|purchase order)[\s#:.-]*(?:no|number)?[\s#:.-]*([A-Za-z0-9/\-]{3,25})", re.IGNORECASE
)
AMOUNT_PATTERN = re.compile(
    r"\b(?<!sub)(?<!sub )(?:grand total|amount due|amount payable|total)\b[\s:₹Rs.]*([\d,]+\.?\d*)",
    re.IGNORECASE,
)
SUBTOTAL_PATTERN = re.compile(r"(?:sub\s*-?\s*total)[\s:₹Rs.]*([\d,]+\.?\d*)", re.IGNORECASE)
TAX_PATTERN = re.compile(r"(?:tax|gst)(?:\s*amount)?[\s:₹Rs.]*([\d,]+\.?\d*)", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")

DATE_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y", "%m/%d/%Y"]

# Heuristic table-row matcher: "1  Widget description  40  320.00  12,800.00"
# (line-no, description, quantity, unit price, amount). Like every other
# pattern in this module, this is regex/positional heuristics over OCR text,
# not a trained model -- it works when the source table reads left-to-right
# on one line per row, which holds for typical single-column invoice layouts
# but will miss line-wrapped descriptions or heavily merged OCR columns.
LINE_ITEM_PATTERN = re.compile(
    r"^\s*(\d{1,3})[.\s):-]+"
    r"([A-Za-z][A-Za-z0-9 ,./&()\-]{2,80}?)\s+"
    r"(\d+(?:\.\d+)?)\s+"
    r"([\d,]+\.\d{2})\s+"
    r"([\d,]+\.\d{2})\s*$"
)
SUMMARY_ROW_KEYWORDS = ("subtotal", "sub total", "sub-total", "total", "cgst", "sgst", "igst", "tax", "discount")


def _clean_amount(raw):
    try:
        return float(raw.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _parse_date(raw):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_fields(raw_text: str, base_confidence: float = 70.0):
    """Extract candidate field values from raw OCR text.

    `base_confidence` is the OCR engine's own average word confidence; each
    parsed field's confidence is derived from it (full weight when a clean
    regex match is found, reduced when we have to guess).
    """
    results = {}
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

    gstin_match = GSTIN_PATTERN.search(raw_text)
    if gstin_match:
        results["gstin"] = (gstin_match.group(0), base_confidence)

    inv_match = INVOICE_NUMBER_PATTERN.search(raw_text)
    if inv_match:
        results["invoice_number"] = (inv_match.group(1).strip(), base_confidence)

    po_match = PO_NUMBER_PATTERN.search(raw_text)
    if po_match:
        results["po_number"] = (po_match.group(1).strip(), base_confidence * 0.9)

    total_match = AMOUNT_PATTERN.search(raw_text)
    if total_match:
        amount = _clean_amount(total_match.group(1))
        if amount is not None:
            results["total_amount"] = (str(amount), base_confidence)

    subtotal_match = SUBTOTAL_PATTERN.search(raw_text)
    if subtotal_match:
        amount = _clean_amount(subtotal_match.group(1))
        if amount is not None:
            results["subtotal"] = (str(amount), base_confidence * 0.9)

    tax_match = TAX_PATTERN.search(raw_text)
    if tax_match:
        amount = _clean_amount(tax_match.group(1))
        if amount is not None:
            results["tax_amount"] = (str(amount), base_confidence * 0.9)

    date_matches = DATE_PATTERN.findall(raw_text)
    if date_matches:
        parsed = _parse_date(date_matches[0])
        if parsed:
            results["invoice_date"] = (parsed, base_confidence * 0.85)
        if len(date_matches) > 1:
            due_parsed = _parse_date(date_matches[1])
            if due_parsed:
                results["due_date"] = (due_parsed, base_confidence * 0.7)

    # Heuristic: vendor name is usually one of the first non-empty lines
    # that isn't itself a label like "Invoice" or "Tax Invoice".
    for line in lines[:5]:
        lowered = line.lower()
        if len(line) > 3 and not any(kw in lowered for kw in ["invoice", "tax invoice", "bill to", "gstin"]):
            results["vendor_name"] = (line, base_confidence * 0.6)
            break

    return results


def parse_line_items(raw_text: str):
    """Best-effort extraction of a line-items table from raw OCR text.

    Returns a list of dicts: line_no, description, quantity, unit_price,
    amount (all as strings, left for the caller to cast to Decimal). Rows
    that look like a summary line (Subtotal/CGST/SGST/Total/...) rather than
    a real line item are skipped even if they happen to match the numeric
    shape, since those aren't purchased items."""
    items = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = LINE_ITEM_PATTERN.match(line)
        if not match:
            continue
        line_no, description, quantity, unit_price, amount = match.groups()
        if any(kw in description.lower() for kw in SUMMARY_ROW_KEYWORDS):
            continue
        items.append(
            {
                "line_no": line_no,
                "description": description.strip(),
                "quantity": quantity,
                "unit_price": unit_price.replace(",", ""),
                "amount": amount.replace(",", ""),
            }
        )
    return items
