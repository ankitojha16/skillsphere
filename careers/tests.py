from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json
from careers.models import CareerProfile, JobApplication
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


class JobTrackerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='trackeruser', email='tracker@example.com', password='Password123!')
        self.client = Client()
        self.client.login(username='trackeruser', password='Password123!')
        self.app = JobApplication.objects.create(
            user=self.user,
            company_name='Stripe',
            role_title='Backend Systems Engineer',
            status='WISHLIST',
            target_salary='$145,000',
            location='Remote'
        )

    def test_job_tracker_view_renders_kanban(self):
        response = self.client.get(reverse('careers:job_tracker'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Job Application Kanban')
        self.assertContains(response, 'Stripe')
        self.assertContains(response, 'Backend Systems Engineer')
        self.assertContains(response, 'Wishlist')
        self.assertContains(response, 'Offer Extended')

    def test_create_job_application_form_post(self):
        response = self.client.post(reverse('careers:create_job_application'), {
            'company_name': 'GitHub',
            'role_title': 'Python Platform Engineer',
            'status': 'APPLIED',
            'location': 'San Francisco, CA',
            'target_salary': '$155,000',
            'job_description': 'Seeking an engineer with strong Python, Django, Docker, and PostgreSQL skills.'
        })
        self.assertEqual(response.status_code, 302)
        app = JobApplication.objects.filter(company_name='GitHub', user=self.user).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.role_title, 'Python Platform Engineer')
        self.assertEqual(app.status, 'APPLIED')
        self.assertGreater(app.ats_match_score, 0)

    def test_create_job_application_ajax_post(self):
        payload = {
            'company_name': 'Datadog',
            'role_title': 'Infrastructure Engineer',
            'status': 'SCREENING',
            'location': 'New York, NY',
            'ats_match_score': 88
        }
        response = self.client.post(
            reverse('careers:create_job_application'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data['job']['company_name'], 'Datadog')

    def test_update_job_status_view(self):
        response = self.client.post(
            reverse('careers:update_job_status', kwargs={'job_id': self.app.id}),
            data=json.dumps({'status': 'TECHNICAL'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'TECHNICAL')

    def test_delete_job_application_view(self):
        response = self.client.post(
            reverse('careers:delete_job_application', kwargs={'job_id': self.app.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(JobApplication.objects.filter(id=self.app.id).exists())

    def test_generate_outreach_view(self):
        response = self.client.get(
            reverse('careers:generate_outreach', kwargs={'job_id': self.app.id}) + '?outreach_type=linkedin'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('subject', data)
        self.assertIn('message', data)
        self.assertIn('tips', data)
        self.assertIn('Stripe', data['subject'] + data['message'])

