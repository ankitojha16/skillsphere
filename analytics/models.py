import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ProductEvent(models.Model):
    """
    First-party, privacy-conscious telemetry record for beta cohorts.
    Stores internal IDs and aggregate metrics only.
    Zero collection of passwords, tokens, full emails, or PII.
    """
    EVENT_TYPES = [
        ('registration_completed', 'Registration Completed'),
        ('first_login', 'First Login'),
        ('login', 'User Login'),
        ('returning_login', 'Returning Student Login'),
        ('onboarding_completed', 'Onboarding Completed'),
        ('course_viewed', 'Course Viewed'),
        ('course_enrolled', 'Course Enrolled'),
        ('first_lesson_started', 'First Lesson Started'),
        ('lesson_completed', 'Lesson Completed'),
        ('course_completed', 'Course Completed'),
        ('assessment_attempted', 'Assessment Attempted'),
        ('first_project_created', 'First Project Created'),
        ('resume_generated', 'Resume Generated'),
        ('opportunity_saved', 'Opportunity Saved'),
        ('opportunity_applied', 'Opportunity Applied'),
        ('certificate_earned', 'Certificate Earned'),
        ('active_user_ping', 'Active User Ping'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_events'
    )
    event_type = models.CharField(max_length=64, choices=EVENT_TYPES, db_index=True)
    event_key = models.CharField(
        max_length=128,
        blank=True,
        db_index=True,
        help_text="Idempotency key e.g. first_login_user42 or enroll_42_course7"
    )
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    session_key = models.CharField(max_length=40, blank=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['event_key'],
                condition=models.Q(event_key__gt=''),
                name='unique_product_event_key'
            )
        ]

    def __str__(self):
        user_label = self.user.username if self.user else 'Anonymous'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.event_type} ({user_label})"

    @classmethod
    def track(cls, user, event_type, metadata=None, session_key='', idempotency_key=None):
        """
        Idempotent privacy-first product telemetry logging.
        """
        try:
            return cls.objects.create(
                user=user if user and getattr(user, 'is_authenticated', False) else None,
                event_type=event_type,
                event_key=idempotency_key or '',
                metadata=metadata or {},
                session_key=session_key
            )
        except Exception:
            return None


class BetaFeedback(models.Model):
    """
    Feedback and bug reports submitted by students during the private beta.
    Restricted to authorized staff triage.
    """
    CATEGORY_CHOICES = [
        ('bug', 'Bug Report'),
        ('usability', 'Usability Problem'),
        ('missing_feature', 'Missing Functionality'),
        ('content', 'Course Content Issue'),
        ('feature', 'Feature Suggestion'),
        ('feedback', 'General Feedback'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('reviewing', 'Reviewing'),
        ('resolved', 'Resolved'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical (P0 Blocker)'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='beta_feedbacks'
    )
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='feedback', db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Rating 1-5")
    description = models.TextField()
    page_url = models.CharField(max_length=500, blank=True)
    screenshot = models.ImageField(upload_to='feedback_screenshots/', null=True, blank=True)
    screenshot_data_uri = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    admin_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.get_category_display()} #{self.id} ({self.status})"


class BetaInvitation(models.Model):
    """
    Manages controlled, invite-only access for student beta cohorts (10-20 students).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]

    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=32, unique=True, db_index=True)
    cohort_name = models.CharField(max_length=64, default='Cohort 1')
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_beta_invitations'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    registered_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='beta_invitation'
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'cohort_name']),
        ]

    def __str__(self):
        return f"Invite [{self.code}] for {self.email} ({self.status})"



class DurableTaskJob(models.Model):
    """
    Durable, fault-tolerant background task model for enterprise scaling.
    Guarantees persistent queueing across process restarts with exponential retries,
    idempotency enforcement, timeouts, and dead-letter monitoring.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('dead_letter', 'Dead Letter'),
    ]

    task_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    task_name = models.CharField(max_length=120, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default='pending', db_index=True)
    retries = models.PositiveSmallIntegerField(default=0)
    max_retries = models.PositiveSmallIntegerField(default=3)
    timeout_seconds = models.PositiveIntegerField(default=60)
    error_message = models.TextField(blank=True, default='')
    worker_id = models.CharField(max_length=80, blank=True, default='')
    scheduled_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['task_name', 'status']),
        ]

    def __str__(self):
        return f"Task {self.task_name} ({self.status}) [{self.task_id}]"
