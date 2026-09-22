from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/invoices/", include("apps.invoices.urls")),
    path("api/exceptions/", include("apps.invoices.exception_urls")),
    path("api/vendors/", include("apps.vendors.urls")),
    path("api/purchase-orders/", include("apps.purchase_orders.urls")),
    path("api/approvals/", include("apps.approvals.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/audit-logs/", include("apps.audit_logs.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
