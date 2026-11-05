from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from goals.models import LearningGoal

class GoalsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username='usera', email='usera@test.com', password='Password123!')
        self.user_b = User.objects.create_user(username='userb', email='userb@test.com', password='Password123!')
        self.goal_a = LearningGoal.objects.create(
            user=self.user_a,
            title='Goal A',
            target_date=timezone.now().date() + timedelta(days=7)
        )

    def test_goals_list_view(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('goals:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Goal A')

    def test_create_goal(self):
        self.client.force_login(self.user_a)
        response = self.client.post(reverse('goals:create'), {
            'title': 'New Goal Title',
            'description': 'Goal Description',
            'target_date': (timezone.now().date() + timedelta(days=10)).strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LearningGoal.objects.filter(user=self.user_a, title='New Goal Title').exists())

    def test_toggle_goal_completion(self):
        self.client.force_login(self.user_a)
        self.assertFalse(self.goal_a.is_completed)

        response = self.client.post(reverse('goals:toggle', kwargs={'goal_id': self.goal_a.id}))
        self.assertEqual(response.status_code, 302)
        self.goal_a.refresh_from_db()
        self.assertTrue(self.goal_a.is_completed)

    def test_user_data_isolation(self):
        # User B should NOT be able to toggle or delete User A's goal
        self.client.force_login(self.user_b)
        response = self.client.post(reverse('goals:toggle', kwargs={'goal_id': self.goal_a.id}))
        self.assertEqual(response.status_code, 404)

        delete_response = self.client.post(reverse('goals:delete', kwargs={'goal_id': self.goal_a.id}))
        self.assertEqual(delete_response.status_code, 404)
