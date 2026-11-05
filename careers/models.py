from django.db import models
from django.contrib.auth.models import User

class CareerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='career_profile')
    professional_headline = models.CharField(max_length=255, blank=True, help_text="e.g. Aspiring Full Stack Python Developer | CS Sophomore")
    professional_summary = models.TextField(blank=True, help_text="High-level career narrative and objective")
    career_interests = models.JSONField(default=list, blank=True, help_text="List of career domain interests")
    preferred_roles = models.JSONField(default=list, blank=True, help_text="Target role titles")
    preferred_locations = models.JSONField(default=list, blank=True, help_text="Target geographic or remote locations")
    target_career_path = models.CharField(max_length=100, default='fullstack-developer', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Career Profile'
        verbose_name_plural = 'Career Profiles'

    def __str__(self):
        return f"{self.user.username}'s Career Profile"
