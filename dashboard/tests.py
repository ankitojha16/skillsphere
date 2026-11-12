import json
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
        # Check daily micro drill SM-2 UI components
        self.assertContains(response, 'Daily Knowledge Warm-Up')
        self.assertContains(response, 'dailyDrillModal')

    def test_daily_micro_drill_apis_and_sm2(self):
        from learning.spaced_repetition import calculate_sm2
        
        # Test SM-2 calculation
        sm2_perfect = calculate_sm2(repetitions=0, easiness_factor=2.5, interval_days=1, quality=5)
        self.assertEqual(sm2_perfect['repetitions'], 1)
        self.assertEqual(sm2_perfect['interval_days'], 1)
        self.assertEqual(sm2_perfect['status'], 'memorized')

        sm2_fail = calculate_sm2(repetitions=2, easiness_factor=2.5, interval_days=6, quality=1)
        self.assertEqual(sm2_fail['repetitions'], 0)
        self.assertEqual(sm2_fail['interval_days'], 1)
        self.assertEqual(sm2_fail['status'], 'relearning')

        self.client.force_login(self.user)
        # Test GET drill cards
        resp_get = self.client.get(reverse('dashboard:daily_drill_get'))
        self.assertEqual(resp_get.status_code, 200)
        data_get = resp_get.json()
        self.assertTrue(data_get['success'])
        self.assertEqual(len(data_get['cards']), 3)
        self.assertNotIn('correct', data_get['cards'][0])  # ensure answers aren't leaked

        # Test POST submit drill answers with user confidence rating
        card_id = data_get['cards'][0]['id']
        resp_post = self.client.post(
            reverse('dashboard:daily_drill_submit'),
            data=json.dumps({
                'answers': {card_id: 1},
                'confidences': {card_id: 4}
            }),
            content_type='application/json'
        )
        self.assertEqual(resp_post.status_code, 200)
        data_post = resp_post.json()
        self.assertTrue(data_post['success'])
        self.assertIn('correct_count', data_post)
        self.assertEqual(data_post['total_cards'], 3)
        self.assertIn('streak_bonus', data_post)
        self.assertIn('sm2', data_post['results'][0])




