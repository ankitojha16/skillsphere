from django.db import models
from django.contrib.auth.models import User
from courses.models import Course

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    chapter_name = models.CharField(max_length=150, default='Module 1: Core Fundamentals')
    title = models.CharField(max_length=200)
    lesson_order = models.PositiveIntegerField(default=1)
    estimated_minutes = models.PositiveIntegerField(default=15)
    content = models.TextField(help_text='HTML/Markdown formatted content with code snippets')
    external_resources = models.TextField(blank=True, help_text='External documentation and resource links')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['lesson_order', 'id']

    def __str__(self):
        return f"{self.course.title} - #{self.lesson_order} {self.title}"

    def is_completed_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.user_progress.filter(user=user, is_completed=True).exists()


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name_plural = 'Lesson Progress Records'

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.user.username} - {self.lesson.title}: {status}"
