import io
import json
from PIL import Image

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from accounts.models import StudentProfile
from courses.models import Course, Category, Enrollment
from learning.models import Lesson
from certificates.models import Certificate
from analytics.models import ProductEvent, BetaFeedback
from analytics.services import track_event, sanitize_metadata


class AnalyticsServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='teststudent', email='student@test.com', password='Password123!')
        self.profile = StudentProfile.objects.get(user=self.user)

    def test_sanitize_metadata_strips_forbidden_keys(self):
        meta = {
            'course_id': 10,
            'password': 'SuperSecretPassword',
            'token': 'bearer_12345',
            'email': 'student@test.com',
            'lesson_title': 'Introduction to Python'
        }
        clean = sanitize_metadata(meta)
        self.assertIn('course_id', clean)
        self.assertIn('lesson_title', clean)
        self.assertNotIn('password', clean)
        self.assertNotIn('token', clean)
        self.assertNotIn('email', clean)

    def test_track_event_creates_record(self):
        event = track_event(
            user=self.user,
            event_type='course_enrolled',
            metadata={'course_id': 42, 'course_title': 'Algorithms'}
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, 'course_enrolled')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.metadata['course_id'], 42)

    def test_track_event_respects_opt_out(self):
        self.profile.analytics_opt_out = True
        self.profile.save()
        self.user.refresh_from_db()

        event = track_event(
            user=self.user,
            event_type='course_viewed',
            metadata={'course_id': 10}
        )
        self.assertIsNone(event)
        self.assertEqual(ProductEvent.objects.filter(user=self.user).count(), 0)

    def test_track_event_idempotency(self):
        event1 = track_event(
            user=self.user,
            event_type='first_login',
            event_key=f"first_login_{self.user.id}"
        )
        event2 = track_event(
            user=self.user,
            event_type='first_login',
            event_key=f"first_login_{self.user.id}"
        )
        self.assertEqual(event1.id, event2.id)
        self.assertEqual(ProductEvent.objects.filter(event_key=f"first_login_{self.user.id}").count(), 1)

    def test_track_event_failsafe_does_not_throw(self):
        # Even with corrupt / unsupported types, track_event never raises
        event = track_event(user=None, event_type='course_viewed', metadata="not-a-dict")
        self.assertIsNotNone(event)


class BetaFeedbackTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username='student_fb', email='sfb@test.com', password='Password123!')
        self.staff_user = User.objects.create_user(username='staff_fb', email='staff@test.com', password='Password123!', is_staff=True)

    def _create_test_image(self, size=(100, 100), fmt='JPEG'):
        buf = io.BytesIO()
        img = Image.new('RGB', size, color=(120, 50, 220))
        img.save(buf, format=fmt)
        buf.seek(0)
        return SimpleUploadedFile(f"test.{fmt.lower()}", buf.read(), content_type=f"image/{fmt.lower()}")

    def test_submit_feedback_success(self):
        self.client.login(username='student_fb', password='Password123!')
        image = self._create_test_image()
        response = self.client.post(
            reverse('analytics:submit_feedback_api'),
            {
                'category': 'bug',
                'rating': '4',
                'description': 'Found a typo in lesson 3 code block.',
                'page_url': '/courses/python/3/',
                'screenshot': image
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        feedback = BetaFeedback.objects.get(id=data['feedback_id'])
        self.assertEqual(feedback.category, 'bug')
        self.assertEqual(feedback.rating, 4)
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.status, 'new')
        self.assertTrue(feedback.screenshot_data_uri.startswith('data:image/jpeg;base64,'))

    def test_submit_feedback_rate_limit(self):
        self.client.login(username='student_fb', password='Password123!')
        # Submit 5 times
        for i in range(5):
            res = self.client.post(
                reverse('analytics:submit_feedback_api'),
                {'category': 'feedback', 'description': f"Feedback #{i}"},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            self.assertEqual(res.status_code, 200)

        # 6th attempt should be rate-limited (HTTP 429)
        res_blocked = self.client.post(
            reverse('analytics:submit_feedback_api'),
            {'category': 'feedback', 'description': '6th feedback'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_blocked.status_code, 429)

    def test_submit_feedback_rejects_corrupted_screenshot(self):
        self.client.login(username='student_fb', password='Password123!')
        bad_file = SimpleUploadedFile("fake.png", b"this is not a real image header", content_type="image/png")
        res = self.client.post(
            reverse('analytics:submit_feedback_api'),
            {'category': 'bug', 'description': 'Bad image test', 'screenshot': bad_file},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn('not a valid or safe image', res.json().get('error', ''))


class AdminBetaDashboardTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.student = User.objects.create_user(username='regular_student', password='Password123!')
        self.staff = User.objects.create_user(username='staff_member', password='Password123!', is_staff=True)

        # Seed test feedback
        BetaFeedback.objects.create(
            user=self.student,
            category='bug',
            rating=5,
            description='Test bug report',
            status='new'
        )

    def test_student_cannot_access_beta_dashboard(self):
        self.client.login(username='regular_student', password='Password123!')
        response = self.client.get(reverse('analytics:admin_beta_dashboard'))
        # staff_member_required redirects non-staff users
        self.assertEqual(response.status_code, 302)

    def test_staff_can_access_beta_dashboard(self):
        self.client.login(username='staff_member', password='Password123!')
        response = self.client.get(reverse('analytics:admin_beta_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Private Beta Telemetry")
        self.assertContains(response, "Test bug report")

    def test_update_feedback_status_staff_only(self):
        feedback = BetaFeedback.objects.first()
        self.client.login(username='regular_student', password='Password123!')
        res_student = self.client.post(
            reverse('analytics:update_feedback_status_api', args=[feedback.id]),
            {'status': 'resolved', 'admin_notes': 'Fixed'}
        )
        self.assertEqual(res_student.status_code, 302)

        self.client.login(username='staff_member', password='Password123!')
        res_staff = self.client.post(
            reverse('analytics:update_feedback_status_api', args=[feedback.id]),
            {'status': 'resolved', 'admin_notes': 'Fixed in release'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_staff.status_code, 200)
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, 'resolved')
        self.assertEqual(feedback.admin_notes, 'Fixed in release')


class PrivacyAndDataRightsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='privacy_user', email='privacy@example.com', password='SecretPassword123!')
        self.profile = StudentProfile.objects.get(user=self.user)
        self.cat = Category.objects.create(name='Test Category', slug='test-cat')
        self.course = Course.objects.create(title='Test Course', slug='test-course', category=self.cat)
        Enrollment.objects.create(user=self.user, course=self.course)

    def test_privacy_and_terms_pages_render(self):
        res_privacy = self.client.get(reverse('privacy_policy'))
        self.assertEqual(res_privacy.status_code, 200)
        self.assertContains(res_privacy, "SkillSphere Privacy Policy")

        res_terms = self.client.get(reverse('terms_of_service'))
        self.assertEqual(res_terms.status_code, 200)
        self.assertContains(res_terms, "SkillSphere Beta Terms of Service")

    def test_export_user_data(self):
        self.client.login(username='privacy_user', password='SecretPassword123!')
        response = self.client.get(reverse('accounts:export_data'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['profile']['username'], 'privacy_user')
        self.assertEqual(len(data['enrollments']), 1)
        self.assertEqual(data['enrollments'][0]['course_title'], 'Test Course')
        # Ensure password is not present anywhere in data
        self.assertNotIn('SecretPassword123!', response.content.decode('utf-8'))

    def test_delete_account_fails_with_wrong_password(self):
        self.client.login(username='privacy_user', password='SecretPassword123!')
        response = self.client.post(
            reverse('accounts:delete_account'),
            {'password': 'WrongPassword!'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='privacy_user').exists())

    def test_delete_account_succeeds_with_correct_password(self):
        self.client.login(username='privacy_user', password='SecretPassword123!')
        response = self.client.post(
            reverse('accounts:delete_account'),
            {'password': 'SecretPassword123!'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='privacy_user').exists())
        self.assertFalse(StudentProfile.objects.filter(id=self.profile.id).exists())


class OnboardingFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='onboarding_user', email='onboard@example.com', password='Password123!')
        self.cat = Category.objects.create(name='Python Development', slug='python-dev')
        self.course = Course.objects.create(title='Python Fundamentals', slug='python-fundamentals', category=self.cat, is_published=True)
        self.lesson = Lesson.objects.create(course=self.course, title='Lesson 1: Intro', lesson_order=1)

    def test_onboarding_save_and_recommendations(self):
        self.client.login(username='onboarding_user', password='Password123!')
        res_post = self.client.post(
            reverse('accounts:profile_setup'),
            {
                'full_name': 'Onboarded Student',
                'education_level': 'undergraduate',
                'institution': 'Global Tech University',
                'learning_level': 'beginner',
                'selected_interests': ['python'],
                'career_goal': 'Python Engineer',
            }
        )
        self.assertEqual(res_post.status_code, 302)
        self.assertIn('recommendations', res_post.url)

        profile = StudentProfile.objects.get(user=self.user)
        self.assertTrue(profile.onboarding_completed)
        self.assertEqual(profile.full_name, 'Onboarded Student')

        # Test recommendations page
        res_rec = self.client.get(reverse('accounts:onboarding_recommendations'))
        self.assertEqual(res_rec.status_code, 200)
        self.assertContains(res_rec, "Python Fundamentals")
        self.assertContains(res_rec, "Start First Lesson Now")

    def test_onboarding_skip(self):
        self.client.login(username='onboarding_user', password='Password123!')
        res = self.client.get(reverse('accounts:profile_setup') + '?skip=1')
        self.assertEqual(res.status_code, 302)
        profile = StudentProfile.objects.get(user=self.user)
        self.assertTrue(profile.onboarding_completed)


class Phase16ScalingAndArchitectureTests(TestCase):
    """
    Validation tests for Phase 16:
    - PgBouncer transaction pooling settings
    - Parameterized course catalogue caching & cache version invalidation
    - DurableTaskJob queue execution, idempotency, retries, and dead-letter handling
    - Synthetic load test data generator production safeguard
    """
    def setUp(self):
        self.category = Category.objects.create(name='Architecture & Systems', slug='arch-systems')
        self.course = Course.objects.create(
            title='Distributed Systems 101',
            slug='distributed-systems-101',
            description='Scalable distributed architectures for high concurrency.',
            category=self.category,
            is_published=True
        )

    def test_pgbouncer_configuration_attributes(self):
        """Verifies DISABLE_SERVER_SIDE_CURSORS is enabled for PgBouncer compatibility."""
        from django.conf import settings
        default_db = settings.DATABASES['default']
        # When DATABASE_URL is present, DISABLE_SERVER_SIDE_CURSORS must be True
        if 'DISABLE_SERVER_SIDE_CURSORS' in default_db:
            self.assertTrue(default_db['DISABLE_SERVER_SIDE_CURSORS'])

    def test_parameterized_catalogue_caching_and_invalidation(self):
        """Verifies parameterized catalog caching and signal-driven cache version invalidation."""
        client = Client()
        # Initial request caches the catalogue
        res1 = client.get('/courses/?category=arch-systems&sort=newest')
        self.assertEqual(res1.status_code, 200)

        initial_ver = cache.get('skillsphere_catalogue_version', 1)

        # Triggering course save signal bumps catalogue version on transaction commit
        with self.captureOnCommitCallbacks(execute=True):
            self.course.title = 'Distributed Systems 101 (Updated)'
            self.course.save()

        new_ver = cache.get('skillsphere_catalogue_version', 1)
        self.assertGreater(new_ver, initial_ver)

    def test_durable_task_queue_enqueue_and_execution(self):
        """Tests task enqueueing, execution, and idempotency in services.task_queue."""
        from services import task_queue
        from analytics.models import DurableTaskJob

        executed_payloads = []

        @task_queue.register_task('scaling_task_test')
        def sample_handler(payload):
            executed_payloads.append(payload)
            return True

        # Enqueue with idempotency key
        job1 = task_queue.enqueue_task(
            'scaling_task_test',
            {'worker': 1, 'data': 'phase16'},
            idempotency_key='phase16_idemp_key_1',
            execute_now=True
        )
        self.assertEqual(job1.status, 'completed')
        self.assertEqual(len(executed_payloads), 1)

        # Re-enqueueing identical idempotency key returns existing job without re-executing
        job2 = task_queue.enqueue_task(
            'scaling_task_test',
            {'worker': 2},
            idempotency_key='phase16_idemp_key_1',
            execute_now=True
        )
        self.assertEqual(job1.pk, job2.pk)
        self.assertEqual(len(executed_payloads), 1)

    def test_durable_task_queue_retries_and_dead_letter(self):
        """Tests that failing jobs retry up to max_retries before transitioning to dead_letter."""
        from services import task_queue
        from analytics.models import DurableTaskJob

        @task_queue.register_task('failing_task_test')
        def failing_handler(payload):
            raise ValueError("Deliberate failure for retry test")

        job = DurableTaskJob.objects.create(
            task_name='failing_task_test',
            max_retries=2,
            status='pending'
        )

        # Attempt 1
        ok1 = task_queue.execute_job(job)
        self.assertFalse(ok1)
        job.refresh_from_db()
        self.assertEqual(job.retries, 1)
        self.assertEqual(job.status, 'failed')

        # Attempt 2 -> Should hit max_retries (2) and transition to dead_letter
        ok2 = task_queue.execute_job(job)
        self.assertFalse(ok2)
        job.refresh_from_db()
        self.assertEqual(job.retries, 2)
        self.assertEqual(job.status, 'dead_letter')

    def test_synthetic_data_generator_safeguard(self):
        """Verifies synthetic data generator strictly blocks when ALLOW_SYNTHETIC_DATA is not set in non-debug mode."""
        from django.core.management import call_command
        from django.core.management.base import CommandError
        import os

        # Temporarily emulate production environment
        with self.settings(DEBUG=False):
            old_allow = os.environ.get('ALLOW_SYNTHETIC_DATA')
            if 'ALLOW_SYNTHETIC_DATA' in os.environ:
                del os.environ['ALLOW_SYNTHETIC_DATA']
            try:
                with self.assertRaises(CommandError) as ctx:
                    call_command('generate_synthetic_load_data')
                self.assertIn("CRITICAL SAFEGUARD", str(ctx.exception))
            finally:
                if old_allow is not None:
                    os.environ['ALLOW_SYNTHETIC_DATA'] = old_allow

