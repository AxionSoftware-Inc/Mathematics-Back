from rest_framework import serializers
from .models import LaboratoryModule


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
