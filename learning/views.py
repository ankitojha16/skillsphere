import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.text import slugify

from courses.models import Course, Enrollment, CourseModule
from .models import (
    Lesson,
    LessonProgress,
    VideoProgress,
    LessonBookmark,
    StudentNote,
    Exercise,
    ExerciseSubmission,
    Assignment,
    AssignmentSubmission
)
from goals.models import LearningActivity
from services.pdf_service import PDFService
from services.ai_service import AIService
from gamification.services import award_user_xp

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

    # Build completion set for all lessons
    completed_lesson_ids = set(
        LessonProgress.objects.filter(
            user=request.user,
            lesson__course=course,
            is_completed=True
        ).values_list('lesson_id', flat=True)
    )

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

    # Accurate weighted progress
    progress_info = course.get_user_progress(request.user)

    # Modules structure (if CourseModule exists, use modules, else fallback to chapter_name)
    course_modules = list(course.modules.filter(is_published=True).prefetch_related('lessons'))
    modules_data = []

    if course_modules:
        for mod in course_modules:
            mod_lessons = list(mod.lessons.all().order_by('lesson_order', 'id'))
            modules_data.append({
                'module': mod,
                'title': mod.title,
                'lessons': [
                    {
                        'lesson': ml,
                        'is_completed': ml.id in completed_lesson_ids,
                        'is_current': ml.id == lesson.id,
                    }
                    for ml in mod_lessons
                ]
            })
    else:
        # Fallback grouping by chapter_name
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
        for ch_title, ch_items in chapters.items():
            modules_data.append({
                'module': None,
                'title': ch_title,
                'lessons': ch_items,
            })

    # Video progress
    video_prog = VideoProgress.objects.filter(user=request.user, lesson=lesson).first()

    # Bookmark state
    is_bookmarked = LessonBookmark.objects.filter(user=request.user, lesson=lesson).exists()

    # Personal notes
    student_note_obj = StudentNote.objects.filter(user=request.user, lesson=lesson).first()
    student_note_content = student_note_obj.content if student_note_obj else ""

    # Exercises
    exercises = list(lesson.exercises.all().order_by('order', 'id'))
    passed_exercise_ids = set(
        ExerciseSubmission.objects.filter(
            user=request.user,
            exercise__lesson=lesson,
            is_passed=True
        ).values_list('exercise_id', flat=True)
    )
    exercises_data = [
        {
            'exercise': ex,
            'is_passed': ex.id in passed_exercise_ids,
        }
        for ex in exercises
    ]

    # Course Assessments status
    final_quiz = course.course_assessments.filter(assessment_type='final_quiz', is_active=True).first()
    final_mock = course.course_assessments.filter(assessment_type='final_mock', is_active=True).first()

    context = {
        'course': course,
        'lesson': lesson,
        'modules_data': modules_data,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'current_is_completed': current_is_completed,
        'progress_info': progress_info,
        'video_prog': video_prog,
        'is_bookmarked': is_bookmarked,
        'student_note_content': student_note_content,
        'exercises_data': exercises_data,
        'final_quiz': final_quiz,
        'final_mock': final_mock,
    }

    return render(request, 'learning/lesson.html', context)


@login_required
def complete_lesson_toggle(request, course_slug, lesson_id):
    if request.method != 'POST':
        return redirect('learning:lesson_detail', course_slug=course_slug, lesson_id=lesson_id)

    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

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
        progress.is_completed = not progress.is_completed
        progress.completed_at = timezone.now() if progress.is_completed else None
        progress.save()

    if progress.is_completed:
        LearningActivity.objects.create(
            user=request.user,
            activity_type='COMPLETE_LESSON',
            reference_id=lesson.id,
            description=f"Completed '{lesson.title}' in {course.title}"
        )
        award_user_xp(request.user, 25, f"Completed lesson: {lesson.title}", activity_key=f"lesson_{lesson.id}")
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
            'exercises_completed': course_progress.get('exercises_completed', 0),
            'exercises_total': course_progress.get('exercises_total', 0),
            'is_unlocked': course_progress['is_unlocked'],
        })

    next_action = request.POST.get('next_action')
    if next_action == 'advance':
        next_lesson = course.lessons.filter(lesson_order__gt=lesson.lesson_order).order_by('lesson_order').first()
        if next_lesson:
            return redirect('learning:lesson_detail', course_slug=course.slug, lesson_id=next_lesson.id)

    return redirect('learning:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)


@login_required
def video_progress_api(request, course_slug, lesson_id):
    """Saves server-validated video watch progress or marks as watched."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    course = get_object_or_404(Course, slug=course_slug)
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        return JsonResponse({'error': 'Enrollment required'}, status=403)

    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    try:
        data = json.loads(request.body) if request.body else request.POST
        position = float(data.get('position') or data.get('position_seconds') or 0)
        duration = float(data.get('duration') or data.get('duration_seconds') or 0)
        watched = float(data.get('watched') or data.get('watched_seconds') or 0)
        mark_completed = bool(data.get('mark_completed', False))
    except Exception:
        position = 0.0
        duration = 0.0
        watched = 0.0
        mark_completed = False

    video_prog, _ = VideoProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={
            'last_position_seconds': position,
            'total_duration_seconds': duration,
            'watched_seconds': watched,
        }
    )

    if position > 0:
        video_prog.last_position_seconds = position
    if duration > 0:
        video_prog.total_duration_seconds = duration
    if watched > video_prog.watched_seconds:
        video_prog.watched_seconds = watched

    # Mark video completed if requested or watched >= 85% of total duration
    if mark_completed:
        video_prog.is_completed = True
        if duration > 0:
            video_prog.watched_seconds = duration
        elif lesson.video_duration_seconds > 0:
            video_prog.watched_seconds = lesson.video_duration_seconds
    elif duration > 0 and (video_prog.watched_seconds / duration) >= 0.85:
        video_prog.is_completed = True

    video_prog.save()

    return JsonResponse({
        'success': True,
        'is_completed': video_prog.is_completed,
        'watched_seconds': video_prog.watched_seconds,
        'position': video_prog.last_position_seconds
    })


@login_required
def bookmark_toggle_api(request, course_slug, lesson_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    course = get_object_or_404(Course, slug=course_slug)
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        return JsonResponse({'error': 'Enrollment required'}, status=403)

    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    bookmark = LessonBookmark.objects.filter(user=request.user, lesson=lesson).first()
    if bookmark:
        bookmark.delete()
        is_bookmarked = False
    else:
        LessonBookmark.objects.create(user=request.user, lesson=lesson)
        is_bookmarked = True

    return JsonResponse({'success': True, 'is_bookmarked': is_bookmarked})


@login_required
def student_note_api(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        return JsonResponse({'error': 'Enrollment required'}, status=403)

    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    if request.method == 'POST':
        try:
            body = json.loads(request.body) if request.body else request.POST
            content = (body.get('content') or body.get('notes') or '').strip()
        except Exception:
            content = (request.POST.get('content') or request.POST.get('notes') or '').strip()

        note, _ = StudentNote.objects.get_or_create(user=request.user, lesson=lesson)
        note.content = content
        note.save()
        return JsonResponse({'success': True, 'content': note.content})

    note = StudentNote.objects.filter(user=request.user, lesson=lesson).first()
    return JsonResponse({'content': note.content if note else ''})


@login_required
def download_lesson_notes_pdf_view(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.warning(request, "Enrollment is required to download course notes.")
        return redirect('courses:detail', slug=course.slug)

    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    pdf_bytes = PDFService.generate_lesson_notes_pdf(lesson)
    filename = f"SkillSphere_Notes_{slugify(lesson.title)}.pdf"

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def exercise_submit_api(request, course_slug, lesson_id, exercise_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    course = get_object_or_404(Course, slug=course_slug)
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        return JsonResponse({'error': 'Enrollment required'}, status=403)

    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    exercise = get_object_or_404(Exercise, id=exercise_id, lesson=lesson)

    try:
        body = json.loads(request.body) if request.body else request.POST
        submitted_code = body.get('code', '').strip()
    except Exception:
        submitted_code = request.POST.get('code', '').strip()

    if not submitted_code:
        return JsonResponse({'success': False, 'message': 'Submitted code cannot be empty.'}, status=400)

    # Validate against expected output / solution keywords
    expected = (exercise.expected_output or "").strip().lower()
    is_passed = True

    if expected:
        # Check if student's solution contains expected return or tokens
        code_lower = submitted_code.lower()
        if expected not in code_lower and not any(token in code_lower for token in expected.split()):
            is_passed = False

    submission = ExerciseSubmission.objects.create(
        user=request.user,
        exercise=exercise,
        submitted_code=submitted_code,
        is_passed=is_passed
    )

    if is_passed:
        award_user_xp(request.user, 15, f"Completed practical exercise: {exercise.title}", activity_key=f"exercise_{exercise.id}")

    # Re-calculate course progress
    prog = course.get_user_progress(request.user)

    return JsonResponse({
        'success': True,
        'is_passed': is_passed,
        'message': 'Exercise solved successfully! XP awarded.' if is_passed else 'Solution attempted, but output did not match expected criteria. Review the hint and try again.',
        'course_percentage': prog['percentage'],
        'is_unlocked': prog['is_unlocked'],
    })


@login_required
def ai_notes_assist_api(request, course_slug, lesson_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    course = get_object_or_404(Course, slug=course_slug)
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        return JsonResponse({'error': 'Enrollment required'}, status=403)

    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    try:
        body = json.loads(request.body) if request.body else request.POST
        action = body.get('action', 'summarize')
    except Exception:
        action = request.POST.get('action', 'summarize')

    context_text = f"Title: {lesson.title}\nTakeaways: {lesson.key_takeaways}\nContent:\n{lesson.content}"
    result = AIService.assist_study_notes(action=action, lesson_title=lesson.title, context_text=context_text)

    return JsonResponse({
        'success': True,
        'action': action,
        'text': result.get('text', ''),
        'provider': result.get('provider', 'offline-knowledge-engine'),
        'provider_label': result.get('provider_label', 'SkillSphere Knowledge Engine'),
        'is_fallback': result.get('is_fallback', True),
    })
