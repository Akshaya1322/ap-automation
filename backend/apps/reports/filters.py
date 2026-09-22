from apps.invoices.models import Invoice


def filtered_invoices(request):
    qs = Invoice.objects.select_related("vendor")
    params = request.query_params

    date_from = params.get("date_from")
    date_to = params.get("date_to")
    vendor = params.get("vendor")
    status = params.get("status")
    department = params.get("department")

    if date_from:
        qs = qs.filter(invoice_date__gte=date_from)
    if date_to:
        qs = qs.filter(invoice_date__lte=date_to)
    if vendor:
        qs = qs.filter(vendor_id=vendor)
    if status:
        qs = qs.filter(status=status)
    if department:
        qs = qs.filter(department=department)

    return qs
