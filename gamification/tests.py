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


class LeagueAndDuelTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='leaguer', email='leaguer@test.com', password='Password123!')
        self.client.force_login(self.user)

    def test_leagues_view_authenticated(self):
        resp = self.client.get(reverse('gamification:leagues'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Weekly Competitive League')
        self.assertContains(resp, 'Cohort Standings')
        self.assertContains(resp, 'Top 7: Promotion Zone')
        self.assertContains(resp, 'leaguer')

    def test_start_duel_api(self):
        resp = self.client.get(reverse('gamification:start_duel') + '?topic=python')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(len(data.get('questions', [])), 5)
        self.assertEqual(data.get('time_limit'), 60)
        self.assertIn(data.get('opponent_name', ''), ['DevBot 3000', 'CodeViper', 'ByteMaster', 'AlgoRival', 'CyberKnight'])


    def test_submit_duel_api_victory(self):
        import json
        from gamification.models import SkillDuel
        # All correct answers for Python duel questions:
        # id 1: 0 (O(1))
        # id 2: 1 (yield)
        # id 3: 1 (prevent race conditions)
        # id 4: 1 (cls)
        # id 5: 1 (extend())
        payload = {
            'topic_key': 'python',
            'opponent_name': 'DevBot 3000',
            'answers': {
                '1': 0,
                '2': 1,
                '3': 1,
                '4': 1,
                '5': 1
            },
            'time_taken': 35
        }
        resp = self.client.post(
            reverse('gamification:submit_duel'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('challenger_score'), 5)
        # Score is 5/5: user wins and earns 1.5x streak combo multiplier (30 * 1.5 = 45 XP)
        self.assertEqual(data.get('outcome'), 'VICTORY')
        self.assertEqual(data.get('combo_multiplier'), 1.5)
        self.assertEqual(data.get('xp_awarded'), 45)
        self.assertTrue(SkillDuel.objects.filter(challenger=self.user).exists())

    def test_start_duel_web_security_topic(self):
        resp = self.client.get(reverse('gamification:start_duel') + '?topic=web')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('topic'), 'Web Architecture & Security')
        self.assertEqual(len(data.get('questions', [])), 5)
        self.assertIn('Clickjacking', data['questions'][0]['question'])

    def test_public_user_badge_svg_endpoint(self):
        self.client.logout()
        # Test badge generation for existing user
        resp = self.client.get(reverse('gamification:user_badge', kwargs={'username': self.user.username}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'image/svg+xml')
        content = resp.content.decode('utf-8')
        self.assertIn(f'aria-label="SkillSphere Badge for {self.user.username}"', content)
        self.assertIn('Bronze League', content)
        self.assertIn('Experience', content)
        self.assertIn('Streak', content)

        # Test fallback for non-existent username
        resp_fallback = self.client.get(reverse('gamification:user_badge', kwargs={'username': 'ghost_developer'}))
        self.assertEqual(resp_fallback.status_code, 200)
        self.assertEqual(resp_fallback['Content-Type'], 'image/svg+xml')
        self.assertIn('ghost_developer', resp_fallback.content.decode('utf-8'))

        # Test Cyberpunk Theme
        resp_cyber = self.client.get(reverse('gamification:user_badge', kwargs={'username': self.user.username}) + '?theme=cyberpunk')
        self.assertEqual(resp_cyber.status_code, 200)
        self.assertIn('#ec4899', resp_cyber.content.decode('utf-8'))

        # Test Compact Shield Style
        resp_compact = self.client.get(reverse('gamification:user_badge', kwargs={'username': self.user.username}) + '?style=compact')
        self.assertEqual(resp_compact.status_code, 200)
        self.assertIn('width="350" height="68"', resp_compact.content.decode('utf-8'))


class CodeArenaTests(TestCase):
    def setUp(self):
        import json
        self.client = Client()
        self.user = User.objects.create_user(username='arenawarrior', email='warrior@test.com', password='Password123!')
        self.client.force_login(self.user)

        from assessments.models import CodingChallenge, CodingTestCase
        self.challenge = CodingChallenge.objects.create(
            title='Two Sum Blitz',
            slug='two-sum-blitz',
            difficulty='Easy',
            category='Arrays',
            description='Return two indices that sum to target.',
            function_name='two_sum',
            python_starter='def two_sum(nums, target):\n    pass',
            xp_reward=50
        )
        CodingTestCase.objects.create(
            challenge=self.challenge,
            input_data='[[2, 7, 11, 15], 9]',
            expected_output='[0, 1]',
            is_hidden=False,
            order=1
        )

    def test_arena_hub_view(self):
        url = reverse('gamification:arena_hub')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '1v1 Multiplayer Code Arena')
        self.assertContains(resp, '1200')
        self.assertContains(resp, 'FIDE Competitive ELO Rating')

    def test_start_arena_match_api(self):
        url = reverse('gamification:arena_start')
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('match_id', data)

        from gamification.models import CodeArenaMatch
        match = CodeArenaMatch.objects.filter(id=data['match_id']).first()
        self.assertIsNotNone(match)
        self.assertEqual(match.player_one, self.user)
        self.assertEqual(match.status, 'IN_PROGRESS')

    def test_arena_match_progress_and_submission(self):
        import json
        from gamification.models import CodeArenaMatch, UserArenaRating
        match = CodeArenaMatch.objects.create(
            player_one=self.user,
            player_two=None,
            player_two_name='Grandmaster Bot',
            is_bot_match=True,
            challenge=self.challenge,
            player_one_elo_before=1200,
            player_two_elo_before=1250,
            total_cases=1,
            status='IN_PROGRESS'
        )

        # 1. Test Match View
        view_url = reverse('gamification:arena_match', kwargs={'match_id': match.id})
        resp_view = self.client.get(view_url)
        self.assertEqual(resp_view.status_code, 200)
        self.assertContains(resp_view, 'Grandmaster Bot')
        self.assertContains(resp_view, 'Two Sum Blitz')

        # 2. Test Progress API
        prog_url = reverse('gamification:arena_progress', kwargs={'match_id': match.id})
        resp_prog = self.client.post(prog_url, data=json.dumps({'cases_passed': 1}), content_type='application/json')
        self.assertEqual(resp_prog.status_code, 200)
        data_prog = resp_prog.json()
        self.assertEqual(data_prog['p1_passed'], 1)

        # 3. Test Submit Match API (Victory)
        submit_url = reverse('gamification:arena_submit', kwargs={'match_id': match.id})
        resp_sub = self.client.post(submit_url, data=json.dumps({'cases_passed': 1, 'time_remaining': 120}), content_type='application/json')
        self.assertEqual(resp_sub.status_code, 200)
        data_sub = resp_sub.json()
        self.assertEqual(data_sub['status'], 'success')
        self.assertTrue(data_sub['is_winner'])
        self.assertGreater(data_sub['user_elo_change'], 0)
        self.assertEqual(data_sub['xp_awarded'], 75)

        # Check rating updated
        rating = UserArenaRating.objects.get(user=self.user)
        self.assertGreater(rating.elo, 1200)
        self.assertEqual(rating.matches_won, 1)
        self.assertEqual(rating.matches_played, 1)






