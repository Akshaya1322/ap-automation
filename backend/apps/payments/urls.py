from rest_framework.routers import DefaultRouter

from apps.payments.views import PaymentRequestViewSet

router = DefaultRouter()
router.register("", PaymentRequestViewSet, basename="payment")

urlpatterns = router.urls
