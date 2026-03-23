from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .integral_solver import IntegralSolverError, solve_single_integral
from .models import LaboratoryModule
from .serializers import IntegralSolveRequestSerializer, LaboratoryModuleSerializer

class LaboratoryModuleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LaboratoryModule.objects.all()
    serializer_class = LaboratoryModuleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method == "GET":
            queryset = queryset.filter(is_enabled=True, slug="integral-studio")
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


class IntegralSolveAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = IntegralSolveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = solve_single_integral(
                expression=serializer.validated_data["expression"],
                lower=serializer.validated_data["lower"],
                upper=serializer.validated_data["upper"],
            )
        except IntegralSolverError as exc:
            return Response(
                {"status": "error", "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "status": result.status,
                "message": result.message,
                **result.payload,
            }
        )
