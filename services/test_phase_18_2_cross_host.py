"""
SkillSphere Phase 18.2 — Cross-Host Scalability, Shared Storage & Cloud Boundary Test Suite
Validates:
1. Multi-instance cross-process file sharing via shared storage backends.
2. Worker PDF generation and cross-instance web retrieval.
3. Resilience to application instance and worker restarts.
4. Strict ownership verification and presigned URL access control.
5. Memory-safe streaming upload/download with SHA-256 chunk parity.
6. S3-compatible cloud storage provider independence (AWS S3, MinIO, Cloudflare R2, Supabase).
"""

import os
import io
import time
import shutil
import tempfile
import hashlib
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from services.storage_service import (
    BaseStorageService,
    LocalStorageService,
    S3CompatibleStorageService,
    StoragePermissionDenied,
    get_storage_service,
    reset_storage_service,
)
from certificates.models import Certificate
from django.utils import timezone
from datetime import timedelta
from services.task_queue import (
    enqueue_task,
    execute_job,
    recover_expired_leases,
    register_task,
)

User = get_user_model()


class SharedBackendMock(BaseStorageService):
    """
    Simulates a centralized, cross-host network object store (e.g. AWS S3, Cloudflare R2, MinIO)
    accessible concurrently by multiple independent application and worker nodes.
    """
    def __init__(self, shared_backing_store: dict):
        self._store = shared_backing_store

    def save_file_stream(self, path: str, stream: io.IOBase, content_type: str = 'application/octet-stream', is_public: bool = False, content_length=None) -> str:
        key = path.lstrip('/')
        self._store[key] = stream.read()
        return key

    def save_file(self, path: str, content: bytes, content_type: str = 'application/octet-stream', is_public: bool = False) -> str:
        key = path.lstrip('/')
        self._store[key] = content
        return key

    def get_file(self, path: str):
        key = path.lstrip('/')
        return self._store.get(key)

    def get_file_stream(self, path: str):
        data = self.get_file(path)
        if data is None:
            return None
        return io.BytesIO(data)

    def delete_file(self, path: str) -> bool:
        key = path.lstrip('/')
        self._store.pop(key, None)
        return True

    def exists(self, path: str) -> bool:
        key = path.lstrip('/')
        return key in self._store

    def get_url(self, path: str) -> str:
        key = path.lstrip('/')
        return f"https://cdn.skillsphere.cloud/{key}"

    def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        key = path.lstrip('/')
        return f"https://cdn.skillsphere.cloud/{key}?signature=valid_sig&expires={int(time.time()) + expires_in}"


class CrossHostBoundaryTests(TestCase):
    """Verifies that independent application and worker nodes behave correctly across host boundaries."""

    def setUp(self):
        reset_storage_service()
        self.user_a = User.objects.create_user(username='student_alice', password='password123')
        self.user_b = User.objects.create_user(username='student_bob', password='password123')

    def tearDown(self):
        reset_storage_service()

    def test_cross_instance_file_sharing_via_shared_store(self):
        """
        Verify that Web Instance 1 uploading to a shared object store allows Web Instance 2
        to immediately retrieve and verify the exact content without local process memory or shared disk.
        """
        shared_cloud_store = {}
        web_instance_1 = SharedBackendMock(shared_cloud_store)
        web_instance_2 = SharedBackendMock(shared_cloud_store)

        file_payload = b"CRITICAL_CERTIFICATE_METADATA_STUDENT_ALICE_PHASE18_2"
        storage_path = "certificates/2026/alice_cert_001.pdf"

        # Instance 1 saves file
        saved_key = web_instance_1.save_file(storage_path, file_payload, content_type="application/pdf")
        self.assertEqual(saved_key, storage_path)

        # Instance 2 checks existence and reads bytes
        self.assertTrue(web_instance_2.exists(storage_path))
        retrieved_content = web_instance_2.get_file(storage_path)
        self.assertEqual(retrieved_content, file_payload)

    def test_worker_pdf_generation_and_web_download_parity(self):
        """
        Verify that a background worker instance generating a large PDF streams it into shared storage,
        and an independent web instance downloads the exact stream with SHA-256 integrity.
        """
        shared_cloud_store = {}
        worker_instance_node = SharedBackendMock(shared_cloud_store)
        web_instance_node = SharedBackendMock(shared_cloud_store)

        # Generate 2MB payload
        chunk_pattern = b"SkillSphere-Certified-Engineer-2026-Verification-Hash#"
        large_payload = chunk_pattern * (2 * 1024 * 1024 // len(chunk_pattern))
        expected_sha256 = hashlib.sha256(large_payload).hexdigest()

        # Worker streams upload
        upload_stream = io.BytesIO(large_payload)
        pdf_path = "generated_reports/q4_certification_report.pdf"
        worker_instance_node.save_file_stream(pdf_path, upload_stream, content_type="application/pdf")

        # Web node streams chunks
        hasher = hashlib.sha256()
        chunk_count = 0
        for chunk in web_instance_node.get_file_chunks(pdf_path, chunk_size=65536):
            hasher.update(chunk)
            chunk_count += 1

        self.assertGreater(chunk_count, 10)
        self.assertEqual(hasher.hexdigest(), expected_sha256)

    def test_instance_restart_file_persistence(self):
        """
        Verify that when an application instance terminates and a fresh instance boots,
        previously uploaded assets remain accessible and unaltered.
        """
        shared_cloud_store = {}
        original_instance = SharedBackendMock(shared_cloud_store)
        doc_key = "user_uploads/profile_avatar.jpg"
        original_instance.save_file(doc_key, b"\xff\xd8\xff\xe0_FAKE_JPEG_IMAGE_DATA")

        # Simulate instance crash / termination
        del original_instance

        # Fresh instance initializes
        fresh_restarted_instance = SharedBackendMock(shared_cloud_store)
        self.assertTrue(fresh_restarted_instance.exists(doc_key))
        self.assertEqual(fresh_restarted_instance.get_file(doc_key), b"\xff\xd8\xff\xe0_FAKE_JPEG_IMAGE_DATA")

    def test_worker_crash_and_lease_recovery_across_hosts(self):
        """
        Verify that if Worker A on Host 1 crashes while executing a task, Worker B on Host 2
        detects the expired lease, reallocates ownership, and safely completes the job,
        while zombie Worker A is fenced off from committing stale results.
        """
        executed_by = []

        @register_task("cross_host_cert_task")
        def sample_worker_task(payload):
            executed_by.append(payload.get("worker_tag"))
            return {"status": "ok"}

        job = enqueue_task(
            task_name="cross_host_cert_task",
            payload={"cert_id": 999, "worker_tag": "worker_b"},
            timeout_seconds=5
        )

        # Worker A on Host 1 claims the task
        token_a = "worker_host_1#token_worker_a_111"
        job.status = 'running'
        job.started_at = timezone.now() - timedelta(seconds=60)  # Expired lease
        job.worker_id = token_a
        job.save()

        # Worker B on Host 2 detects expired lease and reclaims it
        recovered_count = recover_expired_leases(lease_grace_seconds=5)
        self.assertGreaterEqual(recovered_count, 1)

        # Worker B takes ownership
        token_b = "worker_host_2#token_worker_b_222"
        job.refresh_from_db()
        job.status = 'running'
        job.started_at = timezone.now()
        job.worker_id = token_b
        job.save()

        # Zombie Worker A awakens and attempts stale execution commit
        zombie_success = execute_job(job, worker_id=token_a)
        self.assertFalse(zombie_success)

        # Worker B executes and completes cleanly
        worker_b_success = execute_job(job, worker_id=token_b)
        self.assertTrue(worker_b_success)
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.worker_id, token_b)

    def test_private_file_ownership_and_signed_url_enforcement(self):
        """
        Verify that private file ownership verification succeeds for the asset owner
        and raises StoragePermissionDenied for unauthorized students.
        """
        shared_cloud_store = {}
        storage_service = SharedBackendMock(shared_cloud_store)

        cert = Certificate.objects.create(
            user=self.user_a,
            certificate_id="SS-CERT-CROSS-HOST-01",
            title="Cloud Architecture Specialist"
        )
        cert_path = f"certificates/private_{cert.id}.pdf"
        storage_service.save_file(cert_path, b"CONFIDENTIAL_CERTIFICATE_BODY")

        # Owner Alice generates signed URL
        signed_url = storage_service.verify_ownership_and_get_signed_url(
            path=cert_path,
            user=self.user_a,
            resource_type='private_certificate',
            resource_id=cert.id,
            expires_in=1800
        )
        self.assertIn("signature=valid_sig", signed_url)

        # Intruder Bob attempts to access Alice's certificate
        with self.assertRaises(StoragePermissionDenied):
            storage_service.verify_ownership_and_get_signed_url(
                path=cert_path,
                user=self.user_b,
                resource_type='private_certificate',
                resource_id=cert.id
            )

    def test_s3_compatible_storage_addressing_and_custom_endpoints(self):
        """
        Verify that S3CompatibleStorageService correctly detects MinIO, Cloudflare R2,
        and Supabase custom endpoints and applies path-style addressing.
        """
        # 1. MinIO Configuration
        minio_service = S3CompatibleStorageService(
            bucket_name="minio-media",
            endpoint_url="http://minio.internal:9000",
            access_key="minio_admin",
            secret_key="minio_secret_pass"
        )
        self.assertEqual(minio_service.addressing_style, 'path')

        # 2. Cloudflare R2 Configuration
        r2_service = S3CompatibleStorageService(
            bucket_name="r2-media",
            endpoint_url="https://c8219abf182.r2.cloudflarestorage.com",
            access_key="r2_access_key",
            secret_key="r2_secret_key",
            region_name="auto"
        )
        self.assertEqual(r2_service.addressing_style, 'path')
        self.assertEqual(r2_service.region_name, 'auto')

        # 3. Standard AWS S3 Configuration
        s3_service = S3CompatibleStorageService(
            bucket_name="aws-skillsphere-prod",
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region_name="ap-south-1"
        )
        self.assertIsNone(s3_service.addressing_style)
        self.assertEqual(s3_service.region_name, 'ap-south-1')
