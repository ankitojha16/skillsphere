from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class OpportunityOrganization(models.Model):
    """
    Verified partner organizations, universities, and verified employer profiles.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    logo_url = models.URLField(blank=True, default='', help_text="Organization logo image URL")
    website_url = models.URLField(blank=True, help_text="Official verified website")
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=True, help_text="Verified partner badge")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Opportunity Organization'
        verbose_name_plural = 'Opportunity Organizations'

    def __str__(self):
        return self.name


class Opportunity(models.Model):
    OPPORTUNITY_TYPE_CHOICES = [
        ('internship', 'Internship'),
        ('job', 'Full-time / Entry-level Job'),
        ('remote', 'Remote Opportunity'),
        ('hackathon', 'Hackathon'),
        ('competition', 'Coding Competition'),
        ('scholarship', 'Scholarship / Fellowship'),
        ('challenge', 'Student Challenge'),
        ('mentorship', 'Mentorship Program'),
    ]

    CATEGORY_CHOICES = [
        ('software-development', 'Software Development'),
        ('web-development', 'Web Development'),
        ('python-development', 'Python Development'),
        ('data-science', 'Data Science & AI'),
        ('ai-ml', 'AI / Machine Learning'),
        ('ui-ux', 'UI/UX Design'),
        ('fintech', 'Finance Technology'),
        ('research', 'Research & Academia'),
        ('remote-internships', 'Remote Internships'),
        ('student-programs', 'Student Programs & Competitions'),
    ]

    WORK_MODE_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-Site'),
    ]

    SOURCE_TYPE_CHOICES = [
        ('official_partner', 'Official Partner'),
        ('curated_platform', 'Platform Curated'),
        ('authorized_recruiter', 'Authorized Recruiter'),
    ]

    title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    organization_ref = models.ForeignKey(
        OpportunityOrganization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opportunities'
    )
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_opportunities',
        help_text="Recruiter or staff member who published this listing"
    )
    opportunity_type = models.CharField(
        max_length=30,
        choices=OPPORTUNITY_TYPE_CHOICES,
        default='internship',
        db_index=True
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField()
    required_skills = models.CharField(max_length=500, help_text="Comma-separated required skills")
    preferred_skills = models.CharField(max_length=500, blank=True, help_text="Comma-separated preferred or bonus skills")
    eligibility = models.TextField(blank=True, help_text="Academic criteria, graduation year, or experience requirements")
    location = models.CharField(max_length=255, default='Remote')
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='remote')
    stipend_information = models.CharField(max_length=255, blank=True, help_text="Stipend / salary or award info")
    compensation_details = models.CharField(max_length=255, blank=True, help_text="Detailed compensation/award structure")
    funding_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Award pool, scholarship amount, or monthly stipend (in currency)"
    )
    required_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="List of required application materials e.g. ['Resume', 'Portfolio', 'Transcripts']"
    )
    application_url = models.URLField(help_text="Official verified application link")
    deadline = models.DateField(null=True, blank=True, db_index=True)
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPE_CHOICES, default='curated_platform')
    source_name = models.CharField(max_length=150, blank=True, default='SkillSphere Verified Partners')
    last_verified_at = models.DateTimeField(default=timezone.now)
    min_age = models.PositiveIntegerField(
        default=18,
        help_text="Minimum age: 14 for student challenges/hackathons, 18 for full-time jobs/contracts"
    )
    is_minor_safe = models.BooleanField(
        default=True,
        help_text="Approved for high school and minor student participation"
    )
    verification_status = models.BooleanField(default=True, help_text="Verified authentic listing from official source")
    is_active = models.BooleanField(default=True, db_index=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline', '-created_at']
        verbose_name_plural = 'Opportunities'
        indexes = [
            models.Index(fields=['opportunity_type', 'is_active', 'is_archived']),
            models.Index(fields=['deadline', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} at {self.organization} ({self.get_opportunity_type_display()})"

    def get_required_skills_list(self):
        if not self.required_skills:
            return []
        return [s.strip() for s in self.required_skills.split(',') if s.strip()]

    def get_preferred_skills_list(self):
        if not self.preferred_skills:
            return []
        return [s.strip() for s in self.preferred_skills.split(',') if s.strip()]

    def get_all_skills_list(self):
        all_skills = list(self.get_required_skills_list())
        for s in self.get_preferred_skills_list():
            if s not in all_skills:
                all_skills.append(s)
        return all_skills

    @property
    def is_expired(self):
        if not self.deadline:
            return False
        return self.deadline < timezone.now().date()


class OpportunitySkill(models.Model):
    """
    Normalized relational linkage between an Opportunity and individual skills,
    distinguishing required vs preferred skills with weighting.
    """
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='skill_links')
    skill_name = models.CharField(max_length=100, db_index=True)
    is_required = models.BooleanField(default=True, help_text="True if mandatory requirement, False if preferred")
    weight = models.PositiveIntegerField(default=3, help_text="Matching weight: 3 for required, 1 for preferred")

    class Meta:
        unique_together = ('opportunity', 'skill_name')
        ordering = ['-is_required', 'skill_name']

    def __str__(self):
        req = "Required" if self.is_required else "Preferred"
        return f"{self.skill_name} ({req}) - {self.opportunity.title}"


class SavedOpportunity(models.Model):
    """
    Student application pipeline tracker.
    Tracks each stage: saved -> preparing -> applied -> assessment -> interview -> selected/rejected/withdrawn.
    Links the exact resume version snapshot used, notes, and follow-up reminders.
    """
    STATUS_CHOICES = [
        ('saved', 'Saved / Wishlist'),
        ('interested', 'Interested'),  # Kept for backward compatibility
        ('preparing', 'Preparing Application'),
        ('applied', 'Applied'),
        ('assessment', 'Assessment / Test'),
        ('interview', 'Interview'),
        ('selected', 'Selected / Offer 🎉'),
        ('rejected', 'Rejected / Not Selected'),
        ('withdrawn', 'Withdrawn'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_opportunities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='saves')
    application_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='saved', db_index=True)
    resume_version = models.ForeignKey(
        'resumes.ResumeVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opportunity_applications',
        help_text="Exact resume version snapshot submitted for this role"
    )
    application_notes = models.TextField(blank=True, help_text="Student private notes, interview questions, or next steps")
    applied_at = models.DateTimeField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True, help_text="Scheduled follow-up reminder date")
    external_reference = models.CharField(
        max_length=150,
        blank=True,
        help_text="External application tracking ID or confirmation number"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'opportunity'], name='unique_user_saved_opportunity')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.opportunity.title} ({self.get_application_status_display()})"

    @property
    def normalized_status(self):
        if self.application_status == 'interested':
            return 'saved'
        return self.application_status


# Alias for clean semantic imports
OpportunityApplication = SavedOpportunity


class ApplicationStatusHistory(models.Model):
    """
    Audit trail recording application stage transitions with timestamps,
    notes, and who enacted the change.
    """
    application = models.ForeignKey(SavedOpportunity, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.application.opportunity.title}: {self.from_status} -> {self.to_status} at {self.created_at}"


class OpportunityReport(models.Model):
    """
    Moderation and reporting for suspicious, inaccurate, or expired listings.
    """
    REASON_CHOICES = [
        ('scam', 'Suspicious / Fraudulent Listing'),
        ('expired', 'Expired Opportunity / Past Deadline'),
        ('broken_link', 'Broken Application URL'),
        ('inaccurate_info', 'Inaccurate Requirements or Compensation'),
        ('minor_safety', 'Unsafe / Inappropriate for Minor Students'),
        ('other', 'Other Issue'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved / Listing Actioned'),
        ('dismissed', 'Dismissed / Listing Verified Safe'),
    ]

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opportunity_reports')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    details = models.TextField(help_text="Specific details regarding the reported listing issue")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report on {self.opportunity.title} by {self.reported_by.username} ({self.get_reason_display()})"


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
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interview_invitations',
        help_text="Optional linked opportunity"
    )
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


