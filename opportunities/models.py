from django.db import models
from django.contrib.auth.models import User

class Opportunity(models.Model):
    CATEGORY_CHOICES = [
        ('software-development', 'Software Development'),
        ('web-development', 'Web Development'),
        ('python-development', 'Python Development'),
        ('data-science', 'Data Science'),
        ('ai-ml', 'AI / Machine Learning'),
        ('ui-ux', 'UI/UX Design'),
        ('fintech', 'Finance Technology'),
        ('research', 'Research'),
        ('remote-internships', 'Remote Internships'),
        ('student-programs', 'Student Programs'),
    ]

    WORK_MODE_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-Site'),
    ]

    title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    required_skills = models.CharField(max_length=255, help_text="Comma-separated skill requirements")
    eligibility = models.TextField(blank=True, help_text="Academic criteria, graduation year, or experience requirements")
    location = models.CharField(max_length=255, default='Remote')
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='remote')
    stipend_information = models.CharField(max_length=255, blank=True, help_text="Verified stipend details e.g. '$1,500/month' or 'Unpaid / Educational'")
    application_url = models.URLField(help_text="Official verified application link")
    deadline = models.DateField(null=True, blank=True)
    verification_status = models.BooleanField(default=True, help_text="Verified authentic listing from official source")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['deadline', '-created_at']
        verbose_name_plural = 'Opportunities'

    def __str__(self):
        return f"{self.title} at {self.organization}"


class SavedOpportunity(models.Model):
    STATUS_CHOICES = [
        ('interested', 'Interested'),
        ('preparing', 'Preparing'),
        ('applied', 'Applied'),
        ('interview', 'Interview'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_opportunities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='saves')
    application_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='interested')
    application_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'opportunity'], name='unique_user_saved_opportunity')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.opportunity.title} ({self.application_status})"


class CandidateShortlist(models.Model):
    STATUS_CHOICES = [
        ('review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interview_requested', 'Interview Requested'),
        ('offered', 'Offer Extended'),
        ('archived', 'Archived'),
    ]

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shortlisted_candidates')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recruiter_shortlists')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='shortlisted')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['recruiter', 'candidate'], name='unique_recruiter_candidate_shortlist')
        ]

    def __str__(self):
        return f"{self.recruiter.username} -> {self.candidate.username} ({self.status})"


class InterviewInvitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Response'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_interview_invitations')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_interview_invitations')
    role_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    message = models.TextField()
    meeting_link = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Interview: {self.role_title} at {self.company_name} for {self.candidate.username}"

