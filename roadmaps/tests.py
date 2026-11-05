from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from roadmaps.models import LearningRoadmap, RoadmapMilestone

class RoadmapsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='roadmapuser', email='roadmap@test.com', password='Password123!')
        self.other_user = User.objects.create_user(username='otheruser', email='other@test.com', password='Password123!')
        self.client.force_login(self.user)

    def test_generate_roadmap(self):
        url = reverse('roadmaps:generate')
        response = self.client.post(url, {
            'target_skill': 'Python',
            'current_level': 'Beginner',
            'career_goal': 'Backend Engineer',
            'daily_time': '1 hour/day',
            'duration': '3 months',
        })
        self.assertEqual(response.status_code, 302)

        roadmap = LearningRoadmap.objects.filter(user=self.user, target_skill='Python').first()
        self.assertIsNotNone(roadmap)
        self.assertGreaterEqual(roadmap.milestones.count(), 3)

    def test_milestone_completion_toggle(self):
        roadmap = LearningRoadmap.objects.create(user=self.user, title='Test Map', target_skill='Django')
        m1 = RoadmapMilestone.objects.create(roadmap=roadmap, title='M1', milestone_order=1)
        m2 = RoadmapMilestone.objects.create(roadmap=roadmap, title='M2', milestone_order=2)

        toggle_url = reverse('roadmaps:toggle_milestone', kwargs={'milestone_id': m1.id})
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, 302)

        m1.refresh_from_db()
        self.assertTrue(m1.is_completed)
        self.assertEqual(roadmap.get_progress()['percentage'], 50)

    def test_roadmap_isolation(self):
        roadmap = LearningRoadmap.objects.create(user=self.user, title='User Map')
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('roadmaps:detail', kwargs={'roadmap_id': roadmap.id}))
        self.assertEqual(response.status_code, 404)
