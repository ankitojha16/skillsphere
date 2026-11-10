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
        self.assertContains(resp, 'communityLeaderboard')
        self.assertContains(resp, 'Platform Leaderboard')
        self.assertContains(resp, 'gamertester')
        self.assertContains(resp, 'Your Rank: #1')

    def test_award_xp_idempotency_with_activity_key(self):
        from gamification.models import XPTransaction

        # First call awards 50 XP
        gamification = award_user_xp(self.user, 50, "Completed Lesson 1", activity_key="lesson_101")
        self.assertEqual(gamification.total_xp, 50)
        self.assertEqual(XPTransaction.objects.filter(user=self.user, activity_key="lesson_101").count(), 1)

        # Repeated request with same activity_key should NOT duplicate XP
        gamification = award_user_xp(self.user, 50, "Completed Lesson 1 Again", activity_key="lesson_101")
        gamification.refresh_from_db()
        self.assertEqual(gamification.total_xp, 50)
        self.assertEqual(XPTransaction.objects.filter(user=self.user, activity_key="lesson_101").count(), 1)

