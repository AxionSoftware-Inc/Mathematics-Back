from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class ScientificPaper(models.Model):
    title = models.CharField(max_length=500, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    authors = models.CharField(max_length=500, blank=True, null=True)
    keywords = models.CharField(max_length=500, blank=True, null=True)
    article = models.OneToOneField(
        "application.Article",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_paper",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, default='draft', choices=[('draft', 'Draft'), ('published', 'Published')])

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or "Untitled Paper"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        update_fields: list[str] = []

        if not self.slug:
            self.slug = self.build_slug()
            update_fields.append("slug")

        if self.status == "published":
            article = self.sync_public_article()
            if article and self.article_id != article.id:
                self.article = article
                update_fields.append("article")
            if self.published_at is None:
                self.published_at = timezone.now()
                update_fields.append("published_at")
        elif self.article_id:
            if self.article.is_published:
                self.article.is_published = False
                self.article.save()
            if self.published_at is not None:
                self.published_at = None
                update_fields.append("published_at")

        if update_fields:
            super().save(update_fields=update_fields)

    def build_slug(self) -> str:
        base = slugify(self.title or "untitled-paper") or "untitled-paper"
        return f"paper-{self.pk}-{base}"[:255]

    def get_public_article_slug(self) -> str:
        base = slugify(self.title or "scientific-paper") or "scientific-paper"
        return f"journal-paper-{self.pk}-{base}"[:255]

    def estimate_read_time_minutes(self) -> int:
        words = len((self.content or "").split())
        return max(1, round(words / 200)) if words else 1

    def sync_public_article(self):
        from application.models import Article, Project

        article = self.article or Article()
        article.title = (self.title or "Untitled Paper").strip()
        article.slug = self.get_public_article_slug()
        article.content = self.content or ""
        article.summary = (self.abstract or "").strip() or None
        article.author = (self.authors or "").strip() or None
        article.project = Project.objects.filter(slug="quantum-uz").first()
        article.read_time_minutes = self.estimate_read_time_minutes()
        article.is_published = self.status == "published"
        article.save()
        return article
