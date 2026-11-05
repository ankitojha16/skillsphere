from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from courses.models import Category, Course, Enrollment
from learning.models import Lesson, LessonProgress

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
        self.lesson1 = Lesson.objects.create(
            course=self.course,
            title='Lesson 1: Intro',
            lesson_order=1,
            estimated_minutes=15,
            content='<p>Lesson 1 content</p>'
        )
        self.lesson2 = Lesson.objects.create(
            course=self.course,
            title='Lesson 2: Models',
            lesson_order=2,
            estimated_minutes=20,
            content='<p>Lesson 2 content</p>'
        )
        Enrollment.objects.create(user=self.enrolled_user, course=self.course)

    def test_unenrolled_student_cannot_access_lesson(self):
        self.client.force_login(self.unenrolled_user)
        url = reverse('learning:lesson_detail', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})
        response = self.client.get(url)
        # Should redirect to course detail with message
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('courses:detail', kwargs={'slug': self.course.slug})))

    def test_enrolled_student_can_access_lesson(self):
        self.client.force_login(self.enrolled_user)
        url = reverse('learning:lesson_detail', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lesson 1: Intro')

    def test_lesson_completion_and_progress_calculation(self):
        self.client.force_login(self.enrolled_user)
        toggle_url = reverse('learning:complete_toggle', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})

        # Initially 0%
        initial_progress = self.course.get_user_progress(self.enrolled_user)
        self.assertEqual(initial_progress['percentage'], 0)
        self.assertEqual(initial_progress['completed'], 0)

        # Mark lesson 1 complete
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, 302)

        # Now 50% (1 of 2 lessons)
        mid_progress = self.course.get_user_progress(self.enrolled_user)
        self.assertEqual(mid_progress['percentage'], 50)
        self.assertEqual(mid_progress['completed'], 1)

        # Mark lesson 2 complete
        toggle_url2 = reverse('learning:complete_toggle', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson2.id})
        self.client.post(toggle_url2)

        # Now 100% (2 of 2 lessons)
        final_progress = self.course.get_user_progress(self.enrolled_user)
        self.assertEqual(final_progress['percentage'], 100)
        self.assertEqual(final_progress['completed'], 2)
