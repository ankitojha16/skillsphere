from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from courses.models import Course, Enrollment
from .models import Lesson, LessonProgress
from goals.models import LearningActivity

@login_required
def lesson_view(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)

    # Permission check: Student must be enrolled
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    if not is_enrolled:
        messages.warning(request, f"Please enroll in '{course.title}' to access the lessons and materials.")
        return redirect('courses:detail', slug=course.slug)

    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    all_lessons = list(course.lessons.all().order_by('lesson_order', 'id'))

    # Build completion dictionary for all lessons
    completed_lesson_ids = set(
        LessonProgress.objects.filter(
            user=request.user,
            lesson__course=course,
            is_completed=True
        ).values_list('lesson_id', flat=True)
    )

    # Current lesson completion status
    current_is_completed = lesson.id in completed_lesson_ids

    # Find previous and next lessons
    prev_lesson = None
    next_lesson = None
    for idx, l in enumerate(all_lessons):
        if l.id == lesson.id:
            if idx > 0:
                prev_lesson = all_lessons[idx - 1]
            if idx < len(all_lessons) - 1:
                next_lesson = all_lessons[idx + 1]
            break

    # Progress calculation
    total_count = len(all_lessons)
    completed_count = len(completed_lesson_ids)
    progress_percentage = int(round((completed_count / total_count) * 100)) if total_count > 0 else 0

    # Group lessons by chapter
    chapters = {}
    for l in all_lessons:
        ch = l.chapter_name or "Course Content"
        if ch not in chapters:
            chapters[ch] = []
        chapters[ch].append({
            'lesson': l,
            'is_completed': l.id in completed_lesson_ids,
            'is_current': l.id == lesson.id,
        })

    return render(request, 'learning/lesson.html', {
        'course': course,
        'lesson': lesson,
        'chapters': chapters,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'current_is_completed': current_is_completed,
        'progress_percentage': progress_percentage,
        'completed_count': completed_count,
        'total_count': total_count,
    })


@login_required
def complete_lesson_toggle(request, course_slug, lesson_id):
    if request.method != 'POST':
        return redirect('learning:lesson_detail', course_slug=course_slug, lesson_id=lesson_id)

    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    # Verify enrollment
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Not enrolled'}, status=403)
        return redirect('courses:detail', slug=course.slug)

    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'is_completed': True, 'completed_at': timezone.now()}
    )

    if not created:
        # Toggle completion
        progress.is_completed = not progress.is_completed
        progress.completed_at = timezone.now() if progress.is_completed else None
        progress.save()

    # If marked completed, log activity and award XP
    if progress.is_completed:
        LearningActivity.objects.create(
            user=request.user,
            activity_type='COMPLETE_LESSON',
            reference_id=lesson.id,
            description=f"Completed '{lesson.title}' in {course.title}"
        )
        try:
            from gamification.services import award_user_xp, award_badge_if_eligible
            award_user_xp(request.user, 25, f"Completed lesson: {lesson.title}")
            course_prog = course.get_user_progress(request.user)
            if course_prog['percentage'] == 100:
                award_user_xp(request.user, 150, f"Completed entire course: {course.title}!")
                award_badge_if_eligible(request.user, 'first-course-complete')
        except Exception:
            pass
        messages.success(request, f"Great job! Marked '{lesson.title}' as completed.")
    else:
        messages.info(request, f"Marked '{lesson.title}' as incomplete.")

    course_progress = course.get_user_progress(request.user)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_completed': progress.is_completed,
            'percentage': course_progress['percentage'],
            'completed_count': course_progress['completed'],
            'total_count': course_progress['total'],
        })

    # If standard post and marked completed, advance to next lesson if requested
    next_action = request.POST.get('next_action')
    if next_action == 'advance':
        next_lesson = course.lessons.filter(lesson_order__gt=lesson.lesson_order).order_by('lesson_order').first()
        if next_lesson:
            return redirect('learning:lesson_detail', course_slug=course.slug, lesson_id=next_lesson.id)

    return redirect('learning:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
