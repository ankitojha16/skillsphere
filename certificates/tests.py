from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from certificates.models import Certificate
from courses.models import Course, Category, Enrollment, CourseAssessment, CourseAssessmentAttempt
from learning.models import Lesson, LessonProgress

class CertificateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='certtester', email='cert@test.com', password='Password123!')
        self.client = Client()
        self.client.login(username='certtester', password='Password123!')
        
        self.category = Category.objects.create(name='Backend', slug='backend')
        self.course = Course.objects.create(
            title='Python Fundamentals',
            slug='python-fundamentals',
            category=self.category,
            instructor_name='SkillSphere Lead Developer',
            description='Learn Python'
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title='Intro to Syntax',
            lesson_order=1,
            content='Hello world'
        )
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)

        # Final Quiz & Final Mock
        self.quiz = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_quiz',
            title='Final Quiz',
            duration_minutes=20,
            passing_percentage=70
        )
        self.mock = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_mock',
            title='Final Mock Exam',
            duration_minutes=30,
            passing_percentage=70
        )

    def test_certificate_claim_blocked_when_requirements_incomplete(self):
        # 0% completion, exams not taken -> claiming should be blocked
        response = self.client.post(reverse('certificates:center'), {
            'claim_course_id': self.course.id,
            'recipient_name': 'Ankit Kumar'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Certificate.objects.filter(user=self.user, course=self.course).exists())

    def test_certificate_issuance_when_all_requirements_met(self):
        # 1. 100% course lessons
        LessonProgress.objects.create(user=self.user, lesson=self.lesson, is_completed=True)

        # 2. Passed Final Quiz
        CourseAssessmentAttempt.objects.create(
            user=self.user,
            assessment=self.quiz,
            score=5,
            total_questions=5,
            percentage=100,
            is_passed=True
        )

        # 3. Passed Final Mock
        CourseAssessmentAttempt.objects.create(
            user=self.user,
            assessment=self.mock,
            score=5,
            total_questions=5,
            percentage=100,
            is_passed=True
        )

        # Claim with custom student name
        response = self.client.post(reverse('certificates:center'), {
            'claim_course_id': self.course.id,
            'recipient_name': 'Ankit Kumar'
        })
        self.assertEqual(response.status_code, 302)

        cert = Certificate.objects.filter(user=self.user, course=self.course).first()
        self.assertIsNotNone(cert)
        self.assertEqual(cert.recipient_name, 'Ankit Kumar')
        self.assertTrue(cert.certificate_id.startswith('SS-CERT-'))

        # Duplicate claim attempt is prevented
        response2 = self.client.post(reverse('certificates:center'), {
            'claim_course_id': self.course.id,
            'recipient_name': 'Ankit Kumar'
        })
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(Certificate.objects.filter(user=self.user, course=self.course).count(), 1)

    def test_certificate_pdf_download_and_preview(self):
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title='Mastery in Python',
            certificate_id='SS-CERT-2026-TEST01',
            recipient_name='Test Student'
        )
        # Download
        dl_res = self.client.get(reverse('certificates:download_pdf', kwargs={'pk': cert.pk}))
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res['Content-Type'], 'application/pdf')
        self.assertTrue(len(dl_res.content) > 1000)

        # Preview
        pv_res = self.client.get(reverse('certificates:preview_pdf', kwargs={'pk': cert.pk}))
        self.assertEqual(pv_res.status_code, 200)
        self.assertEqual(pv_res['Content-Type'], 'application/pdf')
        self.assertIn('inline', pv_res['Content-Disposition'])

    def test_public_certificate_verification(self):
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title='Mastery in Python',
            certificate_id='SS-CERT-2026-VERIFY01',
            recipient_name='Test Student'
        )
        # Anonymous client can verify
        anon_client = Client()
        response = anon_client.get(reverse('certificates:verify', kwargs={'certificate_id': 'SS-CERT-2026-VERIFY01'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Official Verified Credential')
        self.assertContains(response, 'Test Student')
        # Private email is hidden
        self.assertNotContains(response, 'cert@test.com')

    def test_invalid_certificate_verification_returns_404(self):
        anon_client = Client()
        response = anon_client.get(reverse('certificates:verify', kwargs={'certificate_id': 'SS-CERT-FAKE-9999'}))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Certificate Not Verified', status_code=404)
