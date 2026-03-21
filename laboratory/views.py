from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import LaboratoryModule
from .serializers import LaboratoryModuleSerializer

class LaboratoryModuleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LaboratoryModule.objects.all()
    serializer_class = LaboratoryModuleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method == "GET":
            queryset = queryset.filter(is_enabled=True)
        return queryset

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        value = self.kwargs[lookup_url_kwarg]

        if value.isdigit():
            obj = queryset.filter(pk=value).first()
            if obj:
                return obj

        return get_object_or_404(queryset, slug=value)
