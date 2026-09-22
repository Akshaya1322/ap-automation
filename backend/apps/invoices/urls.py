from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.invoices.views import InvoiceUploadView, InvoiceViewSet

router = DefaultRouter()
router.register("", InvoiceViewSet, basename="invoice")

urlpatterns = [
    path("upload/", InvoiceUploadView.as_view(), name="invoice-upload"),
    path("", include(router.urls)),
]
