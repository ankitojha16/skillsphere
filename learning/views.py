import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.text import slugify

from django.db import transaction, IntegrityError
logger = logging.getLogger('skillsphere.learning')

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
    AssignmentSubmission,
    Flashcard,
    FlashcardReview
)
from goals.models import LearningActivity
from services.pdf_service import PDFService
from services.ai_service import AIService
from gamification.services import award_user_xp
from analytics.services import track_event

def get_lesson_knowledge_check(lesson):
    """
    Generates 3 structured, beginner-friendly conceptual check questions
    tailored to the lesson with immediate feedback and explanations.
    """
    title = lesson.title
    chapter = lesson.chapter_name or "Core Module"
    return [
        {
            "id": 1,
            "question": f"What is the foundational purpose of {title} in software development?",
            "options": [
                f"To structure logic, optimize execution, and make code maintainable and readable.",
                f"To bypass automated unit tests and accelerate unverified deployments.",
                f"To permanently convert high-level code into unreadable machine byte sequences.",
                f"To eliminate the need for memory management and algorithmic thinking entirely."
            ],
            "correct_idx": 0,
            "explanation": f"In {chapter}, understanding {title} provides the structural foundation for writing predictable, high-performance, and clean code."
        },
        {
            "id": 2,
            "question": f"Which of the following represents an industry best practice when implementing {title}?",
            "options": [
                "Hardcoding arbitrary values without documenting edge cases or assumptions.",
                "Writing modular, self-documenting code with clear variable names and boundary checks.",
                "Writing the entire solution inside a single global variable without functions.",
                "Ignoring error messages and suppress compiler/runtime warnings."
            ],
            "correct_idx": 1,
            "explanation": "Industry-grade code prioritizes modularity, descriptive naming, and defensive error handling to prevent runtime regressions."
        },
        {
            "id": 3,
            "question": f"What is a common pitfall beginners should actively avoid when working with {title}?",
            "options": [
                "Testing their logic against small, incremental example inputs first.",
                "Breaking down complex requirements into simpler sub-tasks.",
                "Assuming code works without verifying edge cases, boundary conditions, or null states.",
                "Reading the official documentation and study notes carefully before writing code."
            ],
            "correct_idx": 2,
            "explanation": "Beginners frequently skip boundary testing. Always verify edge cases (zero, empty inputs, or out-of-range bounds) before marking a module complete."
        }
    ]

@login_required
def lesson_view(request, course_slug, lesson_id):
    try:
        course = get_object_or_404(Course, slug=course_slug, is_published=True)

        # Permission check: Student must be enrolled
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
        if not is_enrolled:
            messages.warning(request, f"Please enroll in '{course.title}' to access the lessons and materials.")
            return redirect('courses:detail', slug=course.slug)

        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        all_lessons = list(course.lessons.all().order_by('lesson_order', 'id'))

        # Build completion set for all lessons
        try:
            completed_lesson_ids = set(
                LessonProgress.objects.filter(
                    user=request.user,
                    lesson__course=course,
                    is_completed=True
                ).values_list('lesson_id', flat=True)
            )
        except Exception as e:
            logger.warning(f"Failed to fetch completed lessons for user {request.user.id}: {e}")
            completed_lesson_ids = set()

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

        # Authoritative real-time progress lookup without stale cache
        Course.invalidate_user_progress_cache(request.user.id, course.id)
        try:
            progress_info = course.get_user_progress(request.user, use_cache=False)
        except Exception as e:
            logger.error(f"Error calculating course progress in lesson_view: {e}", exc_info=True)
            total_cnt = len(all_lessons)
            comp_cnt = len(completed_lesson_ids)
            pct = int(round((comp_cnt / total_cnt) * 80)) if total_cnt > 0 else 0
            progress_info = {
                'percentage': pct,
                'overall_progress': pct,
                'weighted_course_progress': pct,
                'video_progress': (comp_cnt / total_cnt) if total_cnt > 0 else 0.0,
                'video_progress_percentage': int(round((comp_cnt / total_cnt) * 100)) if total_cnt > 0 else 0,
                'video_completion_percentage': int(round((comp_cnt / total_cnt) * 100)) if total_cnt > 0 else 0,
                'assessment_bonus_percentage': 0,
                'optional_assessment_progress': 0.0,
                'optional_assessment_progress_percentage': 0,
                'completed_mandatory_lessons': comp_cnt,
                'total_mandatory_lessons': total_cnt,
                'mandatory_lessons_ratio_str': f"{comp_cnt}/{total_cnt}",
                'completed': comp_cnt,
                'total': total_cnt,
                'required_percentage': 80,
                'exercises_completed': 0,
                'exercises_total': 0,
                'assignments_completed': 0,
                'assignments_total': 0,
                'is_unlocked': False,
                'has_optional_assessments': False,
                'available_optional_assessments': [],
                'optional_assessments_count': 0,
                'optional_assessments_completed': 0,
                'quiz_passed': False,
                'mock_passed': False,
                'has_quiz': False,
                'has_mock': False,
                'is_completed': comp_cnt >= total_cnt and total_cnt > 0,
                'is_certificate_eligible': comp_cnt >= total_cnt and total_cnt > 0,
                'certificate_issued': False,
                'missing_requirements': [],
                'optional_remaining_activities': [],
            }

        # Check real-time certificate issued status
        from certificates.models import Certificate
        progress_info['certificate_issued'] = Certificate.objects.filter(user=request.user, course=course).exists()

        # Modules structure
        try:
            course_modules = list(course.modules.filter(is_published=True).prefetch_related('lessons'))
        except Exception:
            course_modules = []
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
        try:
            video_prog = VideoProgress.objects.filter(user=request.user, lesson=lesson).first()
        except Exception:
            video_prog = None

        # Bookmark state
        try:
            is_bookmarked = LessonBookmark.objects.filter(user=request.user, lesson=lesson).exists()
        except Exception:
            is_bookmarked = False

        # Personal notes
        try:
            student_note_obj = StudentNote.objects.filter(user=request.user, lesson=lesson).first()
            student_note_content = student_note_obj.content if student_note_obj else ""
        except Exception:
            student_note_content = ""

        # Exercises
        try:
            exercises = list(lesson.exercises.all().order_by('order', 'id'))
            submissions_map = {}
            for sub in ExerciseSubmission.objects.filter(user=request.user, exercise__lesson=lesson).order_by('id'):
                submissions_map[sub.exercise_id] = sub

            exercises_data = [
                {
                    'exercise': ex,
                    'is_passed': submissions_map.get(ex.id).is_passed if ex.id in submissions_map else False,
                    'user_code': submissions_map.get(ex.id).submitted_code if ex.id in submissions_map else "",
                }
                for ex in exercises
            ]
        except Exception as e:
            logger.warning(f"Error loading exercises: {e}")
            exercises_data = []

        # Course Assessments status
        try:
            final_quiz = course.course_assessments.filter(assessment_type='final_quiz', is_active=True).first()
            final_mock = course.course_assessments.filter(assessment_type='final_mock', is_active=True).first()
        except Exception:
            final_quiz = None
            final_mock = None

        # Knowledge check
        try:
            knowledge_check = get_lesson_knowledge_check(lesson)
        except Exception:
            knowledge_check = []

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
            'optional_assessments': progress_info.get('available_optional_assessments', []),
            'final_quiz': final_quiz,
            'final_mock': final_mock,
            'knowledge_check': knowledge_check,
        }

        # Telemetry: Track first lesson started (idempotent per user)
        track_event(
            user=request.user,
            event_type='first_lesson_started',
            metadata={'course_id': course.id, 'lesson_id': lesson.id, 'course_title': course.title},
            event_key=f"first_lesson_{request.user.id}"
        )

        return render(request, 'learning/lesson.html', context)
    except Exception as e:
        logger.error(f"Catastrophic error in lesson_view for course {course_slug}, lesson {lesson_id}: {e}", exc_info=True)
        messages.error(request, "Unable to load the requested lesson right now. Redirecting to course outline.")
        return redirect('courses:detail', slug=course_slug)


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

    desired_state = request.POST.get('action') or request.POST.get('target_state') or request.GET.get('action')

    with transaction.atomic():
        try:
            with transaction.atomic():
                progress, created = LessonProgress.objects.get_or_create(
                    user=request.user,
                    lesson=lesson,
                    defaults={'is_completed': True, 'completed_at': timezone.now()}
                )
        except IntegrityError:
            progress = LessonProgress.objects.filter(user=request.user, lesson=lesson).first()
            created = False

        prev_completed = progress.is_completed if not created else False

        if desired_state in ('complete', 'completed', 'mark_completed'):
            target_completed = True
        elif desired_state in ('incomplete', 'uncompleted', 'mark_incomplete'):
            target_completed = False
        else:
            target_completed = not progress.is_completed if not created else True

        if not created and progress.is_completed != target_completed:
            progress.is_completed = target_completed
            progress.completed_at = timezone.now() if target_completed else None
            progress.save(update_fields=['is_completed', 'completed_at'])

        if target_completed and not prev_completed:
            LearningActivity.objects.create(
                user=request.user,
                activity_type='COMPLETE_LESSON',
                reference_id=lesson.id,
                description=f"Completed '{lesson.title}' in {course.title}"
            )
            award_user_xp(request.user, 25, f"Completed lesson: {lesson.title}", activity_key=f"lesson_{lesson.id}")

            # Telemetry: Lesson completed
            track_event(
                user=request.user,
                event_type='lesson_completed',
                metadata={'course_id': course.id, 'lesson_id': lesson.id},
                event_key=f"lesson_comp_{request.user.id}_{lesson.id}"
            )
            messages.success(request, f"Great job! Marked '{lesson.title}' as completed.")
        elif not target_completed and prev_completed:
            messages.info(request, f"Marked '{lesson.title}' as incomplete.")

    Course.invalidate_user_progress_cache(request.user.id, course.id)
    course_progress = course.get_user_progress(request.user, use_cache=False)

    # Telemetry: Course completion check (idempotent per user & course)
    if course_progress.get('percentage', 0) >= 100 or course_progress.get('overall_progress', 0) >= 100:
        track_event(
            user=request.user,
            event_type='course_completed',
            metadata={'course_id': course.id, 'course_slug': course.slug, 'course_title': course.title},
            event_key=f"course_comp_{request.user.id}_{course.id}"
        )

    from certificates.models import Certificate
    course_progress['certificate_issued'] = Certificate.objects.filter(user=request.user, course=course).exists()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_completed': progress.is_completed,
            'percentage': course_progress['percentage'],
            'overall_progress': course_progress['overall_progress'],
            'video_progress': course_progress['video_progress'],
            'video_progress_percentage': course_progress['video_progress_percentage'],
            'optional_assessment_progress': course_progress['optional_assessment_progress'],
            'optional_assessment_progress_percentage': course_progress['optional_assessment_progress_percentage'],
            'completed_count': course_progress['completed'],
            'total_count': course_progress['total'],
            'completed_mandatory_lessons': course_progress['completed_mandatory_lessons'],
            'total_mandatory_lessons': course_progress['total_mandatory_lessons'],
            'exercises_completed': course_progress.get('exercises_completed', 0),
            'exercises_total': course_progress.get('exercises_total', 0),
            'has_optional_assessments': course_progress.get('has_optional_assessments', False),
            'optional_assessments_count': course_progress.get('optional_assessments_count', 0),
            'optional_assessments_completed': course_progress.get('optional_assessments_completed', 0),
            'is_unlocked': course_progress['is_unlocked'],
            'is_certificate_eligible': course_progress.get('is_certificate_eligible', False),
            'certificate_issued': course_progress.get('certificate_issued', False),
            'missing_requirements': course_progress.get('missing_requirements', []),
            'optional_remaining_activities': course_progress.get('optional_remaining_activities', []),
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

    Course.invalidate_user_progress_cache(request.user.id, course.id)
    prog = course.get_user_progress(request.user, use_cache=False)

    return JsonResponse({
        'success': True,
        'is_completed': video_prog.is_completed,
        'watched_seconds': video_prog.watched_seconds,
        'position': video_prog.last_position_seconds,
        'percentage': prog['percentage'],
        'required_percentage': prog.get('required_percentage', 80),
        'completed_count': prog['completed'],
        'total_count': prog['total'],
        'exercises_completed': prog.get('exercises_completed', 0),
        'exercises_total': prog.get('exercises_total', 0),
        'is_unlocked': prog['is_unlocked'],
        'quiz_passed': prog.get('quiz_passed', False),
        'mock_passed': prog.get('mock_passed', False),
        'is_certificate_eligible': prog.get('is_certificate_eligible', False),
        'certificate_issued': prog.get('certificate_issued', False),
        'missing_requirements': prog.get('missing_requirements', []),
        'optional_remaining_activities': prog.get('optional_remaining_activities', []),
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
        'percentage': prog['percentage'],
        'required_percentage': prog.get('required_percentage', 80),
        'course_percentage': prog['percentage'],
        'completed_count': prog['completed'],
        'total_count': prog['total'],
        'exercises_completed': prog.get('exercises_completed', 0),
        'exercises_total': prog.get('exercises_total', 0),
        'is_unlocked': prog['is_unlocked'],
        'quiz_passed': prog.get('quiz_passed', False),
        'mock_passed': prog.get('mock_passed', False),
        'is_certificate_eligible': prog.get('is_certificate_eligible', False),
        'certificate_issued': prog.get('certificate_issued', False),
        'missing_requirements': prog.get('missing_requirements', []),
        'optional_remaining_activities': prog.get('optional_remaining_activities', []),
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
        custom_question = body.get('question', '').strip()
    except Exception:
        action = request.POST.get('action', 'summarize')
        custom_question = request.POST.get('question', '').strip()

    context_text = f"Title: {lesson.title}\nTakeaways: {lesson.key_takeaways}\nContent:\n{lesson.content}"
    if custom_question:
        context_text = f"Student Question: {custom_question}\n\nLesson Context:\n" + context_text

    result = AIService.assist_study_notes(action=action, lesson_title=lesson.title, context_text=context_text)

    return JsonResponse({
        'success': True,
        'action': action,
        'text': result.get('text', ''),
        'provider': result.get('provider', 'offline-knowledge-engine'),
        'provider_label': result.get('provider_label', 'SkillSphere Knowledge Engine'),
        'is_fallback': result.get('is_fallback', True),
    })


# ============================================================================
# Spaced Repetition Flashcards Views (SM-2 Engine)
# ============================================================================

@login_required
def flashcards_hub_view(request):
    """
    Spaced Repetition Flashcard Hub.
    Lists all enrolled course decks with cards due today, mastery counts, and review triggers.
    """
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    decks = []
    total_due_today = 0
    now = timezone.now()

    for enr in enrollments:
        course = enr.course
        total_cards = course.flashcards.count()
        if total_cards == 0:
            # Auto-seed initial cards from lessons
            lessons = course.lessons.exclude(key_takeaways='').all()
            if lessons:
                for idx, les in enumerate(lessons, 1):
                    Flashcard.objects.create(
                        course=course,
                        lesson=les,
                        front=f"Core Concept from {les.title}: What is the primary takeaway?",
                        back=les.key_takeaways or les.title,
                        category=les.chapter_name or 'Core Concept',
                        order=idx
                    )
                total_cards = course.flashcards.count()

        reviews = FlashcardReview.objects.filter(user=request.user, flashcard__course=course)
        reviewed_card_ids = set(reviews.values_list('flashcard_id', flat=True))

        due_count = (total_cards - len(reviewed_card_ids)) + reviews.filter(next_review_due__lte=now).count()
        mastered_count = reviews.filter(repetition__gte=3, ease_factor__gte=2.4).count()

        total_due_today += due_count
        decks.append({
            'course': course,
            'total_cards': total_cards,
            'due_count': due_count,
            'mastered_count': mastered_count,
        })

    return render(request, 'learning/flashcards_hub.html', {
        'decks': decks,
        'total_due_today': total_due_today,
    })


@login_required
def flashcards_study_view(request, course_id):
    """
    Interactive Spaced Repetition Study Session for a Course.
    Fetches cards due today and serves the 3D flip card review interface.
    """
    course = get_object_or_404(Course, id=course_id)
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, "Please enroll in this course to review its flashcard decks.")
        return redirect('courses:detail', slug=course.slug)

    now = timezone.now()
    cards = list(course.flashcards.all().select_related('lesson'))
    if not cards:
        default_prompts = [
            ("What is the primary architectural principle emphasized in this course?",
             "Modularity, clean separation of concerns, and defensive error handling.",
             "Architecture"),
            ("How do database indexes optimize lookup performance?",
             "By constructing balanced search trees (B-Trees) that reduce lookup complexity from O(N) to O(log N).",
             "Databases"),
            ("What is the difference between synchronous blocking and asynchronous non-blocking execution?",
             "Synchronous execution halts thread progress waiting for I/O; asynchronous uses an event loop to yield control during I/O operations.",
             "Performance"),
            ("Why is automated testcase validation critical in production deployment pipelines?",
             "It prevents regressions, verifies contract compliance, and provides deterministic safety during CI/CD.",
             "Testing")
        ]
        for idx, (f, b, cat) in enumerate(default_prompts, 1):
            Flashcard.objects.create(
                course=course,
                front=f,
                back=b,
                category=cat,
                order=idx
            )
        cards = list(course.flashcards.all())

    reviews_map = {
        r.flashcard_id: r
        for r in FlashcardReview.objects.filter(user=request.user, flashcard__in=cards)
    }

    due_cards = []
    upcoming_cards = []
    for c in cards:
        rev = reviews_map.get(c.id)
        if not rev or rev.next_review_due <= now:
            due_cards.append((c, rev))
        else:
            upcoming_cards.append((c, rev))

    study_queue = due_cards if due_cards else upcoming_cards

    cards_payload = [
        {
            'id': c.id,
            'front': c.front,
            'back': c.back,
            'category': c.category,
            'difficulty': c.difficulty,
            'repetition': rev.repetition if rev else 0,
            'interval_days': rev.interval_days if rev else 1,
            'ease_factor': rev.ease_factor if rev else 2.5,
            'is_due': (not rev or rev.next_review_due <= now),
        }
        for c, rev in study_queue
    ]

    return render(request, 'learning/flashcards_study.html', {
        'course': course,
        'cards_json': json.dumps(cards_payload),
        'total_cards': len(cards_payload),
    })


@login_required
def flashcards_record_review_view(request):
    """
    POST API: records user's quality rating (0=Again, 1=Hard, 2=Good, 3=Easy)
    for a flashcard using SM-2 algorithm, logs activity, awards XP.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        if request.content_type == 'application/json':
            body = json.loads(request.body)
        else:
            body = request.POST

        card_id = int(body.get('card_id'))
        quality = int(body.get('quality', 2))

        card = get_object_or_404(Flashcard, id=card_id)
        review, _ = FlashcardReview.objects.get_or_create(user=request.user, flashcard=card)
        review.record_review(quality)

        xp_gain = 10 if quality == 3 else (5 if quality == 2 else 2)
        award_user_xp(request.user, xp_gain, f"Spaced Repetition: {card.category}")

        LearningActivity.objects.create(
            user=request.user,
            activity_type='FLASHCARD_REVIEW',
            reference_id=card.id,
            description=f"Spaced repetition review on '{card.front[:40]}...' ({card.course.title})"
        )

        return JsonResponse({
            'success': True,
            'interval_days': review.interval_days,
            'repetition': review.repetition,
            'ease_factor': review.ease_factor,
            'next_due': review.next_review_due.strftime('%Y-%m-%d'),
            'xp_awarded': xp_gain
        })
    except Exception as e:
        logger.error(f"Flashcard review error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def flashcards_auto_generate_view(request, course_id):
    """
    1-Click generation of flashcards from course lessons.
    """
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    created_count = 0

    for idx, les in enumerate(lessons, 1):
        if les.key_takeaways:
            Flashcard.objects.create(
                course=course,
                lesson=les,
                front=f"Key Principle from Lesson #{les.lesson_order}: {les.title}",
                back=les.key_takeaways,
                category=les.chapter_name or 'Core Concept',
                order=idx
            )
            created_count += 1

    messages.success(request, f"Generated {created_count} flashcards from course lesson takeaways!")
    return redirect('learning:flashcards_study', course_id=course.id)


@login_required
def socratic_debug_api(request):
    """
    Socratic AI Code Debugger API.
    Analyzes code + error traceback and returns a 3-tier hint ladder
    (Conceptual clue -> Edge-case pointer -> 1-click diff patch).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        if request.content_type == 'application/json':
            body = json.loads(request.body)
        else:
            body = request.POST

        language = body.get('language', 'python')
        code = body.get('code', '')
        error_trace = body.get('error_trace', '')
        lesson_title = body.get('lesson_title', '')

        if not code.strip():
            return JsonResponse({'error': 'No code provided for debugging'}, status=400)

        result = AIService.debug_code_socratic(
            language=language,
            code=code,
            error_trace=error_trace,
            lesson_title=lesson_title
        )

        return JsonResponse({
            'success': True,
            'debug': result
        })
    except Exception as e:
        logger.error(f"socratic_debug_api error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def lesson_podcast_api(request, course_slug, lesson_id):
    """
    Synthesizes a 2-person podcast conversation (Alex & Morgan)
    summarizing the current lesson for conversational audio playback.
    """
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    try:
        content_summary = f"{lesson.key_takeaways or ''}\n\n{lesson.content or ''}"
        podcast_data = AIService.generate_lesson_podcast(
            lesson_title=lesson.title,
            lesson_content=content_summary,
            course_title=course.title
        )

        return JsonResponse({
            'success': True,
            'podcast': podcast_data
        })
    except Exception as e:
        logger.error(f"lesson_podcast_api error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


