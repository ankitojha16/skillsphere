from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from courses.models import Category, Course, Enrollment
from learning.models import Lesson, LessonProgress

class DashboardTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username='dashuser', email='dash@test.com', password='Password123!')
        self.category = Category.objects.create(name='AI', slug='ai')
        self.course = Course.objects.create(title='AI Basics', slug='ai-basics', category=self.category)
        self.lesson = Lesson.objects.create(course=self.course, title='L1', lesson_order=1, estimated_minutes=10)
        Enrollment.objects.create(user=self.user, course=self.course)

    def test_dashboard_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Basics')
        self.assertContains(response, 'Enrolled Courses')

    def test_dashboard_unauthenticated_redirects(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('accounts:login')))

    def test_dashboard_has_career_suite_launchpad(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'careerSuiteLaunchpad')
        self.assertContains(response, 'Career & Engineering Launchpad')
        self.assertContains(response, 'Mock Interview')
        self.assertContains(response, 'ATS Resume Studio')
        self.assertContains(response, 'Developer Portfolio')
        self.assertContains(response, 'Certificates Center')

    def test_healthz_and_telemetry_endpoints(self):
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('checks', data)
        self.assertEqual(data['checks']['database']['status'], 'ok')
        self.assertIn('latency_ms', data['checks']['database'])

        api_resp = self.client.get('/api/health/')
        self.assertEqual(api_resp.status_code, 200)
        self.assertEqual(api_resp.json()['status'], 'healthy')

    def test_robots_txt_endpoint(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertContains(response, 'User-agent: *')
        self.assertContains(response, 'Allow: /courses/')
        self.assertContains(response, 'Disallow: /admin/')
        self.assertContains(response, 'Sitemap:')

    def test_sitemap_xml_endpoint(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertContains(response, '/courses/')
        self.assertContains(response, '/careers/')
        self.assertContains(response, '</urlset>')

    def test_dashboard_has_52_week_study_heatmap(self):
        self.client.force_login(self.user)
        LessonProgress.objects.create(
            user=self.user,
            lesson=self.lesson,
            is_completed=True,
            completed_at=timezone.now()
        )
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '52-Week Study Consistency Heatmap')
        self.assertContains(response, 'studyHeatmapGrid')
        self.assertContains(response, 'heatmapDaysData')
        self.assertIn('heatmap_days_json', response.context)
        self.assertGreaterEqual(response.context['total_active_days'], 1)

    def test_study_lounge_page_loads(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:study_lounge'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Virtual Study Lounge & Focus Hub')
        self.assertContains(response, 'timerDisplay')
        self.assertContains(response, 'Procedural Ambient Mixer')

    def test_log_focus_session_view(self):
        import json
        from goals.models import LearningActivity
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('dashboard:log_focus_session'),
            data=json.dumps({'minutes': 25, 'course_id': self.course.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('xp_awarded'), 25)
        self.assertEqual(data.get('today_pomodoros'), 1)
        self.assertTrue(
            LearningActivity.objects.filter(
                user=self.user,
                activity_type='FOCUS_SESSION',
                reference_id=self.course.id
            ).exists()
        )

    def test_brand_logo_and_opening_splash_rendered(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        # Check brand logo SVG asset
        self.assertContains(response, 'logo-icon.svg')
        self.assertContains(response, 'brand-sphere-img')
        # Check opening splash intro animation elements
        self.assertContains(response, 'skillsphereIntroSplash')
        self.assertContains(response, 'splash-stage')
        self.assertContains(response, 'opening-animation.css')
        self.assertContains(response, 'opening-animation.js')



