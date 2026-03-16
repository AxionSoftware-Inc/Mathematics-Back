from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MahsulotAPI, CategoryViewSet, TagViewSet, ArticleViewSet, 
    BookViewSet, CourseViewSet, DashboardStatsAPI, UserViewSet,
    ProjectViewSet, SoftwareAppViewSet, AppVersionViewSet, DocumentationViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'articles', ArticleViewSet)
router.register(r'books', BookViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'users', UserViewSet, basename='users')
router.register(r'projects', ProjectViewSet)
router.register(r'software-apps', SoftwareAppViewSet)
router.register(r'app-versions', AppVersionViewSet)
router.register(r'docs', DocumentationViewSet)

urlpatterns = [
    path('admin-dashboard-stats/', DashboardStatsAPI.as_view(), name='admin-dashboard-stats'),
    path('mahsulot/', MahsulotAPI.as_view(), name='mahsulot-api'),
    path('', include(router.urls)),
]
