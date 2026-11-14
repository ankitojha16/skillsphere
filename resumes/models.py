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
    section_order = models.JSONField(
        default=list,
        blank=True,
        help_text="Ordered list of section identifiers: header, summary, skills, projects, education, certifications, experience"
    )
    target_career_track = models.CharField(max_length=100, blank=True, help_text="Associated CareerTrack slug, e.g. python-developer")
    resume_data = models.JSONField(
        default=dict,
        help_text="Structured resume content: contact, summary, education, experience, internships, skills, projects, certifications, links"
    )
    ats_score = models.PositiveIntegerField(default=0, help_text="Educational ATS readability rating (0-100)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def get_section_order(self):
        if self.section_order and len(self.section_order) > 0:
            return self.section_order
        return ['summary', 'skills', 'projects', 'education', 'certifications', 'experience']

    @property
    def skills(self):
        if isinstance(self.resume_data, dict):
            return self.resume_data.get('skills', [])
        return []

    @property
    def summary(self):
        if isinstance(self.resume_data, dict):
            return self.resume_data.get('summary', '')
        return ''

    @property
    def projects(self):
        if isinstance(self.resume_data, dict):
            return self.resume_data.get('projects', [])
        return []

    @property
    def experience(self):
        if isinstance(self.resume_data, dict):
            return self.resume_data.get('experience', [])
        return []


class ResumeVersion(models.Model):
    """
    Immutable version snapshot of a Resume. Allows students to maintain
    multiple tailored versions (e.g. Frontend vs Full-Stack) and roll back edits.
    """
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(default=1)
    version_title = models.CharField(max_length=200, default='Initial Version')
    template = models.CharField(max_length=50, default='ats')
    snapshot_data = models.JSONField(default=dict, help_text="Frozen snapshot of resume_data at this point in time")
    pdf_file = models.FileField(upload_to='resumes/versions/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number', '-created_at']
        unique_together = ('resume', 'version_number')
        verbose_name = 'Resume Version'
        verbose_name_plural = 'Resume Versions'

    def __str__(self):
        return f"{self.resume.title} (v{self.version_number})"
