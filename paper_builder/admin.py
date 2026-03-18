from django.contrib import admin
from .models import ScientificPaper

@admin.register(ScientificPaper)
class ScientificPaperAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'article', 'published_at', 'created_at', 'updated_at')
    list_filter = ('status', 'published_at', 'created_at')
    search_fields = ('title', 'authors', 'slug')
