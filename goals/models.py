from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class LearningGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['is_completed', 'target_date']

    def __str__(self):
        status = "Done" if self.is_completed else "Pending"
        return f"{self.title} ({status}) - {self.user.username}"

    @property
    def is_overdue(self):
        if self.is_completed:
            return False
        return self.target_date < timezone.now().date()


class LearningActivity(models.Model):
    ACTIVITY_CHOICES = [
        ('ENROLL', 'Course Enrolled'),
        ('COMPLETE_LESSON', 'Lesson Completed'),
        ('GOAL_CREATED', 'Goal Created'),
        ('GOAL_COMPLETED', 'Goal Completed'),
        ('FOCUS_SESSION', 'Pomodoro Focus Session'),
        ('FLASHCARD_REVIEW', 'Flashcard Spaced Repetition'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_CHOICES)
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Learning Activities'

    def __str__(self):
        return f"{self.user.username}: {self.description} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
