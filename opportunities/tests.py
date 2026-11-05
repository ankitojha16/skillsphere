from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from opportunities.models import Opportunity, SavedOpportunity

class OpportunityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='opptester', email='opp@test.com', password='Password123!')
        self.client = Client()
        self.client.login(username='opptester', password='Password123!')
        self.opp = Opportunity.objects.create(
            title='Backend Python Fellowship',
            organization='Global Tech Foundation',
            category='python-development',
            required_skills='Python, Django, PostgreSQL',
            work_mode='remote',
            application_url='https://example.com/apply',
            description='Build backend microservices for open source tools.'
        )

    def test_opportunity_list_and_search(self):
        response = self.client.get(reverse('opportunities:list'), {'q': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Backend Python Fellowship')

    def test_toggle_save_opportunity(self):
        response = self.client.post(reverse('opportunities:toggle_save_opportunity', kwargs={'pk': self.opp.pk}))
        self.assertEqual(response.status_code, 302)
        saved = SavedOpportunity.objects.filter(user=self.user, opportunity=self.opp).first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.application_status, 'interested')

    def test_application_tracker_status_pipeline(self):
        saved = SavedOpportunity.objects.create(
            user=self.user,
            opportunity=self.opp,
            application_status='interested'
        )
        response = self.client.post(reverse('opportunities:tracker'), {
            'saved_id': saved.id,
            'status': 'interview',
            'notes': 'Interview scheduled with hiring director.',
        })
        self.assertEqual(response.status_code, 302)
        saved.refresh_from_db()
        self.assertEqual(saved.application_status, 'interview')
        self.assertEqual(saved.application_notes, 'Interview scheduled with hiring director.')
