"""
SkillSphere Workspace Intelligence Service.
Aggregates authentic student platform data into daily plans, task recommendations,
unified calendar feeds, and verified weekly progress intelligence.
Strict Zero-Fabrication Policy: Only actual recorded database activities are compiled.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Q, Count

from workspace.models import WorkspaceTask, CalendarEvent, FocusSession, PersonalNote, WorkspaceBookmark
from courses.models import Course, Enrollment
from learning.models import Lesson, LessonProgress, ExerciseSubmission
from roadmaps.models import LearningRoadmap, RoadmapMilestone
from projects.models import ProjectIdea, ProjectMilestone
from opportunities.models import SavedOpportunity, ApplicationStatusHistory
from certificates.models import Certificate
from gamification.models import UserBadge, UserGamification
from events.models import Event, SavedEvent


class WorkspaceIntelligenceService:

    @classmethod
    def get_student_workspace_summary(cls, user: User) -> Dict[str, Any]:
        """
        Compiles the complete single-pane-of-glass overview for /workspace/.
        """
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)

        # 1. Daily Tasks Summary
        user_tasks = WorkspaceTask.objects.filter(user=user)
        pending_tasks = user_tasks.filter(is_completed=False)
        overdue_tasks = pending_tasks.filter(due_date__lt=today).order_by('due_date', '-priority')
        today_tasks = pending_tasks.filter(due_date=today).order_by('-priority', 'created_at')
        upcoming_tasks = pending_tasks.filter(due_date__gt=today).order_by('due_date')[:5]
        completed_today_count = user_tasks.filter(is_completed=True, completed_at__date=today).count()
        total_pending_count = pending_tasks.count()

        # 2. Active Course Enrollments with Progress
        enrollments = Enrollment.objects.filter(
            user=user
        ).select_related('course').order_by('-enrolled_at')[:4]

        active_courses = []
        for enr in enrollments:
            course = enr.course
            progress_data = course.get_user_progress(user)
            # Find next incomplete lesson
            completed_lesson_ids = LessonProgress.objects.filter(
                user=user, lesson__course=course, is_completed=True
            ).values_list('lesson_id', flat=True)
            next_lesson = course.lessons.exclude(id__in=completed_lesson_ids).order_by('lesson_order').first()

            active_courses.append({
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
                'progress_percentage': progress_data.get('percentage', 0),
                'completed_lessons': progress_data.get('completed', 0),
                'total_lessons': progress_data.get('total', 0),
                'next_lesson': next_lesson,
            })

        # 3. Learning Roadmap Progress
        active_roadmap = LearningRoadmap.objects.filter(user=user).order_by('-updated_at').first()
        roadmap_summary = None
        if active_roadmap:
            progress = active_roadmap.get_progress()
            next_milestone = active_roadmap.milestones.filter(is_completed=False).order_by('milestone_order').first()
            roadmap_summary = {
                'id': active_roadmap.id,
                'title': active_roadmap.title,
                'target_skill': active_roadmap.target_skill,
                'percentage': progress.get('percentage', 0),
                'completed': progress.get('completed', 0),
                'total': progress.get('total', 0),
                'next_milestone': next_milestone,
            }

        # 4. Active Projects in Delivery Pipeline
        active_projects_qs = ProjectIdea.objects.filter(
            user=user,
            workflow_status__in=['idea', 'planning', 'in_progress']
        ).order_by('-updated_at')[:3]

        active_projects = []
        for proj in active_projects_qs:
            next_p_milestone = proj.milestones.filter(is_completed=False).order_by('order').first()
            active_projects.append({
                'id': proj.id,
                'ref': proj.project_ref,
                'title': proj.title,
                'workflow_status': proj.get_workflow_status_display(),
                'raw_status': proj.workflow_status,
                'progress_percentage': proj.get_progress_percentage(),
                'next_milestone': next_p_milestone,
                'completion_date': proj.completion_date,
            })

        # 5. Opportunity Deadlines & Follow-ups
        saved_opps = SavedOpportunity.objects.filter(
            user=user,
            application_status__in=['saved', 'preparing', 'applied', 'interviewing', 'interested']
        ).select_related('opportunity').order_by('opportunity__deadline')[:5]

        opportunity_deadlines = []
        for so in saved_opps:
            opp = so.opportunity
            days_left = None
            if opp.deadline:
                days_left = (opp.deadline - today).days if isinstance(opp.deadline, date) else (opp.deadline.date() - today).days
            opportunity_deadlines.append({
                'id': opp.id,
                'title': opp.title,
                'company': opp.organization,
                'deadline': opp.deadline,
                'days_left': days_left,
                'is_urgent': days_left is not None and 0 <= days_left <= 3,
                'is_expired': days_left is not None and days_left < 0,
                'application_status': so.normalized_status,
                'follow_up_date': so.follow_up_date,
            })

        # 6. Focus Sessions Statistics
        focus_today = FocusSession.objects.filter(user=user, completed=True, created_at__date=today)
        focus_minutes_today = focus_today.aggregate(total=Sum('duration_minutes'))['total'] or 0
        focus_sessions_today_count = focus_today.count()

        focus_week = FocusSession.objects.filter(user=user, completed=True, created_at__date__gte=week_ago)
        focus_minutes_week = focus_week.aggregate(total=Sum('duration_minutes'))['total'] or 0

        # 7. Gamification & Recent Achievements
        gamification = UserGamification.objects.filter(user=user).first()
        recent_badges = UserBadge.objects.filter(
            user=user, awarded_at__date__gte=week_ago
        ).select_related('badge').order_by('-awarded_at')[:3]
        recent_certs = Certificate.objects.filter(
            user=user, issued_at__date__gte=week_ago
        ).order_by('-issued_at')[:2]

        return {
            'today': today,
            'day_name': now.strftime('%A'),
            'today_formatted': now.strftime('%B %d, %Y'),
            # Task counts
            'today_tasks': today_tasks,
            'overdue_tasks': overdue_tasks,
            'upcoming_tasks': upcoming_tasks,
            'total_pending_count': total_pending_count,
            'overdue_count': overdue_tasks.count(),
            'completed_today_count': completed_today_count,
            # Subsystems
            'active_courses': active_courses,
            'roadmap_summary': roadmap_summary,
            'active_projects': active_projects,
            'opportunity_deadlines': opportunity_deadlines,
            # Focus sessions
            'focus_minutes_today': focus_minutes_today,
            'focus_sessions_today_count': focus_sessions_today_count,
            'focus_minutes_week': focus_minutes_week,
            # Stats & Achievements
            'current_streak': gamification.current_streak if gamification else 0,
            'total_xp': gamification.total_xp if gamification else 0,
            'recent_badges': recent_badges,
            'recent_certs': recent_certs,
        }

    @classmethod
    def generate_suggested_daily_tasks(cls, user: User) -> List[Dict[str, Any]]:
        """
        Generates actionable, personalized daily task recommendations based strictly
        on uncompleted platform milestones. Students can adopt them with one click.
        """
        suggestions = []
        existing_task_titles = set(
            WorkspaceTask.objects.filter(user=user, is_completed=False).values_list('title', flat=True)
        )

        # 1. Course lesson recommendation
        enrollment = Enrollment.objects.filter(
            user=user
        ).select_related('course').order_by('-enrolled_at').first()

        if enrollment:
            course = enrollment.course
            completed_lesson_ids = LessonProgress.objects.filter(
                user=user, lesson__course=course, is_completed=True
            ).values_list('lesson_id', flat=True)
            next_lesson = course.lessons.exclude(id__in=completed_lesson_ids).order_by('lesson_order').first()
            if next_lesson:
                title = f"Study: {next_lesson.title} ({course.title})"
                if title not in existing_task_titles:
                    suggestions.append({
                        'title': title,
                        'description': f"Continue learning module in {course.title}. Estimated time: {next_lesson.estimated_minutes} min.",
                        'task_type': 'course',
                        'priority': 'medium',
                        'estimated_minutes': next_lesson.estimated_minutes or 20,
                        'course_id': course.id,
                        'lesson_id': next_lesson.id,
                    })

        # 2. Roadmap Milestone recommendation
        roadmap = LearningRoadmap.objects.filter(user=user).order_by('-updated_at').first()
        if roadmap:
            next_milestone = roadmap.milestones.filter(is_completed=False).order_by('milestone_order').first()
            if next_milestone:
                title = f"Roadmap: Complete {next_milestone.title}"
                if title not in existing_task_titles:
                    suggestions.append({
                        'title': title,
                        'description': f"Advance your {roadmap.title} goal. Next milestone: {next_milestone.description[:120]}...",
                        'task_type': 'personal',
                        'priority': 'high',
                        'estimated_minutes': 45,
                        'roadmap_milestone_id': next_milestone.id,
                    })

        # 3. Active Project Milestone
        active_project = ProjectIdea.objects.filter(
            user=user, workflow_status__in=['idea', 'planning', 'in_progress']
        ).order_by('-updated_at').first()

        if active_project:
            next_p_milestone = active_project.milestones.filter(is_completed=False).order_by('order').first()
            if next_p_milestone:
                title = f"Project: {next_p_milestone.title} ({active_project.title})"
                if title not in existing_task_titles:
                    suggestions.append({
                        'title': title,
                        'description': f"Deliver milestone for project {active_project.title}.",
                        'task_type': 'project',
                        'priority': 'high',
                        'estimated_minutes': 60,
                        'project_id': active_project.id,
                    })

        # 4. Approaching Application Follow-up / Deadline
        today = timezone.now().date()
        approaching_so = SavedOpportunity.objects.filter(
            user=user,
            application_status__in=['saved', 'preparing', 'applied']
        ).filter(
            Q(opportunity__deadline__lte=today + timedelta(days=5), opportunity__deadline__gte=today) |
            Q(follow_up_date__lte=today + timedelta(days=2), follow_up_date__gte=today)
        ).select_related('opportunity').first()

        if approaching_so:
            opp = approaching_so.opportunity
            title = f"Application: Review & Polish for {opp.organization}"
            if title not in existing_task_titles:
                suggestions.append({
                    'title': title,
                    'description': f"Upcoming deadline for {opp.title} at {opp.organization}.",
                    'task_type': 'career',
                    'priority': 'urgent',
                    'estimated_minutes': 30,
                    'saved_opportunity_id': approaching_so.id,
                })

        return suggestions

    @classmethod
    def get_unified_calendar_events(cls, user: User, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """
        Merges personal events, task deadlines, opportunity application deadlines,
        and project target dates into a unified calendar feed.
        """
        events = []

        # 1. Student Personal Calendar Events
        personal_events = CalendarEvent.objects.filter(
            user=user,
            start_time__lte=end_dt,
            end_time__gte=start_dt
        )
        for ev in personal_events:
            events.append({
                'id': f"event-{ev.id}",
                'raw_id': ev.id,
                'title': ev.title,
                'description': ev.description,
                'start': ev.start_time.isoformat(),
                'end': ev.end_time.isoformat(),
                'allDay': ev.is_all_day,
                'color': ev.color or '#6366f1',
                'type': ev.event_type,
                'is_official': False,
                'category_label': ev.get_event_type_display(),
                'can_edit': True,
            })

        # 2. Workspace Task Deadlines
        start_date = start_dt.date()
        end_date = end_dt.date()
        tasks = WorkspaceTask.objects.filter(
            user=user,
            due_date__gte=start_date,
            due_date__lte=end_date
        )
        for task in tasks:
            color = '#10b981' if task.is_completed else ('#ef4444' if task.is_overdue else '#3b82f6')
            events.append({
                'id': f"task-{task.id}",
                'raw_id': task.id,
                'title': f"{'✓ ' if task.is_completed else '○ '}{task.title}",
                'description': task.description or f"Task priority: {task.get_priority_display()}",
                'start': datetime.combine(task.due_date, datetime.min.time()).isoformat(),
                'end': datetime.combine(task.due_date, datetime.max.time()).isoformat(),
                'allDay': True,
                'color': color,
                'type': 'task_deadline',
                'is_official': False,
                'category_label': f"Task: {task.get_task_type_display()}",
                'can_edit': False,
                'is_completed': task.is_completed,
            })

        # 3. Saved Opportunity Official Deadlines & Follow-ups
        saved_opps = SavedOpportunity.objects.filter(
            user=user,
            opportunity__deadline__isnull=False,
            opportunity__deadline__lte=end_date,
            opportunity__deadline__gte=start_date
        ).select_related('opportunity')

        for so in saved_opps:
            opp = so.opportunity
            start_iso = datetime.combine(opp.deadline, datetime.min.time()).isoformat() if isinstance(opp.deadline, date) else opp.deadline.isoformat()
            events.append({
                'id': f"opp-{opp.id}",
                'raw_id': opp.id,
                'title': f"🎯 Deadline: {opp.title} ({opp.organization})",
                'description': f"Official Opportunity Deadline: {opp.get_opportunity_type_display()}",
                'start': start_iso,
                'end': start_iso,
                'allDay': True,
                'color': '#ec4899',
                'type': 'opportunity_deadline',
                'is_official': True,
                'category_label': 'Official Program Deadline',
                'can_edit': False,
                'url': f"/opportunities/{opp.id}/",
            })

        # 4. Project Target Completion Dates
        projects = ProjectIdea.objects.filter(
            user=user,
            completion_date__isnull=False,
            completion_date__gte=start_date,
            completion_date__lte=end_date
        )
        for proj in projects:
            events.append({
                'id': f"proj-{proj.id}",
                'raw_id': proj.id,
                'title': f"🚀 Project Target: {proj.title}",
                'description': f"Delivery target for {proj.get_workflow_status_display()}",
                'start': datetime.combine(proj.completion_date, datetime.min.time()).isoformat(),
                'end': datetime.combine(proj.completion_date, datetime.max.time()).isoformat(),
                'allDay': True,
                'color': '#8b5cf6',
                'type': 'project_target',
                'is_official': False,
                'category_label': 'Project Target',
                'can_edit': False,
            })

        # 5. Saved Events (Hackathons / Competitions)
        saved_events = SavedEvent.objects.filter(
            user=user,
            event__start_date__lte=end_dt,
            event__end_date__gte=start_dt
        ).select_related('event')

        for se in saved_events:
            ev = se.event
            events.append({
                'id': f"event-saved-{ev.id}",
                'raw_id': ev.id,
                'title': f"🏆 {ev.title}",
                'description': f"{ev.organizer} - {ev.get_category_display()}",
                'start': ev.start_date.isoformat(),
                'end': ev.end_date.isoformat(),
                'allDay': False,
                'color': '#f59e0b',
                'type': 'official_event',
                'is_official': True,
                'category_label': ev.get_category_display(),
                'can_edit': False,
            })

        # Sort chronologically
        events.sort(key=lambda x: x['start'])
        return events

    @classmethod
    def calculate_weekly_intelligence(cls, user: User, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Compiles an honest, auditable 7-day progress intelligence report.
        Zero-Fabrication Policy: All metrics reflect recorded rows.
        """
        if target_date is None:
            target_date = timezone.now().date()

        start_date = target_date - timedelta(days=6)

        # 1. Lessons completed
        lessons_completed_count = LessonProgress.objects.filter(
            user=user,
            is_completed=True,
            completed_at__date__gte=start_date,
            completed_at__date__lte=target_date
        ).count()

        # 2. Focus Sessions & Minutes
        focus_qs = FocusSession.objects.filter(
            user=user,
            completed=True,
            created_at__date__gte=start_date,
            created_at__date__lte=target_date
        )
        focus_sessions_count = focus_qs.count()
        total_focus_minutes = focus_qs.aggregate(total=Sum('duration_minutes'))['total'] or 0

        # 3. Coding Exercises Passed
        exercises_passed = ExerciseSubmission.objects.filter(
            user=user,
            is_passed=True,
            submitted_at__date__gte=start_date,
            submitted_at__date__lte=target_date
        ).count()

        # 4. Project Milestones Completed
        project_milestones_done = ProjectMilestone.objects.filter(
            project__user=user,
            is_completed=True,
            completed_at__date__gte=start_date,
            completed_at__date__lte=target_date
        ).count()

        # 5. Roadmap Milestones Checked Off
        roadmap_milestones_done = RoadmapMilestone.objects.filter(
            roadmap__user=user,
            is_completed=True,
            completed_at__date__gte=start_date,
            completed_at__date__lte=target_date
        ).count()

        # 6. Applications Updated / Followed up
        apps_updated = ApplicationStatusHistory.objects.filter(
            application__user=user,
            created_at__date__gte=start_date,
            created_at__date__lte=target_date
        ).count()

        # 7. Certificates Earned
        certs_earned = Certificate.objects.filter(
            user=user,
            issued_at__date__gte=start_date,
            issued_at__date__lte=target_date
        ).count()

        # 8. Tasks Completed
        tasks_completed_count = WorkspaceTask.objects.filter(
            user=user,
            is_completed=True,
            completed_at__date__gte=start_date,
            completed_at__date__lte=target_date
        ).count()

        # Grounded Recommendations for next week
        recommendations = []
        if lessons_completed_count == 0:
            recommendations.append("Dedicate at least two 25-minute Pomodoro sessions to progress your enrolled course curriculum.")
        else:
            recommendations.append(f"Great momentum completing {lessons_completed_count} lessons! Consider consolidating knowledge with practical code exercises.")

        if total_focus_minutes < 60:
            recommendations.append("Try scheduling deep-work focus sessions earlier in the day to build consistent study habits.")
        else:
            recommendations.append(f"Recorded {total_focus_minutes} minutes of dedicated focus time. Keep this sustainable pace next week.")

        if project_milestones_done == 0:
            recommendations.append("Advance your active project by breaking down the next phase into manageable daily checklist milestones.")
        else:
            recommendations.append(f"Completed {project_milestones_done} project milestone(s). Push your code to GitHub and update documentation.")

        if apps_updated == 0:
            recommendations.append("Review saved opportunities and verify deadline dates to avoid last-minute rushes.")

        return {
            'target_date': target_date,
            'start_date': start_date,
            'period_label': f"{start_date.strftime('%b %d')} – {target_date.strftime('%b %d, %Y')}",
            'lessons_completed': lessons_completed_count,
            'focus_sessions': focus_sessions_count,
            'focus_minutes': total_focus_minutes,
            'exercises_passed': exercises_passed,
            'project_milestones_done': project_milestones_done,
            'roadmap_milestones_done': roadmap_milestones_done,
            'apps_updated': apps_updated,
            'certs_earned': certs_earned,
            'tasks_completed': tasks_completed_count,
            'recommendations': recommendations,
        }
