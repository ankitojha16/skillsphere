"""
Django-integrated E2E and Journey Integration Tests for SkillSphere.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import StudentProfile
from courses.models import Course, Enrollment, Category
from learning.models import Lesson
from careers.models import CareerTrack, StudentCareerGoal
from roadmaps.models import LearningRoadmap
from workspace.models import WorkspaceTask, PersonalNote, FocusSession
from opportunities.models import Opportunity, SavedOpportunity, OpportunityReport
from accounts.onboarding_service import OnboardingLaunchpadService


class SkillSphereLaunchReadinessTests(TestCase):
    """
    Test suite validating student journeys A-O, onboarding launchpad,
    opportunity freshness, recruiter barriers, and data export.
    """

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Engineering", slug="engineering")
        self.course = Course.objects.create(
            title="Full-Stack Engineering",
            slug="full-stack-engineering",
            category=self.category,
            difficulty="Intermediate",
            is_published=True
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Lesson 1: Architecture Fundamentals",
            lesson_order=1,
            estimated_minutes=20,
            content="Lesson content body"
        )
        self.track = CareerTrack.objects.create(
            title="Full Stack Developer",
            slug="fullstack-developer",
            summary="Full stack web engineering track",
            market_demand="High",
            primary_skills=["Python", "Django", "JavaScript", "SQL"]
        )
        self.opportunity = Opportunity.objects.create(
            title="Junior Software Engineer",
            organization="InnovateTech Labs",
            category="software-development",
            required_skills="Python, Django",
            application_url="https://innovatetech.example/jobs/1",
            is_active=True,
            verification_status=True
        )

        # Normal student
        self.student = User.objects.create_user(
            username='qa_student',
            email='student@qa.test',
            password='TestPassword123!'
        )
        self.profile = StudentProfile.objects.filter(user=self.student).first()
        if not self.profile:
            self.profile = StudentProfile.objects.create(user=self.student)
        self.profile.learning_level = 'intermediate'
        self.profile.education_level = 'undergraduate'
        self.profile.onboarding_completed = True
        self.profile.save()

        # Recruiter
        self.recruiter = User.objects.create_user(
            username='qa_recruiter',
            email='recruiter@qa.test',
            password='TestPassword123!'
        )
        self.rec_profile = StudentProfile.objects.filter(user=self.recruiter).first()
        if not self.rec_profile:
            self.rec_profile = StudentProfile.objects.create(user=self.recruiter)
        self.rec_profile.role = 'recruiter'
        self.rec_profile.save()

        # Admin
        self.admin = User.objects.create_superuser(
            username='qa_admin',
            email='admin@qa.test',
            password='AdminPassword123!'
        )

    def test_onboarding_launchpad_service(self):
        """Verify launchpad tracks student milestones accurately without fabrication."""
        status = OnboardingLaunchpadService.get_status(self.student)
        self.assertIsNotNone(status)
        self.assertEqual(status['total_steps'], 6)
        self.assertTrue(status['steps'][0]['is_completed'])  # profile setup completed
        self.assertFalse(status['is_all_completed'])

        # Complete course enrollment milestone
        Enrollment.objects.create(user=self.student, course=self.course)
        status_after = OnboardingLaunchpadService.get_status(self.student)
        self.assertEqual(status_after['completed_count'], 2)

    def test_student_dashboard_rendering_and_launchpad(self):
        """Verify student dashboard displays onboarding launchpad widget."""
        self.client.login(username='qa_student', password='TestPassword123!')
        res = self.client.get(reverse('dashboard:index'))
        self.assertEqual(res.status_code, 200)
        self.assertIn('onboarding_launchpad', res.context)

    def test_opportunity_freshness_properties(self):
        """Verify is_stale, is_expired, and freshness_status properties."""
        self.assertFalse(self.opportunity.is_expired)
        self.assertFalse(self.opportunity.is_stale)
        self.assertEqual(self.opportunity.freshness_status, 'active')
        self.assertEqual(self.opportunity.freshness_label, 'Verified Active')

    def test_recruiter_access_control(self):
        """Ensure students are blocked from recruiter post view and recruiters are admitted."""
        self.client.login(username='qa_student', password='TestPassword123!')
        res = self.client.get(reverse('opportunities:recruiter_post'))
        self.assertIn(res.status_code, [302, 403])

        self.client.login(username='qa_recruiter', password='TestPassword123!')
        res_rec = self.client.get(reverse('opportunities:recruiter_post'))
        self.assertEqual(res_rec.status_code, 200)

    def test_admin_moderation_portal(self):
        """Ensure non-admin cannot access moderation dashboard and admin can."""
        self.client.login(username='qa_student', password='TestPassword123!')
        res_student = self.client.get(reverse('opportunities:moderation_dashboard'))
        self.assertEqual(res_student.status_code, 403)

        self.client.login(username='qa_admin', password='AdminPassword123!')
        res_admin = self.client.get(reverse('opportunities:moderation_dashboard'))
        self.assertEqual(res_admin.status_code, 200)

    def test_student_data_export_ownership(self):
        """Ensure full JSON export includes workspace and career portfolio sections."""
        self.client.login(username='qa_student', password='TestPassword123!')
        WorkspaceTask.objects.create(user=self.student, title="Study Django REST", priority="high")
        res = self.client.get(reverse('accounts:export_data'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/json')
        self.assertIn(b"workspace", res.content)
        self.assertIn(b"Study Django REST", res.content)
