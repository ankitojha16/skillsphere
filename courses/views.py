import json
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.cache import cache
from .models import (
    Course, Category, Enrollment, CourseModule,
    CourseAssessment, CourseAssessmentQuestion,
    CourseAssessmentAttempt, CourseCompletion
)
from learning.models import Lesson, LessonProgress, Exercise
from goals.models import LearningActivity

def course_list_view(request):
    # Tier-1 In-memory cache for public category metadata (15 mins TTL)
    categories = cache.get('skillsphere_published_categories')
    if categories is None:
        categories = list(
            Category.objects.annotate(course_count=Count('courses', distinct=True))
            .filter(courses__is_published=True)
            .distinct()
        )
        cache.set('skillsphere_published_categories', categories, 900)

    # Base courses queryset with annotated total_lessons and enrollment_count to eliminate N+1 queries
    courses = Course.objects.filter(is_published=True).select_related('category').annotate(
        enrollment_count=Count('enrollments', distinct=True),
        total_lessons=Count('lessons', distinct=True)
    )

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        courses = courses.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(instructor_name__icontains=q)
        )

    # Category filter
    selected_category = request.GET.get('category', '').strip()
    if selected_category and selected_category != 'all':
        courses = courses.filter(category__slug=selected_category)

    # Difficulty filter
    selected_difficulty = request.GET.get('difficulty', '').strip()
    if selected_difficulty and selected_difficulty != 'all':
        courses = courses.filter(difficulty__iexact=selected_difficulty)

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'popularity':
        courses = courses.order_by('-enrollment_count', '-created_at')
    elif sort_by == 'title':
        courses = courses.order_by('title')
    # Check if this is the default unfiltered catalogue for anonymous visitors
    is_default_catalogue = (
        not request.user.is_authenticated and
        not q and
        (not selected_category or selected_category == 'all') and
        (not selected_difficulty or selected_difficulty == 'all') and
        sort_by == 'newest'
    )
    if is_default_catalogue:
        cached_catalogue = cache.get('skillsphere_course_catalogue_base')
        if cached_catalogue is not None:
            courses_list = cached_catalogue
        else:
            courses_list = list(courses)
            cache.set('skillsphere_course_catalogue_base', courses_list, 900)
    else:
        courses_list = list(courses)

    total_courses_count = len(courses_list)

    # Prepare enrolled course IDs and batch fetch progress for authenticated user
    user_enrolled_course_ids = set()
    user_progress_map = {}
    if request.user.is_authenticated:
        user_enrolled_course_ids = set(
            Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
        )
        if user_enrolled_course_ids:
            # Batch fetch completions and lesson progress in 2 fast queries instead of 40+ per-course loops
            completions = {
                c.course_id: c
                for c in CourseCompletion.objects.filter(
                    user=request.user,
                    course_id__in=user_enrolled_course_ids
                )
            }
            lesson_progress_counts = dict(
                LessonProgress.objects.filter(
                    user=request.user,
                    is_completed=True,
                    lesson__course_id__in=user_enrolled_course_ids
                ).values('lesson__course_id').annotate(cnt=Count('id')).values_list('lesson__course_id', 'cnt')
            )
            for c_id in user_enrolled_course_ids:
                comp = completions.get(c_id)
                comp_lessons = lesson_progress_counts.get(c_id, 0)
                if comp:
                    user_progress_map[c_id] = {
                        'percentage': comp.learning_progress,
                        'completed': comp_lessons,
                        'is_completed': comp.is_completed,
                    }
                else:
                    user_progress_map[c_id] = {
                        'percentage': 0,
                        'completed': comp_lessons,
                        'is_completed': False,
                    }

    courses_data = []
    for course in courses_list:
        is_enrolled = course.id in user_enrolled_course_ids
        total_lessons = getattr(course, 'total_lessons', None) or course.total_lessons_count

        if is_enrolled and course.id in user_progress_map:
            cached_prog = user_progress_map[course.id]
            pct = cached_prog.get('percentage', 0)
            comp_count = cached_prog.get('completed', 0)
            is_comp = cached_prog.get('is_completed', False)
            if comp_count > 0 and total_lessons > 0:
                calc_pct = min(100, int(round((comp_count / total_lessons) * 100)))
                pct = max(pct, calc_pct)
            if pct >= 100 or (comp_count >= total_lessons and total_lessons > 0):
                pct = 100
                is_comp = True
            prog = {
                'percentage': pct,
                'completed': comp_count,
                'total': total_lessons,
                'is_completed': is_comp,
            }
        else:
            prog = {
                'percentage': 0,
                'completed': 0,
                'total': total_lessons,
                'is_completed': False
            }

        # Strict 4-State Enrollment Logic:
        # 1. Logged-out -> 'logged_out' ("Log In to Enroll")
        # 2. Logged-in not enrolled -> 'not_enrolled' ("Enroll")
        # 3. Enrolled 100% complete -> 'completed' ("Review Course")
        # 4. Enrolled in progress -> 'in_progress' ("Continue Learning")
        if not request.user.is_authenticated:
            enrollment_state = 'logged_out'
        elif not is_enrolled:
            enrollment_state = 'not_enrolled'
        elif prog.get('percentage', 0) == 100 or prog.get('is_completed', False):
            enrollment_state = 'completed'
        else:
            enrollment_state = 'in_progress'

        courses_data.append({
            'course': course,
            'is_enrolled': is_enrolled,
            'progress': prog,
            'enrollment_state': enrollment_state,
        })

    return render(request, 'courses/list.html', {
        'courses_data': courses_data,
        'categories': categories,
        'selected_category': selected_category,
        'selected_difficulty': selected_difficulty,
        'sort_by': sort_by,
        'q': q,
        'total_courses_count': total_courses_count,
    })


def course_detail_view(request, slug):
    syllabus_cache_key = f'skillsphere_course_syllabus_{slug}'
    syllabus = cache.get(syllabus_cache_key)
    if not syllabus:
        course = get_object_or_404(
            Course.objects.filter(is_published=True)
            .select_related('category')
            .annotate(total_lessons=Count('lessons', distinct=True)),
            slug=slug
        )
        lessons = list(course.lessons.all().order_by('lesson_order', 'id'))
        modules = list(course.modules.prefetch_related('lessons').order_by('order'))
        assessments = list(course.course_assessments.filter(is_active=True).order_by('assessment_type'))

        # Pre-calculate lessons with exercises in 1 query to avoid N+1 queries in template
        lesson_ids_with_exercises = set(
            Exercise.objects.filter(lesson__course=course).values_list('lesson_id', flat=True)
        )
        syllabus = {
            'course': course,
            'lessons': lessons,
            'modules': modules,
            'assessments': assessments,
            'lesson_ids_with_exercises': lesson_ids_with_exercises,
            'total_lessons': getattr(course, 'total_lessons', len(lessons)),
            'objectives': course.get_objectives_list(),
        }
        cache.set(syllabus_cache_key, syllabus, 900)

    course = syllabus['course']
    lessons = syllabus['lessons']
    modules = syllabus['modules']
    assessments = syllabus['assessments']
    lesson_ids_with_exercises = syllabus['lesson_ids_with_exercises']
    total_lessons = syllabus['total_lessons']
    objectives = syllabus['objectives']

    is_enrolled = False
    progress_info = {
        'percentage': 0,
        'completed': 0,
        'total': total_lessons,
        'is_unlocked': False,
        'is_completed': False,
        'quiz_passed': False,
        'mock_passed': False
    }
    first_incomplete_lesson = None
    completed_lesson_ids = set()

    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
        if is_enrolled:
            progress_info = course.get_user_progress(request.user)
            completed_lesson_ids = set(
                LessonProgress.objects.filter(
                    user=request.user,
                    lesson__course=course,
                    is_completed=True
                ).values_list('lesson_id', flat=True)
            )
            # Find next incomplete lesson from prefetched list
            for lesson in lessons:
                if lesson.id not in completed_lesson_ids:
                    first_incomplete_lesson = lesson
                    break
            if not first_incomplete_lesson and lessons:
                first_incomplete_lesson = lessons[0]

    # Strict 4-State Enrollment Logic:
    if not request.user.is_authenticated:
        enrollment_state = 'logged_out'
    elif not is_enrolled:
        enrollment_state = 'not_enrolled'
    elif progress_info.get('percentage', 0) == 100 or progress_info.get('is_completed', False):
        enrollment_state = 'completed'
    else:
        enrollment_state = 'in_progress'

    first_lesson = lessons[0] if lessons else None

    return render(request, 'courses/detail.html', {
        'course': course,
        'modules': modules,
        'lessons': lessons,
        'first_lesson': first_lesson,
        'assessments': assessments,
        'completed_lesson_ids': completed_lesson_ids,
        'lesson_ids_with_exercises': lesson_ids_with_exercises,
        'is_enrolled': is_enrolled,
        'enrollment_state': enrollment_state,
        'progress_info': progress_info,
        'first_incomplete_lesson': first_incomplete_lesson,
        'objectives': course.get_objectives_list(),
    })


@login_required
def enroll_course_view(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if request.method == 'POST':
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'curriculum_version': course.curriculum_version}
        )
        if created:
            LearningActivity.objects.create(
                user=request.user,
                activity_type='ENROLL',
                reference_id=course.id,
                description=f"Enrolled in {course.title}"
            )
            messages.success(request, f"Successfully enrolled in '{course.title}'! Let's get started.")
        else:
            messages.info(request, f"You are already enrolled in '{course.title}'.")

        # Redirect to first lesson if available, otherwise course detail
        first_lesson = course.lessons.order_by('lesson_order').first()
        if first_lesson:
            return redirect('learning:lesson_detail', course_slug=course.slug, lesson_id=first_lesson.id)
        return redirect('courses:detail', slug=course.slug)

    return redirect('courses:detail', slug=course.slug)


@login_required
def upgrade_curriculum_view(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if request.method == 'POST':
        enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
        if enrollment and enrollment.curriculum_version < course.curriculum_version:
            enrollment.curriculum_version = course.curriculum_version
            enrollment.save(update_fields=['curriculum_version'])
            messages.success(request, f"Successfully upgraded your curriculum for '{course.title}' to Version {course.curriculum_version}!")
        else:
            messages.info(request, "You are already on the latest curriculum version.")
    return redirect('courses:detail', slug=course.slug)


@login_required
def unenroll_course_view(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        deleted_count, _ = Enrollment.objects.filter(user=request.user, course=course).delete()
        if deleted_count > 0:
            # Also clean up lesson progress for this course
            LessonProgress.objects.filter(user=request.user, lesson__course=course).delete()
            messages.info(request, f"You have unenrolled from '{course.title}'.")
        return redirect('courses:my_learning')
    return redirect('courses:detail', slug=course.slug)


@login_required
def my_learning_view(request):
    enrollments = list(
        Enrollment.objects.filter(user=request.user)
        .select_related('course', 'course__category')
        .order_by('-enrolled_at')
    )
    total_enrolled = len(enrollments)
    enrolled_items = []
    filter_tab = request.GET.get('tab', 'all')  # all, in_progress, completed

    if enrollments:
        course_ids = [e.course_id for e in enrollments]
        # Batch completions
        completions = {
            c.course_id: c
            for c in CourseCompletion.objects.filter(user=request.user, course_id__in=course_ids)
        }
        # Batch completed lesson IDs
        completed_lesson_ids = set(
            LessonProgress.objects.filter(
                user=request.user,
                is_completed=True,
                lesson__course_id__in=course_ids
            ).values_list('lesson_id', flat=True)
        )
        # Batch lessons ordered
        lessons_by_course = {}
        for l in Lesson.objects.filter(course_id__in=course_ids).order_by('lesson_order', 'id'):
            lessons_by_course.setdefault(l.course_id, []).append(l)

        for enrollment in enrollments:
            course = enrollment.course
            course_lessons = lessons_by_course.get(course.id, [])
            prog = course.get_user_progress(request.user)

            # Find next incomplete lesson
            next_lesson = None
            for l in course_lessons:
                if l.id not in completed_lesson_ids:
                    next_lesson = l
                    break
            if not next_lesson and course_lessons:
                next_lesson = course_lessons[0]

            item = {
                'enrollment': enrollment,
                'course': course,
                'progress': prog,
                'next_lesson': next_lesson,
                'is_completed': prog['is_completed'],
            }

            if filter_tab == 'completed' and not prog['is_completed']:
                continue
            elif filter_tab == 'in_progress' and (prog['is_completed'] or prog['total'] == 0):
                continue

            enrolled_items.append(item)

    return render(request, 'courses/my_learning.html', {
        'enrolled_items': enrolled_items,
        'active_tab': filter_tab,
        'total_enrolled': total_enrolled,
    })


@login_required
def assessment_intro_view(request, slug, assessment_type):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    assessment = get_object_or_404(course.course_assessments, assessment_type=assessment_type, is_active=True)

    progress = course.get_user_progress(request.user)
    is_unlocked = progress['is_unlocked']

    attempts = list(assessment.attempts.filter(user=request.user).order_by('-started_at'))
    best_attempt = max(attempts, key=lambda a: a.percentage) if attempts else None
    has_passed = any(a.is_passed for a in attempts)

    return render(request, 'courses/assessment_intro.html', {
        'course': course,
        'assessment': assessment,
        'progress': progress,
        'is_unlocked': is_unlocked,
        'attempts': attempts,
        'best_attempt': best_attempt,
        'has_passed': has_passed,
        'question_count': assessment.questions.count(),
    })


@login_required
def take_assessment_view(request, slug, assessment_type):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    assessment = get_object_or_404(course.course_assessments, assessment_type=assessment_type, is_active=True)
    # Enforce course enrollment for optional assessment
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, "Please enroll in the course before taking this assessment.")
        return redirect('courses:detail', slug=course.slug)

    questions = list(assessment.questions.all().order_by('order', 'id'))
    if not questions:
        messages.warning(request, "Assessment question bank is currently being prepared.")
        return redirect('courses:detail', slug=course.slug)

    attempt_number = assessment.attempts.filter(user=request.user).count() + 1

    return render(request, 'courses/assessment_take.html', {
        'course': course,
        'assessment': assessment,
        'questions': questions,
        'total_questions': len(questions),
        'duration_seconds': assessment.duration_minutes * 60,
        'attempt_number': attempt_number,
    })


@login_required
def submit_assessment_view(request, slug, assessment_type):
    if request.method != 'POST':
        return redirect('courses:assessment_intro', slug=slug, assessment_type=assessment_type)

    course = get_object_or_404(Course, slug=slug, is_published=True)
    assessment = get_object_or_404(course.course_assessments, assessment_type=assessment_type, is_active=True)

    # Server-side enrollment verification
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, "Enrollment required to take assessments.")
        return redirect('courses:detail', slug=course.slug)

    questions = list(assessment.questions.all().order_by('order', 'id'))
    total_q = len(questions)

    score = 0
    topic_breakdown = {}
    answers_record = {}

    for q in questions:
        field_name = f"question_{q.id}"
        selected = request.POST.get(field_name, '').strip().upper()
        is_correct = (selected == q.correct_answer)
        if is_correct:
            score += 1

        topic = q.topic or "Core"
        if topic not in topic_breakdown:
            topic_breakdown[topic] = {'total': 0, 'correct': 0}
        topic_breakdown[topic]['total'] += 1
        if is_correct:
            topic_breakdown[topic]['correct'] += 1

        answers_record[str(q.id)] = {
            'selected': selected,
            'correct': q.correct_answer,
            'is_correct': is_correct,
            'explanation': q.explanation
        }

    percentage = int(round((score / total_q) * 100)) if total_q > 0 else 0
    is_passed = percentage >= assessment.passing_percentage

    attempt_count = assessment.attempts.filter(user=request.user).count() + 1
    attempt = CourseAssessmentAttempt.objects.create(
        user=request.user,
        assessment=assessment,
        score=score,
        total_questions=total_q,
        percentage=percentage,
        is_passed=is_passed,
        attempt_number=attempt_count,
        answers_json=json.dumps(answers_record),
        completed_at=timezone.now()
    )

    if is_passed:
        from gamification.services import award_user_xp
        xp_amount = 100 if assessment_type == 'final_quiz' else 150
        award_user_xp(request.user, xp_amount, f"Passed {assessment.title} ({percentage}%)")

    # Refresh course completion state
    prog = course.get_user_progress(request.user)

    return render(request, 'courses/assessment_result.html', {
        'course': course,
        'assessment': assessment,
        'attempt': attempt,
        'is_passed': is_passed,
        'percentage': percentage,
        'score': score,
        'total_questions': total_q,
        'topic_breakdown': topic_breakdown,
        'answers_record': answers_record,
        'course_progress': prog,
    })
