# SkillSphere Phase 18.1 — Shared Storage Verification & Portability Tests

## 1. Executive Summary

This report establishes the storage portability guarantees for SkillSphere across multi-instance topologies, comparing isolated container filesystems, shared network volumes, and cloud object storage (S3/R2).

---

## 2. Storage Topology Comparison

```
Isolated Disks (BROKEN)              Shared Volume (STAGING)              Object Storage (PRODUCTION)
┌─────────────┐  ┌─────────────┐     ┌─────────────┐  ┌─────────────┐     ┌─────────────┐  ┌─────────────┐
│ Web Node 1  │  │ Web Node 2  │     │ Web Node 1  │  │ Web Node 2  │     │ Web Node 1  │  │ Web Node 2  │
│ [media/ A]  │  │ [media/ B]  │     └──────┬──────┘  └──────┬──────┘     └──────┬──────┘  └──────┬──────┘
└─────────────┘  └─────────────┘            │                │                   │                │
       ❌ Unshared                          ▼                ▼                   ▼                ▼
(Node 2 cannot read Node 1's files)   ┌─────────────────────────────┐     ┌─────────────────────────────┐
                                      │   Named Volume (staging)    │     │   Amazon S3 / Cloudflare R2 │
                                      │       /app/media            │     │   skillsphere-media-bucket  │
                                      └─────────────────────────────┘     └─────────────────────────────┘
                                           ✅ Shared Read/Write                ✅ Cloud-Native Shared Object
```

### 2.1 The Unshared Local Disk Defect
As demonstrated in `services/test_phase_18_1_validation.py:test_isolated_storage_failure_without_shared_volume`:
- When Instance 1 and Instance 2 execute with separate, unmounted local media directories:
  - Instance 1 uploads `certificates/cert_isolated.pdf`.
  - Instance 1 sees `exists() == True`.
  - When a student request is routed to Instance 2 to download the certificate, Instance 2 checks its local disk, sees `exists() == False`, and returns HTTP 404.
- **Architectural Principle**: A local storage class must NEVER be assumed to be shared across container instances unless an explicit shared volume (`staging_media`) is mounted to `/app/media` on all pods.

### 2.2 Shared Volume Verification
As verified in `services/test_phase_18_1_validation.py:test_shared_volume_cross_instance_file_access`:
- When both instances mount the shared physical volume:
  - Instance 1 writes `student_resumes/shared_resume_123.pdf`.
  - Instance 2 immediately reads the exact file bytes with byte-for-byte fidelity.
  - Chunked streaming generator yields 16-byte/64-KB blocks safely across instances.

---

## 3. Security & Authorization Enforcement

### 3.1 Path Traversal Protection
All file operations pass through `_sanitize_path()`:
```python
clean_path = os.path.normpath(str(path)).lstrip('/')
if '..' in clean_path.split(os.path.sep):
    raise ValueError(f"Path traversal detected in path '{path}'")
```
Attempts to escape the media boundary (e.g. `../../etc/passwd` or `resumes/../../../secret.env`) trigger immediate `ValueError` and HTTP 400 Bad Request.

### 3.2 IDOR Object-Level Ownership Checks
`verify_ownership_and_get()` checks user authorization:
- `resume_export`: Accessible only by resume owner or staff.
- `private_certificate`: Accessible only by certificate owner or staff.
- `feedback_screenshot`: Accessible only by reporting user or staff.
- Cross-user attempts raise `StoragePermissionDenied` (HTTP 403).
