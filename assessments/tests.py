from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from assessments.models import (
    SkillAssessment, AssessmentQuestion, AssessmentAttempt,
    CodingChallenge, CodingTestCase, ChallengeSubmission
)

class AssessmentsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='quiztaker', email='quiz@test.com', password='Password123!')
        self.client.force_login(self.user)

        self.assessment = SkillAssessment.objects.create(
            title='Python Fundamentals',
            category='Python',
            difficulty='Beginner'
        )
        self.q1 = AssessmentQuestion.objects.create(
            assessment=self.assessment,
            question_text='What is a list?',
            topic_tag='Data Types',
            option_a='Mutable sequence',
            option_b='Immutable sequence',
            option_c='Hash map',
            option_d='None',
            correct_answer='A',
            explanation='Lists are mutable sequences.'
        )
        self.q2 = AssessmentQuestion.objects.create(
            assessment=self.assessment,
            question_text='What is a tuple?',
            topic_tag='Data Types',
            option_a='Mutable',
            option_b='Immutable sequence',
            option_c='Function',
            option_d='None',
            correct_answer='B',
            explanation='Tuples are immutable.'
        )

    def test_assessment_list_and_take(self):
        resp = self.client.get(reverse('assessments:list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Python Fundamentals')

        take_resp = self.client.get(reverse('assessments:take', kwargs={'assessment_id': self.assessment.id}))
        self.assertEqual(take_resp.status_code, 200)
        self.assertContains(take_resp, 'What is a list?')

    def test_submit_assessment_scores_accurately(self):
        submit_url = reverse('assessments:submit', kwargs={'assessment_id': self.assessment.id})
        response = self.client.post(submit_url, {
            f'question_{self.q1.id}': 'A',  # Correct
            f'question_{self.q2.id}': 'A',  # Incorrect (correct is B)
        })
        self.assertEqual(response.status_code, 302)

        attempt = AssessmentAttempt.objects.filter(user=self.user, assessment=self.assessment).first()
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.total_questions, 2)
        self.assertEqual(attempt.percentage, 50)
        self.assertIn('Data Types', attempt.strengths + attempt.weaknesses)

    def test_assessment_result_view_has_action_controls_and_confetti(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.user,
            assessment=self.assessment,
            score=2,
            total_questions=2,
            percentage=100,
            ai_feedback='Outstanding mastery of Python sequences.',
            strengths='Data Types',
            weaknesses='None'
        )
        url = reverse('assessments:result', kwargs={'attempt_id': attempt.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Retake Assessment')
        self.assertContains(response, 'Track Weak Areas as Goal')
        self.assertContains(response, 'canvas-confetti')


class CodingChallengesTests(TestCase):
    def setUp(self):
        import json
        self.client = Client()
        self.user = User.objects.create_user(username='coder101', email='coder@test.com', password='Password123!')
        self.client.force_login(self.user)

        self.challenge = CodingChallenge.objects.create(
            title='Two Sum',
            slug='two-sum',
            difficulty='Easy',
            category='Arrays',
            description='Given an array nums and target, return indices.',
            constraints='2 <= nums.length <= 10^4',
            hints='Use a hash map for O(n) lookup.\nComplement is target - num.',
            python_starter='def two_sum(nums, target):\n    pass',
            javascript_starter='function twoSum(nums, target) {}',
            function_name='two_sum',
            xp_reward=50,
            is_active=True,
        )

        # Visible test case
        self.tc1 = CodingTestCase.objects.create(
            challenge=self.challenge,
            input_data='[[2, 7, 11, 15], 9]',
            expected_output='[0, 1]',
            is_hidden=False,
            order=1
        )

        # Hidden test case
        self.tc2 = CodingTestCase.objects.create(
            challenge=self.challenge,
            input_data='[[-1, -2, -3, -4, -5], -8]',
            expected_output='[2, 4]',
            is_hidden=True,
            order=2
        )

    def test_coding_challenge_helpers(self):
        self.assertEqual(len(self.challenge.get_hints_list()), 2)
        self.assertEqual(len(self.challenge.get_constraints_list()), 1)
        self.assertEqual(self.challenge.acceptance_rate, 85.0)

    def test_challenges_list_view(self):
        url = reverse('assessments:challenge_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Two Sum')
        self.assertContains(resp, 'Arrays &amp; Hashing')

        # Test filter by difficulty
        resp_filter = self.client.get(url + '?difficulty=Easy')
        self.assertEqual(resp_filter.status_code, 200)
        self.assertContains(resp_filter, 'Two Sum')

        # Test filter by Hard (should be empty for our challenge)
        resp_hard = self.client.get(url + '?difficulty=Hard')
        self.assertEqual(resp_hard.status_code, 200)
        self.assertNotContains(resp_hard, 'Two Sum')

    def test_challenge_detail_view(self):
        url = reverse('assessments:challenge_detail', kwargs={'slug': self.challenge.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Two Sum')
        self.assertContains(resp, 'two_sum()')
        self.assertContains(resp, 'Python 3 (Pyodide)')
        self.assertContains(resp, 'JavaScript ES6')

    def test_challenge_test_cases_api_visible_vs_hidden(self):
        url = reverse('assessments:challenge_test_cases', kwargs={'slug': self.challenge.slug})

        # Default: visible only
        resp_vis = self.client.get(url + '?mode=visible')
        self.assertEqual(resp_vis.status_code, 200)
        data_vis = resp_vis.json()
        self.assertEqual(len(data_vis['test_cases']), 1)
        self.assertFalse(data_vis['test_cases'][0]['is_hidden'])

        # Mode all: visible + hidden
        resp_all = self.client.get(url + '?mode=all')
        self.assertEqual(resp_all.status_code, 200)
        data_all = resp_all.json()
        self.assertEqual(len(data_all['test_cases']), 2)

    def test_submit_challenge_solution_accepted_and_xp(self):
        import json
        url = reverse('assessments:challenge_submit', kwargs={'slug': self.challenge.slug})
        payload = {
            'language': 'python',
            'code': 'def two_sum(nums, target): return [0, 1]',
            'status': 'Accepted',
            'runtime_ms': 22,
            'memory_kb': 14200,
            'passed_cases': 2,
            'total_cases': 2
        }

        # First solve: should award 50 XP
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['submission_status'], 'Accepted')
        self.assertEqual(data['xp_awarded'], 50)
        self.assertTrue(data['is_first_solve'])

        # Verify ChallengeSubmission was saved
        from assessments.models import ChallengeSubmission
        self.assertEqual(ChallengeSubmission.objects.filter(user=self.user, challenge=self.challenge).count(), 1)

        # Second solve: should succeed but NOT duplicate XP
        resp2 = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2['xp_awarded'], 0)
        self.assertFalse(data2['is_first_solve'])

    def test_submit_challenge_wrong_answer_no_xp(self):
        import json
        url = reverse('assessments:challenge_submit', kwargs={'slug': self.challenge.slug})
        payload = {
            'language': 'python',
            'code': 'def two_sum(nums, target): return []',
            'status': 'Wrong Answer',
            'runtime_ms': 18,
            'memory_kb': 14100,
            'passed_cases': 0,
            'total_cases': 2
        }

        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['submission_status'], 'Wrong Answer')
        self.assertEqual(data['xp_awarded'], 0)
        self.assertFalse(data['is_first_solve'])

    def test_seed_expanded_assessments_command(self):
        from django.core.management import call_command
        import io
        from learning.models import Exercise

        out = io.StringIO()
        call_command('seed_expanded_assessments', stdout=out)
        output = out.getvalue()
        self.assertIn('MILESTONE 3 SEEDING COMPLETED SUCCESSFULLY', output)

        # Verify all 5 categories exist
        expected_cats = ['HTML_CSS', 'JavaScript', 'CPP', 'Cloud_Fundamentals', 'Data_Science']
        for cat in expected_cats:
            ass = SkillAssessment.objects.filter(category=cat).first()
            self.assertIsNotNone(ass, f"Missing assessment for category {cat}")
            self.assertGreaterEqual(ass.questions.count(), 10, f"Assessment {cat} has less than 10 questions")

        # Verify category filtering on assessments list view
        resp_cloud = self.client.get(reverse('assessments:list') + '?category=Cloud_Fundamentals')
        self.assertEqual(resp_cloud.status_code, 200)
        self.assertContains(resp_cloud, 'Cloud Architecture')

        resp_ds = self.client.get(reverse('assessments:list') + '?category=Data_Science')
        self.assertEqual(resp_ds.status_code, 200)
        self.assertContains(resp_ds, 'Data Science, Applied Statistics')



