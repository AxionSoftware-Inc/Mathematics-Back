from django.core.exceptions import ValidationError
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=100, unique=True) # Quantum Uz, Ket Website, Dirac
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Mahsulot(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    description = models.TextField()

class Category(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='tags')
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Article(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)
    content = models.TextField()
    summary = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=100, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
    tags = models.ManyToManyField(Tag, blank=True)
    cover_image = models.ImageField(upload_to='articles/images/', blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    read_time_minutes = models.PositiveIntegerField(default=5)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Book(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)
    author = models.CharField(max_length=255)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='books/covers/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='books/pdfs/', blank=True, null=True)
    sample_pdf_file = models.FileField(upload_to='books/samples/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    pages = models.PositiveIntegerField(blank=True, null=True)
    language = models.CharField(max_length=50, default='O\'zbek')
    published_date = models.DateField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    tags = models.ManyToManyField(Tag, blank=True)
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Course(models.Model):
    LEVEL_CHOICES = (
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    )

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)
    instructor = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    level_type = models.CharField(max_length=50, choices=LEVEL_CHOICES, default='Beginner')
    duration_hours = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    tags = models.ManyToManyField(Tag, blank=True)
    views = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Documentation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='docs')
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        constraints = [
            models.UniqueConstraint(fields=['project', 'slug'], name='unique_doc_slug_per_project'),
        ]

    def clean(self):
        errors = {}

        if self.parent_id:
            if self.parent_id == self.id:
                errors['parent'] = "Bo'lim o'zini ota bo'la olmaydi."
            elif self.project_id and self.parent.project_id != self.project_id:
                errors['parent'] = "Parent documentation tanlangan loyiha bilan bir xil bo'lishi kerak."

            ancestor = self.parent
            while ancestor:
                if ancestor.pk == self.pk:
                    errors['parent'] = "Circular tree yaratib bo'lmaydi."
                    break
                ancestor = ancestor.parent

        if errors:
            raise ValidationError(errors)

    def get_depth(self):
        depth = 0
        ancestor = self.parent
        while ancestor:
            depth += 1
            ancestor = ancestor.parent
        return depth

    def get_breadcrumbs(self):
        nodes = []
        ancestor = self
        while ancestor:
            nodes.append(ancestor.title)
            ancestor = ancestor.parent
        return list(reversed(nodes))

    def get_tree_label(self):
        return " / ".join(self.get_breadcrumbs())

    def __str__(self):
        return f"[{self.project.name}] {self.get_tree_label()}"

class VisitorLog(models.Model):
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["path"]),
            models.Index(fields=["timestamp", "path"]),
        ]

    def __str__(self):
        return f"{self.ip_address} visited {self.path} at {self.timestamp}"

class SoftwareApp(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='apps')
    name = models.CharField(max_length=100) # e.g. "Main App", "Helper Tool"
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"

class AppVersion(models.Model):
    app = models.ForeignKey(SoftwareApp, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=50) # e.g. "1.2.3"
    file = models.FileField(upload_to='apps/versions/')
    release_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.app.name} v{self.version_number}"
