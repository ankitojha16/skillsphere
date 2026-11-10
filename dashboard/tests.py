from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from courses.models import Category, Course, Enrollment
from learning.models import Lesson, LessonProgress

class DashboardTests(TestCase):
    def setUp(self):
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
