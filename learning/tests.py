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

