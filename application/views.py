from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate
from .mixins import ViewCountMixin

from .models import Mahsulot, Category, Tag, Article, Book, Course, VisitorLog
from .serializers import (
    MahsulotSerializer, CategorySerializer, TagSerializer, 
    ArticleSerializer, BookSerializer, CourseSerializer, UserSerializer
)

class ProjectFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        project_slug = self.request.query_params.get("project")
        if project_slug:
            queryset = queryset.filter(project__slug=project_slug)
        return queryset

class DashboardStatsAPI(APIView):
    def get(self, request):
        today = timezone.now().date()
        week_ago = today - timedelta(days=6)
        
        stats = {
            "articles_count": Article.objects.count(),
            "books_count": Book.objects.count(),
            "courses_count": Course.objects.count(),
            "visitors_today": VisitorLog.objects.filter(timestamp__date=today).count(),
            "visitors_week": VisitorLog.objects.filter(timestamp__date__gte=week_ago).count(),
        }
        
        popular_pages = VisitorLog.objects.values('path').annotate(count=Count('id')).order_by('-count')[:5]
        stats['popular_pages'] = list(popular_pages)
        
        visitors_by_day = VisitorLog.objects.filter(timestamp__date__gte=week_ago)\
            .annotate(date=TruncDate('timestamp'))\
            .values('date')\
            .annotate(count=Count('id'))\
            .order_by('date')
            
        chart_data_dict = {str(item['date']): item['count'] for item in visitors_by_day}
        
        labels = []
        data = []
        for i in range(7):
            d = week_ago + timedelta(days=i)
            labels.append(d.strftime("%d %b"))
            data.append(chart_data_dict.get(str(d), 0))
            
        stats['chart_labels'] = labels
        stats['chart_data'] = data
        
        return Response(stats)

class MahsulotAPI(APIView):
    def get(self, request):
        project_slug = request.query_params.get('project')
        malumot = Mahsulot.objects.all()
        if project_slug:
            malumot = malumot.filter(project__slug=project_slug)
        serializer = MahsulotSerializer(malumot, many=True)
        return Response(serializer.data)

    def post(self, request):
        kop_narsami = isinstance(request.data, list)
        serializer = MahsulotSerializer(data=request.data, many=kop_narsami)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class CategoryViewSet(ProjectFilterMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class TagViewSet(ProjectFilterMixin, viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class ArticleViewSet(ProjectFilterMixin, ViewCountMixin, viewsets.ModelViewSet):
    queryset = Article.objects.select_related("category").prefetch_related("tags").all()
    serializer_class = ArticleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method == "GET":
            queryset = queryset.filter(is_published=True)
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

class BookViewSet(ProjectFilterMixin, ViewCountMixin, viewsets.ModelViewSet):
    queryset = Book.objects.select_related("category").prefetch_related("tags").all()
    serializer_class = BookSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        value = self.kwargs[lookup_url_kwarg]

        if value.isdigit():
            obj = queryset.filter(pk=value).first()
            if obj:
                return obj

        return get_object_or_404(queryset, slug=value)

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        book = self.get_object()
        if book.pdf_file:
            book.downloads += 1
            book.save()
            return FileResponse(book.pdf_file.open(), as_attachment=True, filename=book.pdf_file.name.split('/')[-1])
        return Response({"error": "Full PDF not available for this book."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def read_sample(self, request, pk=None):
        book = self.get_object()
        if book.sample_pdf_file:
            return FileResponse(book.sample_pdf_file.open(), as_attachment=False)
        return Response({"error": "Sample PDF not available."}, status=status.HTTP_404_NOT_FOUND)

class CourseViewSet(ProjectFilterMixin, ViewCountMixin, viewsets.ModelViewSet):
    queryset = Course.objects.select_related("category").prefetch_related("tags").all()
    serializer_class = CourseSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        value = self.kwargs[lookup_url_kwarg]

        if value.isdigit():
            obj = queryset.filter(pk=value).first()
            if obj:
                return obj

        return get_object_or_404(queryset, slug=value)

from django.contrib.auth.models import User
from .serializers import UserSerializer
from rest_framework.permissions import IsAdminUser

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
