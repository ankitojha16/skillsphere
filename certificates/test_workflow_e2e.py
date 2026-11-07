import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from certificates.models import Certificate
from courses.models import Course, Category, Enrollment, CourseAssessment, CourseAssessmentAttempt
from learning.models import Lesson, LessonProgress

class CertificateWorkflowE2ETests(TestCase):
    """
    Full end-to-end verification of the certificate workflow:
    - Reach exactly 85% progress
    - Complete mandatory requirements and pass applicable assessments
    - Confirm certificate eligibility
    - Claim certificate
    - Download real PDF (with %PDF- header check)
    - Refresh and verify persistence
    - Claim again and verify no duplicate certificate is created
    - Verify authorization isolation (another student cannot access private certificate)
    """
    def setUp(self):
        self.student = User.objects.create_user(username='student_e2e', email='student_e2e@test.com', password='Password123!')
        self.other_student = User.objects.create_user(username='student_other', email='student_other@test.com', password='Password123!')

        self.client = Client()
        self.other_client = Client()

        self.category = Category.objects.create(name='Computer Science', slug='cs')
        self.course = Course.objects.create(
            title='Full-Stack Systems Architecture',
            slug='full-stack-systems',
            category=self.category,
            instructor_name='Prof. Turing',
            description='In-depth full stack systems architecture'
        )

        Enrollment.objects.create(user=self.student, course=self.course)
        Enrollment.objects.create(user=self.other_student, course=self.course)

        # 20 lessons -> 17 lessons = exactly 85%
        self.lessons = [
            Lesson.objects.create(
                course=self.course,
                title=f"Lesson #{i}",
                lesson_order=i,
                content=f"Curriculum text #{i}"
            )
            for i in range(1, 21)
        ]

        # Course assessments
        self.quiz = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_quiz',
            title='Systems Architecture Quiz',
            duration_minutes=20,
            passing_percentage=70
        )
        self.mock = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_mock',
            title='Systems Architecture Mock Exam',
            duration_minutes=30,
            passing_percentage=70
        )

    def test_complete_certificate_e2e_workflow(self):
        # 1. Login as primary student
        self.client.login(username='student_e2e', password='Password123!')

        # 2. Complete exactly 17 lessons out of 20 (17 / 20 * 100 = 85%)
        for i in range(17):
            LessonProgress.objects.create(user=self.student, lesson=self.lessons[i], is_completed=True)

        prog_before_exams = self.course.get_user_progress(self.student)
        self.assertEqual(prog_before_exams['percentage'], 85)
        self.assertTrue(prog_before_exams['is_unlocked'])
        self.assertFalse(prog_before_exams['is_certificate_eligible'], "Must not be eligible before passing mandatory exams")

        # 3. Pass mandatory assessments
        CourseAssessmentAttempt.objects.create(
            user=self.student,
            assessment=self.quiz,
            score=8,
            total_questions=10,
            percentage=80,
            is_passed=True
        )
        CourseAssessmentAttempt.objects.create(
            user=self.student,
            assessment=self.mock,
            score=9,
            total_questions=10,
            percentage=90,
            is_passed=True
        )

        # 4. Confirm certificate eligibility
        prog_eligible = self.course.get_user_progress(self.student)
        self.assertEqual(prog_eligible['percentage'], 85)
        self.assertTrue(prog_eligible['is_certificate_eligible'], "Must be eligible at 85% with passed assessments")
        self.assertEqual(prog_eligible['missing_requirements'], [])

        # 5. Claim certificate via Center POST
        claim_res = self.client.post(reverse('certificates:center'), {
            'claim_course_id': self.course.id,
            'recipient_name': 'E2E Test Student'
        })
        self.assertEqual(claim_res.status_code, 302)

        # 6. Verify certificate created and persistent
        cert = Certificate.objects.filter(user=self.student, course=self.course).first()
        self.assertIsNotNone(cert)
        self.assertEqual(cert.recipient_name, 'E2E Test Student')
        self.assertTrue(cert.certificate_id.startswith('SS-CERT-'))

        # 7. Download PDF and verify binary stream
        download_url = reverse('certificates:download_pdf', kwargs={'pk': cert.pk})
        dl_res = self.client.get(download_url)
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res['Content-Type'], 'application/pdf')
        self.assertIn(f"{cert.certificate_id}.pdf", dl_res['Content-Disposition'])
        # Verify valid PDF magic header %PDF-
        self.assertTrue(dl_res.content.startswith(b'%PDF-'), "Response must be a valid PDF binary stream starting with %PDF-")
        self.assertGreater(len(dl_res.content), 2000, "PDF size must be realistic")

        # 8. Refresh & claim again - verify idempotency (no duplicate created)
        claim_res2 = self.client.post(reverse('certificates:center'), {
            'claim_course_id': self.course.id,
            'recipient_name': 'E2E Test Student'
        })
        self.assertEqual(claim_res2.status_code, 302)
        self.assertEqual(Certificate.objects.filter(user=self.student, course=self.course).count(), 1)

        # 9. Verify isolation: another student attempting to download primary student's certificate is denied (403/404)
        self.other_client.login(username='student_other', password='Password123!')
        unauth_dl = self.other_client.get(download_url)
        # Must not succeed with 200
        self.assertIn(unauth_dl.status_code, [403, 404])
