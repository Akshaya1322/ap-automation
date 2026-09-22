import django_filters

from apps.invoices.models import Invoice


class InvoiceFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status")
    vendor = django_filters.UUIDFilter(field_name="vendor__id")
    department = django_filters.CharFilter(field_name="department")
    date_from = django_filters.DateFilter(field_name="invoice_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="invoice_date", lookup_expr="lte")
    amount_min = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    has_exception = django_filters.BooleanFilter(method="filter_has_exception")

    class Meta:
        model = Invoice
        fields = ["status", "vendor", "department"]

    def filter_has_exception(self, queryset, name, value):
        if value:
            return queryset.filter(exceptions__status="OPEN").distinct()
        return queryset.exclude(exceptions__status="OPEN").distinct()
