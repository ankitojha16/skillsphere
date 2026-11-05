from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from careers.models import CareerProfile
from careers.views import compute_career_stats, compute_career_readiness

class CareerHubTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='careertester', email='test@test.com', password='Password123!')
        self.client = Client()
        self.client.login(username='careertester', password='Password123!')

    def test_career_hub_view_authenticated(self):
        response = self.client.get(reverse('careers:hub'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Career Hub')
        self.assertContains(response, 'Career Path Explorer')

    def test_career_hub_profile_update(self):
        response = self.client.post(reverse('careers:hub'), {
            'headline': 'Senior Python Architect',
            'summary': 'Building distributed microservices.',
            'target_career_path': 'python-developer',
        })
        self.assertEqual(response.status_code, 302)
        profile = CareerProfile.objects.get(user=self.user)
        self.assertEqual(profile.professional_headline, 'Senior Python Architect')
        self.assertEqual(profile.target_career_path, 'python-developer')

    def test_career_path_detail_view(self):
        response = self.client.get(reverse('careers:path_detail', kwargs={'slug': 'python-developer'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Developer')
        self.assertContains(response, 'Required Skills')

    def test_career_analytics_scoring(self):
        stats = compute_career_stats(self.user)
        readiness = compute_career_readiness(self.user, stats)
        self.assertIn('overall_score', readiness)
        self.assertIn('skills_score', readiness)
        self.assertIn('projects_score', readiness)
        self.assertGreaterEqual(readiness['overall_score'], 0)
        self.assertLessEqual(readiness['overall_score'], 100)

        response = self.client.get(reverse('careers:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Career Preparation Analytics')
