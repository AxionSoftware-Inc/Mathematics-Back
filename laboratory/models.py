from django.db import models

from application.models import Project


class LaboratoryModule(models.Model):
    CATEGORY_CHOICES = (
        ("matrix", "Matrix"),
        ("integral", "Integral"),
        ("differential", "Differential"),
        ("analysis", "Analysis"),
        ("geometry", "Geometry"),
        ("custom", "Custom"),
    )

    COMPUTATION_MODE_CHOICES = (
        ("client", "Client"),
        ("hybrid", "Hybrid"),
        ("server", "Server"),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_modules",
    )
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="custom")
    icon_name = models.CharField(max_length=64, default="FlaskConical")
    accent_color = models.CharField(max_length=32, default="blue")
    computation_mode = models.CharField(
        max_length=16,
        choices=COMPUTATION_MODE_CHOICES,
        default="client",
    )
    estimated_minutes = models.PositiveIntegerField(default=10)
    sort_order = models.PositiveIntegerField(default=0)
    is_enabled = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

