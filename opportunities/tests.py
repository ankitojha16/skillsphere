from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from opportunities.models import Opportunity, SavedOpportunity

class OpportunityTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.user = User.objects.create_user(username='opptester', email='opp@test.com', password='Password123!')
        if hasattr(self.user, 'profile'):
            self.user.profile.role = 'recruiter'
            self.user.profile.save()
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

    def test_student_denied_recruiter_access(self):
        student = User.objects.create_user(username='purestudent', email='student@pure.com', password='Password123!')
        if hasattr(student, 'profile'):
            student.profile.role = 'student'
            student.profile.save()
        student_client = Client()
        student_client.login(username='purestudent', password='Password123!')

        # Talent portal redirects student with warning
        res_portal = student_client.get(reverse('opportunities:talent_portal'))
        self.assertEqual(res_portal.status_code, 302)

        # Candidate dossier redirects student
        res_dossier = student_client.get(reverse('opportunities:candidate_dossier', kwargs={'username': 'opptester'}))
        self.assertEqual(res_dossier.status_code, 302)

        # Shortlist view returns 403 Forbidden
        res_shortlist = student_client.get(reverse('opportunities:my_shortlist'))
        self.assertEqual(res_shortlist.status_code, 403)

        # API calls return 403 Forbidden JSON
        res_api = student_client.post(
            reverse('opportunities:toggle_shortlist', kwargs={'username': 'opptester'}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_api.status_code, 403)

    def test_interview_invitation_rate_limit(self):
        from django.core.cache import cache
        cache.clear()
        candidate = User.objects.create_user(username='ratelimited', email='rl@test.com', password='Password123!')
        url = reverse('opportunities:send_interview_invitation', kwargs={'username': 'ratelimited'})
        payload = {
            'role_title': 'Staff Engineer',
            'company_name': 'Tech Corp',
            'meeting_link': 'https://meet.google.com/test',
            'message': 'Hello!'
        }
        # Send 15 invitations
        for _ in range(15):
            res = self.client.post(url, data=payload, content_type='application/json')
            self.assertEqual(res.status_code, 200)
        
        # 16th invitation should trigger HTTP 429
        res_overflow = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(res_overflow.status_code, 429)
        self.assertIn('Hourly interview invitation limit reached', res_overflow.json()['error'])
