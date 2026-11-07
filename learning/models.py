from django.db import models
from django.contrib.auth.models import User
from courses.models import Course

class Lesson(models.Model):
    VIDEO_TYPE_CHOICES = [
        ('required', 'Video Required'),
        ('optional', 'Video Optional'),
        ('notes_only', 'Notes Only / No Video'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    module = models.ForeignKey('courses.CourseModule', on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')
    chapter_name = models.CharField(max_length=150, default='Module 1: Core Fundamentals')
    title = models.CharField(max_length=200)
    lesson_order = models.PositiveIntegerField(default=1)
    estimated_minutes = models.PositiveIntegerField(default=15)
    content = models.TextField(help_text='HTML/Markdown formatted content with code snippets')
    external_resources = models.TextField(blank=True, help_text='External documentation and resource links')
    
    # Video Learning Enhancements
    video_url = models.URLField(max_length=500, blank=True, help_text='YouTube embed or approved video URL')
    video_duration_seconds = models.PositiveIntegerField(default=0)
    video_type = models.CharField(max_length=20, choices=VIDEO_TYPE_CHOICES, default='optional')

    # Comprehensive Notes Enhancements
    key_takeaways = models.TextField(blank=True, help_text='Important bullet points and quick review takeaways')
    common_mistakes = models.TextField(blank=True, help_text='Common pitfalls and anti-patterns to avoid')

    curriculum_version = models.PositiveIntegerField(default=1, help_text='Curriculum version when this lesson was introduced')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['lesson_order', 'id']

    def __str__(self):
        return f"{self.course.title} - #{self.lesson_order} {self.title}"

    def is_completed_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.user_progress.filter(user=user, is_completed=True).exists()

    @property
    def embed_video_url(self):
        """Converts standard YouTube watch links, shortened youtu.be, or embed links into a safe iframe embed URL."""
        if not self.video_url:
            return ""
        url = self.video_url.strip()
        if "youtube.com/embed/" in url:
            if "enablejsapi=1" not in url:
                delim = "&" if "?" in url else "?"
                return f"{url}{delim}enablejsapi=1&rel=0"
            return url
        if "youtube.com/watch" in url:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            vid = params.get('v', [None])[0]
            if vid:
                return f"https://www.youtube.com/embed/{vid}?enablejsapi=1&rel=0"
        if "youtu.be/" in url:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            vid = parsed.path.strip('/')
            if vid:
                return f"https://www.youtube.com/embed/{vid}?enablejsapi=1&rel=0"
        return url


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name_plural = 'Lesson Progress Records'

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.user.username} - {self.lesson.title}: {status}"


class VideoProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='video_watches')
    last_position_seconds = models.FloatField(default=0)
    watched_seconds = models.FloatField(default=0)
    total_duration_seconds = models.FloatField(default=0)
    is_completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({int(self.watched_seconds)}s watched)"


class LessonBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_bookmarks')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.lesson.title}"


class StudentNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_notes')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Notes by {self.user.username} on {self.lesson.title}"


class Exercise(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    starter_code = models.TextField(blank=True)
    expected_output = models.TextField(blank=True)
    hint = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.lesson.title} - Ex #{self.order}: {self.title}"


class ExerciseSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_submissions')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='submissions')
    submitted_code = models.TextField()
    is_passed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        status = "PASSED" if self.is_passed else "ATTEMPTED"
        return f"{self.user.username} - {self.exercise.title} ({status})"


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    max_score = models.PositiveIntegerField(default=100)
    due_days_after_enroll = models.PositiveIntegerField(default=14)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.course.title} - Assignment: {self.title}"


class AssignmentSubmission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('graded', 'Graded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField(help_text='Student write-up, github repo URL, or solution architecture')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    score = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'assignment')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.assignment.title} ({self.status})"
