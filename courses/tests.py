from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from courses.models import Category, Course, Enrollment

class CoursesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='coursetester', email='coursetester@test.com', password='Password123!')
        self.category = Category.objects.create(name='Programming', slug='programming', icon='code')
        self.course = Course.objects.create(
            title='Intro to Python',
            slug='intro-to-python',
            category=self.category,
            difficulty='Beginner',
            instructor_name='Test Instructor',
            description='Test description'
        )

    def test_course_list_view(self):
        response = self.client.get(reverse('courses:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Intro to Python')

    def test_course_search_and_filter(self):
        # Search query
        response = self.client.get(reverse('courses:list'), {'q': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Intro to Python')

        # Filter query mismatch
        response = self.client.get(reverse('courses:list'), {'q': 'NonExistentXYZ'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Courses Found')

    def test_course_detail_view(self):
        response = self.client.get(reverse('courses:detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Intro to Python')

    def test_course_enrollment(self):
        self.client.force_login(self.user)
        enroll_url = reverse('courses:enroll', kwargs={'slug': self.course.slug})

        # Enroll POST
        response = self.client.post(enroll_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Enrollment.objects.filter(user=self.user, course=self.course).exists())

        # Duplicate enrollment should not duplicate record
        self.client.post(enroll_url)
        self.assertEqual(Enrollment.objects.filter(user=self.user, course=self.course).count(), 1)

    def test_course_unenrollment(self):
        self.client.force_login(self.user)
        Enrollment.objects.create(user=self.user, course=self.course)

        unenroll_url = reverse('courses:unenroll', kwargs={'slug': self.course.slug})
        response = self.client.post(unenroll_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Enrollment.objects.filter(user=self.user, course=self.course).exists())
