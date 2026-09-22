from apps.invoices.models import OcrConfidenceLevel

MANDATORY_FIELDS = ["vendor_name", "invoice_number", "invoice_date", "total_amount", "gstin"]

HIGH_THRESHOLD = 85
MEDIUM_THRESHOLD = 60


def confidence_level(score):
    if score is None:
        return None
    if score >= HIGH_THRESHOLD:
        return OcrConfidenceLevel.HIGH
    if score >= MEDIUM_THRESHOLD:
        return OcrConfidenceLevel.MEDIUM
    return OcrConfidenceLevel.LOW
