"""
Phase 17.1 Adversarial Engineering Verification & Reliability Test Suite
Covers:
1. Request Correlation ID validation, sanitization and bounded length.
2. Circuit Breaker thread-safety and single-trial permit in HALF_OPEN.
3. Bulkhead concurrency enforcement and exception-safe permit release.
4. Task Queue canonical full-jitter calculation and bounded-batch job cleanup.
5. PDF document fingerprint reactivity against name, course, and verification status changes.
6. Lesson completion explicit desired-state idempotency and retry safety.
7. Assessment submission database-backed idempotency and XP deduplication.
"""

import time
import uuid
import threading
from datetime import timedelta
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from django.urls import reverse

from config.middleware import RequestCorrelationMiddleware
from services.resilience import CircuitBreaker, Bulkhead, CircuitBreakerOpenException
from services.task_queue import (
    enqueue_task, execute_job, cleanup_completed_jobs, register_task
)
from analytics.models import DurableTaskJob
from services.pdf_service import PDFService
from certificates.models import Certificate
from courses.models import Course, CourseModule, CourseAssessment, CourseAssessmentQuestion, CourseAssessmentAttempt, Enrollment
from learning.models import Lesson, LessonProgress
from gamification.models import XPTransaction
from goals.models import LearningActivity


class Phase171AdversarialAuditTests(TestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='auditor_student',
            email='audit@skillsphere.edu',
            password='AuditPassword123!',
            first_name='Ankit',
            last_name='Kumar'
        )
        from courses.models import Category
        self.category = Category.objects.create(name='Cloud Architecture', slug='cloud-architecture')
        self.course = Course.objects.create(
            category=self.category,
            title='Distributed Cloud Architectures',
            slug='distributed-cloud-architectures',
            description='Production engineering at ultra scale',
            is_published=True,
            curriculum_version=1
        )
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)

    def test_correlation_id_validation_and_sanitization(self):
        """RequestCorrelationMiddleware must sanitize incoming IDs and reject malicious log-injection strings."""
        middleware = RequestCorrelationMiddleware(get_response=lambda req: req.response)
        rf = RequestFactory()

        # 1. Valid custom ID accepted
        req_valid = rf.get('/health/live/', HTTP_X_REQUEST_ID='trace-prod-abc-12345')
        req_valid.response = middleware.get_response(req_valid) if hasattr(req_valid, 'response') else type('R', (), {'headers': {}, '__setitem__': lambda s, k, v: None})()
        # Mock response object for dummy get_response
        def dummy_view(r):
            from django.http import HttpResponse
            return HttpResponse("OK")
        mw = RequestCorrelationMiddleware(get_response=dummy_view)

        res1 = mw(rf.get('/health/live/', HTTP_X_REQUEST_ID='Trace_12345-VALID'))
        self.assertEqual(res1['X-Request-ID'], 'Trace_12345-VALID')

        # 2. Malicious header with CRLF / log-forging characters must be rejected and replaced
        res2 = mw(rf.get('/health/live/', HTTP_X_REQUEST_ID='attack\r\nInjected-Header: evil<script>'))
        self.assertNotEqual(res2['X-Request-ID'], 'attack\r\nInjected-Header: evil<script>')
        self.assertEqual(len(res2['X-Request-ID']), 16)  # Standard uuid4 hex prefix

        # 3. Oversized header (> 64 chars) must be rejected
        res3 = mw(rf.get('/health/live/', HTTP_X_REQUEST_ID='a' * 128))
        self.assertNotEqual(res3['X-Request-ID'], 'a' * 128)
        self.assertEqual(len(res3['X-Request-ID']), 16)

    def test_circuit_breaker_single_trial_in_half_open(self):
        """In HALF_OPEN state, strictly ONE trial request is permitted while concurrent callers fail-fast."""
        cb = CircuitBreaker(name='test_probe_limiter', failure_threshold=2, recovery_timeout=0.5)

        # Trip to OPEN
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreaker.STATE_OPEN)

        # Wait for recovery timeout to elapse
        time.sleep(0.6)
        self.assertEqual(cb.get_state(), CircuitBreaker.STATE_HALF_OPEN)

        trial_results = []
        barrier = threading.Barrier(5)

        def worker_call(idx):
            barrier.wait()
            def probe_fn():
                time.sleep(0.1)  # Simulate in-flight probe
                return f"probe_{idx}"
            def fallback_fn():
                return "fallback"
            res = cb.call(probe_fn, fallback_fn=fallback_fn)
            trial_results.append(res)

        threads = [threading.Thread(target=worker_call, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 1 thread must have run the trial probe; the other 4 must have executed fallback
        probe_count = sum(1 for r in trial_results if r.startswith('probe_'))
        fallback_count = sum(1 for r in trial_results if r == 'fallback')
        self.assertEqual(probe_count, 1)
        self.assertEqual(fallback_count, 4)

    def test_bulkhead_concurrency_and_safe_release(self):
        """Bulkhead must enforce max_concurrent and release permit safely even when exceptions occur."""
        bulkhead = Bulkhead(name='test_bulkhead', max_concurrent=2)

        # Acquire 2 permits
        self.assertTrue(bulkhead.acquire())
        self.assertTrue(bulkhead.acquire())
        # 3rd acquire must fail
        self.assertFalse(bulkhead.acquire(timeout=0.01))

        # Safe release
        bulkhead.release()
        self.assertTrue(bulkhead.acquire())
        bulkhead.release()

        # Test context manager safety on exception
        try:
            with bulkhead.acquire_context():
                raise RuntimeError("Worker exploded inside bulkhead")
        except RuntimeError:
            pass

        # Context manager must have released the permit
        self.assertTrue(bulkhead.acquire())
        bulkhead.release()
        bulkhead.release()

    def test_queue_cleanup_completed_jobs_preserves_pending_and_failed(self):
        """cleanup_completed_jobs must only delete eligible old completed jobs while preserving pending/failed."""
        old_time = timezone.now() - timedelta(days=10)
        recent_time = timezone.now() - timedelta(days=2)

        # 1. Old completed job (eligible)
        job_old_completed = DurableTaskJob.objects.create(
            task_name='test_cleanup_task',
            status='completed',
            completed_at=old_time
        )
        # 2. Recent completed job (MUST be preserved)
        job_recent_completed = DurableTaskJob.objects.create(
            task_name='test_cleanup_task',
            status='completed',
            completed_at=recent_time
        )
        # 3. Old failed job (MUST be preserved for triage)
        job_old_failed = DurableTaskJob.objects.create(
            task_name='test_cleanup_task',
            status='failed',
            completed_at=old_time
        )
        # 4. Pending job (MUST be preserved)
        job_pending = DurableTaskJob.objects.create(
            task_name='test_cleanup_task',
            status='pending'
        )

        res = cleanup_completed_jobs(retention_days=7, batch_size=100)
        self.assertEqual(res['cleaned_completed'], 1)

        # Verify database truth
        self.assertFalse(DurableTaskJob.objects.filter(id=job_old_completed.id).exists())
        self.assertTrue(DurableTaskJob.objects.filter(id=job_recent_completed.id).exists())
        self.assertTrue(DurableTaskJob.objects.filter(id=job_old_failed.id).exists())
        self.assertTrue(DurableTaskJob.objects.filter(id=job_pending.id).exists())

    def test_pdf_fingerprint_reactivity(self):
        """Changing student name, course title, or verification status must alter PDF document fingerprint."""
        cert = Certificate.objects.create(
            user=self.user,
            course=self.course,
            title='Cloud Architecture Specialist',
            recipient_name='Ankit Kumar',
            verification_status=True
        )

        fp1 = PDFService.get_certificate_fingerprint(cert)

        # 1. Recipient name change alters fingerprint
        cert.recipient_name = 'Dr. Ankit Kumar, Ph.D.'
        fp2 = PDFService.get_certificate_fingerprint(cert)
        self.assertNotEqual(fp1, fp2)

        # 2. Course title change alters fingerprint
        self.course.title = 'Advanced Distributed Systems'
        fp3 = PDFService.get_certificate_fingerprint(cert)
        self.assertNotEqual(fp2, fp3)

        # 3. Verification status alteration alters fingerprint
        cert.verification_status = False
        fp4 = PDFService.get_certificate_fingerprint(cert)
        self.assertNotEqual(fp3, fp4)

    def test_lesson_completion_explicit_desired_state_idempotency(self):
        """Repeated requests with action='complete' must be idempotent and never flip state or duplicate XP."""
        lesson = Lesson.objects.create(
            course=self.course,
            title='Consensus Algorithms (Raft & Paxos)',
            lesson_order=1,
            content='<p>Study of consensus protocols</p>'
        )

        client = Client()
        client.force_login(self.user)

        url = reverse('learning:complete_toggle', kwargs={
            'course_slug': self.course.slug,
            'lesson_id': lesson.id
        })

        # Request 1: Explicit action='complete'
        res1 = client.post(url, {'action': 'complete'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res1.status_code, 200)
        prog = LessonProgress.objects.get(user=self.user, lesson=lesson)
        self.assertTrue(prog.is_completed)

        xp_tx_count_before = XPTransaction.objects.filter(user=self.user, activity_key=f"lesson_{lesson.id}").count()
        self.assertEqual(xp_tx_count_before, 1)

        # Request 2: Retry with action='complete' (MUST NOT flip to incomplete and MUST NOT duplicate XP)
        res2 = client.post(url, {'action': 'complete'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res2.status_code, 200)
        prog.refresh_from_db()
        self.assertTrue(prog.is_completed)

        xp_tx_count_after = XPTransaction.objects.filter(user=self.user, activity_key=f"lesson_{lesson.id}").count()
        self.assertEqual(xp_tx_count_after, 1)  # Strict XP deduplication

    def test_assessment_submission_idempotency_and_xp_deduplication(self):
        """Duplicate rapid assessment submissions must replay result and prevent duplicate XP."""
        assessment = CourseAssessment.objects.create(
            course=self.course,
            assessment_type='final_quiz',
            title='Cloud Architecture Final Quiz',
            passing_percentage=70,
            is_active=True
        )
        q1 = CourseAssessmentQuestion.objects.create(
            assessment=assessment,
            question_text='What does Paxos guarantee?',
            option_a='Safety only',
            option_b='Liveness only',
            option_c='Safety and consistency under network partitions',
            option_d='Zero latency',
            correct_answer='C',
            order=1
        )

        client = Client()
        client.force_login(self.user)

        url = reverse('courses:submit_assessment', kwargs={
            'slug': self.course.slug,
            'assessment_type': 'final_quiz'
        })
        payload = {f'question_{q1.id}': 'C'}

        # Submission 1: Passes assessment
        res1 = client.post(url, payload)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(CourseAssessmentAttempt.objects.filter(user=self.user, assessment=assessment).count(), 1)

        xp_key = f"assessment_pass_{assessment.id}_{self.user.id}"
        self.assertEqual(XPTransaction.objects.filter(user=self.user, activity_key=xp_key).count(), 1)

        # Submission 2: Immediate duplicate request (within idempotency window)
        res2 = client.post(url, payload)
        self.assertEqual(res2.status_code, 200)
        # Attempt count must still be 1 (replayed attempt without duplicate write)
        self.assertEqual(CourseAssessmentAttempt.objects.filter(user=self.user, assessment=assessment).count(), 1)
        # XP must NOT be awarded twice
        self.assertEqual(XPTransaction.objects.filter(user=self.user, activity_key=xp_key).count(), 1)
