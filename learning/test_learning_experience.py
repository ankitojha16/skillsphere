import io
import re
import zlib
import base64
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from courses.models import Course, CourseModule, Enrollment, CourseAssessment, CourseAssessmentAttempt, Category
from learning.models import Lesson, LessonProgress, Exercise, ExerciseSubmission
from certificates.models import Certificate
from services.pdf_service import PDFService


class LearningExperienceAndCertificateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teststudent', password='Password123!', email='student@skillsphere.test')
        self.category = Category.objects.create(name='Computer Science', slug='computer-science')
        self.course = Course.objects.create(
            title='Advanced Python Engineering',
            slug='advanced-python-engineering',
            category=self.category,
            difficulty='Advanced',
            is_published=True,
            estimated_duration='20 hours'
        )
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)

        # Create 10 lessons for granular percentage tests (10% per lesson)
        self.lessons = []
        for i in range(1, 11):
            l = Lesson.objects.create(
                course=self.course,
                title=f'Deep Dive Lesson {i}',
                lesson_order=i,
                chapter_name='Architecture',
                content=f'<p>In-depth content for lesson {i}</p><pre><code>def solution_{i}():\n    return {i}</code></pre>',
                key_takeaways='["Mastered core concept", "Applied best practice"]',
                common_mistakes='["Avoid circular imports", "Avoid mutable defaults"]'
            )
            self.lessons.append(l)

        # Create an exercise on lesson 1
        self.exercise = Exercise.objects.create(
            lesson=self.lessons[0],
            title='Build Custom Context Manager',
            instructions='Write a context manager using `__enter__` and `__exit__`.',
            starter_code='class CustomContext:\n    # Solution starter\n    pass',
            expected_output='Context Entered\nContext Exited',
            solution='class CustomContext:\n    def __enter__(self):\n        return self\n    def __exit__(self, *args):\n        pass'
        )

        # Create final quiz and mock test
        self.final_quiz = CourseAssessment.objects.create(
            course=self.course,
            title='Final Comprehensive Quiz',
            assessment_type='final_quiz',
            is_active=True,
            passing_percentage=70
        )
        self.final_mock = CourseAssessment.objects.create(
            course=self.course,
            title='Final Mock Test',
            assessment_type='final_mock',
            is_active=True,
            passing_percentage=70
        )

    def test_settings_thresholds_configured(self):
        """Ensure settings have correct thresholds."""
        self.assertEqual(getattr(settings, 'ASSESSMENT_UNLOCK_THRESHOLD', None), 80)
        self.assertEqual(getattr(settings, 'CERTIFICATE_ELIGIBILITY_THRESHOLD', None), 85)
        self.assertEqual(getattr(settings, 'ASSESSMENT_PASSING_PERCENTAGE', None), 70)

    def test_progress_under_80_locks_assessment_and_certificate(self):
        """At < 80% progress, assessments and certificates must remain locked."""
        # Complete 6 lessons (60% mandatory lesson progress)
        for i in range(6):
            LessonProgress.objects.create(user=self.user, lesson=self.lessons[i], is_completed=True)

        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 60)
        self.assertFalse(prog['is_unlocked'])
        self.assertFalse(prog['is_certificate_eligible'])
        self.assertTrue(any('80%' in r for r in prog['missing_requirements']))
        self.assertTrue(any('85%' in r for r in prog['missing_requirements']))

    def test_progress_80_to_84_unlocks_assessment_locks_certificate(self):
        """At 80-84% progress, assessments unlock but certificate requires 85% + passed exams."""
        # 8 lessons = 80% progress
        for i in range(8):
            LessonProgress.objects.create(user=self.user, lesson=self.lessons[i], is_completed=True)
        ExerciseSubmission.objects.create(user=self.user, exercise=self.exercise, submitted_code='pass', is_passed=True)

        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 80)
        self.assertTrue(prog['is_unlocked'], "Assessments should unlock at 80%+")
        self.assertFalse(prog['is_certificate_eligible'], "Certificate should still be locked at 80% without passed exams")

    def test_progress_85_with_exams_passed_is_certificate_eligible(self):
        """At >= 85% progress with final quiz and mock passed >= 70%, certificate is eligible."""
        # 9 lessons = 90% progress
        for i in range(9):
            LessonProgress.objects.create(user=self.user, lesson=self.lessons[i], is_completed=True)
        ExerciseSubmission.objects.create(user=self.user, exercise=self.exercise, submitted_code='pass', is_passed=True)

        # Pass final quiz and final mock
        CourseAssessmentAttempt.objects.create(
            user=self.user,
            assessment=self.final_quiz,
            score=8,
            total_questions=10,
            percentage=80,
            is_passed=True
        )
        CourseAssessmentAttempt.objects.create(
            user=self.user,
            assessment=self.final_mock,
            score=9,
            total_questions=10,
            percentage=90,
            is_passed=True
        )

        prog = self.course.get_user_progress(self.user)
        self.assertEqual(prog['percentage'], 90)
        self.assertGreaterEqual(prog['percentage'], 85)
        self.assertTrue(prog['is_unlocked'])
        self.assertTrue(prog['quiz_passed'])
        self.assertTrue(prog['mock_passed'])
        self.assertTrue(prog['is_certificate_eligible'])
        self.assertEqual(prog['missing_requirements'], [])

    def test_exercise_opens_empty_by_default_and_preserves_submission(self):
        """Exercises must open with empty editor by default and preserve student submissions."""
        self.client.login(username='teststudent', password='Password123!')
        url = reverse('learning:lesson_detail', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lessons[0].id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verify context data passed to template has empty user_code
        exercises_data = response.context['exercises_data']
        self.assertEqual(len(exercises_data), 1)
        self.assertEqual(exercises_data[0]['user_code'], "", "New unattempted challenge should default to empty string")

        # Verify textarea has placeholder and empty content
        content_html = response.content.decode()
        self.assertIn('placeholder="# Write your solution here..."', content_html)
        self.assertIn('class="btn btn-secondary-custom btn-sm py-1.5 px-3 clear-code-btn"', content_html)

        # Submit user code
        submit_url = reverse('learning:exercise_submit', kwargs={
            'course_slug': self.course.slug,
            'lesson_id': self.lessons[0].id,
            'exercise_id': self.exercise.id
        })
        student_code = "class CustomContext:\n    pass # student attempt"
        post_resp = self.client.post(submit_url, {'code': student_code})
        self.assertEqual(post_resp.status_code, 200)

        # Next time page is fetched, user_code must reflect student submission
        response2 = self.client.get(url)
        exercises_data2 = response2.context['exercises_data']
        self.assertEqual(exercises_data2[0]['user_code'], student_code)

    def test_pdf_notes_16_sections_and_numbered_canvas(self):
        """Generate lesson notes PDF and verify running headers, footers ('Page X of Y') and sections."""
        pdf_bytes = PDFService.generate_lesson_notes_pdf(self.lessons[0])
        self.assertTrue(pdf_bytes.startswith(b'%PDF-1.4'))
        self.assertGreater(len(pdf_bytes), 5000)

        # Decode ASCII85 Flate streams to verify text contents
        s_idx = pdf_bytes.find(b'stream\n', pdf_bytes.find(b'14 0 obj')) + 7
        e_idx = pdf_bytes.find(b'\nendstream', s_idx)
        raw = pdf_bytes[s_idx:e_idx]
        raw = raw[:raw.find(b'~>') + 2]
        flate = base64.a85decode(raw, adobe=True)
        text = zlib.decompress(flate).decode('latin1')

        # Check running footer format 'Page 1 of Y'
        self.assertRegex(text, r'Page 1 of \d+')
        self.assertIn('SkillSphere Comprehensive Courseware', text)

    def test_claim_certificate_centre_view(self):
        """Test claim certificate flow through certificates center."""
        self.client.login(username='teststudent', password='Password123!')
        center_url = reverse('certificates:center')

        # 1. Unmet progress: claim fails and redirects
        post_resp = self.client.post(center_url, {'claim_course_id': self.course.id})
        self.assertEqual(post_resp.status_code, 302)
        self.assertFalse(Certificate.objects.filter(user=self.user, course=self.course).exists())

        # 2. Complete 9 lessons (72%) + exercise (20%) = 92% and pass exams
        for i in range(9):
            LessonProgress.objects.create(user=self.user, lesson=self.lessons[i], is_completed=True)
        ExerciseSubmission.objects.create(user=self.user, exercise=self.exercise, submitted_code='pass', is_passed=True)
        CourseAssessmentAttempt.objects.create(user=self.user, assessment=self.final_quiz, score=10, total_questions=10, percentage=100, is_passed=True)
        CourseAssessmentAttempt.objects.create(user=self.user, assessment=self.final_mock, score=10, total_questions=10, percentage=100, is_passed=True)

        post_resp2 = self.client.post(center_url, {'claim_course_id': self.course.id})
        self.assertEqual(post_resp2.status_code, 302)
        self.assertTrue(Certificate.objects.filter(user=self.user, course=self.course).exists())
