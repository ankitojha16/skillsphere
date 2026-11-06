import json
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import (
    Course, Category, Enrollment, CourseModule,
    CourseAssessment, CourseAssessmentQuestion,
    CourseAssessmentAttempt, CourseCompletion
)
from learning.models import Lesson, LessonProgress
from goals.models import LearningActivity

def course_list_view(request):
    categories = Category.objects.annotate(course_count=Count('courses')).filter(courses__is_published=True).distinct()
    courses = Course.objects.filter(is_published=True).select_related('category').annotate(
        enrollment_count=Count('enrollments')
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
    else:  # newest
        courses = courses.order_by('-created_at')

    # Prepare enrolled course IDs for current user
    user_enrolled_course_ids = set()
    user_progress_map = {}
    if request.user.is_authenticated:
        user_enrolled_course_ids = set(
            Enrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
        )
        for course in courses:
            if course.id in user_enrolled_course_ids:
                user_progress_map[course.id] = course.get_user_progress(request.user)

    courses_data = []
    for course in courses:
        prog = user_progress_map.get(course.id, {'percentage': 0, 'completed': 0, 'total': course.lessons.count()})
        courses_data.append({
            'course': course,
            'is_enrolled': course.id in user_enrolled_course_ids,
            'progress': prog,
        })

    return render(request, 'courses/list.html', {
        'courses_data': courses_data,
        'categories': categories,
        'selected_category': selected_category,
        'selected_difficulty': selected_difficulty,
        'sort_by': sort_by,
        'q': q,
        'total_courses_count': courses.count(),
    })


def course_detail_view(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    lessons = course.lessons.all().order_by('lesson_order', 'id')
    is_enrolled = False
    progress_info = {'percentage': 0, 'completed': 0, 'total': lessons.count(), 'is_unlocked': False, 'is_completed': False, 'quiz_passed': False, 'mock_passed': False}
    first_incomplete_lesson = None
    modules = course.modules.prefetch_related('lessons').order_by('order')
    assessments = course.course_assessments.filter(is_active=True).order_by('assessment_type')
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
            # Find next incomplete lesson
            for lesson in lessons:
                if lesson.id not in completed_lesson_ids:
                    first_incomplete_lesson = lesson
                    break
            if not first_incomplete_lesson and lessons.exists():
                first_incomplete_lesson = lessons.first()

    return render(request, 'courses/detail.html', {
        'course': course,
        'modules': modules,
        'lessons': lessons,
        'assessments': assessments,
        'completed_lesson_ids': completed_lesson_ids,
        'is_enrolled': is_enrolled,
        'progress_info': progress_info,
        'first_incomplete_lesson': first_incomplete_lesson,
        'objectives': course.get_objectives_list(),
    })


@login_required
def enroll_course_view(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if request.method == 'POST':
        enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
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
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course', 'course__category').order_by('-enrolled_at')
    
    enrolled_items = []
    filter_tab = request.GET.get('tab', 'all')  # all, in_progress, completed

    for enrollment in enrollments:
        course = enrollment.course
        progress = course.get_user_progress(request.user)
        
        # Find next lesson
        completed_ids = set(
            LessonProgress.objects.filter(
                user=request.user,
                lesson__course=course,
                is_completed=True
            ).values_list('lesson_id', flat=True)
        )
        next_lesson = course.lessons.exclude(id__in=completed_ids).order_by('lesson_order').first()
        if not next_lesson:
            next_lesson = course.lessons.order_by('lesson_order').first()

        is_completed = progress['total'] > 0 and progress['percentage'] == 100

        item = {
            'enrollment': enrollment,
            'course': course,
            'progress': progress,
            'next_lesson': next_lesson,
            'is_completed': is_completed,
        }

        if filter_tab == 'completed' and not is_completed:
            continue
        elif filter_tab == 'in_progress' and (is_completed or progress['total'] == 0):
            continue

        enrolled_items.append(item)

    return render(request, 'courses/my_learning.html', {
        'enrolled_items': enrolled_items,
        'active_tab': filter_tab,
        'total_enrolled': enrollments.count(),
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

    # Server-side 80% unlock verification
    progress = course.get_user_progress(request.user)
    if not progress['is_unlocked']:
        messages.error(request, f"Assessments are locked until you reach at least 80% course progress (Current: {progress['percentage']}%).")
        return redirect('courses:assessment_intro', slug=course.slug, assessment_type=assessment_type)

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

    # Server-side 80% progress gate verification
    progress = course.get_user_progress(request.user)
    if not progress['is_unlocked']:
        messages.error(request, f"Assessments are locked until you reach at least 80% course progress (Current: {progress['percentage']}%).")
        return redirect('courses:assessment_intro', slug=course.slug, assessment_type=assessment_type)

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
