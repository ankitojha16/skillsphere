from django.test import TransactionTestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
from courses.models import Course, Category, CourseModule, CourseAssessment
from learning.models import Lesson, Exercise
from certificates.models import Certificate
from config.cache import FaultTolerantRedisCache

class ProductionReliabilityAndSecurityTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name='Reliability Category', slug='rel-cat')
        self.course = Course.objects.create(
            title='Reliability Course',
            slug='rel-course',
            category=self.category,
            is_published=True
        )
        self.module = CourseModule.objects.create(course=self.course, title='Module 1', order=1)
        self.lesson = Lesson.objects.create(
            course=self.course,
            module=self.module,
            title='Lesson 1',
            lesson_order=1,
            content='<p>Reliability content</p>'
        )
        self.assessment = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_quiz',
            title='Quiz 1'
        )
        self.exercise = Exercise.objects.create(
            lesson=self.lesson,
            title='Exercise 1',
            instructions='Solve this'
        )
        self.student_a = User.objects.create_user(username='student_alpha', password='Password123!')
        self.student_b = User.objects.create_user(username='student_beta', password='Password123!')

        self.cert_a = Certificate.objects.create(
            user=self.student_a,
            course=self.course,
            title=f"Certified in {self.course.title}",
            certificate_id="SS-CERT-TEST-ALPHA123",
            verification_status=True
        )

    def tearDown(self):
        cache.clear()

    def test_transaction_on_commit_invalidation_rollback(self):
        """Verifies that cache keys are NOT deleted if a transaction rolls back."""
        syllabus_key = f'skillsphere_course_syllabus_{self.course.slug}'
        cache.set(syllabus_key, {'status': 'cached_before_tx'}, 300)

        try:
            with transaction.atomic():
                self.course.title = 'Rollback Title'
                self.course.save()
                raise ValueError("Simulated transaction failure")
        except ValueError:
            pass

        # Because transaction rolled back, on_commit did NOT fire; cache remains valid
        self.assertIsNotNone(cache.get(syllabus_key))

    def test_transaction_on_commit_invalidation_commit(self):
        """Verifies that cache keys ARE deleted once the transaction successfully commits."""
        syllabus_key = f'skillsphere_course_syllabus_{self.course.slug}'
        cache.set(syllabus_key, {'status': 'cached_before_tx'}, 300)

        with transaction.atomic():
            self.course.title = 'Committed Title'
            self.course.save()

        # On commit, cache invalidation executed
        self.assertIsNone(cache.get(syllabus_key))

    def test_course_slug_change_invalidates_both_old_and_new_keys(self):
        """Changing a course's slug must invalidate both the old slug and the new slug keys."""
        old_slug = self.course.slug
        new_slug = 'rel-course-renamed'

        old_key = f'skillsphere_course_syllabus_{old_slug}'
        new_key = f'skillsphere_course_syllabus_{new_slug}'

        cache.set(old_key, {'version': 'old_data'}, 300)
        cache.set(new_key, {'version': 'stale_pre_existing'}, 300)

        self.course.slug = new_slug
        self.course.save()

        self.assertIsNone(cache.get(old_key), "Old slug cache key must be invalidated")
        self.assertIsNone(cache.get(new_key), "New slug cache key must be invalidated")

    def test_cascading_deletion_cache_invalidation(self):
        """Deleting a course cascade-deletes modules, lessons, and assessments without crashing."""
        syllabus_key = f'skillsphere_course_syllabus_{self.course.slug}'
        catalogue_key = 'skillsphere_course_catalogue_base'
        pdf_key = f'lesson_notes_pdf_{self.lesson.id}'

        cache.set(syllabus_key, {'data': 1}, 300)
        cache.set(catalogue_key, ['data'], 300)
        cache.set(pdf_key, b'%PDF-test', 300)

        self.course.delete()

        self.assertIsNone(cache.get(syllabus_key))
        self.assertIsNone(cache.get(catalogue_key))

    def test_authenticated_cache_control_headers(self):
        """Authenticated responses must contain 'private, no-cache, no-store'."""
        client = Client()
        client.force_login(self.student_a)

        resp = client.get('/dashboard/')
        self.assertEqual(resp.status_code, 200)
        cc = resp.headers.get('Cache-Control', '')
        self.assertIn('private', cc)
        self.assertIn('no-store', cc)
        self.assertIn('no-cache', cc)
        self.assertEqual(resp.headers.get('Pragma'), 'no-cache')

    def test_anonymous_cache_control_headers(self):
        """Anonymous course catalogue responses must permit public caching with revalidation."""
        client = Client()
        resp = client.get('/courses/')
        self.assertEqual(resp.status_code, 200)
        cc = resp.headers.get('Cache-Control', '')
        self.assertIn('public', cc)
        self.assertIn('must-revalidate', cc)
        self.assertNotIn('no-store', cc)

    def test_certificate_ownership_isolation(self):
        """Student B must NOT be able to view or download Student A's certificate (returns 404)."""
        client = Client()
        client.force_login(self.student_b)

        # Attempt to download student_a's certificate
        resp_download = client.get(f'/certificates/{self.cert_a.pk}/pdf/')
        self.assertEqual(resp_download.status_code, 404)

        # Attempt to preview student_a's certificate
        resp_preview = client.get(f'/certificates/{self.cert_a.pk}/preview/')
        self.assertEqual(resp_preview.status_code, 404)

    def test_revoked_certificate_denies_download_and_invalidates_cache(self):
        """A revoked certificate must deny download (404) and purge cached PDF bytes."""
        cert_pdf_key = f"cert_pdf_{self.cert_a.certificate_id}"
        cache.set(cert_pdf_key, b'%PDF-cached-bytes', 300)

        client = Client()
        client.force_login(self.student_a)

        # Before revocation: can download
        resp_valid = client.get(f'/certificates/{self.cert_a.pk}/pdf/')
        self.assertEqual(resp_valid.status_code, 200)

        # Revoke certificate
        self.cert_a.verification_status = False
        self.cert_a.save()

        # Signal must have cleared the PDF cache
        self.assertIsNone(cache.get(cert_pdf_key))

        # Subsequent download must return 404
        resp_revoked = client.get(f'/certificates/{self.cert_a.pk}/pdf/')
        self.assertEqual(resp_revoked.status_code, 404)

    def test_fault_tolerant_redis_cache_fallback(self):
        """
        Tests FaultTolerantRedisCache with a non-existent host:
        Must silently fail over to internal LocMemCache without raising ConnectionError.
        """
        # Point to an invalid dummy Redis port
        dummy_cache = FaultTolerantRedisCache(
            'redis://127.0.0.1:65534',
            {'TIMEOUT': 60, 'KEY_PREFIX': 'test_fallback'}
        )

        # Set and get must succeed via internal fallback
        dummy_cache.set('test_key', 'fallback_value', 60)
        val = dummy_cache.get('test_key')
        self.assertEqual(val, 'fallback_value')

        dummy_cache.delete('test_key')
        self.assertIsNone(dummy_cache.get('test_key'))

    def test_multi_instance_consistency_simulation(self):
        """
        Simulates two application instances (Instance A and Instance B).
        Demonstrates that with shared cache, Instance B's update is immediately visible.
        """
        # Instance A populates syllabus cache
        syllabus_key = f'skillsphere_course_syllabus_{self.course.slug}'
        cache.set(syllabus_key, {'title': 'Initial Syllabus Data'}, 300)

        # Instance B updates course module
        self.module.title = 'Updated by Instance B'
        self.module.save()

        # Instance A reads cache: must be invalidated (None) so fresh data is fetched
        self.assertIsNone(cache.get(syllabus_key))
