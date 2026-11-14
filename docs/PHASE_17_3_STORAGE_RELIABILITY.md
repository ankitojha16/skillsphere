# SkillSphere Phase 17.3 — Storage Reliability & Portability Verification

## 1. Executive Overview

In multi-instance production architectures (Kubernetes, AWS ECS/Fargate, Render, Heroku), application instances are ephemeral and horizontally autoscaled. Local filesystem storage (`media/` on ephemeral disks) causes catastrophic data inconsistency: an asset uploaded to Instance A is unavailable when requested through Instance B, and all local files are destroyed whenever an instance restarts or scales down.

Phase 17.3 hardens `services/storage_service.py` to guarantee cloud portability, strict object-level authorization (IDOR prevention), path traversal neutralization, memory-safe chunked streaming, and fail-fast production startup validation.

---

## 2. Storage Architecture & Backend Separation

SkillSphere enforces an abstract storage contract via `BaseStorageService`:

```
                    ┌────────────────────────────┐
                    │     BaseStorageService     │
                    │  (services/storage_service) │
                    └──────────────┬─────────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
      ┌─────────────────────┐             ┌─────────────────────┐
      │ LocalStorageService │             │   S3StorageService  │
      │ (Dev / Single-node) │             │ (Production Fleet)  │
      └─────────────────────┘             └─────────────────────┘
                 │                                   │
                 ▼                                   ▼
          Local Disk Volume                  AWS S3 / Cloudflare R2 /
       (Ephemeral or Shared NFS)               Supabase S3 Storage
```

### Backend Resolution & Fail-Fast Validation
Production instances (`DEBUG=False`) must NEVER silently fall back to ephemeral local storage when S3 credentials are missing or corrupted. 

In `services/storage_service.py`, `validate_storage_configuration()` executes at application startup and service initialization:

```python
def validate_storage_configuration() -> bool:
    backend_type = (os.getenv('STORAGE_BACKEND') or getattr(settings, 'STORAGE_BACKEND', 'local')).lower()
    
    if backend_type in ('s3', 'r2', 'spaces'):
        access_key = os.getenv('STORAGE_ACCESS_KEY') or getattr(settings, 'STORAGE_ACCESS_KEY', None)
        secret_key = os.getenv('STORAGE_SECRET_KEY') or getattr(settings, 'STORAGE_SECRET_KEY', None)
        bucket_name = os.getenv('STORAGE_BUCKET_NAME') or getattr(settings, 'STORAGE_BUCKET_NAME', None)

        if not (access_key and secret_key and bucket_name):
            msg = (
                "Production storage configuration error: STORAGE_BACKEND='s3' requires "
                "STORAGE_ACCESS_KEY, STORAGE_SECRET_KEY, and STORAGE_BUCKET_NAME to be set. "
                "Silent fallback to local ephemeral storage is disabled in production to protect student data."
            )
            if not settings.DEBUG:
                raise ImproperlyConfigured(msg)
            return False
```

- **Production Mode (`DEBUG=False`)**: Raises `django.core.exceptions.ImproperlyConfigured`. The instance will not enter a healthy state and container orchestrators (Kubernetes liveness/readiness probes) will abort deployment before traffic reaches the flawed instance.
- **Development Mode (`DEBUG=True`)**: Emits a `WARNING` log and gracefully falls back to `LocalStorageService` to streamline local development without requiring AWS credentials.

---

## 3. Path Traversal & Injection Defense

All file paths undergo strict sanitization before reaching any filesystem or object store API:

```python
clean_path = os.path.normpath(path).lstrip('/')
if clean_path.startswith('..') or '/../' in clean_path:
    raise SuspiciousOperation(f"Path traversal detected: {path}")
```

- Path components attempting relative traversal (`../../etc/passwd`, `courses/../../../secret.env`) immediately trigger `django.core.exceptions.SuspiciousOperation`.
- Django's core security middleware catches `SuspiciousOperation` and returns an immediate HTTP 400 Bad Request while logging a security audit event.

---

## 4. IDOR Defense & Object-Level Access Control

SkillSphere implements explicit object-level ownership checks via `verify_ownership_and_get`:

```python
storage = get_storage_service()
file_bytes = storage.verify_ownership_and_get(
    path=file_path,
    user=request.user,
    resource_type="resume_export",
    resource_id=resume.id
)
```

### Authorization Matrix:
| Resource Type | Resource Class | Permitted User | Unauthorized Action |
| :--- | :--- | :--- | :--- |
| `resume_export` | `resumes.models.Resume` | `resume.user == request.user` or `request.user.is_staff` | `PermissionDenied` (HTTP 403) |
| `certificate_pdf` | `courses.models.Certificate` | `cert.user == request.user` or `request.user.is_staff` | `PermissionDenied` (HTTP 403) |
| `user_export` | `accounts.models.User` | `target_user == request.user` or `request.user.is_staff` | `PermissionDenied` (HTTP 403) |
| Unknown / Unregistered | Any | Denied by default | `PermissionDenied` (HTTP 403) |

Anonymous requests are strictly rejected (`request.user.is_authenticated` check). Any cross-user inspection attempt emits a structured security warning:
```
[WARNING] [skillsphere.storage]: [StorageService] Unauthorized file access attempt: user=intruder_student, resource_type=resume_export, resource_id=1
```

---

## 5. Large File Chunked Streaming & Memory Safety

Loading multi-megabyte resume PDFs, certificate exports, or analytical archives into memory via `.read()` causes process heap spikes and risks OOM kills under concurrent load.

SkillSphere provides chunked streaming across all backends:

### `get_file_chunks(path, chunk_size=65536)`:
- **LocalStorageService**: Opens file descriptor with context management and yields 64 KB buffers until EOF.
- **S3StorageService**: Utilizes boto3 streaming response (`StreamingBody.read(chunk_size)`) without loading the complete S3 object into memory.
- **HTTP Views**: Compatible with `StreamingHttpResponse(storage.get_file_chunks(path), content_type='application/pdf')`.
- **Memory Footprint**: Strict $O(1)$ memory usage per concurrent stream regardless of file size ($64\text{ KB}$ per request).

---

## 6. Automated Test Verification

Hardening verified via `services/test_phase_17_3_hardening.py`:
- `test_storage_production_configuration_validation`: Confirms `ImproperlyConfigured` raised in production if S3 credentials missing.
- `test_storage_chunked_file_streaming`: Confirms discrete 4 KB / 64 KB block streaming and byte-for-byte fidelity.
- `test_storage_idor_authorization_enforcement`: Confirms student owner access allowed, anonymous and other student access rejected with `PermissionDenied`.
