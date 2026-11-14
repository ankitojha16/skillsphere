# SkillSphere Phase 18.2 — Cross-Host Storage Architecture & Provider Independence

## 1. Architectural Scope and Host Boundary Analysis

### 1.1 The Docker Named Volume Limitation
In Phase 18.1, the staging environment introduced a shared named Docker volume:
```yaml
volumes:
  staging_media:
    driver: local
```
**Why Docker Named Volumes Fail Across Independent Cloud Hosts:**
- A Docker named volume with the default `local` driver binds directly to the storage subsystem of a single host operating system (e.g. `/var/lib/docker/volumes/staging_media/_data`).
- When application containers run on independent physical instances, separate virtual machines (e.g. Amazon EC2 instances, GCP Compute Engine), or independent serverless container tasks (Amazon ECS Fargate across multiple Availability Zones, Google Cloud Run), the local volume driver cannot synchronize data across hosts.
- Attempting to use host-local volumes in a multi-host deployment results in catastrophic split-brain state: an asset uploaded to Host A is absent on Host B, causing intermittent HTTP 404s, broken avatar images, missing student resumes, and unverified certificates.

### 1.2 Enterprise Multi-Host Object Storage Architecture
To achieve true cross-host scalability and cloud portability, SkillSphere standardizes on **Provider-Independent Object Storage** accessed via the universal S3 API specification:

```
                                  +------------------------------------+
                                  |     Edge / Ingress Gateway         |
                                  |    (CloudFront / Cloudflare)       |
                                  +-----------------+------------------+
                                                    |
                      +-----------------------------+-----------------------------+
                      |                                                           |
                      v                                                           v
         +-------------------------+                                 +-------------------------+
         | Host Machine 1 (AZ-1a)  |                                 | Host Machine 2 (AZ-1b)  |
         | - Web Instance A        |                                 | - Web Instance B        |
         | - Worker Daemon A       |                                 | - Worker Daemon B       |
         +------------+------------+                                 +------------+------------+
                      |                                                           |
                      |   REST / HTTPS (SigV4)                                    |   REST / HTTPS (SigV4)
                      +-----------------------------+-----------------------------+
                                                    |
                                                    v
                                  +------------------------------------+
                                  |   Centralized Object Storage       |
                                  |   - AWS S3 (Production Multi-AZ)   |
                                  |   - Cloudflare R2 (Global Egress)  |
                                  |   - MinIO (Self-hosted Staging)    |
                                  |   - Supabase Storage (S3 API)      |
                                  +------------------------------------+
```

---

## 2. Universal S3-Compatible Storage Implementation

SkillSphere implements this pattern via `services/storage_service.py`, using `BaseStorageService` and `S3CompatibleStorageService`.

### 2.1 Provider Compatibility Matrix

| Cloud Provider | Storage Endpoint URL Format | Addressing Style | Region Parameter | Auth Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Amazon S3** | `https://s3.<region>.amazonaws.com` (Default) | `virtual` / Auto | e.g. `ap-south-1` | AWS IAM Role / Access Keys |
| **Cloudflare R2** | `https://<account_id>.r2.cloudflarestorage.com` | `path` | `auto` | R2 API Token (SigV4) |
| **MinIO** | `http://minio.internal:9000` | `path` | `us-east-1` (Default) | MinIO Root / Service Credentials |
| **Supabase Storage** | `https://<project-ref>.supabase.co/storage/v1/s3` | `path` | `us-east-1` / Project Region | Supabase S3 Access Keys |
| **Local Fallback** | Local Filesystem (`default_storage`) | N/A | N/A | File Permissions |

### 2.2 Streaming Uploads and Downloads (`save_file_stream`, `get_file_chunks`)
To prevent memory exhaustion when handling multi-megabyte PDF reports, portfolios, and course archives:
1. **Streaming Uploads (`save_file_stream`)**:
   Uses `boto3` client method `upload_fileobj`, which streams chunks directly from the incoming request or file buffer into the multipart upload pipeline without loading the entire asset into Django worker RAM.
2. **Streaming Downloads (`get_file_chunks`)**:
   Accesses botocore's `StreamingBody` directly from `client.get_object()['Body']` and yields 64 KB chunks. A `try...finally` block guarantees that `stream.close()` is invoked, immediately releasing the underlying HTTP connection back to the connection pool.

### 2.3 Time-Limited Pre-Signed Download URLs (`get_signed_url`)
Private assets (such as individual student course certificates and generated resumes) are protected against unauthorized direct-object access:
- Requests for private assets call `verify_ownership_and_get_signed_url()`, which verifies database ownership before issuing a cryptographically signed URL expiring in 3,600 seconds.
- Clients download large files directly from the cloud object store or CDN, offloading transfer bandwidth completely from application Gunicorn threads.

---

## 3. Boundary & Cross-Host Verification Evidence

The test suite in [`services/test_phase_18_2_cross_host.py`](file:///Users/ankitkumar/Desktop/wealthtrack/AnkitPortfolio/skill%20sphare/services/test_phase_18_2_cross_host.py) independently verified cross-host mechanics across 6 discrete tests:

1. **`test_cross_instance_file_sharing_via_shared_store`**:
   Web Instance 1 writes an asset to the shared backend; Web Instance 2 verifies presence and retrieves byte-for-byte content.
2. **`test_worker_pdf_generation_and_web_download_parity`**:
   Worker A streams a 2 MB PDF into the shared store; Web Instance B reads chunked stream and validates identical SHA-256 hash.
3. **`test_instance_restart_file_persistence`**:
   Simulated instance crash and restart; assets remain 100% accessible on fresh boots.
4. **`test_worker_crash_and_lease_recovery_across_hosts`**:
   Worker A crashes on Host 1; Worker B on Host 2 detects expired lease, reclaims task with fresh fencing token, and successfully executes, rejecting zombie Worker A.
5. **`test_private_file_ownership_and_signed_url_enforcement`**:
   Alice generates valid pre-signed URL; unauthorized student Bob is denied with `StoragePermissionDenied`.
6. **`test_s3_compatible_storage_addressing_and_custom_endpoints`**:
   MinIO and Cloudflare R2 configurations automatically resolve `addressing_style = 'path'`.

**Result**: All 6 tests PASSED in 1.73s (100% OK).
