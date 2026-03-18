from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LaboratoryModuleViewSet

router = DefaultRouter()
router.register(r"modules", LaboratoryModuleViewSet, basename="laboratory-module")

urlpatterns = [
    path("", include(router.urls)),
]

