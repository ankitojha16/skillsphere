from django.db import models
from django.contrib.auth.models import User

class AIConversation(models.Model):
    MODE_CHOICES = [
        ('detailed', 'Detailed Explanation'),
        ('simple', 'Simple / Beginner Friendly'),
        ('code', 'Code Explanation & Snippet'),
        ('example', 'Example & Analogy Based'),
        ('revision', 'Quick Revision Cheat Sheet'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField(max_length=200, default='New Study Session')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='detailed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}: {self.title} ({self.mode})"


class AIMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'Student'),
        ('assistant', 'SkillSphere AI'),
    ]

    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    provider = models.CharField(max_length=60, default='offline-knowledge-engine', help_text="Active provider e.g. gemini-1.5-flash, gpt-4o-mini, offline-knowledge-engine")
    is_fallback = models.BooleanField(default=True, help_text="True if response was served by local educational fallback engine")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:40]}..."
