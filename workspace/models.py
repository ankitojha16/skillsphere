from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class WorkspaceTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('personal', 'Personal Task'),
        ('course', 'Course Study'),
        ('exercise', 'Coding Exercise'),
        ('project', 'Project Milestone'),
        ('career', 'Career & Job Application'),
        ('assessment', 'Assessment Prep'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=30, choices=TASK_TYPE_CHOICES, default='personal', db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    estimated_minutes = models.PositiveIntegerField(default=30)
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Optional foreign key links to existing SkillSphere modules
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='workspace_tasks')
    lesson = models.ForeignKey('learning.Lesson', on_delete=models.SET_NULL, null=True, blank=True, related_name='workspace_tasks')
    project = models.ForeignKey('projects.ProjectIdea', on_delete=models.SET_NULL, null=True, blank=True, related_name='workspace_tasks')
    roadmap_milestone = models.ForeignKey('roadmaps.RoadmapMilestone', on_delete=models.SET_NULL, null=True, blank=True, related_name='workspace_tasks')
    saved_opportunity = models.ForeignKey('opportunities.SavedOpportunity', on_delete=models.SET_NULL, null=True, blank=True, related_name='workspace_tasks')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['is_completed', 'due_date', '-priority', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_completed', 'due_date'], name='ws_task_user_status_idx'),
            models.Index(fields=['user', 'task_type'], name='ws_task_user_type_idx'),
        ]

    def __str__(self):
        status = "✓ Done" if self.is_completed else "○ Pending"
        return f"[{status}] {self.title} ({self.get_task_type_display()})"

    @property
    def is_overdue(self):
        if self.is_completed or not self.due_date:
            return False
        return self.due_date < timezone.now().date()

    @property
    def is_due_today(self):
        if not self.due_date:
            return False
        return self.due_date == timezone.now().date()

    def mark_completed(self, save=True):
        self.is_completed = True
        self.completed_at = timezone.now()
        if save:
            self.save(update_fields=['is_completed', 'completed_at', 'updated_at'])

    def mark_uncompleted(self, save=True):
        self.is_completed = False
        self.completed_at = None
        if save:
            self.save(update_fields=['is_completed', 'completed_at', 'updated_at'])

    def reschedule(self, target_date, save=True):
        self.due_date = target_date
        if save:
            self.save(update_fields=['due_date', 'updated_at'])


class CalendarEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('personal', 'Personal Event'),
        ('study', 'Study Session'),
        ('deadline', 'Deadline Reminder'),
        ('review', 'Milestone Review'),
        ('hackathon', 'Hackathon / Event'),
        ('exam', 'Assessment / Exam'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, default='personal', db_index=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    is_all_day = models.BooleanField(default=False)
    color = models.CharField(max_length=20, default='#6366f1')

    # Optional references
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('projects.ProjectIdea', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time', 'end_time']
        indexes = [
            models.Index(fields=['user', 'start_time', 'end_time'], name='ws_cal_user_time_idx'),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"


class FocusSession(models.Model):
    SESSION_TYPE_CHOICES = [
        ('pomodoro', 'Pomodoro (25m)'),
        ('deep_work', 'Deep Work (50m)'),
        ('quick_review', 'Quick Review (15m)'),
        ('custom', 'Custom Duration'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='focus_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='pomodoro')
    duration_minutes = models.PositiveIntegerField(default=25)
    notes = models.TextField(blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('projects.ProjectIdea', on_delete=models.SET_NULL, null=True, blank=True)
    task = models.ForeignKey(WorkspaceTask, on_delete=models.SET_NULL, null=True, blank=True)
    completed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='ws_focus_user_date_idx'),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.get_session_type_display()} ({self.duration_minutes}m)"


class PersonalNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_notes')
    title = models.CharField(max_length=255)
    content = models.TextField(help_text='Markdown supported personal note content')
    folder = models.CharField(max_length=100, default='General', db_index=True)
    tags = models.CharField(max_length=255, blank=True, help_text='Comma-separated tags')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('learning.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('projects.ProjectIdea', on_delete=models.SET_NULL, null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-updated_at']
        indexes = [
            models.Index(fields=['user', 'folder'], name='ws_note_user_folder_idx'),
            models.Index(fields=['user', '-updated_at'], name='ws_note_user_date_idx'),
        ]

    def __str__(self):
        return f"{self.title} [{self.folder}] - {self.user.username}"

    def get_tags_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]


class WorkspaceBookmark(models.Model):
    BOOKMARK_TYPE_CHOICES = [
        ('lesson', 'Course Lesson'),
        ('project', 'Project Reference'),
        ('opportunity', 'Opportunity'),
        ('resource', 'External Resource'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_bookmarks')
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500)
    bookmark_type = models.CharField(max_length=30, choices=BOOKMARK_TYPE_CHOICES, default='lesson', db_index=True)
    category = models.CharField(max_length=100, default='Reference')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('learning.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('projects.ProjectIdea', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'bookmark_type'], name='ws_bm_user_type_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.title} ({self.get_bookmark_type_display()})"


class NotificationPreference(models.Model):
    DIGEST_CHOICES = [
        ('immediate', 'Immediate'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('off', 'Mute All'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workspace_notification_prefs')
    notify_deadlines = models.BooleanField(default=True)
    notify_unfinished_tasks = models.BooleanField(default=True)
    notify_scheduled_learning = models.BooleanField(default=True)
    notify_project_milestones = models.BooleanField(default=True)
    notify_application_followups = models.BooleanField(default=True)
    notify_new_opportunities = models.BooleanField(default=True)
    advance_reminder_hours = models.PositiveIntegerField(default=24)
    digest_frequency = models.CharField(max_length=20, choices=DIGEST_CHOICES, default='daily')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification Preferences for {self.user.username}"

    @classmethod
    def get_or_create_for_user(cls, user):
        pref, _ = cls.objects.get_or_create(user=user)
        return pref
