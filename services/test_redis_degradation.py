import time
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.cache import cache
from services.redis_service import RedisService

class RedisDegradationAndRecoveryTests(TestCase):
    """
    Automated verification of Redis degradation, timeout handling, and automatic recovery:
    1. Redis available -> reports distributed_redis and distributed_ready=True
    2. Redis unavailable -> reports degraded_local_fallback, warning logged, fallback maintains functionality
    3. Redis timeout -> socket timeout caught, degraded status reported
    4. Redis recovery -> automatic reconnection without deployment restart
    """
    def setUp(self):
        cache.clear()
        RedisService.reset_client()

    def test_01_redis_available_distributed_mode(self):
        """When Redis is reachable, status accurately reports distributed mode."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True

        with patch('redis.from_url', return_value=mock_client):
            with patch.dict('os.environ', {'REDIS_URL': 'redis://fake-host:6379/0'}):
                RedisService.reset_client()
                self.assertTrue(RedisService.is_redis_available())
                status = RedisService.get_backend_status()
                self.assertEqual(status['backend_type'], 'redis')
                self.assertTrue(status['redis_connected'])
                self.assertTrue(status['distributed_ready'])
                self.assertEqual(status['protection_mode'], 'distributed_redis')
                self.assertIsNone(status['warning'])

    def test_02_redis_unavailable_degraded_fallback(self):
        """When Redis is unconfigured or unreachable, degrades to local cache and logs warning."""
        RedisService.reset_client()
        with patch.dict('os.environ', {}, clear=True):
            self.assertFalse(RedisService.is_redis_available())
            status = RedisService.get_backend_status()
            self.assertEqual(status['backend_type'], 'locmem_fallback')
            self.assertFalse(status['redis_connected'])
            self.assertFalse(status['distributed_ready'])
            self.assertEqual(status['protection_mode'], 'degraded_local_fallback')
            self.assertIn("degraded mode", status['warning'])
            self.assertIn("INACTIVE", status['warning'])

            # Core functionality still preserves safety via cache fallback
            acquired, token = RedisService.acquire_lock("lock_test_fallback", ttl_seconds=3)
            self.assertTrue(acquired)
            released = RedisService.release_lock("lock_test_fallback", token)
            self.assertTrue(released)

    def test_03_redis_timeout_degrades_gracefully(self):
        """When Redis socket times out during ping or operation, degrades to local fallback."""
        mock_client = MagicMock()
        mock_client.ping.side_effect = TimeoutError("Connection to Redis timed out")

        with patch('redis.from_url', return_value=mock_client):
            with patch.dict('os.environ', {'REDIS_URL': 'redis://fake-host:6379/0'}):
                RedisService.reset_client()
                self.assertFalse(RedisService.is_redis_available())
                status = RedisService.get_backend_status()
                self.assertEqual(status['protection_mode'], 'degraded_local_fallback')
                self.assertFalse(status['distributed_ready'])

    def test_04_redis_recovery_without_restart(self):
        """When Redis connectivity is restored after a drop, it automatically reconnects without restarting."""
        failing_mock = MagicMock()
        failing_mock.ping.side_effect = ConnectionError("Connection refused")

        recovered_mock = MagicMock()
        recovered_mock.ping.return_value = True

        with patch.dict('os.environ', {'REDIS_URL': 'redis://fake-host:6379/0'}):
            RedisService.reset_client()

            # Phase 1: Connection fails
            with patch('redis.from_url', return_value=failing_mock):
                self.assertFalse(RedisService.is_redis_available())
                status1 = RedisService.get_backend_status()
                self.assertEqual(status1['protection_mode'], 'degraded_local_fallback')

            # Advance monotonic clock past cooldown interval
            RedisService._last_failure_time = time.monotonic() - 10.0

            # Phase 2: Redis comes back online
            with patch('redis.from_url', return_value=recovered_mock):
                self.assertTrue(RedisService.is_redis_available())
                status2 = RedisService.get_backend_status()
                self.assertEqual(status2['protection_mode'], 'distributed_redis')
                self.assertTrue(status2['distributed_ready'])
                self.assertIsNone(status2['warning'])
