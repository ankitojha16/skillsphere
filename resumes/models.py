from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    TEMPLATE_CHOICES = [
        ('ats', 'Professional ATS'),
        ('modern', 'Modern Developer'),
        ('fresher', 'Fresher Resume'),
        ('minimal', 'Minimal Resume'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=255, default='My Resume')
    template = models.CharField(max_length=50, choices=TEMPLATE_CHOICES, default='ats')
    is_primary = models.BooleanField(default=False)
    resume_data = models.JSONField(
        default=dict,
        help_text="Structured resume content: contact, summary, education, experience, internships, skills, projects, certifications, links"
    )
    ats_score = models.PositiveIntegerField(default=0, help_text="Educational ATS readability rating (0-100)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"
