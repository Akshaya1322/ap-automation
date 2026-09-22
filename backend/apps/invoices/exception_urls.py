from rest_framework.routers import DefaultRouter

from apps.invoices.exception_views import ExceptionViewSet

router = DefaultRouter()
router.register("", ExceptionViewSet, basename="exception")

urlpatterns = router.urls
