from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from assessments.models import SkillAssessment, AssessmentQuestion, AssessmentAttempt

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
