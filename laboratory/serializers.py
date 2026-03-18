from rest_framework import serializers

from .models import LaboratoryModule


class LaboratoryModuleSerializer(serializers.ModelSerializer):
    project_slug = serializers.ReadOnlyField(source="project.slug")
    project_name = serializers.ReadOnlyField(source="project.name")

    class Meta:
        model = LaboratoryModule
        fields = [
            "id",
            "project",
            "project_slug",
            "project_name",
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

