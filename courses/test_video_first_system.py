from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from courses.models import (
    Category, Course, Enrollment, CourseModule,
    CourseAssessment, CourseAssessmentQuestion, CourseAssessmentAttempt
)
from learning.models import Lesson, LessonProgress
from certificates.models import Certificate


class VideoFirstSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='videolearner',
            email='videolearner@test.com',
            password='TestPassword123!'
        )
        self.category = Category.objects.create(name='Python Track', slug='python-track', icon='code')

        # Course with 16 lessons and 2 optional assessments
        self.course = Course.objects.create(
            title='Python Programming from Scratch to OOP',
            slug='python-from-scratch-to-oop',
            category=self.category,
            difficulty='Beginner',
            instructor_name='SkillSphere Lead Faculty',
            description='Comprehensive Python curriculum',
            is_published=True,
            curriculum_version=2
        )
        self.module = CourseModule.objects.create(
            course=self.course,
            title='Core Foundations',
            order=1
        )
        self.lessons = []
        for i in range(1, 17):
            lesson = Lesson.objects.create(
                course=self.course,
                module=self.module,
                title=f'Lesson {i}',
                lesson_order=i,
                estimated_minutes=15,
                video_url=f'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            )
            self.lessons.append(lesson)

        # 2 Optional Assessments
        self.quiz = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_quiz',
            title='Comprehensive Course Quiz',
            duration_minutes=20,
            passing_percentage=70,
            is_active=True
        )
        self.mock = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_mock',
            title='Industry Mock Exam',
            duration_minutes=30,
            passing_percentage=70,
            is_active=True
        )

        Enrollment.objects.create(user=self.user, course=self.course)

    def _complete_lessons(self, count):
        for i in range(count):
            LessonProgress.objects.update_or_create(
                user=self.user,
                lesson=self.lessons[i],
                defaults={'is_completed': True}
            )

    def _pass_assessment(self, assessment, score=85):
        CourseAssessmentAttempt.objects.create(
            user=self.user,
            assessment=assessment,
            score=score,
            total_questions=10,
            percentage=score,
            is_passed=True
        )

    # 1. Video lessons only: 16/16 completed = exactly 80% progress
    def test_01_video_lessons_only_16_of_16_gives_80_percent(self):
        self._complete_lessons(16)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 80)
        self.assertEqual(prog['overall_progress'], 80)
        self.assertTrue(prog['is_certificate_eligible'])
        self.assertEqual(prog['completed_mandatory_lessons'], 16)
        self.assertEqual(prog['total_mandatory_lessons'], 16)

    # 2. Incomplete video lessons: 15/16 completed = 75% progress (not eligible)
    def test_02_incomplete_video_lessons_15_of_16_gives_75_percent_locked(self):
        self._complete_lessons(15)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 75)
        self.assertFalse(prog['is_certificate_eligible'])
        self.assertIn("Complete 1 more mandatory video lesson", prog['missing_requirements'][0])

    # 3. Optional tests when lessons incomplete: 15/16 + 100% assessments = 95% progress, but Certificate LOCKED
    def test_03_optional_tests_cannot_compensate_for_incomplete_video(self):
        self._complete_lessons(15)
        self._pass_assessment(self.quiz, score=100)
        self._pass_assessment(self.mock, score=100)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 95)
        self.assertFalse(prog['is_certificate_eligible'])
        self.assertTrue(len(prog['missing_requirements']) > 0)

    # 4. Video + 1 quiz: 16/16 lessons + 1 passed quiz = 90% progress, Certificate READY
    def test_04_video_plus_one_quiz_gives_90_percent_ready(self):
        self._complete_lessons(16)
        self._pass_assessment(self.quiz, score=80)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 90)
        self.assertTrue(prog['is_certificate_eligible'])

    # 5. Full course: 16/16 lessons + 2 passed assessments = 100% progress, Certificate READY
    def test_05_full_course_16_lessons_plus_2_assessments_gives_100_percent(self):
        self._complete_lessons(16)
        self._pass_assessment(self.quiz, score=90)
        self._pass_assessment(self.mock, score=95)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 100)
        self.assertTrue(prog['is_certificate_eligible'])

    # 6. Optional assessments without video: 0/16 lessons + 2 passed assessments = 20% progress, Certificate LOCKED
    def test_06_assessments_without_video_gives_20_percent_locked(self):
        self._pass_assessment(self.quiz, score=90)
        self._pass_assessment(self.mock, score=90)
        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 20)
        self.assertFalse(prog['is_certificate_eligible'])

    # 7. Courses without assessments: 16/16 lessons = 80% progress, Certificate READY
    def test_07_course_without_assessments_gives_80_percent_ready(self):
        no_exam_course = Course.objects.create(
            title='Curriculum Only Track',
            slug='curriculum-only-track',
            category=self.category,
            difficulty='Beginner',
            is_published=True
        )
        mod = CourseModule.objects.create(course=no_exam_course, title='M1', order=1)
        for j in range(1, 17):
            les = Lesson.objects.create(
                course=no_exam_course, module=mod,
                title=f'L {j}', lesson_order=j, estimated_minutes=10
            )
            LessonProgress.objects.create(user=self.user, lesson=les, is_completed=True)

        prog = no_exam_course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 80)
        self.assertTrue(prog['is_certificate_eligible'])
        self.assertFalse(prog['has_optional_assessments'])
        self.assertEqual(prog['optional_assessments_count'], 0)

    # 8. Claim Certificate with 80% video progress succeeds and generates certificate record
    def test_08_claim_certificate_with_80_percent_video_succeeds(self):
        self._complete_lessons(16)
        self.client.force_login(self.user)
        claim_url = reverse('certificates:claim_course_certificate', kwargs={'course_id': self.course.id})
        response = self.client.post(claim_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Certificate.objects.filter(user=self.user, course=self.course).exists())

    # 9. Claim Certificate with 75% video progress fails
    def test_09_claim_certificate_with_75_percent_fails(self):
        self._complete_lessons(15)
        self.client.force_login(self.user)
        claim_url = reverse('certificates:claim_course_certificate', kwargs={'course_id': self.course.id})
        response = self.client.post(claim_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Certificate.objects.filter(user=self.user, course=self.course).exists())
        messages = list(response.context['messages'])
        self.assertTrue(any("Complete 1 more mandatory video lesson" in str(m) for m in messages))

    # 10. Claim Certificate does not require any assessment attempts or passing scores
    def test_10_claim_certificate_zero_assessment_attempts(self):
        self._complete_lessons(16)
        # Verify 0 assessment attempts exist
        self.assertEqual(CourseAssessmentAttempt.objects.filter(user=self.user).count(), 0)
        self.client.force_login(self.user)
        claim_url = reverse('certificates:claim_course_certificate', kwargs={'course_id': self.course.id})
        response = self.client.post(claim_url, follow=True)
        self.assertEqual(response.status_code, 200)
        cert = Certificate.objects.filter(user=self.user, course=self.course).first()
        self.assertIsNotNone(cert)
        self.assertIn("mandatory video lessons", cert.criteria_met)

    # 11. Direct PDF download returns valid PDF when certificate is claimed
    def test_11_direct_pdf_download_returns_valid_pdf(self):
        self._complete_lessons(16)
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title=f"Certificate of Completion - {self.course.title}",
            certificate_id="SS-CERT-2026-TESTPDF1",
            recipient_name="Video Learner"
        )
        self.client.force_login(self.user)
        download_url = reverse('certificates:download_by_course', kwargs={'course_id': self.course.id})
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    # 12. Direct PDF download redirects to claim flow when eligible but unclaimed
    def test_12_direct_pdf_download_redirects_to_claim_when_unclaimed(self):
        self._complete_lessons(16)
        self.client.force_login(self.user)
        download_url = reverse('certificates:download_by_course', kwargs={'course_id': self.course.id})
        response = self.client.get(download_url, follow=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to certificate center with claim CTA
        self.assertIn(reverse('certificates:center'), response.redirect_chain[0][0])
        messages = list(response.context['messages'])
        self.assertTrue(any("Please claim your certificate" in str(m) for m in messages))

    # 13. Certificate verification URL resolves and confirms valid certificate
    def test_13_certificate_verification_url_resolves(self):
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title=f"Certificate of Completion - {self.course.title}",
            certificate_id="SS-CERT-2026-VERIFY1",
            recipient_name="Video Learner"
        )
        verify_url = reverse('certificates:verify', kwargs={'certificate_id': cert.certificate_id})
        response = self.client.get(verify_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, cert.certificate_id)
        self.assertContains(response, "Video Learner")

    # 14. Video player URLs render valid embed format (youtube-nocookie.com, no invalid params)
    def test_14_video_player_embed_url_format(self):
        lesson = self.lessons[0]
        self.assertEqual(lesson.youtube_id, "dQw4w9WgXcQ")
        self.assertIn("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", lesson.embed_video_url)
        self.assertIn("rel=0", lesson.embed_video_url)
        self.assertIn("playsinline=1", lesson.embed_video_url)
        self.assertEqual(lesson.youtube_watch_url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    # 15. Existing user certificates remain valid and downloadable
    def test_15_existing_user_certificates_remain_valid(self):
        # Create an existing certificate from an older curriculum version
        old_cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title=f"Certificate of Completion - {self.course.title}",
            certificate_id="SS-CERT-2025-LEGACY9",
            recipient_name="Legacy Student",
            criteria_met="Completed legacy Version 1 curriculum requirements."
        )
        prog = self.course.get_user_progress(self.user)
        self.assertTrue(prog['certificate_issued'])
        self.assertTrue(prog['is_certificate_eligible'])

        self.client.force_login(self.user)
        download_url = reverse('certificates:download_by_course', kwargs={'course_id': self.course.id})
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
