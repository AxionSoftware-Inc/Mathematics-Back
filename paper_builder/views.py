from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import ScientificPaper
from .serializers import ScientificPaperSerializer

class ScientificPaperViewSet(viewsets.ModelViewSet):
    queryset = ScientificPaper.objects.all()
    serializer_class = ScientificPaperSerializer
    permission_classes = [AllowAny] # Allow any since this is a global writing tool for now

    def get_queryset(self):
        queryset = ScientificPaper.objects.select_related("article").prefetch_related("sections").annotate(
            section_count=Count("sections")
        )
        status_value = self.request.query_params.get("status")
        search = self.request.query_params.get("q")

        if status_value in {"draft", "published"}:
            queryset = queryset.filter(status=status_value)

        if search:
            queryset = queryset.filter(title__icontains=search.strip())

        return queryset
