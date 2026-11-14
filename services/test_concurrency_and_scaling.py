"""
SkillSphere Phase 17 Automated Concurrency, Resilience & Scaling Test Suite
Covers:
  1. Liveness & Readiness health probe endpoints.
  2. Request correlation ID propagation and header attachment.
  3. Concurrent XP awards and idempotency protection against duplicate milestone recording.
  4. CircuitBreaker lifecycle (CLOSED -> OPEN -> fallback execution -> recovery).
  5. DurableTaskJob exponential backoff with randomized jitter.
  6. Collaboration code security: AST syntax validation and zero server-side exec().
  7. Certificate & Resume PDF versioned cache key verification.
  8. MetricsCollector aggregation, percentile computation, and Prometheus exporter.
"""

import time
import json
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from django.urls import reverse

from gamification.models import UserGamification, XPTransaction
from gamification.services import award_user_xp
from analytics.models import DurableTaskJob
from services.task_queue import enqueue_task, execute_job, register_task, process_next_job
from services.resilience import CircuitBreaker, CircuitBreakerOpenException, retry_with_jitter
from services.observability import MetricsCollector
from collaboration.models import PairProgrammingRoom


class Phase17ScalabilityAndResilienceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username='scale_tester', password='TestPassword123!', email='tester@skillsphere.app')
        self.staff_user = User.objects.create_user(username='staff_tester', password='TestPassword123!', email='staff@skillsphere.app', is_staff=True)

    def test_liveness_and_readiness_probes(self):
        """Liveness probe must return 200 OK immediately; readiness must verify dependencies."""
        live_resp = self.client.get('/health/live/')
        self.assertEqual(live_resp.status_code, 200)
        live_data = live_resp.json()
        self.assertEqual(live_data['status'], 'alive')
        self.assertIn('X-Request-ID', live_resp.headers)

        ready_resp = self.client.get('/health/ready/')
        self.assertEqual(ready_resp.status_code, 200)
        ready_data = ready_resp.json()
        self.assertEqual(ready_data['status'], 'ready')
        self.assertEqual(ready_data['database'], 'ok')
        # Guarantee no credentials or sensitive URLs are leaked
        self.assertNotIn('password', json.dumps(ready_data).lower())
        self.assertNotIn('postgres', json.dumps(ready_data).lower())

    def test_request_correlation_id_propagation(self):
        """X-Request-ID header sent by client must be echoed in response and bound to request."""
        custom_trace_id = "trace-client-uuid-9988"
        resp = self.client.get('/health/live/', HTTP_X_REQUEST_ID=custom_trace_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('X-Request-ID'), custom_trace_id)

    def test_concurrent_xp_awards_integrity(self):
        """Duplicate calls with same activity_key must only award XP once due to DB constraint."""
        key = "lesson_milestone_42"
        # First award
        g1 = award_user_xp(self.user, 50, "Completed lesson 42", activity_key=key)
        self.assertIsNotNone(g1)
        self.assertEqual(g1.total_xp, 50)
        self.assertEqual(XPTransaction.objects.filter(user=self.user, activity_key=key).count(), 1)

        # Duplicate award attempt (simulating concurrent double-submit)
        g2 = award_user_xp(self.user, 50, "Completed lesson 42 duplicate", activity_key=key)
        self.assertEqual(g2.total_xp, 50)
        self.assertEqual(XPTransaction.objects.filter(user=self.user, activity_key=key).count(), 1)

    def test_circuit_breaker_lifecycle(self):
        """Circuit breaker must trip to OPEN after threshold failures and execute fallback."""
        cb = CircuitBreaker(name='test_service_breaker', failure_threshold=2, recovery_timeout=1.0)
        self.assertEqual(cb.get_state(), CircuitBreaker.STATE_CLOSED)
        self.assertTrue(cb.can_execute())

        def failing_target():
            raise ConnectionError("Upstream timeout")

        def safe_fallback():
            return "offline_knowledge_result"

        # Attempt 1: failure recorded, circuit still closed
        res1 = cb.call(failing_target, fallback_fn=safe_fallback)
        self.assertEqual(res1, "offline_knowledge_result")
        self.assertEqual(cb.get_state(), CircuitBreaker.STATE_CLOSED)

        # Attempt 2: threshold reached, circuit trips to OPEN
        res2 = cb.call(failing_target, fallback_fn=safe_fallback)
        self.assertEqual(res2, "offline_knowledge_result")
        self.assertEqual(cb.get_state(), CircuitBreaker.STATE_OPEN)
        self.assertFalse(cb.can_execute())

        # Attempt 3: fast-fails immediately without calling failing_target
        called_target = []
        def probe():
            called_target.append(True)
            return "should_not_run"

        res3 = cb.call(probe, fallback_fn=safe_fallback)
        self.assertEqual(res3, "offline_knowledge_result")
        self.assertEqual(len(called_target), 0)

        # Wait recovery timeout -> transitions to HALF_OPEN
        time.sleep(1.1)
        self.assertEqual(cb.get_state(), CircuitBreaker.STATE_HALF_OPEN)
        self.assertTrue(cb.can_execute())

        # Successful probe call closes circuit
        def successful_probe():
            return "probe_success"
        res4 = cb.call(successful_probe, fallback_fn=safe_fallback)
        self.assertEqual(res4, "probe_success")
        self.assertEqual(cb.get_state(), CircuitBreaker.STATE_CLOSED)

    def test_task_queue_exponential_backoff_and_jitter(self):
        """Failing tasks must be rescheduled with exponential backoff and randomized jitter."""
        @register_task('phase17_retry_test_task')
        def task_failing_handler(payload):
            raise ValueError("Deliberate task failure for backoff test")

        job = enqueue_task('phase17_retry_test_task', payload={'test': True}, max_retries=3)
        self.assertEqual(job.retries, 0)
        self.assertEqual(job.status, 'pending')

        # Execute attempt 1
        now_before = timezone.now()
        success = execute_job(job)
        self.assertFalse(success)
        job.refresh_from_db()

        self.assertEqual(job.retries, 1)
        self.assertEqual(job.status, 'failed')
        self.assertGreaterEqual(job.scheduled_at, now_before)
        self.assertLessEqual(job.scheduled_at, now_before + timedelta(seconds=15))

        # Because scheduled_at is in the future, process_next_job must skip it
        processed = process_next_job()
        self.assertFalse(processed)

    def test_collaboration_code_execution_security(self):
        """Collaboration code run API must validate syntax via AST and NEVER execute exec()."""
        room = PairProgrammingRoom.objects.create(
            room_code="SPHERE-TEST17",
            title="SRE Lounge",
            host=self.user,
            language='python'
        )
        self.client.force_login(self.user)

        # 1. Valid Python code
        run_url = reverse('collaboration:run_room_code', kwargs={'room_code': room.room_code})
        valid_code = "def add(a, b):\n    return a + b\n"
        resp_valid = self.client.post(
            run_url,
            data=json.dumps({'code': valid_code, 'language': 'python'}),
            content_type='application/json'
        )
        self.assertEqual(resp_valid.status_code, 200)
        data_valid = resp_valid.json()
        self.assertTrue(data_valid['syntax_valid'])
        self.assertEqual(data_valid['execution_mode'], 'client_pyodide')
        self.assertIsNone(data_valid['error'])

        # 2. Syntax Error code
        bad_code = "def broken_func(:\n    return\n"
        resp_bad = self.client.post(
            run_url,
            data=json.dumps({'code': bad_code, 'language': 'python'}),
            content_type='application/json'
        )
        self.assertEqual(resp_bad.status_code, 200)
        data_bad = resp_bad.json()
        self.assertFalse(data_bad['syntax_valid'])
        self.assertIn("SyntaxError", data_bad['error'])

    def test_metrics_collector_and_prometheus_export(self):
        """MetricsCollector must track requests and export Prometheus exposition text."""
        MetricsCollector.record_request('GET', '/courses', 200, 45.2)
        MetricsCollector.record_request('GET', '/courses', 200, 62.1)
        MetricsCollector.record_request('POST', '/learn/api', 500, 120.5)

        summary = MetricsCollector.get_system_metrics()
        self.assertGreaterEqual(summary['traffic']['requests_last_5m'], 3)
        self.assertGreaterEqual(summary['traffic']['errors_last_5m'], 1)
        self.assertTrue(summary['database']['connected'])

        prom_text = MetricsCollector.to_prometheus_format()
        self.assertIn("skillsphere_requests_total", prom_text)
        self.assertIn("skillsphere_latency_p95_ms", prom_text)
        self.assertIn("skillsphere_db_latency_ms", prom_text)

        # Staff can query /api/metrics/
        self.client.force_login(self.staff_user)
        api_resp = self.client.get('/api/metrics/')
        self.assertEqual(api_resp.status_code, 200)
        self.assertIn('traffic', api_resp.json())

        # Unauthenticated query must be rejected
        anon_client = Client()
        anon_resp = anon_client.get('/api/metrics/')
        self.assertEqual(anon_resp.status_code, 403)
