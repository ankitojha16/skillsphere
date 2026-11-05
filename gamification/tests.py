from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from gamification.models import Badge, UserGamification, UserBadge
from gamification.services import award_user_xp, award_badge_if_eligible

class GamificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='gamertester', email='gamer@test.com', password='Password123!')
        self.badge = Badge.objects.create(name='Explorer', slug='explorer-badge', xp_requirement=100)
        self.client.force_login(self.user)

    def test_award_xp_and_level_advancement(self):
        gamification = award_user_xp(self.user, 120, "Early achievement")
        self.assertEqual(gamification.total_xp, 120)
        self.assertEqual(gamification.current_level, 'Explorer')

        # Advance to Learner (>= 300)
        award_user_xp(self.user, 200, "Advanced milestone")
        gamification.refresh_from_db()
        self.assertEqual(gamification.total_xp, 320)
        self.assertEqual(gamification.current_level, 'Learner')

    def test_award_badge_if_eligible(self):
        self.assertFalse(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())
        awarded = award_badge_if_eligible(self.user, 'explorer-badge')
        self.assertTrue(awarded)
        self.assertTrue(UserBadge.objects.filter(user=self.user, badge=self.badge).exists())

        # Duplicate awarding should return False
        again = award_badge_if_eligible(self.user, 'explorer-badge')
        self.assertFalse(again)

    def test_achievements_view(self):
        resp = self.client.get(reverse('gamification:achievements'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Achievements & Consistency')
