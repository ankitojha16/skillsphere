"""
SkillSphere Workspace Views.
Unified Student Workspace & Smart Productivity Hub controllers.
Provides authenticated endpoints for Dashboard, Daily Planner, Smart Calendar,
Focus Sessions, Personal Notes/Bookmarks, Weekly Progress Intelligence, and AI Study Planner.
"""

from datetime import datetime, date, timedelta
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models

from workspace.models import (
    WorkspaceTask, CalendarEvent, FocusSession,
    PersonalNote, WorkspaceBookmark, NotificationPreference
)
from services.workspace_intelligence import WorkspaceIntelligenceService
from services.ai_study_planner import AIStudyPlannerService
from courses.models import Course
from projects.models import ProjectIdea
from learning.models import Lesson

logger = logging.getLogger('skillsphere.workspace')


# -------------------------------------------------------------------------
# 1. Unified Student Workspace Dashboard
# -------------------------------------------------------------------------
@login_required
def workspace_dashboard_view(request):
    """
    Unified command center: /workspace/
    """
    user = request.user
    summary = WorkspaceIntelligenceService.get_student_workspace_summary(user)
    suggestions = WorkspaceIntelligenceService.generate_suggested_daily_tasks(user)

    # Folders & Pinned notes for quick access
    pinned_notes = PersonalNote.objects.filter(user=user, is_pinned=True)[:3]
    recent_bookmarks = WorkspaceBookmark.objects.filter(user=user).order_by('-created_at')[:4]

    context = {
        'summary': summary,
        'suggestions': suggestions[:3],
        'pinned_notes': pinned_notes,
        'recent_bookmarks': recent_bookmarks,
        'page_title': 'Student Workspace',
    }
    return render(request, 'workspace/dashboard.html', context)


# -------------------------------------------------------------------------
# 2. Smart Daily Planner
# -------------------------------------------------------------------------
@login_required
def planner_view(request):
    """
    Daily task planner with filtering, status pills, and smart suggestions: /workspace/planner/
    """
    user = request.user
    today = timezone.now().date()

    status_filter = request.GET.get('status', 'all')
    type_filter = request.GET.get('type', 'all')
    priority_filter = request.GET.get('priority', 'all')

    tasks_qs = WorkspaceTask.objects.filter(user=user).select_related('course', 'project', 'lesson')

    if status_filter == 'pending':
        tasks_qs = tasks_qs.filter(is_completed=False)
    elif status_filter == 'completed':
        tasks_qs = tasks_qs.filter(is_completed=True)
    elif status_filter == 'overdue':
        tasks_qs = tasks_qs.filter(is_completed=False, due_date__lt=today)
    elif status_filter == 'today':
        tasks_qs = tasks_qs.filter(is_completed=False, due_date=today)

    if type_filter != 'all':
        tasks_qs = tasks_qs.filter(task_type=type_filter)

    if priority_filter != 'all':
        tasks_qs = tasks_qs.filter(priority=priority_filter)

    suggestions = WorkspaceIntelligenceService.generate_suggested_daily_tasks(user)
    enrolled_courses = Course.objects.filter(enrollments__user=user).distinct()
    active_projects = ProjectIdea.objects.filter(user=user, workflow_status__in=['idea', 'planning', 'in_progress'])

    # Counts
    all_user_tasks = WorkspaceTask.objects.filter(user=user)
    counts = {
        'all': all_user_tasks.count(),
        'pending': all_user_tasks.filter(is_completed=False).count(),
        'completed': all_user_tasks.filter(is_completed=True).count(),
        'overdue': all_user_tasks.filter(is_completed=False, due_date__lt=today).count(),
        'today': all_user_tasks.filter(is_completed=False, due_date=today).count(),
    }

    context = {
        'tasks': tasks_qs,
        'suggestions': suggestions,
        'counts': counts,
        'current_status': status_filter,
        'current_type': type_filter,
        'current_priority': priority_filter,
        'enrolled_courses': enrolled_courses,
        'active_projects': active_projects,
        'today': today,
        'page_title': 'Smart Daily Planner',
    }
    return render(request, 'workspace/planner.html', context)


@login_required
@require_POST
def task_create_view(request):
    """
    Creates a new WorkspaceTask.
    """
    user = request.user
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, "Task title is required.")
        return redirect('workspace:planner')

    description = request.POST.get('description', '').strip()
    task_type = request.POST.get('task_type', 'personal')
    priority = request.POST.get('priority', 'medium')
    due_date_str = request.POST.get('due_date', '').strip()
    estimated_minutes = request.POST.get('estimated_minutes', 30)

    try:
        estimated_minutes = int(estimated_minutes)
    except (ValueError, TypeError):
        estimated_minutes = 30

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            due_date = timezone.now().date()

    course_id = request.POST.get('course_id') or None
    project_id = request.POST.get('project_id') or None

    course = None
    if course_id:
        course = Course.objects.filter(id=course_id).first()

    project = None
    if project_id:
        project = ProjectIdea.objects.filter(id=project_id, user=user).first()

    task = WorkspaceTask.objects.create(
        user=user,
        title=title,
        description=description,
        task_type=task_type,
        priority=priority,
        due_date=due_date,
        estimated_minutes=estimated_minutes,
        course=course,
        project=project,
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'title': task.title,
            'priority': task.priority,
            'is_completed': task.is_completed,
        })

    messages.success(request, f"Task '{task.title}' added to your planner.")
    return redirect(request.META.get('HTTP_REFERER', 'workspace:planner'))


@login_required
@require_POST
def task_toggle_view(request, task_id):
    """
    Toggles completion status of a WorkspaceTask.
    """
    task = get_object_or_404(WorkspaceTask, id=task_id, user=request.user)
    if task.is_completed:
        task.mark_uncompleted()
    else:
        task.mark_completed()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'is_completed': task.is_completed,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        })

    return redirect(request.META.get('HTTP_REFERER', 'workspace:planner'))


@login_required
@require_POST
def task_reschedule_view(request, task_id):
    """
    Reschedules an unfinished/overdue task to today, tomorrow, next week, or specific date.
    """
    task = get_object_or_404(WorkspaceTask, id=task_id, user=request.user)
    target = request.POST.get('target', 'today').strip()
    today = timezone.now().date()

    if target == 'today':
        target_date = today
    elif target == 'tomorrow':
        target_date = today + timedelta(days=1)
    elif target == 'next_week':
        target_date = today + timedelta(days=7)
    else:
        try:
            target_date = datetime.strptime(target, '%Y-%m-%d').date()
        except ValueError:
            target_date = today

    task.reschedule(target_date)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'new_due_date': str(task.due_date),
            'is_overdue': task.is_overdue,
        })

    messages.success(request, f"Task rescheduled to {task.due_date.strftime('%b %d, %Y')}.")
    return redirect(request.META.get('HTTP_REFERER', 'workspace:planner'))


@login_required
@require_POST
def task_delete_view(request, task_id):
    """
    Deletes a task with user ownership validation.
    """
    task = get_object_or_404(WorkspaceTask, id=task_id, user=request.user)
    title = task.title
    task.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'deleted_id': task_id})

    messages.success(request, f"Task '{title}' removed.")
    return redirect(request.META.get('HTTP_REFERER', 'workspace:planner'))


@login_required
@require_POST
def task_adopt_suggestion_view(request):
    """
    Adopts a smart suggestion directly into the student's daily planner.
    """
    user = request.user
    title = request.POST.get('title', '').strip()
    if not title:
        return HttpResponseBadRequest("Missing task title")

    description = request.POST.get('description', '').strip()
    task_type = request.POST.get('task_type', 'personal')
    priority = request.POST.get('priority', 'medium')
    estimated_minutes = int(request.POST.get('estimated_minutes', 30))

    course_id = request.POST.get('course_id') or None
    lesson_id = request.POST.get('lesson_id') or None
    project_id = request.POST.get('project_id') or None
    roadmap_milestone_id = request.POST.get('roadmap_milestone_id') or None
    saved_opportunity_id = request.POST.get('saved_opportunity_id') or None

    task = WorkspaceTask.objects.create(
        user=user,
        title=title,
        description=description,
        task_type=task_type,
        priority=priority,
        due_date=timezone.now().date(),
        estimated_minutes=estimated_minutes,
        course_id=course_id,
        lesson_id=lesson_id,
        project_id=project_id,
        roadmap_milestone_id=roadmap_milestone_id,
        saved_opportunity_id=saved_opportunity_id,
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'title': task.title,
        })

    messages.success(request, f"Adopted suggestion '{task.title}' into today's plan!")
    return redirect(request.META.get('HTTP_REFERER', 'workspace:planner'))


# -------------------------------------------------------------------------
# 3. Smart Calendar
# -------------------------------------------------------------------------
@login_required
def calendar_view(request):
    """
    Smart unified calendar interface: /workspace/calendar/
    """
    user = request.user
    enrolled_courses = Course.objects.filter(enrollments__user=user).distinct()
    active_projects = ProjectIdea.objects.filter(user=user, workflow_status__in=['idea', 'planning', 'in_progress'])

    context = {
        'enrolled_courses': enrolled_courses,
        'active_projects': active_projects,
        'page_title': 'Smart Calendar',
    }
    return render(request, 'workspace/calendar.html', context)


@login_required
def calendar_events_json_api(request):
    """
    JSON feed returning merged personal events and official deadlines: /workspace/calendar/events/json/
    """
    user = request.user
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    now = timezone.now()
    start_dt = now - timedelta(days=30)
    end_dt = now + timedelta(days=60)

    if start_str:
        try:
            clean_start = start_str[:10]
            start_dt = timezone.make_aware(datetime.strptime(clean_start, '%Y-%m-%d'))
        except Exception:
            pass

    if end_str:
        try:
            clean_end = end_str[:10]
            end_dt = timezone.make_aware(datetime.strptime(clean_end, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1))
        except Exception:
            pass

    events = WorkspaceIntelligenceService.get_unified_calendar_events(user, start_dt, end_dt)
    return JsonResponse(events, safe=False)


@login_required
@require_POST
def calendar_event_create_view(request):
    """
    Creates a student-authored CalendarEvent.
    """
    user = request.user
    title = request.POST.get('title', '').strip()
    if not title:
        return HttpResponseBadRequest("Event title required")

    description = request.POST.get('description', '').strip()
    event_type = request.POST.get('event_type', 'personal')
    start_str = request.POST.get('start_time', '').strip()
    end_str = request.POST.get('end_time', '').strip()
    is_all_day = request.POST.get('is_all_day') == 'true' or request.POST.get('is_all_day') == '1'
    color = request.POST.get('color', '#6366f1').strip()

    try:
        start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
    except Exception:
        start_time = timezone.now()

    try:
        end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)
    except Exception:
        end_time = start_time + timedelta(hours=1)

    ev = CalendarEvent.objects.create(
        user=user,
        title=title,
        description=description,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        is_all_day=is_all_day,
        color=color,
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'event': {
                'id': f"event-{ev.id}",
                'title': ev.title,
                'start': ev.start_time.isoformat(),
                'end': ev.end_time.isoformat(),
                'color': ev.color,
            }
        })

    messages.success(request, f"Event '{ev.title}' scheduled.")
    return redirect('workspace:calendar')


@login_required
@require_POST
def calendar_event_delete_view(request, event_id):
    """
    Deletes a CalendarEvent with strict ownership check.
    """
    ev = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
    ev.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'deleted_id': event_id})

    messages.success(request, "Event removed from calendar.")
    return redirect('workspace:calendar')


# -------------------------------------------------------------------------
# 4. Focus Sessions
# -------------------------------------------------------------------------
@login_required
def focus_session_view(request):
    """
    Focus session timer and study lounge: /workspace/focus/
    """
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    recent_sessions = FocusSession.objects.filter(user=user, completed=True).select_related('course', 'project')[:8]
    today_sessions = FocusSession.objects.filter(user=user, completed=True, created_at__date=today)
    today_minutes = today_sessions.aggregate(total=models.Sum('duration_minutes'))['total'] or 0

    week_sessions = FocusSession.objects.filter(user=user, completed=True, created_at__date__gte=week_ago)
    week_minutes = week_sessions.aggregate(total=models.Sum('duration_minutes'))['total'] or 0

    enrolled_courses = Course.objects.filter(enrollments__user=user).distinct()
    active_projects = ProjectIdea.objects.filter(user=user, workflow_status__in=['idea', 'planning', 'in_progress'])
    pending_tasks = WorkspaceTask.objects.filter(user=user, is_completed=False)[:10]

    context = {
        'recent_sessions': recent_sessions,
        'today_minutes': today_minutes,
        'today_count': today_sessions.count(),
        'week_minutes': week_minutes,
        'week_count': week_sessions.count(),
        'enrolled_courses': enrolled_courses,
        'active_projects': active_projects,
        'pending_tasks': pending_tasks,
        'page_title': 'Focus Sessions',
    }
    return render(request, 'workspace/focus.html', context)


@login_required
@require_POST
def focus_session_log_api(request):
    """
    Logs a completed focus study session.
    Strict Constraint: Does NOT award artificial XP solely for timer duration.
    """
    user = request.user
    try:
        data = json.loads(request.body) if request.body else request.POST
    except Exception:
        data = request.POST

    duration_minutes = int(data.get('duration_minutes', 25))
    session_type = data.get('session_type', 'pomodoro')
    notes = data.get('notes', '').strip()
    course_id = data.get('course_id') or None
    project_id = data.get('project_id') or None
    task_id = data.get('task_id') or None

    course = Course.objects.filter(id=course_id).first() if course_id else None
    project = ProjectIdea.objects.filter(id=project_id, user=user).first() if project_id else None
    task = WorkspaceTask.objects.filter(id=task_id, user=user).first() if task_id else None

    session = FocusSession.objects.create(
        user=user,
        session_type=session_type,
        duration_minutes=max(1, duration_minutes),
        notes=notes,
        course=course,
        project=project,
        task=task,
        completed=True,
    )

    return JsonResponse({
        'success': True,
        'session_id': session.id,
        'duration_minutes': session.duration_minutes,
        'session_type': session.get_session_type_display(),
        'message': f"Logged {session.duration_minutes}m focus session.",
    })


# -------------------------------------------------------------------------
# 5. Personal Notes & Bookmarks
# -------------------------------------------------------------------------
@login_required
def notes_view(request):
    """
    Personal notes and bookmarks hub: /workspace/notes/
    Private by default.
    """
    user = request.user
    folder_filter = request.GET.get('folder', 'all')
    search_q = request.GET.get('q', '').strip()

    notes_qs = PersonalNote.objects.filter(user=user).select_related('course', 'lesson', 'project')
    if folder_filter != 'all':
        notes_qs = notes_qs.filter(folder=folder_filter)

    if search_q:
        notes_qs = notes_qs.filter(
            models.Q(title__icontains=search_q) |
            models.Q(content__icontains=search_q) |
            models.Q(tags__icontains=search_q)
        )

    # Folders list
    folders = list(PersonalNote.objects.filter(user=user).values_list('folder', flat=True).distinct())
    if not folders:
        folders = ['General', 'Courses', 'Projects', 'Career']

    # Bookmarks
    bookmarks_qs = WorkspaceBookmark.objects.filter(user=user).select_related('course', 'lesson', 'project')
    if search_q:
        bookmarks_qs = bookmarks_qs.filter(
            models.Q(title__icontains=search_q) |
            models.Q(notes__icontains=search_q)
        )

    enrolled_courses = Course.objects.filter(enrollments__user=user).distinct()
    active_projects = ProjectIdea.objects.filter(user=user, workflow_status__in=['idea', 'planning', 'in_progress'])

    context = {
        'notes': notes_qs,
        'bookmarks': bookmarks_qs,
        'folders': sorted(set(folders)),
        'current_folder': folder_filter,
        'search_q': search_q,
        'enrolled_courses': enrolled_courses,
        'active_projects': active_projects,
        'page_title': 'Notes & Bookmarks',
    }
    return render(request, 'workspace/notes.html', context)


@login_required
@require_POST
def note_save_view(request):
    """
    Creates or updates a PersonalNote with ownership check.
    """
    user = request.user
    note_id = request.POST.get('note_id')
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, "Note title is required.")
        return redirect('workspace:notes')

    content = request.POST.get('content', '').strip()
    folder = request.POST.get('folder', 'General').strip() or 'General'
    tags = request.POST.get('tags', '').strip()
    is_pinned = request.POST.get('is_pinned') == '1' or request.POST.get('is_pinned') == 'true'

    course_id = request.POST.get('course_id') or None
    lesson_id = request.POST.get('lesson_id') or None
    project_id = request.POST.get('project_id') or None

    course = Course.objects.filter(id=course_id).first() if course_id else None
    lesson = Lesson.objects.filter(id=lesson_id).first() if lesson_id else None
    project = ProjectIdea.objects.filter(id=project_id, user=user).first() if project_id else None

    if note_id:
        note = get_object_or_404(PersonalNote, id=note_id, user=user)
        note.title = title
        note.content = content
        note.folder = folder
        note.tags = tags
        note.is_pinned = is_pinned
        note.course = course
        note.lesson = lesson
        note.project = project
        note.save()
        messages.success(request, f"Note '{note.title}' updated.")
    else:
        note = PersonalNote.objects.create(
            user=user,
            title=title,
            content=content,
            folder=folder,
            tags=tags,
            is_pinned=is_pinned,
            course=course,
            lesson=lesson,
            project=project,
        )
        messages.success(request, f"Note '{note.title}' created.")

    return redirect('workspace:notes')


@login_required
@require_POST
def note_delete_view(request, note_id):
    """
    Deletes a PersonalNote with ownership check.
    """
    note = get_object_or_404(PersonalNote, id=note_id, user=request.user)
    title = note.title
    note.delete()
    messages.success(request, f"Note '{title}' deleted.")
    return redirect('workspace:notes')


@login_required
@require_POST
def bookmark_save_view(request):
    """
    Saves a reference link or resource bookmark.
    """
    user = request.user
    title = request.POST.get('title', '').strip()
    url = request.POST.get('url', '').strip()
    if not title or not url:
        messages.error(request, "Title and URL are required.")
        return redirect('workspace:notes')

    bookmark_type = request.POST.get('bookmark_type', 'lesson')
    category = request.POST.get('category', 'Reference').strip() or 'Reference'
    notes = request.POST.get('notes', '').strip()

    course_id = request.POST.get('course_id') or None
    project_id = request.POST.get('project_id') or None

    course = Course.objects.filter(id=course_id).first() if course_id else None
    project = ProjectIdea.objects.filter(id=project_id, user=user).first() if project_id else None

    bm = WorkspaceBookmark.objects.create(
        user=user,
        title=title,
        url=url,
        bookmark_type=bookmark_type,
        category=category,
        notes=notes,
        course=course,
        project=project,
    )
    messages.success(request, f"Bookmark '{bm.title}' saved.")
    return redirect('workspace:notes')


@login_required
@require_POST
def bookmark_delete_view(request, bookmark_id):
    """
    Deletes a WorkspaceBookmark with ownership check.
    """
    bm = get_object_or_404(WorkspaceBookmark, id=bookmark_id, user=request.user)
    title = bm.title
    bm.delete()
    messages.success(request, f"Bookmark '{title}' removed.")
    return redirect('workspace:notes')


# -------------------------------------------------------------------------
# 6. Weekly Progress Intelligence
# -------------------------------------------------------------------------
@login_required
def weekly_report_view(request):
    """
    Automated weekly progress intelligence: /workspace/weekly-report/
    Strict Zero-Fabrication: All numbers reflect database activity.
    """
    user = request.user
    report = WorkspaceIntelligenceService.calculate_weekly_intelligence(user)

    context = {
        'report': report,
        'page_title': 'Weekly Progress Intelligence',
    }
    return render(request, 'workspace/weekly_report.html', context)


# -------------------------------------------------------------------------
# 7. AI Study Planner
# -------------------------------------------------------------------------
@login_required
def ai_study_planner_view(request):
    """
    AI Study Planner: /workspace/ai-planner/
    """
    user = request.user
    ai_response = None
    user_question = ""
    is_fallback = False

    if request.method == 'POST':
        user_question = request.POST.get('question', '').strip()
        if user_question:
            res = AIStudyPlannerService.ask_study_planner(user, user_question)
            ai_response = res.get('response')
            is_fallback = res.get('is_fallback', False)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': res.get('success', True),
                    'response': ai_response,
                    'is_fallback': is_fallback,
                })

    context_data = AIStudyPlannerService.gather_study_context(user)

    context = {
        'ai_response': ai_response,
        'user_question': user_question,
        'is_fallback': is_fallback,
        'context_data': context_data,
        'page_title': 'AI Study Planner',
    }
    return render(request, 'workspace/ai_planner.html', context)


# -------------------------------------------------------------------------
# 8. Notification Preferences
# -------------------------------------------------------------------------
@login_required
def notification_settings_view(request):
    """
    Notification preferences: /workspace/notifications/settings/
    """
    user = request.user
    prefs = NotificationPreference.get_or_create_for_user(user)

    if request.method == 'POST':
        prefs.notify_deadlines = request.POST.get('notify_deadlines') == 'on'
        prefs.notify_unfinished_tasks = request.POST.get('notify_unfinished_tasks') == 'on'
        prefs.notify_scheduled_learning = request.POST.get('notify_scheduled_learning') == 'on'
        prefs.notify_project_milestones = request.POST.get('notify_project_milestones') == 'on'
        prefs.notify_application_followups = request.POST.get('notify_application_followups') == 'on'
        prefs.notify_new_opportunities = request.POST.get('notify_new_opportunities') == 'on'

        adv_hours = request.POST.get('advance_reminder_hours', 24)
        try:
            prefs.advance_reminder_hours = int(adv_hours)
        except ValueError:
            prefs.advance_reminder_hours = 24

        prefs.digest_frequency = request.POST.get('digest_frequency', 'daily')
        prefs.save()

        messages.success(request, "Notification preferences updated.")
        return redirect('workspace:notification_settings')

    context = {
        'prefs': prefs,
        'page_title': 'Notification Preferences',
    }
    return render(request, 'workspace/notification_settings.html', context)
