from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DifferentialSolveAPIView,
    IntegralSolveAPIView,
    LaboratoryModuleViewSet,
    MatrixSolveAPIView,
    ProbabilitySolveAPIView,
    SavedLaboratoryResultViewSet,
    SeriesLimitSolveAPIView,
)

router = DefaultRouter()
router.register(r"modules", LaboratoryModuleViewSet, basename="laboratory-module")
router.register(r"results", SavedLaboratoryResultViewSet, basename="laboratory-result")

urlpatterns = [
    path("solve/integral/", IntegralSolveAPIView.as_view(), name="laboratory-integral-solve"),
    path("solve/differential/", DifferentialSolveAPIView.as_view(), name="laboratory-differential-solve"),
    path("solve/matrix/", MatrixSolveAPIView.as_view(), name="laboratory-matrix-solve"),
    path("solve/probability/", ProbabilitySolveAPIView.as_view(), name="laboratory-probability-solve"),
    path("solve/series-limit/", SeriesLimitSolveAPIView.as_view(), name="laboratory-series-limit-solve"),
    path("", include(router.urls)),
]
