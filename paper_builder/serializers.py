from rest_framework import serializers
from .models import ScientificPaper

class ScientificPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScientificPaper
        fields = '__all__'
        read_only_fields = ('slug', 'article', 'published_at', 'created_at', 'updated_at')

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        status_value = attrs.get("status", getattr(instance, "status", "draft"))
        title = attrs.get("title", getattr(instance, "title", ""))
        content = attrs.get("content", getattr(instance, "content", ""))

        if status_value == "published":
            if not (title or "").strip():
                raise serializers.ValidationError({"title": "Published paper uchun sarlavha majburiy."})
            if not (content or "").strip():
                raise serializers.ValidationError({"content": "Published paper uchun matn majburiy."})

        return attrs
