from rest_framework import serializers

from .models import LaboratoryModule, SavedLaboratoryResult


class LaboratoryModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaboratoryModule
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "description",
            "category",
            "icon_name",
            "accent_color",
            "computation_mode",
            "estimated_minutes",
            "sort_order",
            "is_enabled",
            "config",
            "created_at",
            "updated_at",
        ]


class SavedLaboratoryResultSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)

    class Meta:
        model = SavedLaboratoryResult
        fields = [
            "id",
            "module_slug",
            "module_title",
            "mode",
            "title",
            "summary",
            "report_markdown",
            "input_snapshot",
            "structured_payload",
            "metadata",
            "revision",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "revision", "created_at", "updated_at"]

    def validate(self, attrs):
        if not attrs.get("structured_payload"):
            raise serializers.ValidationError({"structured_payload": "Structured payload is required."})
        if not attrs.get("report_markdown", "").strip():
            raise serializers.ValidationError({"report_markdown": "Report markdown is required."})
        return attrs


class IntegralSolveRequestSerializer(serializers.Serializer):
    expression = serializers.CharField(max_length=400)
    lower = serializers.CharField(max_length=80, allow_blank=True, required=False, default="")
    upper = serializers.CharField(max_length=80, allow_blank=True, required=False, default="")

class DifferentialSolveRequestSerializer(serializers.Serializer):
    mode = serializers.CharField(max_length=40)
    expression = serializers.CharField(max_length=400)
    variable = serializers.CharField(max_length=80)
    point = serializers.CharField(max_length=80, allow_blank=True, required=False, default="1")
    order = serializers.CharField(max_length=10, allow_blank=True, required=False, default="1")
    direction = serializers.CharField(max_length=80, allow_blank=True, required=False, default="")
    coordinates = serializers.CharField(max_length=24, allow_blank=True, required=False, default="cartesian")


class MatrixSolveRequestSerializer(serializers.Serializer):
    mode = serializers.CharField(max_length=40)
    expression = serializers.CharField(max_length=800)
    rhs = serializers.CharField(max_length=400, allow_blank=True, required=False, default="")
    dimension = serializers.CharField(max_length=20, allow_blank=True, required=False, default="")


class ProbabilitySolveRequestSerializer(serializers.Serializer):
    mode = serializers.CharField(max_length=40)
    dataset = serializers.CharField(max_length=1200)
    parameters = serializers.CharField(max_length=400, allow_blank=True, required=False, default="")
    dimension = serializers.CharField(max_length=40, allow_blank=True, required=False, default="")


class SeriesLimitSolveRequestSerializer(serializers.Serializer):
    mode = serializers.CharField(max_length=40)
    expression = serializers.CharField(max_length=1200)
    auxiliary = serializers.CharField(max_length=200, allow_blank=True, required=False, default="")
    dimension = serializers.CharField(max_length=40, allow_blank=True, required=False, default="")
