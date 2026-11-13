from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from courses.models import (
    Category, Course, Enrollment, CourseModule,
    CourseAssessment, CourseAssessmentQuestion, CourseAssessmentAttempt
)
from learning.models import Lesson, LessonProgress

class CoursesTests(TestCase):
    def setUp(self):
        cache.clear()
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

    def test_assessment_access_requires_enrollment(self):
        self.client.force_login(self.user)
        # 1. Unenrolled -> taking assessment should redirect to course detail
        take_url = reverse('courses:take_assessment', kwargs={'slug': self.course.slug, 'assessment_type': 'final_quiz'})
        response = self.client.get(take_url)
        self.assertEqual(response.status_code, 302)

        # 2. Enrolled -> taking assessment is available anytime
        Enrollment.objects.create(user=self.user, course=self.course)
        intro_url = reverse('courses:assessment_intro', kwargs={'slug': self.course.slug, 'assessment_type': 'final_quiz'})
        response = self.client.get(intro_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_unlocked'])

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

    def test_enrollment_labels_four_states(self):
        # 1. Logged-out visitor
        res_list = self.client.get(reverse('courses:list'))
        self.assertContains(res_list, 'Log In to Enroll')

        res_detail = self.client.get(reverse('courses:detail', kwargs={'slug': self.course.slug}))
        self.assertContains(res_detail, 'Log In to Enroll')

        # 2. Logged-in non-enrolled user
        self.client.force_login(self.user)
        res_list = self.client.get(reverse('courses:list'))
        self.assertContains(res_list, 'Enroll')
        self.assertNotContains(res_list, 'Log In to Enroll')
        self.assertNotContains(res_list, 'Continue Learning')
        self.assertNotContains(res_list, 'Review Course')

        res_detail = self.client.get(reverse('courses:detail', kwargs={'slug': self.course.slug}))
        self.assertContains(res_detail, 'Enroll')
        self.assertNotContains(res_detail, 'Log In to Enroll')
        self.assertNotContains(res_detail, 'Continue Learning')
        self.assertNotContains(res_detail, 'Review Course')

        # 3. Logged-in enrolled in-progress user
        enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        LessonProgress.objects.create(user=self.user, lesson=self.lesson1, is_completed=True) # 50%
        res_list = self.client.get(reverse('courses:list'))
        self.assertContains(res_list, 'Continue Learning')
        self.assertNotContains(res_list, 'Review Course')

        res_detail = self.client.get(reverse('courses:detail', kwargs={'slug': self.course.slug}))
        self.assertContains(res_detail, 'Continue Learning')
        self.assertNotContains(res_detail, 'Review Course')

        # 4. Logged-in enrolled 100% completed user
        LessonProgress.objects.create(user=self.user, lesson=self.lesson2, is_completed=True) # 100%
        res_list = self.client.get(reverse('courses:list'))
        self.assertContains(res_list, 'Review Course')

        res_detail = self.client.get(reverse('courses:detail', kwargs={'slug': self.course.slug}))
        self.assertContains(res_detail, 'Review Course')

    def test_submit_assessment_unauthorized_and_enrolled(self):
        # 1. Direct POST when unenrolled -> redirects, attempt not created
        self.client.force_login(self.user)
        submit_url = reverse('courses:submit_assessment', kwargs={'slug': self.course.slug, 'assessment_type': 'final_quiz'})
        resp_unenrolled = self.client.post(submit_url, {f'question_{self.q1.id}': 'A'})
        self.assertEqual(resp_unenrolled.status_code, 302)
        self.assertFalse(CourseAssessmentAttempt.objects.filter(user=self.user, assessment=self.final_quiz).exists())

        # 2. Direct POST when enrolled -> allowed anytime
        Enrollment.objects.create(user=self.user, course=self.course)
        resp_enrolled = self.client.post(submit_url, {f'question_{self.q1.id}': 'A'})
        self.assertEqual(resp_enrolled.status_code, 200)
        self.assertTrue(CourseAssessmentAttempt.objects.filter(user=self.user, assessment=self.final_quiz).exists())

    def test_course_bookmarking(self):
        from courses.models import CourseBookmark
        self.client.force_login(self.user)
        bookmark_url = reverse('courses:toggle_bookmark', kwargs={'slug': self.course.slug})

        # AJAX toggle ON
        res = self.client.post(bookmark_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_bookmarked'])
        self.assertTrue(CourseBookmark.objects.filter(user=self.user, course=self.course).exists())

        # AJAX toggle OFF
        res = self.client.post(bookmark_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_bookmarked'])
        self.assertFalse(CourseBookmark.objects.filter(user=self.user, course=self.course).exists())

    def test_course_reviews_and_eligibility(self):
        from courses.models import CourseReview
        self.client.force_login(self.user)
        review_url = reverse('courses:submit_review', kwargs={'slug': self.course.slug})

        # 1. Unenrolled user cannot review
        res = self.client.post(review_url, {'rating': 5, 'comment': 'Great course!'})
        self.assertEqual(res.status_code, 302)
        self.assertFalse(CourseReview.objects.filter(user=self.user, course=self.course).exists())

        # 2. Enrolled with 0 completed lessons cannot review
        Enrollment.objects.create(user=self.user, course=self.course)
        res = self.client.post(review_url, {'rating': 5, 'comment': 'Great course!'})
        self.assertEqual(res.status_code, 302)
        self.assertFalse(CourseReview.objects.filter(user=self.user, course=self.course).exists())

        # 3. Enrolled with >= 1 lesson completed CAN review
        LessonProgress.objects.create(user=self.user, lesson=self.lesson1, is_completed=True)
        res = self.client.post(review_url, {'rating': 5, 'comment': 'Excellent explanation of fundamentals.'})
        self.assertEqual(res.status_code, 302)
        self.assertTrue(CourseReview.objects.filter(user=self.user, course=self.course).exists())
        review = CourseReview.objects.get(user=self.user, course=self.course)
        self.assertEqual(review.rating, 5)

        # 4. Rating summary verification
        avg_r, count = self.course.get_rating_summary()
        self.assertEqual(avg_r, 5.0)
        self.assertEqual(count, 1)

        # 5. Update review
        res = self.client.post(review_url, {'rating': 4, 'comment': 'Updated review comment.'})
        review.refresh_from_db()
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Updated review comment.')

        # 6. Delete review
        delete_url = reverse('courses:delete_review', kwargs={'slug': self.course.slug})
        res = self.client.post(delete_url)
        self.assertEqual(res.status_code, 302)
        self.assertFalse(CourseReview.objects.filter(user=self.user, course=self.course).exists())
        avg_r, count = self.course.get_rating_summary()
        self.assertIsNone(avg_r)
        self.assertEqual(count, 0)

    def test_my_learning_saved_tab(self):
        from courses.models import CourseBookmark
        from learning.models import LessonBookmark
        self.client.force_login(self.user)

        CourseBookmark.objects.create(user=self.user, course=self.course)
        LessonBookmark.objects.create(user=self.user, lesson=self.lesson1)

        saved_url = reverse('courses:my_learning') + '?tab=saved'
        res = self.client.get(saved_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.course.title)
        self.assertContains(res, self.lesson1.title)
        self.assertEqual(res.context['total_saved'], 2)

    def test_course_list_degree_filter(self):
        bba_cat = Category.objects.create(name='Management & Business Leadership', slug='management-business')
        bba_course = Course.objects.create(
            title='Strategic Management & Leadership',
            slug='strategic-management-mba-bba',
            category=bba_cat,
            difficulty='Intermediate',
            instructor_name='Prof. Smith',
            description='Target Degree: BBA / MBA. Executive leadership and corporate strategy',
            is_published=True
        )

        res = self.client.get(reverse('courses:list') + '?degree=BBA')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Strategic Management &amp; Leadership')
        self.assertEqual(res.context['selected_degree'], 'BBA')

    def test_no_degree_acronyms_in_course_names(self):
        """Ensure no course names contain (BTech), (MTech), (BCA), or (BBA) tags."""
        import re
        degree_pattern = re.compile(r'\((?:btech|mtech|bca|bba|mba|bsc|bcom|ba)[^)]*\)', re.IGNORECASE)
        for course in Course.objects.all():
            self.assertFalse(
                degree_pattern.search(course.title),
                f"Course title '{course.title}' contains degree acronym tag in name."
            )

    def test_course_search_autocomplete_api(self):
        url = reverse('courses:search_autocomplete')
        # Short query returns empty
        res = self.client.get(url + '?q=a')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['results'], [])

        # Valid query matching self.course ('Python & Django Core')
        res = self.client.get(url + '?q=Python')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('results', data)
        self.assertTrue(len(data['results']) >= 1)
        first = data['results'][0]
        self.assertIn('title', first)
        self.assertIn('slug', first)
        self.assertIn('url', first)
        self.assertIn('thumbnail', first)

    def test_seed_curated_videos_command(self):
        from django.core.management import call_command
        import io

        # 1. Test dry-run
        out = io.StringIO()
        call_command('seed_curated_videos', '--dry-run', stdout=out)
        output = out.getvalue()
        self.assertIn('DRY RUN COMPLETE', output)

        # 2. Test live sync on targeted course
        test_c = Course.objects.create(
            title='Test MBA Strategy',
            slug='strategic-management-mba',
            category=self.category,
            difficulty='Intermediate'
        )
        test_lesson = Lesson.objects.create(
            course=test_c,
            title='Intro Strategy',
            lesson_order=1,
            video_url='https://www.youtube.com/embed/sPh6S4wIqC4?enablejsapi=1&rel=0'
        )
        out_live = io.StringIO()
        call_command('seed_curated_videos', stdout=out_live)
        test_lesson.refresh_from_db()
        # Verify video_url was updated away from duplicate PM video
        self.assertNotEqual(test_lesson.video_url, 'https://www.youtube.com/embed/sPh6S4wIqC4?enablejsapi=1&rel=0')
        self.assertIn('bNYz4U3eI3U', test_lesson.video_url)

    def test_course_catalogue_pagination(self):
        # Create 20 dummy published courses to test pagination (threshold is 16)
        for i in range(20):
            Course.objects.create(
                title=f'Pagination Test Course {i}',
                slug=f'pagination-test-course-{i}',
                category=self.category,
                difficulty='Beginner',
                is_published=True
            )

        # 1. Page 1
        res = self.client.get(reverse('courses:list'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['courses_data']), 16)
        self.assertTrue(res.context['page_obj'].has_next())
        self.assertFalse(res.context['page_obj'].has_previous())
        self.assertContains(res, 'Course Library Navigation')

        # 2. Page 2 with filter preservation
        res2 = self.client.get(reverse('courses:list') + '?page=2&difficulty=Beginner')
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.context['page_obj'].has_previous())
        self.assertIn('difficulty=Beginner', res2.context['pagination_querystring'])






