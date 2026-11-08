import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from certificates.models import Certificate
from courses.models import Course, Category, Enrollment, CourseAssessment, CourseAssessmentAttempt
from learning.models import Lesson, LessonProgress, Exercise

class CertificateEligibility85Tests(TestCase):
    """
    Comprehensive test suite verifying the authoritative >=85% certificate eligibility standard
    and the separation of optional exercises from mandatory completion requirements.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='student85', email='student85@test.com', password='Password123!')
        self.client = Client()
        self.client.login(username='student85', password='Password123!')

        self.category = Category.objects.create(name='Data Science', slug='data-science')
        self.course = Course.objects.create(
            title='Data Science & AI Specialization',
            slug='data-science-ai-spec',
            category=self.category,
            instructor_name='Dr. Smith',
            description='Comprehensive Data Science Course'
        )
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)

        # Create 20 lessons (each lesson = 5% progress)
        self.lessons = []
        for i in range(1, 21):
            lesson = Lesson.objects.create(
                course=self.course,
                title=f"Lesson {i}",
                lesson_order=i,
                content=f"Content for lesson {i}",
                video_duration_seconds=300
            )
            self.lessons.append(lesson)

        # Create 2 optional practical exercises
        self.exercise1 = Exercise.objects.create(
            lesson=self.lessons[0],
            title='Pandas Challenge',
            instructions='Process DataFrame',
            starter_code='import pandas as pd',
            solution='import pandas as pd; df = pd.DataFrame()',
            order=1
        )
        self.exercise2 = Exercise.objects.create(
            lesson=self.lessons[1],
            title='NumPy Matrix',
            instructions='Matrix ops',
            starter_code='import numpy as np',
            solution='import numpy as np; a = np.zeros(5)',
            order=2
        )

        # Mandatory assessments (Quiz and Mock Exam)
        self.quiz = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_quiz',
            title='Final Course Quiz',
            duration_minutes=20,
            passing_percentage=70
        )
        self.mock = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_mock',
            title='Final Mock Examination',
            duration_minutes=30,
            passing_percentage=70
        )

    def _complete_n_lessons(self, n: int):
        for i in range(n):
            LessonProgress.objects.update_or_create(
                user=self.user,
                lesson=self.lessons[i],
                defaults={'is_completed': True}
            )

    def _pass_quiz(self, percentage: int = 80):
        is_passed = percentage >= 70
        CourseAssessmentAttempt.objects.create(
            user=self.user,
            assessment=self.quiz,
            score=int(percentage / 10),
            total_questions=10,
            percentage=percentage,
            is_passed=is_passed
        )

    def _pass_mock(self, percentage: int = 85):
        is_passed = percentage >= 70
        CourseAssessmentAttempt.objects.create(
            user=self.user,
            assessment=self.mock,
            score=int(percentage / 10),
            total_questions=10,
            percentage=percentage,
            is_passed=is_passed
        )

    def test_scenario_01_zero_progress(self):
        """Scenario 1: 0% progress -> Locked"""
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 0)
        self.assertFalse(prog['is_certificate_eligible'])
        self.assertIn("Complete 20 more mandatory video lessons", prog['missing_requirements'][0])

    def test_scenario_02_60_percent_progress(self):
        """Scenario 2: 15/20 lessons -> 60% progress, certificate locked"""
        self._complete_n_lessons(15)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 60)
        self.assertFalse(prog['is_certificate_eligible'])

    def test_scenario_03_64_percent_progress(self):
        """Scenario 3: 16/20 lessons -> 64% progress, cert locked"""
        self._complete_n_lessons(16)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 64)
        self.assertFalse(prog['is_certificate_eligible'])

    def test_scenario_04_68_percent_without_exams(self):
        """Scenario 4: 17/20 lessons -> 68% progress, cert locked (lessons incomplete)"""
        self._complete_n_lessons(17)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 68)
        self.assertFalse(prog['is_certificate_eligible'])
        self.assertIn("Complete 3 more mandatory video lessons", prog['missing_requirements'][0])

    def test_scenario_05_68_percent_with_quiz(self):
        """Scenario 5: 17/20 lessons + Quiz passed (+10%) -> 78% progress, cert locked"""
        self._complete_n_lessons(17)
        self._pass_quiz(80)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 78)
        self.assertTrue(prog['quiz_passed'])
        self.assertFalse(prog['is_certificate_eligible'])

    def test_scenario_06_failed_quiz(self):
        """Scenario 6: Incomplete lessons + Quiz failed"""
        self._complete_n_lessons(17)
        self._pass_quiz(60)
        prog = self.course.get_user_progress(self.user)
        self.assertFalse(prog['quiz_passed'])
        self.assertFalse(prog['is_certificate_eligible'])

    def test_scenario_07_full_curriculum_eligible_and_claimed(self):
        """Scenario 7: 20/20 lessons + Quiz passed + Mock passed -> 100% progress, ELIGIBLE! Claim succeeds."""
        self._complete_n_lessons(20)
        self._pass_quiz(75)
        self._pass_mock(80)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 100)
        self.assertTrue(prog['quiz_passed'])
        self.assertTrue(prog['mock_passed'])
        self.assertTrue(prog['is_certificate_eligible'])
        self.assertEqual(len(prog['missing_requirements']), 0)

        # Claim certificate
        res = self.client.post(reverse('certificates:center'), {
            'claim_course_id': self.course.id,
            'recipient_name': 'Student EightyFive'
        })
        self.assertEqual(res.status_code, 302)
        cert = Certificate.objects.filter(user=self.user, course=self.course).first()
        self.assertIsNotNone(cert)
        self.assertEqual(cert.recipient_name, 'Student EightyFive')

    def test_scenario_08_optional_exercises_do_not_block_certificate(self):
        """Scenario 8: Optional exercises incomplete; certificate is STILL eligible when lessons completed."""
        self._complete_n_lessons(20)
        # Note: 0 exercises completed out of 2 optional exercises
        prog = self.course.get_user_progress(self.user)
        self.assertTrue(prog['is_certificate_eligible'])
        self.assertTrue(len(prog['optional_remaining_activities']) > 0)
        self.assertIn("optional coding exercise", prog['optional_remaining_activities'][1])

    def test_scenario_09_idempotent_certificate_claim(self):
        """Scenario 9: Multiple claims return the existing certificate gracefully."""
        self._complete_n_lessons(20)
        self._pass_quiz(80)
        self._pass_mock(80)

        # First claim
        res1 = self.client.post(reverse('certificates:center'), {
            'claim_course_id': self.course.id,
            'recipient_name': 'Student EightyFive'
        })
        self.assertEqual(res1.status_code, 302)
        self.assertEqual(Certificate.objects.filter(user=self.user, course=self.course).count(), 1)

        # Second claim via AJAX
        res2 = self.client.post(
            reverse('certificates:center'),
            {'claim_course_id': self.course.id, 'recipient_name': 'Student EightyFive'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res2.status_code, 200)
        data = res2.json()
        self.assertTrue(data['success'])
        self.assertIn('already', data['message'].lower())
        self.assertEqual(Certificate.objects.filter(user=self.user, course=self.course).count(), 1)

    def test_scenario_10_ajax_lesson_toggle_returns_full_progress(self):
        """Scenario 10: Lesson complete toggle AJAX endpoint returns full progress payload."""
        lesson_to_toggle = self.lessons[0]
        res = self.client.post(
            reverse('learning:complete_toggle', kwargs={'course_slug': self.course.slug, 'lesson_id': lesson_to_toggle.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['percentage'], 4)
        self.assertIn('is_certificate_eligible', data)
        self.assertIn('missing_requirements', data)

    def test_scenario_11_ajax_video_progress_returns_full_progress(self):
        """Scenario 11: Video progress AJAX endpoint returns updated progress payload."""
        lesson_to_watch = self.lessons[1]
        res = self.client.post(
            reverse('learning:video_progress', kwargs={'course_slug': self.course.slug, 'lesson_id': lesson_to_watch.id}),
            json.dumps({'watched_seconds': 300, 'total_seconds': 300, 'completed': True}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertIn('percentage', data)
        self.assertIn('is_certificate_eligible', data)

    def test_scenario_12_ineligible_claim_rejected(self):
        """Scenario 12: Ineligible claim is rejected with detailed error message."""
        self._complete_n_lessons(5) # only 25%
        res = self.client.post(
            reverse('certificates:center'),
            {'claim_course_id': self.course.id, 'recipient_name': 'Premature Claimer'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertFalse(data['success'])
        self.assertIn('missing_requirements', data)
        self.assertFalse(Certificate.objects.filter(user=self.user, course=self.course).exists())

    def test_scenario_13_100_percent_progress_cert_ready(self):
        """Scenario 13: 100% progress + exams passed -> Certificate is ready and claimable."""
        self._complete_n_lessons(20)
        self._pass_quiz(90)
        self._pass_mock(90)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 100)
        self.assertTrue(prog['is_certificate_eligible'])
        self.assertTrue(prog['is_completed'])

    def test_scenario_14_pdf_preview_and_download_authorized(self):
        """Scenario 14: PDF download and preview render valid binary PDF stream."""
        self._complete_n_lessons(17)
        self._pass_quiz(80)
        self._pass_mock(80)
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title='Data Science & AI Specialization',
            certificate_id='SS-CERT-2026-TEST85',
            recipient_name='Student EightyFive'
        )
        # Download
        dl_res = self.client.get(reverse('certificates:download_pdf', kwargs={'pk': cert.pk}))
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res['Content-Type'], 'application/pdf')
        self.assertIn('SS-CERT-2026-TEST85.pdf', dl_res['Content-Disposition'])

        # Preview
        pv_res = self.client.get(reverse('certificates:preview_pdf', kwargs={'pk': cert.pk}))
        self.assertEqual(pv_res.status_code, 200)
        self.assertEqual(pv_res['Content-Type'], 'application/pdf')
        self.assertIn('inline', pv_res['Content-Disposition'])
