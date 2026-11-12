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

    def test_owner_cannot_exceed_team_size_limit(self):
        # Set team capacity to 2 (owner + 1 member)
        self.project.team_size = 2
        self.project.save()

        # Add 1 active member -> team is now full
        member1 = User.objects.create_user(username='member1', email='m1@test.com', password='Password123!')
        CollaborationMembership.objects.create(project=self.project, user=member1, role='Dev', status='active')

        # Second applicant tries to get accepted
        req2 = CollaborationRequest.objects.create(
            project=self.project,
            user=self.applicant,
            role_requested='Backend Engineer',
            status='pending'
        )

        owner_client = Client()
        owner_client.login(username='collabowner', password='Password123!')

        response = owner_client.post(reverse('collaboration:manage', kwargs={'pk': self.project.pk}), {
            'action': 'handle_request',
            'request_id': req2.id,
            'decision': 'accept',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cannot accept member: team capacity")
        req2.refresh_from_db()
        self.assertEqual(req2.status, 'pending')
        self.assertFalse(CollaborationMembership.objects.filter(project=self.project, user=self.applicant).exists())

    def test_lounge_hub_view(self):
        client = Client()
        client.login(username='collabowner', password='Password123!')
        response = client.get(reverse('collaboration:lounge_hub'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Collaborative Pair Programming')

    def test_create_and_join_lounge_room(self):
        client = Client()
        client.login(username='collabowner', password='Password123!')
        
        # Create room
        res = client.post(reverse('collaboration:create_room'), {
            'title': 'High Scale Distributed Sharding',
            'language': 'python'
        })
        self.assertEqual(res.status_code, 302)
        
        from collaboration.models import PairProgrammingRoom
        room = PairProgrammingRoom.objects.filter(host=self.owner).first()
        self.assertIsNotNone(room)
        self.assertTrue(room.room_code.startswith('SPHERE-'))
        self.assertEqual(room.title, 'High Scale Distributed Sharding')

        # Applicant joins room
        client_app = Client()
        client_app.login(username='applicant', password='Password123!')
        res_join = client_app.post(reverse('collaboration:join_room'), {
            'room_code': room.room_code
        })
        self.assertEqual(res_join.status_code, 302)
        room.refresh_from_db()
        self.assertEqual(room.collaborator, self.applicant)

    def test_pair_room_view(self):
        from collaboration.models import PairProgrammingRoom
        room = PairProgrammingRoom.objects.create(
            room_code='SPHERE-TEST1',
            title='Test Session',
            host=self.owner,
            language='python'
        )
        client = Client()
        client.login(username='collabowner', password='Password123!')
        res = client.get(reverse('collaboration:pair_room', kwargs={'room_code': 'SPHERE-TEST1'}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(response=res, text='SPHERE-TEST1')
        self.assertContains(response=res, text='Run Shared Code')

    def test_room_sync_api(self):
        from collaboration.models import PairProgrammingRoom
        room = PairProgrammingRoom.objects.create(
            room_code='SPHERE-SYNC1',
            title='Sync Session',
            host=self.owner,
            language='python'
        )
        client = Client()
        client.login(username='collabowner', password='Password123!')
        
        # POST sync update
        sync_payload = {
            'code': 'print("Synced distributed execution")',
            'language': 'python',
            'whiteboard': {'nodes': [{'id': 'n1', 'type': 'db', 'label': 'Master DB', 'x': 50, 'y': 50}], 'connections': []},
            'chat_message': 'Hey, check out the new PostgreSQL primary cluster!'
        }
        res = client.post(
            reverse('collaboration:room_sync', kwargs={'room_code': 'SPHERE-SYNC1'}),
            data=sync_payload,
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('Master DB', str(data['whiteboard']))

        # GET sync fetch
        res_get = client.get(reverse('collaboration:room_sync', kwargs={'room_code': 'SPHERE-SYNC1'}))
        self.assertEqual(res_get.status_code, 200)
        data_get = res_get.json()
        self.assertEqual(len(data_get['chat_messages']), 1)
        self.assertEqual(data_get['chat_messages'][0]['sender'], 'collabowner')

    def test_run_room_code_api(self):
        from collaboration.models import PairProgrammingRoom
        room = PairProgrammingRoom.objects.create(
            room_code='SPHERE-RUN1',
            title='Execution Test',
            host=self.owner,
            language='python'
        )
        client = Client()
        client.login(username='collabowner', password='Password123!')
        run_payload = {
            'code': 'x = 10 * 42\nprint(f"Computed: {x}")',
            'language': 'python'
        }
        res = client.post(
            reverse('collaboration:run_room_code', kwargs={'room_code': 'SPHERE-RUN1'}),
            data=run_payload,
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('Computed: 420', data['output'])

