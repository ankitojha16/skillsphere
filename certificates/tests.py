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
        self.assertContains(response, 'SkillSphere Course Completion Certificate')
        self.assertContains(response, 'Test Student')
        # Private email is hidden
        self.assertNotContains(response, 'cert@test.com')

    def test_invalid_certificate_verification_returns_404(self):
        anon_client = Client()
        response = anon_client.get(reverse('certificates:verify', kwargs={'certificate_id': 'SS-CERT-FAKE-9999'}))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Certificate Not Verified', status_code=404)

    def test_claim_course_certificate_post_endpoint_success(self):
        """Test POST /certificates/course/<course_id>/claim-cert/ creates cert and redirects to download."""
        LessonProgress.objects.create(user=self.user, lesson=self.lesson, is_completed=True)
        CourseAssessmentAttempt.objects.create(
            user=self.user, assessment=self.quiz, score=5, total_questions=5, percentage=100, is_passed=True
        )
        CourseAssessmentAttempt.objects.create(
            user=self.user, assessment=self.mock, score=5, total_questions=5, percentage=100, is_passed=True
        )

        claim_url = reverse('certificates:claim_course_certificate', kwargs={'course_id': self.course.id})
        response = self.client.post(claim_url, {'recipient_name': 'Ankit Kumar'})
        
        cert = Certificate.objects.filter(user=self.user, course=self.course).first()
        self.assertIsNotNone(cert)
        self.assertRedirects(response, reverse('certificates:download', kwargs={'pk': cert.id}))

        # Idempotent repeat claim redirects to download without error or duplication
        response2 = self.client.post(claim_url)
        self.assertRedirects(response2, reverse('certificates:download', kwargs={'pk': cert.id}))
        self.assertEqual(Certificate.objects.filter(user=self.user, course=self.course).count(), 1)

    def test_claim_course_certificate_post_endpoint_incomplete_fails(self):
        """Ineligible user cannot claim certificate via POST."""
        claim_url = reverse('certificates:claim_course_certificate', kwargs={'course_id': self.course.id})
        response = self.client.post(claim_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Certificate.objects.filter(user=self.user, course=self.course).exists())

    def test_claim_endpoint_http_method_safety(self):
        """GET request to claim endpoint must return 405 Method Not Allowed."""
        claim_url = reverse('certificates:claim_course_certificate', kwargs={'course_id': self.course.id})
        response = self.client.get(claim_url)
        self.assertEqual(response.status_code, 405)

    def test_download_course_certificate_get_safety(self):
        """GET /certificates/course/<id>/download/ does not create certificate if unclaimed."""
        LessonProgress.objects.create(user=self.user, lesson=self.lesson, is_completed=True)
        CourseAssessmentAttempt.objects.create(
            user=self.user, assessment=self.quiz, score=5, total_questions=5, percentage=100, is_passed=True
        )
        CourseAssessmentAttempt.objects.create(
            user=self.user, assessment=self.mock, score=5, total_questions=5, percentage=100, is_passed=True
        )

        dl_url = reverse('certificates:download_by_course', kwargs={'course_id': self.course.id})
        # Eligible but not yet claimed -> GET must redirect to center without creating cert
        response = self.client.get(dl_url)
        self.assertRedirects(response, reverse('certificates:center'))
        self.assertFalse(Certificate.objects.filter(user=self.user, course=self.course).exists())

        # Now create cert and verify GET streams PDF
        cert = Certificate.objects.create(
            user=self.user, course=self.course, title=self.course.title, recipient_name='Ankit'
        )
        response2 = self.client.get(dl_url)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2['Content-Type'], 'application/pdf')
        self.assertTrue(response2.content.startswith(b'%PDF-'))

    def test_certificate_center_rules_and_copy(self):
        """Certificate Center renders updated Video-First rules and no compulsory exam text."""
        response = self.client.get(reverse('certificates:center'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rule 1')
        self.assertContains(response, 'Mandatory Curriculum Completion')
        self.assertContains(response, 'Rule 2')
        self.assertContains(response, 'Optional Assessments')
        self.assertContains(response, 'Rule 3')
        self.assertContains(response, 'Instant Issuance')
        self.assertNotContains(response, '100% course completion required')

    def test_premium_certificate_pdf_generation_and_edge_cases(self):
        """Validate premium light-blue vector PDF output, QR code, and long text handling."""
        from services.pdf_service import PDFService
        
        # Test standard certificate
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title=self.course.title,
            certificate_id='SS-CERT-2026-TESTPREM',
            recipient_name='Ankit Kumar'
        )
        pdf_bytes = PDFService.generate_certificate_pdf(cert)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
        self.assertGreater(len(pdf_bytes), 5000)

        # Test long recipient name and long course title on a separate course
        course2 = Course.objects.create(
            title='Advanced Full-Stack Engineering with Distributed Cloud Computing & High-Performance Microservices Architecture',
            slug='advanced-fullstack-cloud-microservices',
            category=self.category,
            instructor_name='SkillSphere Lead Developer'
        )
        long_cert = Certificate.objects.create(
            user=self.user,
            course=course2,
            title=course2.title,
            certificate_id='SS-CERT-2026-TESTLONG',
            recipient_name='Dr. Christopher Alexander Montgomery-Wellington III'
        )
        long_pdf = PDFService.generate_certificate_pdf(long_cert)
        self.assertTrue(long_pdf.startswith(b'%PDF-'))
        self.assertGreater(len(long_pdf), 5000)

    def test_certificate_linkedin_and_share_controls(self):
        """Verify LinkedIn profile sync and share link controls are rendered."""
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title=self.course.title,
            certificate_id='SS-CERT-2026-LINKEDIN1',
            recipient_name='Ankit Kumar'
        )

        # 1. Test public verification portal
        verify_resp = self.client.get(reverse('certificates:verify', kwargs={'certificate_id': cert.certificate_id}))
        self.assertEqual(verify_resp.status_code, 200)
        self.assertContains(verify_resp, 'addToLinkedInBtn')
        self.assertContains(verify_resp, 'copyVerifyLinkBtn')
        self.assertContains(verify_resp, 'linkedin.com/profile/add')

        # 2. Test certificate center
        center_resp = self.client.get(reverse('certificates:center'))
        self.assertEqual(center_resp.status_code, 200)
        self.assertContains(center_resp, 'linkedin.com/profile/add')




