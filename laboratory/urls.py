from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IntegralSolveAPIView, DifferentialSolveAPIView, LaboratoryModuleViewSet

router = DefaultRouter()
router.register(r"modules", LaboratoryModuleViewSet, basename="laboratory-module")

urlpatterns = [
    path("solve/integral/", IntegralSolveAPIView.as_view(), name="laboratory-integral-solve"),
    path("solve/differential/", DifferentialSolveAPIView.as_view(), name="laboratory-differential-solve"),
    path("", include(router.urls)),
]
