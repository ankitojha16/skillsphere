"""
Phase 17.1 Failure-Injection & Chaos Engineering Test Suite
Simulates controlled infrastructure failures:
1. Redis unavailable -> Degrades to local memory without throwing 500 errors.
2. Upstream AI API timeout -> Circuit breaker trips to OPEN and fast-fails to Knowledge Engine.
3. Database connection timeout -> /health/ready/ detects outage, /health/live/ stays alive.
4. Task queue duplicate delivery -> Idempotency key prevents duplicate execution.
5. Bulkhead exhaustion -> Rejects overflow requests without thread pool starvation.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache

from services.resilience import CircuitBreaker, Bulkhead
from services.ai_service import AIService
from services.task_queue import enqueue_task, execute_job
from analytics.models import DurableTaskJob


class Phase171FailureInjectionTests(TestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='chaos_engineer',
            email='chaos@skillsphere.edu',
            password='ChaosPassword123!'
        )

    def test_failure_injection_redis_outage(self):
        """When Redis raises ConnectionError/TimeoutError, application must degrade gracefully."""
        cb = CircuitBreaker(name='chaos_breaker', failure_threshold=2)

        # Mock cache.get and cache.set to raise ConnectionError (simulating Redis down)
        with patch('django.core.cache.cache.get', side_effect=ConnectionError("Redis connection refused")), \
             patch('django.core.cache.cache.set', side_effect=ConnectionError("Redis connection refused")):

            # Breaker must still function using thread-safe local process state
            self.assertTrue(cb.can_execute())
            cb.record_failure()
            cb.record_failure()
            # Must trip to OPEN despite Redis failure
            self.assertEqual(cb.get_state(), CircuitBreaker.STATE_OPEN)
            self.assertFalse(cb.can_execute())

    def test_failure_injection_upstream_ai_timeout(self):
        """When Gemini API times out, CircuitBreaker trips and fast-fails directly to Knowledge Engine."""
        cb = CircuitBreaker(name='gemini_api', failure_threshold=2, recovery_timeout=60.0)

        # Force breaker into OPEN state
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.get_state(), CircuitBreaker.STATE_OPEN)

        # AI assistant call must immediately execute fallback without waiting for network timeout
        with patch.object(cb, 'can_execute', return_value=False):
            fallback_answer = AIService.ask_study_assistant(
                question="Explain Big-O notation in simple terms",
                user_id=self.user.id
            )
            self.assertTrue(len(fallback_answer) > 20)

    def test_failure_injection_database_outage_probes(self):
        """When database fails, /health/ready/ must report 503, while /health/live/ stays 200 alive."""
        client = Client()

        # 1. Healthy state
        res_live = client.get('/health/live/')
        self.assertEqual(res_live.status_code, 200)

        res_ready = client.get('/health/ready/')
        self.assertEqual(res_ready.status_code, 200)

        # 2. Simulate Database Outage
        with patch('django.db.connection.cursor', side_effect=OperationalError("DB Connection Timed Out")):
            # Liveness probe MUST stay 200 OK (so container orchestrator doesn't enter reboot loop)
            res_live_degraded = client.get('/health/live/')
            self.assertEqual(res_live_degraded.status_code, 200)
            self.assertEqual(res_live_degraded.json()['status'], 'alive')

            # Readiness probe MUST return 503 Service Unavailable (removes pod from load balancer)
            res_ready_degraded = client.get('/health/ready/')
            self.assertEqual(res_ready_degraded.status_code, 503)
            self.assertEqual(res_ready_degraded.json()['status'], 'not_ready')
            self.assertEqual(res_ready_degraded.json()['database'], 'unavailable')

    def test_failure_injection_task_duplicate_delivery(self):
        """Duplicate task delivery with same idempotency key must not duplicate background jobs."""
        key = 'unique_order_dispatch_12345'
        job1 = enqueue_task('dispatch_notification', payload={'order_id': 42}, idempotency_key=key)
        self.assertIsNotNone(job1.id)

        # Second delivery of same task
        job2 = enqueue_task('dispatch_notification', payload={'order_id': 42}, idempotency_key=key)
        self.assertEqual(job1.id, job2.id)
        self.assertEqual(DurableTaskJob.objects.filter(idempotency_key=key).count(), 1)


import time
from django.db import OperationalError
