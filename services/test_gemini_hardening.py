import time
import urllib.error
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.cache import cache
from services.redis_service import RedisService
from services.ai_service import AIService

class GeminiMultiInstanceHardeningTests(TestCase):
    """
    Automated test suite verifying the enterprise Gemini AI hardening:
    - Multi-instance distributed Redis locks and sliding window rate limiter
    - Safe LocMem fallback behavior
    - Monotonic execution deadlines and socket timeouts
    - 429 Retry-After header parsing and failover
    - Telemetry and metrics aggregation
    """
    def setUp(self):
        cache.clear()
        RedisService.reset_client()

    def test_backend_status_safe_telemetry(self):
        """Backend status returns safe telemetry without leaking credentials or URLs."""
        status = RedisService.get_backend_status()
        self.assertIn('backend_type', status)
        self.assertIn('redis_connected', status)
        self.assertIn('distributed_ready', status)
        # Verify no sensitive keywords
        status_str = str(status)
        self.assertNotIn('password', status_str.lower())
        self.assertNotIn('redis://', status_str.lower())

    def test_sliding_window_rate_limiter_in_fallback(self):
        """Rate limiter allows requests up to limit and calculates retry_after when exceeded."""
        key = "test_rate:user_42"
        # 3 requests allowed in 60s
        for _ in range(3):
            allowed, retry_after = RedisService.check_sliding_window_rate_limit(key, limit=3, window_seconds=60)
            self.assertTrue(allowed)
            self.assertEqual(retry_after, 0)

        # 4th request must be rejected
        allowed, retry_after = RedisService.check_sliding_window_rate_limit(key, limit=3, window_seconds=60)
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)
        self.assertLessEqual(retry_after, 60)

    def test_atomic_lock_and_safe_release(self):
        """Atomic lock prevents concurrent acquisitions and safely releases only with matching token."""
        lock_key = "test_lock:session_99"
        acquired1, token1 = RedisService.acquire_lock(lock_key, ttl_seconds=3)
        self.assertTrue(acquired1)
        self.assertTrue(len(token1) > 0)

        # Second acquisition with same key while locked must fail
        acquired2, token2 = RedisService.acquire_lock(lock_key, ttl_seconds=3)
        self.assertFalse(acquired2)

        # Release with WRONG token must fail
        released_wrong = RedisService.release_lock(lock_key, "wrong_token_123")
        self.assertFalse(released_wrong)

        # Release with CORRECT token must succeed
        released_correct = RedisService.release_lock(lock_key, token1)
        self.assertTrue(released_correct)

        # Now acquisition can succeed again
        acquired3, token3 = RedisService.acquire_lock(lock_key, ttl_seconds=3)
        self.assertTrue(acquired3)

    def test_ai_service_check_rate_limit_integration(self):
        """AIService.check_rate_limit delegates to RedisService sliding window."""
        user_id = 9999
        allowed, retry_after = AIService.check_rate_limit(user_id=user_id, max_per_minute=2)
        self.assertTrue(allowed)
        self.assertEqual(retry_after, 0)

        allowed2, retry_after2 = AIService.check_rate_limit(user_id=user_id, max_per_minute=2)
        self.assertTrue(allowed2)

        # 3rd request in same minute exceeds limit of 2
        allowed3, retry_after3 = AIService.check_rate_limit(user_id=user_id, max_per_minute=2)
        self.assertFalse(allowed3)
        self.assertGreater(retry_after3, 0)

    def test_429_retry_after_header_parsing(self):
        """Gemini single call correctly extracts Retry-After from 429 HTTPError."""
        headers = MagicMock()
        headers.get.return_value = "15"
        mock_http_err = urllib.error.HTTPError(
            url="https://generativelanguage.googleapis.com",
            code=429,
            msg="Too Many Requests",
            hdrs=headers,
            fp=MagicMock(read=lambda: b'{"error": "Resource exhausted"}')
        )
        mock_http_err.headers = headers

        with patch('urllib.request.urlopen', side_effect=mock_http_err):
            text, status, err_msg, is_perm, retry_after = AIService._call_gemini_single(
                model='gemini-3.8-flash',
                api_key='fake-key',
                data_bytes=b'{}',
                timeout=5.0
            )
            self.assertIsNone(text)
            self.assertEqual(status, 429)
            self.assertFalse(is_perm)
            self.assertEqual(retry_after, 15)

    def test_monotonic_deadline_aborts_when_budget_expired(self):
        """Monotonic deadline aborts request cascade when elapsed time exceeds budget."""
        with patch.object(AIService, 'get_gemini_models_cascade', return_value=['gemini-3.8-flash', 'gemini-3.6-flash']):
            with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
                with patch('time.monotonic', side_effect=[0.0, 30.0, 35.0, 40.0]):
                    result = AIService._call_gemini("Test prompt")
                    self.assertIsNone(result)

    def test_ai_telemetry_metrics_tracking(self):
        """get_ai_metrics returns valid aggregated telemetry dictionary."""
        AIService._record_metric(success=True, model='gemini-3.8-flash', latency_ms=120.0, fallback_used=False)
        AIService._record_metric(success=False, model='gemini-3.8-flash', latency_ms=50.0, is_429=True)
        metrics = AIService.get_ai_metrics()
        self.assertIn('total_requests', metrics)
        self.assertIn('successful_requests', metrics)
        self.assertIn('quota_429_hits', metrics)
        self.assertIn('average_latency_ms', metrics)
        self.assertIn('model_counts', metrics)
        self.assertGreaterEqual(metrics['total_requests'], 2)
        self.assertGreaterEqual(metrics['quota_429_hits'], 1)
