from rest_framework.routers import DefaultRouter

from apps.purchase_orders.views import PurchaseOrderViewSet

router = DefaultRouter()
router.register("", PurchaseOrderViewSet, basename="purchase-order")

urlpatterns = router.urls
