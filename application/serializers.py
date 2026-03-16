from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Mahsulot, Category, Tag, Article, Book, Course, Project, SoftwareApp, AppVersion, Documentation

class DocumentationSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    project_slug = serializers.ReadOnlyField(source='project.slug')

    class Meta:
        model = Documentation
        fields = (
            'id',
            'project',
            'project_slug',
            'title',
            'slug',
            'content',
            'order',
            'parent',
            'created_at',
            'updated_at',
            'children',
        )

    def get_children(self, obj):
        if not self.context.get('include_children'):
            return []

        queryset = obj.children.select_related('project', 'parent').all()
        return DocumentationSerializer(queryset, many=True, context=self.context).data

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        project = attrs.get('project') or getattr(instance, 'project', None)
        parent = attrs.get('parent', getattr(instance, 'parent', None))

        if parent:
            if instance and parent.pk == instance.pk:
                raise serializers.ValidationError({'parent': "Bo'lim o'zini ota bo'la olmaydi."})
            if project and parent.project_id != project.id:
                raise serializers.ValidationError({'parent': 'Parent documentation tanlangan loyiha bilan bir xil bo\'lishi kerak.'})

            ancestor = parent
            current_id = instance.pk if instance else None
            while ancestor:
                if current_id and ancestor.pk == current_id:
                    raise serializers.ValidationError({'parent': "Circular tree yaratib bo'lmaydi."})
                    break
                ancestor = ancestor.parent

        return attrs

class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = '__all__'

class SoftwareAppSerializer(serializers.ModelSerializer):
    latest_version = serializers.SerializerMethodField()
    
    class Meta:
        model = SoftwareApp
        fields = '__all__'

    def get_latest_version(self, obj):
        version = obj.versions.filter(is_active=True).first()
        if version:
            return AppVersionSerializer(version, context=self.context).data
        return None

class ProjectSerializer(serializers.ModelSerializer):
    apps = SoftwareAppSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
        read_only_fields = ('date_joined',)

class MahsulotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mahsulot
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class ArticleSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    tags_names = serializers.StringRelatedField(many=True, read_only=True, source='tags')

    class Meta:
        model = Article
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    tags_names = serializers.StringRelatedField(many=True, read_only=True, source='tags')

    class Meta:
        model = Book
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    tags_names = serializers.StringRelatedField(many=True, read_only=True, source='tags')

    class Meta:
        model = Course
        fields = '__all__'
