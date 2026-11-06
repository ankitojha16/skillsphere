from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from courses.models import Course, Category, CourseModule, CourseAssessment, Enrollment, CourseCompletion
from learning.models import Lesson, LessonProgress, Exercise

class CacheConsistencyAndIsolationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name='Computer Science', slug='cs')
        self.course = Course.objects.create(
            title='Python Fundamentals',
            slug='python-fundamentals',
            category=self.category,
            is_published=True
        )
        self.module = CourseModule.objects.create(
            course=self.course,
            title='Module 1',
            order=1
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            module=self.module,
            title='Intro to Python',
            lesson_order=1,
            content='<p>Content</p>'
        )
        self.assessment = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_quiz',
            title='Final Quiz'
        )
        self.exercise = Exercise.objects.create(
            lesson=self.lesson,
            title='Exercise 1',
            instructions='Print Hello'
        )
        self.user = User.objects.create_user(username='student1', password='Password123!')

    def tearDown(self):
        cache.clear()

    def test_course_detail_populates_public_syllabus_cache(self):
        """Verifies course_detail_view caches the course curriculum structure."""
        client = Client()
        cache_key = f'skillsphere_course_syllabus_{self.course.slug}'
        self.assertIsNone(cache.get(cache_key))

        response = client.get(f'/courses/{self.course.slug}/')
        self.assertEqual(response.status_code, 200)

        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['course'].id, self.course.id)
        self.assertEqual(len(cached_data['lessons']), 1)
        self.assertEqual(len(cached_data['modules']), 1)
        self.assertEqual(len(cached_data['assessments']), 1)

    def test_cache_isolation_no_user_progress_or_enrollment_in_public_cache(self):
        """
        Guarantees that public course syllabus and catalogue cache objects do NOT
        store any private enrollment, progress, completion or user data.
        """
        # Enroll user and mark progress
        Enrollment.objects.create(user=self.user, course=self.course)
        LessonProgress.objects.create(user=self.user, lesson=self.lesson, is_completed=True)
        CourseCompletion.objects.create(user=self.user, course=self.course, learning_progress=100, is_completed=True)

        client = Client()
        # Request as authenticated enrolled user
        client.force_login(self.user)
        resp_auth = client.get(f'/courses/{self.course.slug}/')
        self.assertEqual(resp_auth.status_code, 200)

        # Inspect the syllabus cache
        cache_key = f'skillsphere_course_syllabus_{self.course.slug}'
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)

        # The cache structure must ONLY contain course-wide metadata
        self.assertNotIn('is_enrolled', cached_data)
        self.assertNotIn('progress_info', cached_data)
        self.assertNotIn('user', cached_data)
        self.assertNotIn('student1', str(cached_data))

        # Request as anonymous user: must NOT see student1's enrolled state
        client.logout()
        resp_anon = client.get(f'/courses/{self.course.slug}/')
        self.assertContains(resp_anon, 'Log In to Enroll')
        self.assertNotContains(resp_anon, 'Continue Learning')

    def test_course_update_signal_invalidates_syllabus_and_catalogue(self):
        """Saving a course must invalidate syllabus and catalogue base cache."""
        syllabus_key = f'skillsphere_course_syllabus_{self.course.slug}'
        catalogue_key = 'skillsphere_course_catalogue_base'
        cache.set(syllabus_key, {'dummy': 'data'}, 300)
        cache.set(catalogue_key, ['dummy'], 300)

        self.course.title = 'Updated Python Title'
        self.course.save()

        self.assertIsNone(cache.get(syllabus_key))
        self.assertIsNone(cache.get(catalogue_key))

    def test_module_update_signal_invalidates_syllabus_and_catalogue(self):
        """Updating a module must invalidate the course syllabus and catalogue cache."""
        syllabus_key = f'skillsphere_course_syllabus_{self.course.slug}'
        catalogue_key = 'skillsphere_course_catalogue_base'
        cache.set(syllabus_key, {'dummy': 'data'}, 300)
        cache.set(catalogue_key, ['dummy'], 300)

        self.module.title = 'Advanced Concepts'
        self.module.save()

        self.assertIsNone(cache.get(syllabus_key))
        self.assertIsNone(cache.get(catalogue_key))

    def test_lesson_update_signal_invalidates_syllabus_and_notes_pdf(self):
        """Updating a lesson must invalidate syllabus, catalogue base, and its notes PDF cache."""
        syllabus_key = f'skillsphere_course_syllabus_{self.course.slug}'
        pdf_key = f'lesson_notes_pdf_{self.lesson.id}'
        catalogue_key = 'skillsphere_course_catalogue_base'
        cache.set(syllabus_key, {'dummy': 'data'}, 300)
        cache.set(pdf_key, b'%PDF-dummy', 300)
        cache.set(catalogue_key, ['dummy'], 300)

        self.lesson.title = 'Updated Lesson Title'
        self.lesson.save()

        self.assertIsNone(cache.get(syllabus_key))
        self.assertIsNone(cache.get(pdf_key))
        self.assertIsNone(cache.get(catalogue_key))

    def test_assessment_update_signal_invalidates_syllabus(self):
        """Updating an assessment must invalidate the course syllabus cache."""
        syllabus_key = f'skillsphere_course_syllabus_{self.course.slug}'
        cache.set(syllabus_key, {'dummy': 'data'}, 300)

        self.assessment.title = 'Updated Final Quiz'
        self.assessment.save()

        self.assertIsNone(cache.get(syllabus_key))

    def test_exercise_update_signal_invalidates_syllabus(self):
        """Updating an exercise must invalidate the course syllabus cache."""
        syllabus_key = f'skillsphere_course_syllabus_{self.course.slug}'
        cache.set(syllabus_key, {'dummy': 'data'}, 300)

        self.exercise.title = 'Updated Exercise'
        self.exercise.save()

        self.assertIsNone(cache.get(syllabus_key))

    def test_category_update_signal_invalidates_categories_cache(self):
        """Updating a category must clear published categories cache."""
        cat_key = 'skillsphere_published_categories'
        cache.set(cat_key, ['dummy'], 300)

        self.category.name = 'Data Engineering'
        self.category.save()

        self.assertIsNone(cache.get(cat_key))
