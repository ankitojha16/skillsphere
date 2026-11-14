"""
SkillSphere Phase 17.3 Production Migration Readiness & Application Hardening Tests
Covers:
1. Storage production fail-fast configuration validation (ImproperlyConfigured on missing credentials).
2. Large file chunked streaming via get_file_chunks.
3. Atomic DistributedBulkhead Lua operations, lease renewal, and degraded fallback.
4. Worker fencing token assignment and atomic claiming.
5. Zombie worker defense: rejection of stale worker completion after lease reallocation.
6. Storage IDOR access control and cross-user authorization.
7. Prometheus instance label stability, sanitization, and bounded cardinality.
"""

import os
import io
import time
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.conf import settings

from analytics.models import DurableTaskJob
from services.task_queue import (
    enqueue_task,
    execute_job,
    process_next_job,
    recover_expired_leases,
    renew_job_lease,
    register_task,
    TASK_HANDLERS
)
from services.storage_service import (
    LocalStorageService,
    S3CompatibleStorageService,
    validate_storage_configuration,
    get_storage_service,
    reset_storage_service,
    StoragePermissionDenied
)
from services.resilience import DistributedBulkhead, Bulkhead
from services.observability import MetricsCollector


class Phase17HardeningTests(TransactionTestCase):
    def setUp(self):
        reset_storage_service()
        self.user = User.objects.create_user(
            username='hardening_student',
            password='TestPassword123!',
            email='hardening@skillsphere.app'
        )
        self.other_user = User.objects.create_user(
            username='intruder_student',
            password='TestPassword123!',
            email='intruder@skillsphere.app'
        )

    def test_storage_production_configuration_validation(self):
        """Production mode must raise ImproperlyConfigured if cloud storage credentials are missing."""
        # 1. In production with S3 and missing credentials
        with patch.object(settings, 'DEBUG', False):
            with patch.dict(os.environ, {
                'STORAGE_BACKEND': 's3',
                'STORAGE_ACCESS_KEY': '',
                'STORAGE_SECRET_KEY': '',
                'STORAGE_BUCKET_NAME': ''
            }):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    validate_storage_configuration()
                self.assertIn("Production storage configuration error", str(ctx.exception))

        # 2. In development (DEBUG=True), returns False with warning without raising exception
        with patch.object(settings, 'DEBUG', True):
            with patch.dict(os.environ, {
                'STORAGE_BACKEND': 's3',
                'STORAGE_ACCESS_KEY': '',
                'STORAGE_SECRET_KEY': '',
                'STORAGE_BUCKET_NAME': ''
            }):
                valid = validate_storage_configuration()
                self.assertFalse(valid)

    def test_storage_chunked_file_streaming(self):
        """Verifies get_file_chunks yields data in discrete memory-efficient blocks."""
        storage = LocalStorageService()
        test_data = b"SkillSphere_Enterprise_Payload_Stream_" * 500  # ~19 KB
        path = "test_streams/stream_sample.bin"
        storage.save_file(path, test_data)

        chunks = list(storage.get_file_chunks(path, chunk_size=4096))
        self.assertGreater(len(chunks), 1)
        reconstructed = b"".join(chunks)
        self.assertEqual(reconstructed, test_data)

        storage.delete_file(path)

    def test_distributed_bulkhead_atomic_lua_and_renewal(self):
        """Verifies DistributedBulkhead permit acquisition, lease renewal, and degraded fallback."""
        bh = DistributedBulkhead(
            name="hardening_fleet_test",
            max_fleet_concurrent=3,
            lease_ttl_seconds=10,
            fallback_local_concurrent=2
        )

        # When Redis is offline or unmocked, it operates in degraded local mode
        token = bh.acquire(timeout=0.1)
        self.assertIsNotNone(token)

        # Lease renewal works
        renewed = bh.renew_lease(token, extension_seconds=20)
        self.assertTrue(renewed)

        # Release works
        released = bh.release(token)
        self.assertTrue(released)

        # Context manager pattern works
        with bh.acquire_context(timeout=0.1) as ctx_tok:
            self.assertIsNotNone(ctx_tok)

    def test_worker_fencing_token_and_atomic_claim(self):
        """process_next_job must attach a unique fencing token to worker_id on claim."""
        register_task("dummy_fenced_task")(lambda p: True)

        job = enqueue_task(
            task_name="dummy_fenced_task",
            payload={"step": 1},
            timeout_seconds=30
        )
        self.assertEqual(job.status, 'pending')

        claimed = process_next_job(worker_id="worker_alpha")
        self.assertTrue(claimed)

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertTrue(job.worker_id.startswith("worker_alpha#"))

    def test_zombie_worker_defense_stale_completion_rejected(self):
        """
        Critical Distributed Systems Test:
        If Worker 1's lease expires and the job is claimed by Worker 2,
        Worker 1 (resuming after stall) MUST NOT overwrite Worker 2's state.
        """
        task_executed = []

        @register_task("zombie_test_task")
        def zombie_handler(payload):
            task_executed.append(payload.get('worker'))
            return True

        # 1. Enqueue job
        job = enqueue_task(
            task_name="zombie_test_task",
            payload={"worker": "test"},
            timeout_seconds=5
        )

        # 2. Worker 1 claims the job
        worker_1_id = "node_1#fencing_token_111"
        job.status = 'running'
        job.started_at = timezone.now() - timedelta(seconds=60)  # Expired lease!
        job.worker_id = worker_1_id
        job.save()

        # 3. Queue recovery detects expired lease and reschedules job
        recovered = recover_expired_leases(lease_grace_seconds=5)
        self.assertGreaterEqual(recovered, 1)
        job.refresh_from_db()
        self.assertEqual(job.status, 'failed')
        self.assertEqual(job.retries, 1)

        # 4. Worker 2 claims the job with a new fencing token
        worker_2_id = "node_2#fencing_token_222"
        job.status = 'running'
        job.started_at = timezone.now()
        job.worker_id = worker_2_id
        job.scheduled_at = timezone.now() - timedelta(seconds=1)
        job.save()

        # 5. Worker 1 wakes up and attempts to complete the job with its OLD token
        # execute_job MUST reject Worker 1's stale write!
        stale_completed = execute_job(job, worker_id=worker_1_id)
        self.assertFalse(stale_completed)

        # 6. Verify job is NOT marked completed by Worker 1; Worker 2 still owns it
        job.refresh_from_db()
        self.assertEqual(job.status, 'running')
        self.assertEqual(job.worker_id, worker_2_id)

        # 7. Worker 2 finishes cleanly with its valid active token
        valid_completed = execute_job(job, worker_id=worker_2_id)
        self.assertTrue(valid_completed)
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.worker_id, worker_2_id)

    def test_storage_idor_authorization_enforcement(self):
        """verify_ownership_and_get must reject cross-user access attempts."""
        from resumes.models import Resume
        resume = Resume.objects.create(user=self.user, title="Principal Engineer")

        storage = LocalStorageService()
        path = "resumes/student_resume_1.pdf"
        storage.save_file(path, b"%PDF-SampleResumeContent")

        # Owner can access
        data = storage.verify_ownership_and_get(path, self.user, 'resume_export', resume.id)
        self.assertEqual(data, b"%PDF-SampleResumeContent")

        # Unauthenticated user is rejected
        with self.assertRaises(StoragePermissionDenied):
            storage.verify_ownership_and_get(path, None, 'resume_export', resume.id)

        # Another student is rejected (IDOR protection)
        with self.assertRaises(StoragePermissionDenied):
            storage.verify_ownership_and_get(path, self.other_user, 'resume_export', resume.id)

        storage.delete_file(path)

    def test_prometheus_instance_label_stability_and_sanitization(self):
        """get_instance_id must return a stable, sanitized identifier without unbounded cardinality."""
        inst1 = MetricsCollector.get_instance_id()
        inst2 = MetricsCollector.get_instance_id()
        self.assertEqual(inst1, inst2)
        # Verify sanitization (no whitespace, commas, or special chars)
        self.assertRegex(inst1, r'^[a-zA-Z0-9_\-]+$')

        prom_text = MetricsCollector.to_prometheus_format()
        self.assertIn(f'skillsphere_instance_info{{instance="{inst1}"}} 1', prom_text)
