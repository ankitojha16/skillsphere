import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from courses.models import Category, Course, Enrollment, CourseModule
from learning.models import (
    Lesson, LessonProgress, VideoProgress, LessonBookmark,
    StudentNote, Exercise, ExerciseSubmission
)

class LearningTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.enrolled_user = User.objects.create_user(username='enrolled', email='enrolled@test.com', password='Password123!')
        self.unenrolled_user = User.objects.create_user(username='unenrolled', email='unenrolled@test.com', password='Password123!')

        self.category = Category.objects.create(name='Web Dev', slug='web-dev')
        self.course = Course.objects.create(
            title='Django Full Stack',
            slug='django-full-stack',
            category=self.category,
            difficulty='Intermediate'
        )
        self.module = CourseModule.objects.create(
            course=self.course,
            title='Module 1: Architecture',
            order=1
        )
        self.lesson1 = Lesson.objects.create(
            course=self.course,
            module=self.module,
            title='Lesson 1: Intro',
            lesson_order=1,
            estimated_minutes=15,
            content='<p>Lesson 1 content</p>',
            video_url='https://www.youtube.com/watch?v=kqtD5dpn9C8',
            video_duration_seconds=600,
            key_takeaways=json.dumps(["Takeaway 1", "Takeaway 2"]),
            common_mistakes=json.dumps(["Mistake 1"])
        )
        self.lesson2 = Lesson.objects.create(
            course=self.course,
            module=self.module,
            title='Lesson 2: Models',
            lesson_order=2,
            estimated_minutes=20,
            content='<p>Lesson 2 content</p>'
        )
        self.exercise1 = Exercise.objects.create(
            lesson=self.lesson1,
            title='Test Exercise',
            instructions='Print Hello',
            starter_code='print("Hello")',
            expected_output='Hello',
            order=1
        )
        Enrollment.objects.create(user=self.enrolled_user, course=self.course)

    def test_unenrolled_student_cannot_access_lesson(self):
        self.client.force_login(self.unenrolled_user)
        url = reverse('learning:lesson_detail', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('courses:detail', kwargs={'slug': self.course.slug})))

    def test_enrolled_student_can_access_lesson(self):
        self.client.force_login(self.enrolled_user)
        url = reverse('learning:lesson_detail', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lesson 1: Intro')

    def test_lesson_completion_and_weighted_progress(self):
        self.client.force_login(self.enrolled_user)
        toggle_url = reverse('learning:complete_toggle', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})

        # Initially 0%
        initial_progress = self.course.get_user_progress(self.enrolled_user)
        self.assertEqual(initial_progress['percentage'], 0)

        # Mark lesson 1 complete (Course has 2 lessons and 1 exercise: 60% weight for lessons, 20% for exercises, 20% for assignments)
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, 302)

        mid_progress = self.course.get_user_progress(self.enrolled_user)
        self.assertEqual(mid_progress['completed'], 1)
        self.assertTrue(mid_progress['percentage'] > 0)

    def test_video_progress_api(self):
        self.client.force_login(self.enrolled_user)
        url = reverse('learning:video_progress', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})

        # Send 550s out of 600s (> 85% completion)
        response = self.client.post(url, json.dumps({
            'watched_seconds': 550,
            'duration_seconds': 600,
            'position_seconds': 550
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_completed'])
        self.assertTrue(VideoProgress.objects.filter(user=self.enrolled_user, lesson=self.lesson1, is_completed=True).exists())

    def test_bookmark_toggle_api(self):
        self.client.force_login(self.enrolled_user)
        url = reverse('learning:bookmark_toggle', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})

        # Bookmark
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_bookmarked'])
        self.assertTrue(LessonBookmark.objects.filter(user=self.enrolled_user, lesson=self.lesson1).exists())

        # Un-bookmark
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_bookmarked'])
        self.assertFalse(LessonBookmark.objects.filter(user=self.enrolled_user, lesson=self.lesson1).exists())

    def test_student_notes_api(self):
        self.client.force_login(self.enrolled_user)
        url = reverse('learning:student_note', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})

        response = self.client.post(url, json.dumps({
            'notes': 'Important memo on MVT pattern.'
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        note = StudentNote.objects.filter(user=self.enrolled_user, lesson=self.lesson1).first()
        self.assertIsNotNone(note)
        self.assertEqual(note.content, 'Important memo on MVT pattern.')

    def test_notes_pdf_download(self):
        self.client.force_login(self.enrolled_user)
        url = reverse('learning:download_notes_pdf', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(len(response.content) > 1000)

    def test_exercise_submission_api(self):
        self.client.force_login(self.enrolled_user)
        url = reverse('learning:exercise_submit', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id, 'exercise_id': self.exercise1.id})

        response = self.client.post(url, json.dumps({
            'exercise_id': self.exercise1.id,
            'code': 'print("Hello")'
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_passed'])
        self.assertTrue(ExerciseSubmission.objects.filter(user=self.enrolled_user, exercise=self.exercise1, is_passed=True).exists())

    def test_lesson_embed_video_url_property(self):
        # 1. Standard watch?v= URL
        self.lesson1.video_url = 'https://www.youtube.com/watch?v=ttWkL4nU2qY'
        self.assertEqual(self.lesson1.embed_video_url, 'https://www.youtube.com/embed/ttWkL4nU2qY?enablejsapi=1&rel=0')

        # 2. Short youtu.be URL
        self.lesson1.video_url = 'https://youtu.be/kqtD5dpn9C8'
        self.assertEqual(self.lesson1.embed_video_url, 'https://www.youtube.com/embed/kqtD5dpn9C8?enablejsapi=1&rel=0')

        # 3. Already embed URL with params
        self.lesson1.video_url = 'https://www.youtube.com/embed/kqtD5dpn9C8?enablejsapi=1&rel=0'
        self.assertEqual(self.lesson1.embed_video_url, 'https://www.youtube.com/embed/kqtD5dpn9C8?enablejsapi=1&rel=0')

        # 4. Empty video URL
        self.lesson1.video_url = ''
        self.assertEqual(self.lesson1.embed_video_url, '')

    def test_mark_video_watched_manually(self):
        self.client.force_login(self.enrolled_user)
        url = reverse('learning:video_progress', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})

        resp = self.client.post(url, json.dumps({'mark_completed': True}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_completed'])

        prog = VideoProgress.objects.filter(user=self.enrolled_user, lesson=self.lesson1).first()
        self.assertIsNotNone(prog)
        self.assertTrue(prog.is_completed)

    def test_complete_lesson_toggle_ajax_granular_counts(self):
        self.client.force_login(self.enrolled_user)
        url = reverse('learning:complete_toggle', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})

        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_completed'])
        self.assertIn('completed_count', data)
        self.assertIn('total_count', data)
        self.assertIn('percentage', data)
        self.assertEqual(data['completed_count'], 1)
        self.assertEqual(data['total_count'], 2)

    def test_unenrolled_api_access_blocked(self):
        # Ensure that an authenticated student who is NOT enrolled is blocked from learning APIs
        self.client.force_login(self.unenrolled_user)

        # 1. Video Progress API -> 403
        resp_video = self.client.post(
            reverse('learning:video_progress', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id}),
            json.dumps({'position': 10}),
            content_type='application/json'
        )
        self.assertEqual(resp_video.status_code, 403)

        # 2. Bookmark API -> 403
        resp_bm = self.client.post(
            reverse('learning:bookmark_toggle', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})
        )
        self.assertEqual(resp_bm.status_code, 403)

        # 3. Student Note API -> 403
        resp_note = self.client.post(
            reverse('learning:student_note', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id}),
            json.dumps({'notes': 'Hacking notes'}),
            content_type='application/json'
        )
        self.assertEqual(resp_note.status_code, 403)

        # 4. Exercise Submit API -> 403
        resp_ex = self.client.post(
            reverse('learning:exercise_submit', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id, 'exercise_id': self.exercise1.id}),
            json.dumps({'code': 'print("Hello")'}),
            content_type='application/json'
        )
        self.assertEqual(resp_ex.status_code, 403)

        # 5. AI Notes Assist API -> 403
        resp_ai = self.client.post(
            reverse('learning:ai_notes_assist', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id}),
            json.dumps({'action': 'summarize'}),
            content_type='application/json'
        )
        self.assertEqual(resp_ai.status_code, 403)

        # 6. PDF Download View -> 302 redirect with message
        resp_pdf = self.client.get(
            reverse('learning:download_notes_pdf', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})
        )
        self.assertEqual(resp_pdf.status_code, 302)


import io
import re
from courses.models import CourseAssessment, CourseAssessmentQuestion
from certificates.models import Certificate
from services.pdf_service import PDFService


class CurriculumExpansionAndCertificateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Programming Test', slug='programming-test')
        self.course = Course.objects.create(
            title='Python Programming from Scratch to OOP',
            slug='python-programming-from-scratch',
            category=self.category,
            difficulty='Beginner',
            is_published=True,
            curriculum_version=2,
            legacy_total_lessons=4
        )

        # Create 16 lessons (1..4 version 1, 5..16 version 2)
        self.lessons = []
        for i in range(1, 17):
            lesson = Lesson.objects.create(
                course=self.course,
                lesson_order=i,
                title='Control Flow: If-Else & Loops' if i == 2 else f'Lesson {i}',
                chapter_name=f'Chapter {(i-1)//4 + 1}',
                estimated_minutes=20,
                content=f'<p>In-depth content for lesson {i}</p>',
                curriculum_version=1 if i <= 4 else 2
            )
            self.lessons.append(lesson)

        # Create Course Assessments
        self.quiz = CourseAssessment.objects.create(
            course=self.course,
            title='Python Final Quiz',
            assessment_type='final_quiz',
            passing_percentage=70,
            duration_minutes=30,
            is_active=True
        )
        self.mock = CourseAssessment.objects.create(
            course=self.course,
            title='Python Final Mock',
            assessment_type='final_mock',
            passing_percentage=70,
            duration_minutes=45,
            is_active=True
        )

        # Users
        self.user_v1 = User.objects.create_user(username='student_v1', password='Password123!', email='v1@example.com')
        self.user_v2 = User.objects.create_user(username='student_v2', password='Password123!', email='v2@example.com')
        self.user_other = User.objects.create_user(username='student_other', password='Password123!', email='other@example.com')

        # Enrollments
        self.enrollment_v1 = Enrollment.objects.create(user=self.user_v1, course=self.course, curriculum_version=1)
        self.enrollment_v2 = Enrollment.objects.create(user=self.user_v2, course=self.course, curriculum_version=2)

    def test_pdf_generation_academic_notes_page_count(self):
        """Phase 1: Verify 'Control Flow: If-Else & Loops' generates >= 6 pages of academic notes with %PDF- header."""
        control_flow_lesson = self.lessons[1]  # order 2
        pdf_bytes = PDFService.generate_lesson_notes_pdf(control_flow_lesson)

        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))

        page_count = len(re.findall(rb'/Type\s*/Page\b', pdf_bytes))
        # Deep academic content produces 11 pages
        self.assertGreaterEqual(page_count, 6)
        self.assertEqual(page_count, 11)

    def test_curriculum_versioning_progress_denominators(self):
        """Phase 7: Existing v1 student has denominator 4; v2 student has denominator 16."""
        # Complete first 4 lessons for both users
        for i in range(4):
            LessonProgress.objects.create(user=self.user_v1, lesson=self.lessons[i], is_completed=True)
            LessonProgress.objects.create(user=self.user_v2, lesson=self.lessons[i], is_completed=True)

        prog_v1 = self.course.get_user_progress(self.user_v1)
        self.assertEqual(prog_v1['total'], 4)
        self.assertEqual(prog_v1['completed'], 4)
        self.assertEqual(prog_v1['percentage'], 100)

        prog_v2 = self.course.get_user_progress(self.user_v2)
        self.assertEqual(prog_v2['total'], 16)
        self.assertEqual(prog_v2['completed'], 4)
        self.assertEqual(prog_v2['percentage'], 25)

    def test_curriculum_voluntary_upgrade(self):
        """Phase 7: Voluntary upgrade POST /courses/<slug>/upgrade-curriculum/ transitions student to v2."""
        self.client.login(username='student_v1', password='Password123!')
        url = reverse('courses:upgrade_curriculum', kwargs={'slug': self.course.slug})

        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)

        self.enrollment_v1.refresh_from_db()
        self.assertEqual(self.enrollment_v1.curriculum_version, 2)

    def test_certificate_claim_and_download_workflow(self):
        """Phase 5 & 6: Verify claim endpoint idempotency and download headers."""
        from courses.models import CourseAssessmentAttempt

        # Complete all 16 lessons for v2 student
        for lesson in self.lessons:
            LessonProgress.objects.create(user=self.user_v2, lesson=lesson, is_completed=True)

        # Pass both final quiz and final mock
        CourseAssessmentAttempt.objects.create(
            user=self.user_v2,
            assessment=self.quiz,
            score=10,
            total_questions=10,
            percentage=100,
            is_passed=True
        )
        CourseAssessmentAttempt.objects.create(
            user=self.user_v2,
            assessment=self.mock,
            score=10,
            total_questions=10,
            percentage=100,
            is_passed=True
        )

        self.client.login(username='student_v2', password='Password123!')

        # 1. Claim Certificate via POST (JSON / AJAX request)
        claim_url = reverse('certificates:claim_course_certificate', kwargs={'course_id': self.course.id})
        response = self.client.post(claim_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('certificate_id', data)

        cert = Certificate.objects.get(user=self.user_v2, course=self.course)

        # 2. Idempotent claim
        response_repeat = self.client.post(claim_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_repeat.status_code, 200)
        self.assertEqual(response_repeat.json()['certificate_id'], cert.certificate_id)

        # 3. Direct course download pathway GET /certificates/course/<id>/download/
        course_download_url = reverse('certificates:download_course_certificate', kwargs={'course_id': self.course.id})
        dl_resp = self.client.get(course_download_url)
        self.assertEqual(dl_resp.status_code, 200)
        self.assertEqual(dl_resp['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', dl_resp['Content-Disposition'])
        self.assertTrue(int(dl_resp['Content-Length']) > 0)
        self.assertIn('private', dl_resp['Cache-Control'])

        # 4. Download by PK GET /certificates/<pk>/download/
        pk_download_url = reverse('certificates:download_certificate_pdf', kwargs={'pk': cert.pk})
        pk_resp = self.client.get(pk_download_url)
        self.assertEqual(pk_resp.status_code, 200)
        self.assertEqual(pk_resp['Content-Type'], 'application/pdf')

        # 5. Ownership isolation: Another student should receive 404 Not Found (enumeration prevention)
        self.client.login(username='student_other', password='Password123!')
        unauth_resp = self.client.get(pk_download_url)
        self.assertEqual(unauth_resp.status_code, 404)



