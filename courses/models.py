from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='book-open', help_text='Lucide icon name')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    thumbnail = models.ImageField(upload_to='courses/', null=True, blank=True)
    thumbnail_url = models.CharField(max_length=500, blank=True, help_text='External image URL')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Beginner')
    instructor_name = models.CharField(max_length=120, default='SkillSphere Instructor')
    instructor_title = models.CharField(max_length=150, blank=True, default='Lead Curriculum Developer')
    estimated_duration = models.CharField(max_length=50, default='12 hours')
    learning_objectives = models.TextField(blank=True, help_text='Newline-separated list of objectives')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_thumbnail_url(self):
        if self.thumbnail and hasattr(self.thumbnail, 'url'):
            return self.thumbnail.url
        if self.thumbnail_url:
            return self.thumbnail_url
        # Fallback dark high-tech gradient image with category name
        return f"https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=800&q=80"

    def get_objectives_list(self):
        if not self.learning_objectives:
            return []
        return [line.strip() for line in self.learning_objectives.split('\n') if line.strip()]

    @property
    def total_lessons_count(self):
        """Authoritative single-source count of published lessons for this course."""
        if hasattr(self, 'total_lessons') and self.total_lessons is not None:
            return self.total_lessons
        return self.lessons.count()

    def get_total_lessons(self):
        return self.total_lessons_count

    def get_user_progress(self, user):
        """
        Authoritative single-source-of-truth progress calculation for SkillSphere.
        Returns accurate weighted progress (0 to 100), activity breakdown,
        assessment unlock status (>= 80%), certificate eligibility (>= 85% + mandatory exams),
        and explicit list of missing requirements.
        """
        unlock_threshold = getattr(settings, 'ASSESSMENT_UNLOCK_THRESHOLD', 80)
        cert_threshold = getattr(settings, 'CERTIFICATE_ELIGIBILITY_THRESHOLD', 85)
        passing_pct = getattr(settings, 'ASSESSMENT_PASSING_PERCENTAGE', 70)

        if not user or not user.is_authenticated:
            return {
                'percentage': 0,
                'completed': 0,
                'total': self.get_total_lessons(),
                'is_unlocked': False,
                'quiz_passed': False,
                'mock_passed': False,
                'is_completed': False,
                'is_certificate_eligible': False,
                'exercises_completed': 0,
                'exercises_total': 0,
                'missing_requirements': ['Log in to track progress and unlock certificates.'],
            }

        total_lessons = self.lessons.count()
        if total_lessons == 0:
            return {
                'percentage': 0,
                'completed': 0,
                'total': 0,
                'is_unlocked': False,
                'quiz_passed': False,
                'mock_passed': False,
                'is_completed': False,
                'is_certificate_eligible': False,
                'exercises_completed': 0,
                'exercises_total': 0,
                'missing_requirements': ['Course curriculum is being prepared.'],
            }

        from learning.models import LessonProgress, Exercise, ExerciseSubmission, Assignment, AssignmentSubmission
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__course=self,
            is_completed=True
        ).count()

        total_exercises = Exercise.objects.filter(lesson__course=self).count()
        completed_exercises = 0
        if total_exercises > 0:
            completed_exercises = ExerciseSubmission.objects.filter(
                user=user,
                exercise__lesson__course=self,
                is_passed=True
            ).values('exercise_id').distinct().count()

        total_assignments = Assignment.objects.filter(course=self).count()
        completed_assignments = 0
        if total_assignments > 0:
            completed_assignments = AssignmentSubmission.objects.filter(
                user=user,
                assignment__course=self,
                status__in=['submitted', 'reviewed', 'graded']
            ).values('assignment_id').distinct().count()

        # Calculate authoritative course progress based on mandatory curriculum (lessons)
        percentage = min(100, int(round((completed_lessons / total_lessons) * 100)))

        is_unlocked = percentage >= unlock_threshold

        # Check CourseAssessment pass states
        has_quiz = self.course_assessments.filter(assessment_type='final_quiz', is_active=True).exists()
        has_mock = self.course_assessments.filter(assessment_type='final_mock', is_active=True).exists()

        quiz_passed = False
        if has_quiz:
            quiz_passed = CourseAssessmentAttempt.objects.filter(
                user=user,
                assessment__course=self,
                assessment__assessment_type='final_quiz',
                is_passed=True
            ).exists()
        else:
            quiz_passed = True  # Not required if not part of course

        mock_passed = False
        if has_mock:
            mock_passed = CourseAssessmentAttempt.objects.filter(
                user=user,
                assessment__course=self,
                assessment__assessment_type='final_mock',
                is_passed=True
            ).exists()
        else:
            mock_passed = True  # Not required if not part of course

        # Authoritative certificate eligibility: >= 85% progress AND passing mandatory assessments
        has_required_percentage = percentage >= cert_threshold
        is_certificate_eligible = has_required_percentage and quiz_passed and mock_passed

        # Check if already issued
        from certificates.models import Certificate
        certificate_issued = Certificate.objects.filter(user=user, course=self).exists()

        # Explicit list of missing requirements (mandatory only)
        missing_requirements = []
        if not has_required_percentage:
            missing_requirements.append(f"Reach {cert_threshold}% course progress (Currently: {percentage}%)")
        if has_quiz and not quiz_passed:
            if is_unlocked:
                missing_requirements.append(f"Pass Final Course Quiz with at least {passing_pct}%")
            else:
                missing_requirements.append(f"Reach {unlock_threshold}% progress to unlock Final Course Quiz")
        if has_mock and not mock_passed:
            if is_unlocked:
                missing_requirements.append(f"Pass Final Mock Examination with at least {passing_pct}%")
            else:
                missing_requirements.append(f"Reach {unlock_threshold}% progress to unlock Final Mock Test")

        # Optional activities remaining (for feedback, but never block certificate)
        optional_remaining_activities = []
        if total_exercises > completed_exercises:
            optional_remaining_activities.append(f"{total_exercises - completed_exercises} optional coding exercise(s) available for practice")
        if total_assignments > completed_assignments:
            optional_remaining_activities.append(f"{total_assignments - completed_assignments} optional project assignment(s) available")

        # Auto-sync CourseCompletion record
        completion, _ = CourseCompletion.objects.get_or_create(user=user, course=self)
        if (completion.learning_progress != percentage or
            completion.is_assessment_unlocked != is_unlocked or
            completion.quiz_passed != (quiz_passed and has_quiz) or
            completion.mock_passed != (mock_passed and has_mock) or
            completion.is_completed != is_certificate_eligible):
            completion.learning_progress = percentage
            completion.is_assessment_unlocked = is_unlocked
            completion.quiz_passed = bool(quiz_passed and has_quiz)
            completion.mock_passed = bool(mock_passed and has_mock)
            if is_certificate_eligible and not completion.is_completed:
                from django.utils import timezone
                completion.is_completed = True
                completion.completed_at = timezone.now()
            elif not is_certificate_eligible:
                completion.is_completed = False
            completion.save()

        return {
            'percentage': percentage,
            'required_percentage': cert_threshold,
            'completed': completed_lessons,
            'total': total_lessons,
            'exercises_completed': completed_exercises,
            'exercises_total': total_exercises,
            'assignments_completed': completed_assignments,
            'assignments_total': total_assignments,
            'is_unlocked': is_unlocked,
            'quiz_passed': bool(quiz_passed and has_quiz),
            'mock_passed': bool(mock_passed and has_mock),
            'has_quiz': has_quiz,
            'has_mock': has_mock,
            'is_completed': is_certificate_eligible,
            'is_certificate_eligible': is_certificate_eligible,
            'certificate_issued': certificate_issued,
            'missing_requirements': missing_requirements,
            'optional_remaining_activities': optional_remaining_activities,
        }


class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"

    def total_lessons(self):
        return self.lessons.count()


class CourseAssessment(models.Model):
    ASSESSMENT_TYPES = [
        ('final_quiz', 'Final Course Quiz'),
        ('final_mock', 'Final Mock Examination'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_assessments')
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    passing_percentage = models.PositiveIntegerField(default=70)
    max_attempts = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'assessment_type')
        ordering = ['assessment_type']

    def __str__(self):
        return f"{self.course.title} - {self.get_assessment_type_display()}"


class CourseAssessmentQuestion(models.Model):
    assessment = models.ForeignKey(CourseAssessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    topic = models.CharField(max_length=150, default='Core Concepts')
    option_a = models.CharField(max_length=350)
    option_b = models.CharField(max_length=350)
    option_c = models.CharField(max_length=350)
    option_d = models.CharField(max_length=350)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q#{self.id} for {self.assessment.title}: {self.question_text[:50]}"


class CourseAssessmentAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_assessment_attempts')
    assessment = models.ForeignKey(CourseAssessment, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    percentage = models.PositiveIntegerField(default=0)
    is_passed = models.BooleanField(default=False)
    attempt_number = models.PositiveIntegerField(default=1)
    answers_json = models.TextField(default='{}')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        status = "PASSED" if self.is_passed else "FAILED"
        return f"{self.user.username} - {self.assessment.title} Attempt #{self.attempt_number}: {self.percentage}% ({status})"


class CourseCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_completions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='completions')
    learning_progress = models.PositiveIntegerField(default=0)
    is_assessment_unlocked = models.BooleanField(default=False)
    quiz_passed = models.BooleanField(default=False)
    mock_passed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} - {self.course.title} (Progress: {self.learning_progress}%, Completed: {self.is_completed})"


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"
