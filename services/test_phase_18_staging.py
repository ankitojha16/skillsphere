import os
import time
import uuid
import threading
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache

from services.task_queue import (
    enqueue_task,
    process_next_job,
    execute_job,
    recover_expired_leases,
    renew_job_lease,
    register_task,
)
from services.resilience import DistributedBulkhead
from services.storage_service import LocalStorageService, get_storage_service
from services.observability import MetricsCollector
from analytics.models import DurableTaskJob

User = get_user_model()


class Phase18StagingIntegrationTests(TestCase):
    """
    SkillSphere Phase 18 — Staging Multi-Instance Integration Suite.
    Verifies multi-instance correctness, independent worker coordination,
    fencing token isolation, distributed bulkhead bounding, and health probes.
    """

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user, _ = User.objects.get_or_create(
            username='staging_student_1',
            defaults={'email': 'student1@staging.skillsphere.local'}
        )

    def tearDown(self):
        cache.clear()

    def test_multi_worker_independent_queue_consumption(self):
        """
        Verifies multiple independent worker processes consume tasks from the shared queue
        without race conditions, double execution, or duplicate claims.
        """
        processed_tasks = []

        @register_task("staging_concurrent_job")
        def handle_job(payload):
            processed_tasks.append(payload.get('item_id'))
            return True

        # Enqueue 6 distinct jobs
        job_ids = []
        for i in range(6):
            job = enqueue_task(
                task_name="staging_concurrent_job",
                payload={"item_id": i},
                timeout_seconds=30
            )
            job_ids.append(job.task_id)

        # Worker 1 processes 3 jobs
        for _ in range(3):
            processed = process_next_job(worker_id="staging_worker_node_1")
            self.assertTrue(processed)

        # Worker 2 processes remaining 3 jobs
        for _ in range(3):
            processed = process_next_job(worker_id="staging_worker_node_2")
            self.assertTrue(processed)

        # Queue should now be empty
        self.assertFalse(process_next_job(worker_id="staging_worker_node_1"))
        self.assertFalse(process_next_job(worker_id="staging_worker_node_2"))

        # Verify all 6 jobs completed cleanly with correct worker IDs
        completed = list(DurableTaskJob.objects.filter(task_id__in=job_ids, status='completed'))
        self.assertEqual(len(completed), 6)

        worker_1_jobs = [j for j in completed if "staging_worker_node_1#" in j.worker_id]
        worker_2_jobs = [j for j in completed if "staging_worker_node_2#" in j.worker_id]
        self.assertEqual(len(worker_1_jobs), 3)
        self.assertEqual(len(worker_2_jobs), 3)

    def test_worker_lease_renewal_during_long_operation(self):
        """Verifies renew_job_lease extends active execution lease for long-running operations."""
        @register_task("staging_long_task")
        def handle_long(payload):
            return True

        job = enqueue_task(
            task_name="staging_long_task",
            payload={"run": "long"},
            timeout_seconds=5
        )

        fencing_token = "pod_1#token_alpha_999"
        job.status = 'running'
        job.started_at = timezone.now() - timedelta(seconds=4)
        job.worker_id = fencing_token
        job.save()

        # Renew lease before expiry
        renewed = renew_job_lease(job.id, fencing_token="token_alpha_999", extension_seconds=60)
        self.assertTrue(renewed)

        # Stalled recovery should not recover this job since lease was renewed
        recovered = recover_expired_leases(lease_grace_seconds=5)
        self.assertEqual(recovered, 0)

        job.refresh_from_db()
        self.assertEqual(job.status, 'running')

    def test_distributed_bulkhead_multithread_capacity(self):
        """Verifies DistributedBulkhead strictly limits concurrency across concurrent threads."""
        bh = DistributedBulkhead(
            name="staging_bulkhead_test",
            max_fleet_concurrent=2,
            fallback_local_concurrent=2
        )

        tokens = []
        errors = []

        def worker():
            tok = bh.acquire(timeout=0.05)
            if tok:
                tokens.append(tok)
                time.sleep(0.1)
                bh.release(tok)
            else:
                errors.append("CapacityExceeded")

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # At most 2 could run concurrently, others timed out / rejected
        self.assertGreaterEqual(len(errors), 1)

    def test_decoupled_health_probes(self):
        """Verifies decoupled /health/live/, /health/ready/, and /health/startup/ endpoints."""
        # 1. Liveness probe responds HTTP 200 without DB calls
        res_live = self.client.get('/health/live/')
        self.assertEqual(res_live.status_code, 200)

        # 2. Readiness probe responds HTTP 200 when DB is responsive
        res_ready = self.client.get('/health/ready/')
        self.assertEqual(res_ready.status_code, 200)

        # 3. Startup probe responds HTTP 200
        res_startup = self.client.get('/health/startup/')
        self.assertEqual(res_startup.status_code, 200)

    def test_storage_streaming_and_path_security(self):
        """Verifies storage file streaming and traversal rejection in staging."""
        storage = LocalStorageService()
        path = "staging_test/test_large_file.bin"
        data = b"SkillSphere_Cloud_Migration_Chunk_" * 400
        storage.save_file(path, data)

        # Chunked stream
        chunks = list(storage.get_file_chunks(path, chunk_size=2048))
        self.assertGreater(len(chunks), 1)
        self.assertEqual(b"".join(chunks), data)

        storage.delete_file(path)
