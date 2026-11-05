from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from collaboration.models import CollaborationProject, CollaborationMembership, CollaborationRequest

class CollaborationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='collabowner', email='owner@test.com', password='Password123!')
        self.applicant = User.objects.create_user(username='applicant', email='app@test.com', password='Password123!')
        self.project = CollaborationProject.objects.create(
            owner=self.owner,
            title='Autonomous Dev Tool',
            category='Web Development',
            technologies='Python, Django',
            required_roles='Backend Engineer',
            team_size=3,
            status='recruiting',
            description='Building developer CLI utilities.'
        )

    def test_project_list_view(self):
        client = Client()
        client.login(username='applicant', password='Password123!')
        response = client.get(reverse('collaboration:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Autonomous Dev Tool')

    def test_submit_join_request(self):
        client = Client()
        client.login(username='applicant', password='Password123!')
        response = client.post(reverse('collaboration:detail', kwargs={'pk': self.project.pk}), {
            'role_requested': 'Backend Engineer',
            'message': 'I have built Django APIs and would love to build this with you.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CollaborationRequest.objects.filter(project=self.project, user=self.applicant).exists())

    def test_owner_accepts_applicant(self):
        req = CollaborationRequest.objects.create(
            project=self.project,
            user=self.applicant,
            role_requested='Backend Engineer',
            status='pending'
        )
        owner_client = Client()
        owner_client.login(username='collabowner', password='Password123!')

        response = owner_client.post(reverse('collaboration:manage', kwargs={'pk': self.project.pk}), {
            'action': 'handle_request',
            'request_id': req.id,
            'decision': 'accept',
        })
        self.assertEqual(response.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, 'accepted')
        self.assertTrue(CollaborationMembership.objects.filter(project=self.project, user=self.applicant, status='active').exists())
