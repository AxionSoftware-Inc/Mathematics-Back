from django.contrib import admin

from .models import LaboratoryModule


@admin.register(LaboratoryModule)
class LaboratoryModuleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "category",
        "computation_mode",
        "project",
        "is_enabled",
        "sort_order",
    )
    list_filter = ("category", "computation_mode", "is_enabled", "project")
    search_fields = ("title", "slug", "summary")
    ordering = ("sort_order", "title")

