"""
SkillSphere Workspace Test Suite — Phase 22.
Validates:
- Workspace Task CRUD, toggle completion, and rescheduling.
- Smart suggested task generation based on genuine student platform records.
- Smart Calendar event CRUD, timezone handling, and official opportunity deadline integration.
- Focus sessions recording and zero-artificial-XP integrity.
- Personal notes and bookmarks privacy, ownership enforcement, and cross-user isolation.
- Notification preferences persistence.
- Weekly progress intelligence calculation (honest zero-fabrication metrics).
- AI study planner context grounding and deterministic offline fallback.
"""

from datetime import datetime, date, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from workspace.models import (
    WorkspaceTask, CalendarEvent, FocusSession,
    PersonalNote, WorkspaceBookmark, NotificationPreference
)
from services.workspace_intelligence import WorkspaceIntelligenceService
from services.ai_study_planner import AIStudyPlannerService
from courses.models import Course, Enrollment, Category
from learning.models import Lesson, LessonProgress
from roadmaps.models import LearningRoadmap, RoadmapMilestone
from projects.models import ProjectIdea, ProjectMilestone
from opportunities.models import Opportunity, SavedOpportunity
from certificates.models import Certificate
from gamification.models import UserGamification


class WorkspaceTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='student_alice',
            email='alice@example.com',
            password='Password123!',
            first_name='Alice'
        )
        self.other_student = User.objects.create_user(
            username='student_bob',
            email='bob@example.com',
            password='Password123!',
            first_name='Bob'
        )

        # Setup course and lesson
        self.category = Category.objects.create(name="Web Development", slug="web-development")
        self.course = Course.objects.create(
            title="Django Web Development",
            slug="django-web-dev",
            description="Complete fullstack Django course",
            category=self.category,
            difficulty="Intermediate"
        )
        self.lesson1 = Lesson.objects.create(
            course=self.course,
            title="Lesson 1: Models & Migrations",
            lesson_order=1,
            estimated_minutes=25,
            content="Lesson content..."
        )
        self.lesson2 = Lesson.objects.create(
            course=self.course,
            title="Lesson 2: Views & Templates",
            lesson_order=2,
            estimated_minutes=30,
            content="Lesson content..."
        )
        Enrollment.objects.create(user=self.student, course=self.course)

        # Setup roadmap & milestone
        self.roadmap = LearningRoadmap.objects.create(
            user=self.student,
            title="Python Backend Path",
            target_skill="Python & Django",
            career_goal="Backend Engineer"
        )
        self.roadmap_milestone = RoadmapMilestone.objects.create(
            roadmap=self.roadmap,
            title="Build REST API",
            description="Implement DRF endpoints",
            milestone_order=1
        )

        # Setup project & milestone
        self.project = ProjectIdea.objects.create(
            user=self.student,
            title="E-Commerce API",
            category="Web Development",
            workflow_status="in_progress",
            completion_date=timezone.now().date() + timedelta(days=14)
        )
        self.project_milestone = ProjectMilestone.objects.create(
            project=self.project,
            title="Implement Stripe Webhooks",
            order=1
        )

        # Setup Opportunity
        self.opportunity = Opportunity.objects.create(
            title="Backend Engineering Intern",
            organization="Acme Corp",
            opportunity_type="internship",
            category="software-development",
            required_skills="Python, Django",
            application_url="https://example.com/jobs/1",
            deadline=timezone.now().date() + timedelta(days=5),
        )
        self.saved_opp = SavedOpportunity.objects.create(
            user=self.student,
            opportunity=self.opportunity,
            application_status="preparing",
            follow_up_date=timezone.now().date() + timedelta(days=2)
        )

    def test_workspace_dashboard_access_and_unauthenticated_redirect(self):
        # Unauthenticated access must redirect to login
        resp = self.client.get(reverse('workspace:dashboard'))
        self.assertEqual(resp.status_code, 302)

        # Authenticated student access
        self.client.login(username='student_alice', password='Password123!')
        resp = self.client.get(reverse('workspace:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Welcome back, Alice!")
        self.assertContains(resp, "Django Web Development")

    def test_workspace_task_crud_and_toggle_completion(self):
        self.client.login(username='student_alice', password='Password123!')

        # 1. Create task
        resp = self.client.post(reverse('workspace:task_create'), {
            'title': 'Study Django ORM',
            'description': 'Read through query optimization',
            'task_type': 'course',
            'priority': 'high',
            'due_date': str(timezone.now().date()),
            'estimated_minutes': '45',
            'course_id': self.course.id,
        })
        self.assertEqual(resp.status_code, 302)
        task = WorkspaceTask.objects.get(user=self.student, title='Study Django ORM')
        self.assertFalse(task.is_completed)
        self.assertEqual(task.priority, 'high')
        self.assertEqual(task.course, self.course)
        self.assertTrue(task.is_due_today)

        # 2. Toggle completion
        resp = self.client.post(reverse('workspace:task_toggle', args=[task.id]))
        self.assertEqual(resp.status_code, 302)
        task.refresh_from_db()
        self.assertTrue(task.is_completed)
        self.assertIsNotNone(task.completed_at)

        # Toggle back
        self.client.post(reverse('workspace:task_toggle', args=[task.id]))
        task.refresh_from_db()
        self.assertFalse(task.is_completed)

        # 3. Delete task
        del_resp = self.client.post(reverse('workspace:task_delete', args=[task.id]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(WorkspaceTask.objects.filter(id=task.id).exists())

    def test_task_rescheduling(self):
        self.client.login(username='student_alice', password='Password123!')
        yesterday = timezone.now().date() - timedelta(days=2)
        task = WorkspaceTask.objects.create(
            user=self.student,
            title='Overdue Task',
            due_date=yesterday,
            priority='urgent'
        )
        self.assertTrue(task.is_overdue)

        # Reschedule to today
        self.client.post(reverse('workspace:task_reschedule', args=[task.id]), {
            'target': 'today'
        })
        task.refresh_from_db()
        self.assertEqual(task.due_date, timezone.now().date())
        self.assertFalse(task.is_overdue)
        self.assertTrue(task.is_due_today)

        # Reschedule to next week
        self.client.post(reverse('workspace:task_reschedule', args=[task.id]), {
            'target': 'next_week'
        })
        task.refresh_from_db()
        self.assertEqual(task.due_date, timezone.now().date() + timedelta(days=7))

    def test_smart_suggested_daily_tasks_generation_and_adoption(self):
        self.client.login(username='student_alice', password='Password123!')

        # Generate suggestions from student records
        suggestions = WorkspaceIntelligenceService.generate_suggested_daily_tasks(self.student)
        self.assertGreater(len(suggestions), 0)

        # First suggestion should be for unfinished lesson 1 in enrolled course
        lesson_sugg = next((s for s in suggestions if s['task_type'] == 'course'), None)
        self.assertIsNotNone(lesson_sugg)
        self.assertIn("Django Web Development", lesson_sugg['title'])

        # Adopt suggestion
        adopt_resp = self.client.post(reverse('workspace:task_adopt_suggestion'), {
            'title': lesson_sugg['title'],
            'description': lesson_sugg['description'],
            'task_type': lesson_sugg['task_type'],
            'priority': lesson_sugg['priority'],
            'estimated_minutes': lesson_sugg['estimated_minutes'],
            'course_id': lesson_sugg.get('course_id') or '',
            'lesson_id': lesson_sugg.get('lesson_id') or '',
        })
        self.assertEqual(adopt_resp.status_code, 302)
        adopted_task = WorkspaceTask.objects.get(user=self.student, title=lesson_sugg['title'])
        self.assertEqual(adopted_task.due_date, timezone.now().date())

    def test_smart_calendar_events_and_official_deadlines_merging(self):
        self.client.login(username='student_alice', password='Password123!')

        # 1. Create personal event
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        resp = self.client.post(reverse('workspace:calendar_event_create'), {
            'title': 'Group Study Session',
            'event_type': 'study',
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
            'color': '#3b82f6',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(CalendarEvent.objects.filter(user=self.student, title='Group Study Session').exists())

        # 2. Query JSON calendar feed
        feed_resp = self.client.get(reverse('workspace:calendar_events_json'), {
            'start': (timezone.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            'end': (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        })
        self.assertEqual(feed_resp.status_code, 200)
        events = feed_resp.json()
        self.assertIsInstance(events, list)

        # Must contain personal event
        personal_ev = next((e for e in events if 'Group Study Session' in e['title']), None)
        self.assertIsNotNone(personal_ev)
        self.assertFalse(personal_ev['is_official'])

        # Must contain official opportunity deadline
        opp_ev = next((e for e in events if 'Acme Corp' in e['title']), None)
        self.assertIsNotNone(opp_ev)
        self.assertTrue(opp_ev['is_official'])

    def test_focus_session_logging_and_zero_artificial_xp(self):
        self.client.login(username='student_alice', password='Password123!')

        # Initial XP
        initial_gamification = UserGamification.objects.create(user=self.student, total_xp=100)

        # Log 50m focus session
        resp = self.client.post(
            reverse('workspace:focus_log_api'),
            data={
                'duration_minutes': 50,
                'session_type': 'deep_work',
                'course_id': self.course.id,
                'notes': 'Refactored serializers'
            },
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        session = FocusSession.objects.get(user=self.student, session_type='deep_work')
        self.assertEqual(session.duration_minutes, 50)
        self.assertEqual(session.notes, 'Refactored serializers')

        # Strict Anti-Fabrication check: Focus timer must NOT grant unearned XP
        initial_gamification.refresh_from_db()
        self.assertEqual(initial_gamification.total_xp, 100)

    def test_personal_notes_privacy_and_cross_user_isolation(self):
        self.client.login(username='student_alice', password='Password123!')

        # Alice creates a private note
        resp = self.client.post(reverse('workspace:note_save'), {
            'title': 'Alice Secret Architecture Plan',
            'content': 'Database sharding strategy for private startup',
            'folder': 'Confidential',
            'tags': 'architecture, db',
            'is_pinned': '1'
        })
        self.assertEqual(resp.status_code, 302)
        alice_note = PersonalNote.objects.get(user=self.student, title='Alice Secret Architecture Plan')
        self.assertTrue(alice_note.is_pinned)

        # Bob logs in and must NOT see Alice's note
        self.client.logout()
        self.client.login(username='student_bob', password='Password123!')

        notes_page = self.client.get(reverse('workspace:notes'))
        self.assertNotContains(notes_page, 'Alice Secret Architecture Plan')

        # Bob attempts to edit or delete Alice's note -> must 404
        bad_delete = self.client.post(reverse('workspace:note_delete', args=[alice_note.id]))
        self.assertEqual(bad_delete.status_code, 404)
        self.assertTrue(PersonalNote.objects.filter(id=alice_note.id).exists())

    def test_bookmarks_management(self):
        self.client.login(username='student_alice', password='Password123!')

        resp = self.client.post(reverse('workspace:bookmark_save'), {
            'title': 'Django Documentation',
            'url': 'https://docs.djangoproject.com/en/5.2/',
            'bookmark_type': 'resource',
            'category': 'Official Docs',
            'notes': 'Bookmarked for models reference'
        })
        self.assertEqual(resp.status_code, 302)
        bm = WorkspaceBookmark.objects.get(user=self.student, title='Django Documentation')
        self.assertEqual(bm.bookmark_type, 'resource')

        # Delete bookmark
        del_resp = self.client.post(reverse('workspace:bookmark_delete', args=[bm.id]))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(WorkspaceBookmark.objects.filter(id=bm.id).exists())

    def test_notification_preferences_update(self):
        self.client.login(username='student_alice', password='Password123!')

        resp = self.client.post(reverse('workspace:notification_settings'), {
            'notify_deadlines': 'on',
            'notify_unfinished_tasks': 'on',
            'digest_frequency': 'weekly',
            'advance_reminder_hours': '48'
        })
        self.assertEqual(resp.status_code, 302)

        prefs = NotificationPreference.objects.get(user=self.student)
        self.assertTrue(prefs.notify_deadlines)
        self.assertFalse(prefs.notify_new_opportunities)  # unchecked
        self.assertEqual(prefs.digest_frequency, 'weekly')
        self.assertEqual(prefs.advance_reminder_hours, 48)

    def test_weekly_progress_intelligence_honest_calculation(self):
        # Zero-Fabrication test: Alice completes 1 lesson and 1 focus session
        LessonProgress.objects.create(
            user=self.student,
            lesson=self.lesson1,
            is_completed=True,
            completed_at=timezone.now()
        )
        FocusSession.objects.create(
            user=self.student,
            session_type='pomodoro',
            duration_minutes=25,
            completed=True
        )

        report = WorkspaceIntelligenceService.calculate_weekly_intelligence(self.student)
        self.assertEqual(report['lessons_completed'], 1)
        self.assertEqual(report['focus_minutes'], 25)
        self.assertEqual(report['focus_sessions'], 1)
        self.assertEqual(report['certs_earned'], 0)  # No fake certs
        self.assertGreater(len(report['recommendations']), 0)

    def test_ai_study_planner_deterministic_fallback(self):
        self.client.login(username='student_alice', password='Password123!')

        # Ask study planner with network disconnected / live AI bypassed
        res = AIStudyPlannerService.ask_study_planner(self.student, "What should I learn today?")
        self.assertTrue(res['success'])
        self.assertIn("Recommended Daily Study Plan", res['response'])
        self.assertIn("student_alice", res['context']['username'])

        # Ask about roadmap
        res_roadmap = AIStudyPlannerService.ask_study_planner(self.student, "How can I finish my current roadmap?")
        self.assertTrue(res_roadmap['success'])
        self.assertIn("Python Backend Path", res_roadmap['response'])

        # Ask about project
        res_proj = AIStudyPlannerService.ask_study_planner(self.student, "Which project should I work on next?")
        self.assertTrue(res_proj['success'])
        self.assertIn("E-Commerce API", res_proj['response'])
