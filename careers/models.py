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


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('WISHLIST', 'Wishlist'),
        ('APPLIED', 'Applied'),
        ('SCREENING', 'Screening / HR'),
        ('TECHNICAL', 'Technical / Interview'),
        ('OFFER', 'Offer Extended 🎉'),
        ('REJECTED', 'Archived / Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    company_name = models.CharField(max_length=150)
    role_title = models.CharField(max_length=150)
    job_url = models.URLField(blank=True)
    job_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WISHLIST')
    target_salary = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=100, blank=True)
    ats_match_score = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    applied_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'

    def __str__(self):
        return f"{self.role_title} at {self.company_name} ({self.status})"

