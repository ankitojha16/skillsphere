from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from courses.models import (
    Category, Course, Enrollment, CourseModule,
    CourseAssessment, CourseAssessmentQuestion, CourseAssessmentAttempt
)
from learning.models import Lesson, LessonProgress

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
        self.module = CourseModule.objects.create(
            course=self.course,
            title='Module 1: Fundamentals',
            order=1
        )
        self.lesson1 = Lesson.objects.create(
            course=self.course,
            module=self.module,
            title='Variables',
            lesson_order=1,
            estimated_minutes=15
        )
        self.lesson2 = Lesson.objects.create(
            course=self.course,
            module=self.module,
            title='Loops',
            lesson_order=2,
            estimated_minutes=15
        )

        # Assessments
        self.final_quiz = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_quiz',
            title='Final Quiz',
            duration_minutes=20,
            passing_percentage=70
        )
        self.q1 = CourseAssessmentQuestion.objects.create(
            assessment=self.final_quiz,
            order=1,
            question_text='What is Python?',
            option_a='Language',
            option_b='Snake',
            option_c='Coffee',
            option_d='Car',
            correct_answer='A',
            topic='Basics',
            explanation='Python is a programming language.'
        )

    def test_course_list_view(self):
        response = self.client.get(reverse('courses:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Intro to Python')

    def test_course_search_and_filter(self):
        response = self.client.get(reverse('courses:list'), {'q': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Intro to Python')

        response = self.client.get(reverse('courses:list'), {'q': 'NonExistentXYZ'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Courses Found')

    def test_course_detail_view(self):
        response = self.client.get(reverse('courses:detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Intro to Python')
        self.assertContains(response, 'Module 1: Fundamentals')

    def test_course_enrollment(self):
        self.client.force_login(self.user)
        enroll_url = reverse('courses:enroll', kwargs={'slug': self.course.slug})

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

    def test_assessment_locked_under_80_percent(self):
        self.client.force_login(self.user)
        Enrollment.objects.create(user=self.user, course=self.course)

        # 0% completion -> assessment should be locked
        intro_url = reverse('courses:assessment_intro', kwargs={'slug': self.course.slug, 'assessment_type': 'final_quiz'})
        response = self.client.get(intro_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_unlocked'])

        # Attempting to take assessment under 80% should redirect to intro
        take_url = reverse('courses:take_assessment', kwargs={'slug': self.course.slug, 'assessment_type': 'final_quiz'})
        response = self.client.get(take_url)
        self.assertEqual(response.status_code, 302)

    def test_assessment_unlocked_at_or_above_80_percent(self):
        self.client.force_login(self.user)
        Enrollment.objects.create(user=self.user, course=self.course)

        # Mark both lessons completed -> 100% progress
        LessonProgress.objects.create(user=self.user, lesson=self.lesson1, is_completed=True)
        LessonProgress.objects.create(user=self.user, lesson=self.lesson2, is_completed=True)

        intro_url = reverse('courses:assessment_intro', kwargs={'slug': self.course.slug, 'assessment_type': 'final_quiz'})
        response = self.client.get(intro_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_unlocked'])

        take_url = reverse('courses:take_assessment', kwargs={'slug': self.course.slug, 'assessment_type': 'final_quiz'})
        response = self.client.get(take_url)
        self.assertEqual(response.status_code, 200)

    def test_assessment_submission_and_scoring(self):
        self.client.force_login(self.user)
        Enrollment.objects.create(user=self.user, course=self.course)
        LessonProgress.objects.create(user=self.user, lesson=self.lesson1, is_completed=True)
        LessonProgress.objects.create(user=self.user, lesson=self.lesson2, is_completed=True)

        submit_url = reverse('courses:submit_assessment', kwargs={'slug': self.course.slug, 'assessment_type': 'final_quiz'})
        response = self.client.post(submit_url, {
            f'question_{self.q1.id}': 'A'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_passed'])
        self.assertEqual(response.context['score'], 1)
        self.assertEqual(response.context['percentage'], 100)
        self.assertTrue(CourseAssessmentAttempt.objects.filter(user=self.user, assessment=self.final_quiz, is_passed=True).exists())
