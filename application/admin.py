from urllib.parse import parse_qs

from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import Mahsulot, Category, Tag, Article, Book, Course, VisitorLog, Project, SoftwareApp, AppVersion, Documentation


class DocumentationParentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_tree_label()


class DocumentationAdminForm(forms.ModelForm):
    class Meta:
        model = Documentation
        fields = "__all__"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')
    list_filter = ('project',)
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')
    list_filter = ('project',)
    search_fields = ('name',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'category', 'views', 'is_published', 'created_at')
    list_filter = ('project', 'is_published', 'category', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'author', 'price', 'is_free', 'views', 'downloads', 'is_published')
    list_filter = ('project', 'is_published', 'is_free', 'category', 'language')
    search_fields = ('title', 'author')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'instructor', 'level_type', 'price', 'is_free', 'views', 'is_published')
    list_filter = ('project', 'is_published', 'is_free', 'level_type', 'category')
    search_fields = ('title', 'instructor')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Documentation)
class DocumentationAdmin(admin.ModelAdmin):
    form = DocumentationAdminForm
    list_display = ('tree_title', 'project', 'order', 'created_at')
    list_filter = ('project', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('project', 'order', 'created_at')
    readonly_fields = ('full_path',)
    fields = ('project', 'title', 'slug', 'parent', 'order', 'full_path', 'content')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'parent')

    def _get_project_id(self, request, obj=None):
        project_id = request.POST.get('project') or request.GET.get('project')
        if project_id:
            return project_id

        changelist_filters = request.GET.get('_changelist_filters')
        if changelist_filters:
            parsed = parse_qs(changelist_filters)
            for key in ('project__id__exact', 'project__id', 'project'):
                values = parsed.get(key)
                if values:
                    return values[0]

        if obj:
            return obj.project_id

        return None

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            current_object = None
            object_id = request.resolver_match.kwargs.get('object_id') if request.resolver_match else None
            if object_id:
                current_object = Documentation.objects.filter(pk=object_id).select_related('project').first()

            project_id = self._get_project_id(request, obj=current_object)
            queryset = Documentation.objects.select_related('project', 'parent').order_by('project__name', 'order', 'created_at')
            if project_id:
                queryset = queryset.filter(project_id=project_id)
            if current_object:
                queryset = queryset.exclude(pk=current_object.pk)
            kwargs['form_class'] = DocumentationParentChoiceField
            kwargs['queryset'] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='Tree')
    def tree_title(self, obj):
        indent = '&nbsp;' * 4 * obj.get_depth()
        return format_html('{}{}', format_html(indent), obj.title)

    @admin.display(description='Path')
    def full_path(self, obj):
        if not obj.pk:
            return "Avval saqlang, keyin tree path ko'rinadi."
        return obj.get_tree_label()

@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'path', 'method', 'timestamp')
    list_filter = ('method', 'timestamp')
    search_fields = ('ip_address', 'path')

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Mahsulot)
class MahsulotAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'price')
    list_filter = ('project',)
    search_fields = ('name',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(SoftwareApp)
class SoftwareAppAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'slug', 'latest_version_number')
    list_filter = ('project',)
    search_fields = ('name', 'slug', 'project__name')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Latest version')
    def latest_version_number(self, obj):
        version = obj.versions.filter(is_active=True).first()
        return version.version_number if version else '-'

@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ('app', 'project_name', 'version_number', 'is_active', 'created_at')
    list_filter = ('app__project', 'app', 'is_active', 'created_at')
    search_fields = ('app__name', 'version_number', 'release_notes')

    @admin.display(description='Project')
    def project_name(self, obj):
        return obj.app.project.name
