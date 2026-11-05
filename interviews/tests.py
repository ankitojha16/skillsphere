from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from interviews.models import MockInterview, InterviewResponse

class InterviewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='candidate', email='cand@test.com', password='Password123!')
        self.client.force_login(self.user)

    def test_setup_mock_interview(self):
        setup_url = reverse('interviews:setup')
        response = self.client.post(setup_url, {
            'category': 'Python Developer',
            'difficulty': 'Junior',
            'total_questions': 3,
        })
        self.assertEqual(response.status_code, 302)

        interview = MockInterview.objects.filter(user=self.user).first()
        self.assertIsNotNone(interview)
        self.assertEqual(interview.responses.count(), 3)

    def test_submit_interview_answer_flow(self):
        interview = MockInterview.objects.create(
            user=self.user,
            category='Python Developer',
            difficulty='Junior',
            total_questions=2
        )
        q1 = InterviewResponse.objects.create(
            interview=interview,
            question_order=1,
            question_text='What is Python garbage collection?'
        )
        q2 = InterviewResponse.objects.create(
            interview=interview,
            question_order=2,
            question_text='Explain Python generators.'
        )

        submit_url = reverse('interviews:submit_answer', kwargs={'interview_id': interview.id})
        
        # Submit Answer 1
        resp1 = self.client.post(submit_url, {
            'user_answer': 'Python uses reference counting and a cyclic garbage collector to reclaim unused memory blocks.'
        })
        self.assertEqual(resp1.status_code, 302)
        q1.refresh_from_db()
        self.assertTrue(len(q1.user_answer) > 0)
        self.assertGreater(q1.technical_rating, 0)

        # Submit Answer 2 (completes interview)
        resp2 = self.client.post(submit_url, {
            'user_answer': 'Generators use yield to return an iterator that produces items on demand with minimal memory.'
        })
        self.assertEqual(resp2.status_code, 302)

        interview.refresh_from_db()
        self.assertTrue(interview.is_completed)
        self.assertGreater(interview.overall_score, 0)
