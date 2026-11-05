from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='book-open', help_text='Lucide icon name')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    thumbnail = models.ImageField(upload_to='courses/', null=True, blank=True)
    thumbnail_url = models.CharField(max_length=500, blank=True, help_text='External image URL')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Beginner')
    instructor_name = models.CharField(max_length=120, default='SkillSphere Instructor')
    instructor_title = models.CharField(max_length=150, blank=True, default='Lead Curriculum Developer')
    estimated_duration = models.CharField(max_length=50, default='12 hours')
    learning_objectives = models.TextField(blank=True, help_text='Newline-separated list of objectives')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_thumbnail_url(self):
        if self.thumbnail and hasattr(self.thumbnail, 'url'):
            return self.thumbnail.url
        if self.thumbnail_url:
            return self.thumbnail_url
        # Fallback dark high-tech gradient image with category name
        return f"https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=800&q=80"

    def get_objectives_list(self):
        if not self.learning_objectives:
            return []
        return [line.strip() for line in self.learning_objectives.split('\n') if line.strip()]

    def get_total_lessons(self):
        return self.lessons.count()

    def get_user_progress(self, user):
        """Returns percentage progress (0 to 100) and completed lessons count for given user."""
        if not user or not user.is_authenticated:
            return {'percentage': 0, 'completed': 0, 'total': self.get_total_lessons()}
        
        total = self.lessons.count()
        if total == 0:
            return {'percentage': 0, 'completed': 0, 'total': 0}
        
        from learning.models import LessonProgress
        completed = LessonProgress.objects.filter(
            user=user,
            lesson__course=self,
            is_completed=True
        ).count()
        percentage = int(round((completed / total) * 100))
        return {'percentage': percentage, 'completed': completed, 'total': total}


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"
