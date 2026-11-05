from django.db import models
from django.contrib.auth.models import User

class Event(models.Model):
    CATEGORY_CHOICES = [
        ('hackathon', 'Hackathon'),
        ('competition', 'Coding Competition'),
        ('workshop', 'Workshop'),
        ('webinar', 'Webinar'),
        ('conference', 'Tech Conference'),
        ('career_fair', 'Career Fair'),
        ('student_program', 'Student Program'),
    ]

    title = models.CharField(max_length=255)
    organizer = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=True)
    location = models.CharField(max_length=255, default='Online / Virtual')
    registration_url = models.URLField(help_text="Official event registration URL")
    verification_status = models.BooleanField(default=True, help_text="Verified authentic event from official organizers")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class SavedEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_events')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='saves')
    reminder_set = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'event'], name='unique_user_saved_event')
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.event.title}"
