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


# =============================================================================
# SkillSphere Career Studio Models
# =============================================================================

class CareerTrack(models.Model):
    """
    Curated engineering and tech career tracks (e.g. Frontend, Backend, AI/ML).
    """
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner Friendly'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced / Specialized'),
    ]

    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    title = models.CharField(max_length=150)
    icon = models.CharField(max_length=50, default='compass', help_text="Lucide icon identifier, e.g. code, server, cpu")
    badge = models.CharField(max_length=50, default='In Demand', help_text="Short label: e.g. High Demand, Cutting Edge")
    summary = models.TextField(help_text="Concise career narrative and role summary")
    overview = models.TextField(blank=True, help_text="Comprehensive overview of role, responsibilities, and industry landscape")
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Intermediate')
    average_salary_range = models.CharField(max_length=100, blank=True, help_text="e.g. ₹6L - ₹18L / $85k - $145k")
    market_demand = models.CharField(max_length=50, default='High', help_text="Market hiring trend: High, Surging, Stable")
    
    # Structured Curated Data
    primary_skills = models.JSONField(default=list, help_text="List of core required technical skills")
    tools_and_technologies = models.JSONField(default=list, help_text="List of industry tools, libraries, and frameworks")
    suggested_projects = models.JSONField(default=list, help_text="List of recommended portfolio project briefs")
    interview_topics = models.JSONField(default=list, blank=True, help_text="High-frequency technical interview questions and topics")
    learning_milestones = models.JSONField(default=list, blank=True, help_text="Sequential learning milestone definitions")

    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'title']
        verbose_name = 'Career Track'
        verbose_name_plural = 'Career Tracks'

    def __str__(self):
        return self.title

    def get_essential_skills(self):
        return self.skill_requirements.filter(importance='essential')


class CareerSkillRequirement(models.Model):
    """
    Granular technical skill requirement belonging to a CareerTrack.
    Supports weighted matching and evidence verification.
    """
    IMPORTANCE_CHOICES = [
        ('essential', 'Essential Core (3x)'),
        ('recommended', 'Recommended (2x)'),
        ('bonus', 'Bonus / Advanced (1x)'),
    ]

    CATEGORY_CHOICES = [
        ('frontend', 'Frontend & UI'),
        ('backend', 'Backend & Architecture'),
        ('database', 'Databases & Storage'),
        ('devops', 'DevOps & Cloud'),
        ('data_ai', 'Data Science & AI/ML'),
        ('security', 'Cybersecurity & Auditing'),
        ('methodology', 'Software Engineering & Practices'),
    ]

    track = models.ForeignKey(CareerTrack, on_delete=models.CASCADE, related_name='skill_requirements')
    skill_name = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='backend')
    importance = models.CharField(max_length=20, choices=IMPORTANCE_CHOICES, default='essential')
    weight = models.PositiveIntegerField(default=3, help_text="Weight in gap calculation: 3=essential, 2=recommended, 1=bonus")
    description = models.TextField(blank=True, help_text="What this skill entails in a professional context")
    benchmark_description = models.CharField(max_length=255, blank=True, help_text="What constitutes evidence of proficiency")

    class Meta:
        ordering = ['-weight', 'skill_name']
        unique_together = ('track', 'skill_name')
        verbose_name = 'Career Skill Requirement'
        verbose_name_plural = 'Career Skill Requirements'

    def __str__(self):
        return f"{self.skill_name} ({self.track.title}) - {self.importance}"


class StudentCareerGoal(models.Model):
    """
    Tracks a student's chosen primary career track, secondary interests, and target timeline.
    """
    STATUS_CHOICES = [
        ('exploring', 'Exploring & Learning'),
        ('actively_pursuing', 'Actively Building Portfolio'),
        ('ready_for_interviews', 'Interview Ready'),
        ('placed', 'Career Placed / Hired'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='career_goal')
    primary_track = models.ForeignKey(CareerTrack, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_students')
    secondary_tracks = models.ManyToManyField(CareerTrack, blank=True, related_name='secondary_students')
    target_timeline_months = models.PositiveIntegerField(default=6, help_text="Target readiness timeline in months")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='exploring')
    notes = models.TextField(blank=True, help_text="Personal career notes or ambitions")
    selected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Career Goal'
        verbose_name_plural = 'Student Career Goals'

    def __str__(self):
        track_title = self.primary_track.title if self.primary_track else "No Primary Track"
        return f"{self.user.username} -> {track_title}"


class StudentSkillEvidence(models.Model):
    """
    Transparent skill evidence record. Connects student demonstrated performance
    across courses, assessments, code challenges, projects, and certificates.
    """
    EVIDENCE_TYPES = [
        ('course_completion', 'Course Completion'),
        ('assessment_score', 'Skill Assessment (>=70%)'),
        ('coding_submission', 'Coding Challenge Passed'),
        ('project_built', 'Verified Portfolio Project'),
        ('certificate_earned', 'Signed Platform Certificate'),
        ('self_reported', 'Self-Reported Claim (Unverified)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_evidence')
    skill_name = models.CharField(max_length=100, db_index=True)
    evidence_type = models.CharField(max_length=30, choices=EVIDENCE_TYPES)
    is_verified = models.BooleanField(default=False, help_text="True if backed by completed platform artifact")
    confidence_score = models.PositiveIntegerField(default=50, help_text="Confidence rating: 80-100% verified, <50% self-reported")
    evidence_title = models.CharField(max_length=255, help_text="Human-readable title of the backing artifact")
    reference_id = models.CharField(max_length=100, blank=True, help_text="Optional identifier/key of course, assessment, or certificate")
    metadata = models.JSONField(default=dict, blank=True, help_text="Detailed metrics (e.g. quiz score %, submission timestamp)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-confidence_score', '-is_verified', '-updated_at']
        indexes = [
            models.Index(fields=['user', 'skill_name']),
            models.Index(fields=['user', 'is_verified']),
        ]
        verbose_name = 'Student Skill Evidence'
        verbose_name_plural = 'Student Skill Evidence Records'

    def __str__(self):
        tag = "VERIFIED" if self.is_verified else "CLAIM"
        return f"[{tag}] {self.user.username} - {self.skill_name} ({self.confidence_score}%)"


class SkillGapReport(models.Model):
    """
    Snapshot of a student's skill gap analysis relative to a chosen CareerTrack.
    Provides transparent mathematical evidence breakdown and next actions.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_gap_reports')
    track = models.ForeignKey(CareerTrack, on_delete=models.CASCADE, related_name='gap_reports')
    overall_match_percentage = models.PositiveIntegerField(default=0, help_text="Weighted match score 0-100%")
    demonstrated_skills = models.JSONField(default=list, help_text="Skills meeting verified proficiency")
    improving_skills = models.JSONField(default=list, help_text="Skills in active progress or self-reported")
    missing_skills = models.JSONField(default=list, help_text="Required skills with zero evidence")
    action_plan = models.JSONField(default=list, help_text="Prioritized recommended learning and project tasks")
    score_explanation = models.TextField(blank=True, help_text="Transparent explanation of how this score was computed")
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-calculated_at']
        unique_together = ('user', 'track')
        verbose_name = 'Skill Gap Report'
        verbose_name_plural = 'Skill Gap Reports'

    def __str__(self):
        return f"{self.user.username} vs {self.track.title}: {self.overall_match_percentage}%"
