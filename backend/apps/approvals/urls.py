from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.approvals.matrix_views import ApprovalMatrixRuleViewSet
from apps.approvals.views import ApprovalStepViewSet

router = DefaultRouter()
router.register("", ApprovalStepViewSet, basename="approval")

matrix_router = DefaultRouter()
matrix_router.register("", ApprovalMatrixRuleViewSet, basename="approval-matrix-rule")

urlpatterns = [
    path("matrix/", include(matrix_router.urls)),
    path("", include(router.urls)),
]
