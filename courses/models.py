from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings
from django.core.cache import cache

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
    curriculum_version = models.PositiveIntegerField(default=1, help_text='Current active curriculum version')
    legacy_total_lessons = models.PositiveIntegerField(default=0, help_text='Cached lesson count for version 1')
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

    @classmethod
    def invalidate_user_progress_cache(cls, user_id, course_id):
        if user_id and course_id:
            cache.delete(f"user_course_progress_{user_id}_{course_id}")

    def get_total_lessons(self):
        return self.total_lessons_count

    def get_user_progress(self, user, use_cache=True):
        """
        Authoritative single-source-of-truth progress calculation for SkillSphere.
        Implements Video-First Learning System:
          - Video Lessons & Curriculum: 80% weight (Mandatory)
          - Tests, Quizzes & Assessments: 20% weight (100% Optional)
          - Completing all mandatory video lessons = 80% completion and unlocks certificate.
          - Optional assessments can raise progress up to 100%, but never block certificate.
          - Optional assessments cannot compensate for incomplete mandatory video lessons.
        """
        if not user or not user.is_authenticated:
            return {
                'percentage': 0,
                'overall_progress': 0,
                'video_progress': 0.0,
                'video_progress_percentage': 0,
                'optional_assessment_progress': 0.0,
                'optional_assessment_progress_percentage': 0,
                'completed_mandatory_lessons': 0,
                'total_mandatory_lessons': self.get_total_lessons(),
                'completed': 0,
                'total': self.get_total_lessons(),
                'available_optional_assessments': [],
                'optional_assessments_count': 0,
                'optional_assessments_completed': 0,
                'has_optional_assessments': False,
                'is_unlocked': False,
                'quiz_passed': False,
                'mock_passed': False,
                'is_completed': False,
                'is_certificate_eligible': False,
                'certificate_issued': False,
                'exercises_completed': 0,
                'exercises_total': 0,
                'assignments_completed': 0,
                'assignments_total': 0,
                'missing_requirements': ['Log in to track progress and unlock certificates.'],
                'optional_remaining_activities': [],
            }

        cache_key = f"user_course_progress_{user.id}_{self.id}"
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        # Check existing certificate status
        from certificates.models import Certificate
        certificate_issued = Certificate.objects.filter(user=user, course=self).exists()

        # Determine curriculum version applicable to this student
        enrollment = Enrollment.objects.filter(user=user, course=self).first()
        student_curriculum_version = enrollment.curriculum_version if enrollment else self.curriculum_version

        from learning.models import LessonProgress, Exercise, ExerciseSubmission, Assignment, AssignmentSubmission

        # If student completed any lesson with curriculum_version > student_curriculum_version,
        # auto-advance enrollment to latest course version
        if enrollment and student_curriculum_version < self.curriculum_version:
            has_newer_progress = LessonProgress.objects.filter(
                user=user,
                lesson__course=self,
                lesson__curriculum_version__gt=student_curriculum_version,
                is_completed=True
            ).exists()
            if has_newer_progress:
                student_curriculum_version = self.curriculum_version
                enrollment.curriculum_version = self.curriculum_version
                enrollment.save(update_fields=['curriculum_version'])

        # Filter lessons applicable to student's curriculum version
        applicable_lessons = self.lessons.filter(curriculum_version__lte=student_curriculum_version).order_by('lesson_order', 'id')
        total_lessons = applicable_lessons.count()
        if total_lessons == 0:
            applicable_lessons = self.lessons.all().order_by('lesson_order', 'id')
            total_lessons = applicable_lessons.count()

        if total_lessons == 0:
            return {
                'percentage': 0,
                'overall_progress': 0,
                'video_progress': 0.0,
                'video_progress_percentage': 0,
                'optional_assessment_progress': 0.0,
                'optional_assessment_progress_percentage': 0,
                'completed_mandatory_lessons': 0,
                'total_mandatory_lessons': 0,
                'completed': 0,
                'total': 0,
                'available_optional_assessments': [],
                'optional_assessments_count': 0,
                'optional_assessments_completed': 0,
                'has_optional_assessments': False,
                'is_unlocked': False,
                'quiz_passed': False,
                'mock_passed': False,
                'is_completed': False,
                'is_certificate_eligible': False,
                'certificate_issued': False,
                'exercises_completed': 0,
                'exercises_total': 0,
                'assignments_completed': 0,
                'assignments_total': 0,
                'missing_requirements': ['Course curriculum is being prepared.'],
                'optional_remaining_activities': [],
            }

        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__in=applicable_lessons if applicable_lessons.exists() else self.lessons.all(),
            is_completed=True
        ).count()

        total_exercises = Exercise.objects.filter(lesson__in=applicable_lessons if applicable_lessons.exists() else self.lessons.all()).count()
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

        # --------------------------------------------------------------------
        # 1. Video Progress (80% Weight - Mandatory)
        # --------------------------------------------------------------------
        video_ratio = (completed_lessons / total_lessons) if total_lessons > 0 else 0.0
        video_component = video_ratio * 80.0

        # --------------------------------------------------------------------
        # 2. Optional Assessments (20% Weight - 100% Optional)
        # --------------------------------------------------------------------
        active_assessments = list(self.course_assessments.filter(is_active=True).order_by('assessment_type'))
        total_optional_assessments = len(active_assessments)
        completed_optional_assessments = 0
        available_optional_assessments = []

        for a in active_assessments:
            is_passed = CourseAssessmentAttempt.objects.filter(
                user=user, assessment=a, is_passed=True
            ).exists()
            best_attempt = CourseAssessmentAttempt.objects.filter(
                user=user, assessment=a
            ).order_by('-percentage').first()
            attempts_cnt = CourseAssessmentAttempt.objects.filter(user=user, assessment=a).count()
            if is_passed:
                completed_optional_assessments += 1
            available_optional_assessments.append({
                'id': a.id,
                'title': a.title,
                'assessment_type': a.assessment_type,
                'duration_minutes': a.duration_minutes,
                'passing_percentage': a.passing_percentage,
                'is_passed': is_passed,
                'best_score': best_attempt.percentage if best_attempt else None,
                'attempts_count': attempts_cnt,
            })

        if total_optional_assessments > 0:
            assessment_ratio = completed_optional_assessments / total_optional_assessments
        else:
            assessment_ratio = 0.0
        assessment_component = assessment_ratio * 20.0

        # --------------------------------------------------------------------
        # 3. Overall Course Progress
        # --------------------------------------------------------------------
        overall_progress = min(100, int(round(video_component + assessment_component)))

        # --------------------------------------------------------------------
        # 4. Certificate Eligibility (Video-First Threshold)
        # Completing all mandatory video lessons unlocks certificate eligibility.
        # Optional assessments NEVER block certificate eligibility.
        # Optional assessments NEVER compensate for incomplete video lessons.
        # --------------------------------------------------------------------
        all_mandatory_completed = (completed_lessons >= total_lessons and total_lessons > 0)
        is_certificate_eligible = certificate_issued or all_mandatory_completed

        # Missing requirements list (Only mandatory video lessons)
        missing_requirements = []
        if not is_certificate_eligible:
            remaining_lessons = max(0, total_lessons - completed_lessons)
            missing_requirements.append(
                f"Complete {remaining_lessons} more mandatory video lesson{'s' if remaining_lessons != 1 else ''} to reach 80% video completion and unlock your certificate."
            )

        # Optional activities remaining
        optional_remaining_activities = []
        if total_optional_assessments > completed_optional_assessments:
            rem_tests = total_optional_assessments - completed_optional_assessments
            optional_remaining_activities.append(f"{rem_tests} optional test{'s' if rem_tests != 1 else ''} available for extra credit (up to +20%)")
        if total_exercises > completed_exercises:
            optional_remaining_activities.append(f"{total_exercises - completed_exercises} optional coding exercise(s) available for practice")
        if total_assignments > completed_assignments:
            optional_remaining_activities.append(f"{total_assignments - completed_assignments} optional project assignment(s) available")

        # Auto-sync CourseCompletion record
        completion, _ = CourseCompletion.objects.get_or_create(user=user, course=self)
        has_tests = total_optional_assessments > 0
        if (completion.learning_progress != overall_progress or
            completion.is_assessment_unlocked != has_tests or
            completion.is_completed != is_certificate_eligible):
            completion.learning_progress = overall_progress
            completion.is_assessment_unlocked = has_tests
            if is_certificate_eligible and not completion.is_completed:
                from django.utils import timezone
                completion.is_completed = True
                completion.completed_at = timezone.now()
            elif not is_certificate_eligible and not certificate_issued:
                completion.is_completed = False
            completion.save()

        quiz_obj = next((a for a in available_optional_assessments if a['assessment_type'] == 'final_quiz'), None)
        mock_obj = next((a for a in available_optional_assessments if a['assessment_type'] == 'final_mock'), None)

        result = {
            'percentage': overall_progress,
            'overall_progress': overall_progress,
            'weighted_course_progress': overall_progress,
            'video_progress': video_ratio,
            'video_progress_percentage': int(round(video_ratio * 100)),
            'video_completion_percentage': int(round(video_ratio * 100)),
            'assessment_bonus_percentage': int(round(assessment_component)),
            'optional_assessment_progress': assessment_ratio,
            'optional_assessment_progress_percentage': int(round(assessment_ratio * 100)),
            'completed_mandatory_lessons': completed_lessons,
            'total_mandatory_lessons': total_lessons,
            'mandatory_lessons_ratio_str': f"{completed_lessons}/{total_lessons}",
            'completed': completed_lessons,
            'total': total_lessons,
            'required_percentage': 80,
            'exercises_completed': completed_exercises,
            'exercises_total': total_exercises,
            'assignments_completed': completed_assignments,
            'assignments_total': total_assignments,
            'is_unlocked': has_tests,
            'has_optional_assessments': has_tests,
            'available_optional_assessments': available_optional_assessments,
            'optional_assessments_count': total_optional_assessments,
            'optional_assessments_completed': completed_optional_assessments,
            'quiz_passed': quiz_obj['is_passed'] if quiz_obj else False,
            'mock_passed': mock_obj['is_passed'] if mock_obj else False,
            'has_quiz': quiz_obj is not None,
            'has_mock': mock_obj is not None,
            'is_completed': is_certificate_eligible,
            'is_certificate_eligible': is_certificate_eligible,
            'certificate_issued': certificate_issued,
            'missing_requirements': missing_requirements,
            'optional_remaining_activities': optional_remaining_activities,
        }
        if use_cache:
            cache.set(cache_key, result, 120)
        return result


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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.assessment and self.assessment.course_id:
            Course.invalidate_user_progress_cache(self.user_id, self.assessment.course_id)


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
    curriculum_version = models.PositiveIntegerField(default=2, help_text='Curriculum version locked at enrollment')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Course.invalidate_user_progress_cache(self.user_id, self.course_id)

    def delete(self, *args, **kwargs):
        user_id = self.user_id
        course_id = self.course_id
        super().delete(*args, **kwargs)
        Course.invalidate_user_progress_cache(user_id, course_id)
