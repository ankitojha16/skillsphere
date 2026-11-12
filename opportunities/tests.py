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

    def test_opportunity_detail_prep_deck(self):
        response = self.client.get(reverse('opportunities:detail', kwargs={'pk': self.opp.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Candidate Prep Deck')
        self.assertContains(response, 'Practice Mock Interview')
        self.assertContains(response, 'Optimize ATS Resume')
        self.assertContains(response, 'Track as 30-Day Goal')

    def test_talent_portal_view(self):
        candidate = User.objects.create_user(username='topcoder', email='top@coder.com', password='Password123!')
        response = self.client.get(reverse('opportunities:talent_portal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recruiter Talent Portal')
        self.assertContains(response, 'topcoder')

    def test_candidate_dossier_view(self):
        candidate = User.objects.create_user(username='dossierdev', email='dev@dossier.com', password='Password123!')
        response = self.client.get(reverse('opportunities:candidate_dossier', kwargs={'username': 'dossierdev'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Candidate Dossier')
        self.assertContains(response, 'dossierdev')

    def test_toggle_shortlist_api(self):
        candidate = User.objects.create_user(username='shortlistme', email='sl@test.com', password='Password123!')
        url = reverse('opportunities:toggle_shortlist', kwargs={'username': 'shortlistme'})
        
        # 1st toggle -> shortlist
        res1 = self.client.post(url)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertTrue(data1['is_shortlisted'])

        # 2nd toggle -> un-shortlist
        res2 = self.client.post(url)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertFalse(data2['is_shortlisted'])

    def test_send_interview_invitation_api(self):
        candidate = User.objects.create_user(username='interviewee', email='int@test.com', password='Password123!')
        url = reverse('opportunities:send_interview_invitation', kwargs={'username': 'interviewee'})
        payload = {
            'role_title': 'Staff Systems Architect',
            'company_name': 'DeepMind Labs',
            'meeting_link': 'https://meet.google.com/test-room',
            'message': 'We loved your Elo rating and test coverage!'
        }
        res = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('invitation_id', data)

    def test_recruiter_shortlist_view(self):
        candidate = User.objects.create_user(username='pipelinedev', email='p@dev.com', password='Password123!')
        from opportunities.models import CandidateShortlist
        CandidateShortlist.objects.create(recruiter=self.user, candidate=candidate, status='shortlisted')

        response = self.client.get(reverse('opportunities:my_shortlist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'pipelinedev')
        self.assertContains(response, 'Recruiter Shortlist')
