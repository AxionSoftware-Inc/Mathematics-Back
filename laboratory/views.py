from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .integral_solver import IntegralSolverError, solve_single_integral
from .differential_solver import DifferentialSolverError, solve_differential
from .matrix_solver import MatrixSolverError, solve_matrix
from .probability_solver import ProbabilitySolverError, solve_probability
from .models import LaboratoryModule
from .serializers import IntegralSolveRequestSerializer, LaboratoryModuleSerializer, DifferentialSolveRequestSerializer, MatrixSolveRequestSerializer, ProbabilitySolveRequestSerializer

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

class DifferentialSolveAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = DifferentialSolveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = solve_differential(
                mode=serializer.validated_data["mode"],
                expression=serializer.validated_data["expression"],
                variable=serializer.validated_data["variable"],
                point=serializer.validated_data.get("point", "1"),
                order=serializer.validated_data.get("order", "1"),
                direction=serializer.validated_data.get("direction", ""),
                coordinates=serializer.validated_data.get("coordinates", "cartesian"),
            )
        except DifferentialSolverError as exc:
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


class MatrixSolveAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = MatrixSolveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = solve_matrix(
                mode=serializer.validated_data["mode"],
                expression=serializer.validated_data["expression"],
                rhs_expression=serializer.validated_data.get("rhs", ""),
                dimension=serializer.validated_data.get("dimension", ""),
            )
        except MatrixSolverError as exc:
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


class ProbabilitySolveAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ProbabilitySolveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = solve_probability(
                mode=serializer.validated_data["mode"],
                dataset=serializer.validated_data["dataset"],
                parameters=serializer.validated_data.get("parameters", ""),
                dimension=serializer.validated_data.get("dimension", ""),
            )
        except ProbabilitySolverError as exc:
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
