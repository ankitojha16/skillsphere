from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from certificates.models import Certificate
from courses.models import Course, Category, Enrollment
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

    def test_certificate_issuance_and_claim(self):
        # Mark lesson completed
        LessonProgress.objects.create(user=self.user, lesson=self.lesson, is_completed=True)
        
        # Claim certificate
        response = self.client.post(reverse('certificates:center'), {
            'claim_course_id': self.course.id,
        })
        self.assertEqual(response.status_code, 302)
        cert = Certificate.objects.filter(user=self.user, course=self.course).first()
        self.assertIsNotNone(cert)
        self.assertTrue(cert.certificate_id.startswith('SKILL-'))

    def test_certificate_pdf_download(self):
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title='Mastery in Python',
            certificate_id='SKILL-2026-TEST01',
            recipient_name='Test Student'
        )
        response = self.client.get(reverse('certificates:download_pdf', kwargs={'pk': cert.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(len(response.content) > 1000)

    def test_public_certificate_verification(self):
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title='Mastery in Python',
            certificate_id='SKILL-2026-VERIFY01',
            recipient_name='Test Student'
        )
        # Verify with anonymous client
        anon_client = Client()
        response = anon_client.get(reverse('certificates:verify', kwargs={'certificate_id': 'SKILL-2026-VERIFY01'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Official Verified Credential')
        self.assertContains(response, 'Test Student')
        # Ensure private email is not in the public verification page
        self.assertNotContains(response, 'cert@test.com')

    def test_invalid_certificate_verification_returns_404(self):
        anon_client = Client()
        response = anon_client.get(reverse('certificates:verify', kwargs={'certificate_id': 'INVALID-FAKE-ID'}))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Certificate Not Verified', status_code=404)
