from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    TYPE_CHOICES = [
        ('collaboration_request', 'Collaboration Request'),
        ('collaboration_accepted', 'Collaboration Accepted'),
        ('saved_event', 'Saved Event Reminder'),
        ('opportunity_deadline', 'Opportunity Deadline'),
        ('learning_reminder', 'Learning Reminder'),
        ('certificate_issued', 'Certificate Issued'),
        ('community_reply', 'Community Reply'),
        ('system', 'System Notification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='system')
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title} ({'Read' if self.is_read else 'Unread'})"
