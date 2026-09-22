from datetime import date, timedelta

from django.db.models.functions import TruncDate, TruncMonth
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports import services
from apps.reports.filters import filtered_invoices


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        invoice_qs = filtered_invoices(request)

        kpis = services.dashboard_kpis(invoice_qs)

        since_30 = date.today() - timedelta(days=30)
        trend_rows = (
            invoice_qs.filter(created_at__date__gte=since_30)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        processing_trend = [{"date": str(r["day"]), "count": r["count"]} for r in trend_rows]

        since_180 = date.today() - timedelta(days=180)
        monthly_rows = (
            invoice_qs.filter(created_at__date__gte=since_180)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        monthly_volume = [{"month": r["month"].strftime("%Y-%m"), "count": r["count"]} for r in monthly_rows]

        return Response(
            {
                "kpis": kpis,
                "charts": {
                    "processing_trend": processing_trend,
                    "monthly_volume": monthly_volume,
                    "status_distribution": services.invoice_status_report(invoice_qs),
                    "ap_aging": services.ap_aging_report(invoice_qs),
                    "vendor_wise_amount": services.vendor_report(invoice_qs)[:8],
                    "payment_status": services.payment_report(invoice_qs),
                },
            }
        )
