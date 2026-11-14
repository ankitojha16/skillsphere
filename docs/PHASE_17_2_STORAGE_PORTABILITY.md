# SkillSphere Phase 17.2 — Storage Portability & Asset Architecture

## 1. Executive Summary & Design Goals

In containerized or autoscaling environments (e.g. Docker, Kubernetes, AWS ECS, Google Cloud Run), container file systems are ephemeral. If an application instance writes an uploaded avatar or generated document to its local disk (`MEDIA_ROOT`), subsequent requests landing on a different instance will experience HTTP 404 errors.

Phase 17.2 decouples SkillSphere from local filesystem storage by introducing a **provider-independent object storage abstraction** (`services/storage_service.py`).

### Key Design Tenets
1. **Provider Independence**: Unified interface (`BaseStorageService`) supporting local disk, AWS S3, Cloudflare R2, MinIO, and Supabase Storage without vendor lock-in.
2. **Strict Authorization**: User ownership checks are enforced prior to serving private student assets (Insecure Direct Object Reference / IDOR prevention).
3. **Zero Migration Disruption**: Existing files in production are preserved; no forced or destructive file migrations.
4. **Streaming & Memory Efficiency**: Documents are streamed via `io.BytesIO` or presigned URLs, avoiding buffer bloat on large exports.

---

## 2. Storage Abstraction Architecture

```
                                  [ Application Layer ]
                     (Student Profiles, Resumes, Certificates, Analytics)
                                           │
                                           ▼
                              [ services.storage_service ]
                               (get_storage_service())
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
        [ LocalStorageService ]                      [ S3CompatibleStorageService ]
          - Dev / Mount Volume                         - AWS S3
          - Path Traversal Guard                       - Cloudflare R2
          - Django default_storage                     - MinIO / Supabase Storage
                                                       - Presigned URLs & Stream
```

### 2.1 Interface Definition (`BaseStorageService`)
Every storage backend implements the following contract:
- `save_file(path: str, content: bytes, content_type: str, is_public: bool) -> str`
- `get_file(path: str) -> Optional[bytes]`
- `get_file_stream(path: str) -> Optional[io.BytesIO]`
- `delete_file(path: str) -> bool`
- `exists(path: str) -> bool`
- `get_url(path: str) -> str`
- `verify_ownership_and_get(path: str, user: Any, resource_type: str, resource_id: Any) -> bytes`

---

## 3. Asset Classification & Access Control Matrix

| Asset Category | Storage Path | Visibility | Authorization Rule | IDOR Protection |
| :--- | :--- | :--- | :--- | :--- |
| **Student Avatars** | `avatars/` | Authenticated / Public | Student owns profile; public viewing allowed on portfolio. | Profile owner check on write; path sanitization. |
| **Course Thumbnails** | `courses/` | Public | Read-only to all; staff write only. | Public access allowed. |
| **Portfolio Thumbnails** | `portfolios/thumbnails/` | Public | Student owns portfolio project; public viewing allowed. | Project owner check on write. |
| **Feedback Screenshots** | `feedback_screenshots/` | Private | Staff only or user who filed feedback. | `UserFeedback.objects.filter(user=user, id=resource_id)` |
| **Resume PDF Exports** | Dynamic Stream | Private | Student owner only. | `Resume.objects.filter(user=user, id=resource_id)` |
| **Certificate PDFs** | Dynamic Stream | Public/Private | Public verification allows certificate display; raw download requires owner or staff. | Verified via `Certificate.objects.filter(...)` |

---

## 4. Cloud Configuration & Deployment

Storage backend selection is controlled entirely via environment variables without code modification:

```bash
# S3-Compatible Cloud Storage (AWS S3, Cloudflare R2, MinIO, Supabase Storage)
STORAGE_BACKEND=s3
STORAGE_BUCKET_NAME=skillsphere-production-assets
STORAGE_REGION_NAME=ap-south-1
STORAGE_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com  # Optional for R2/MinIO
STORAGE_ACCESS_KEY=your_access_key
STORAGE_SECRET_KEY=your_secret_key
STORAGE_PUBLIC_URL_BASE=https://assets.skillsphere.app             # Optional CDN base

# Local / Volume Storage (Default for development & single-node testing)
STORAGE_BACKEND=local
```

### Path Traversal Protection
`LocalStorageService` strictly validates and sanitizes all relative paths against path traversal attacks:
```python
cleaned = os.path.normpath(str(path)).lstrip('/')
if '..' in cleaned.split(os.path.sep):
    raise ValueError(f"Path traversal detected in path '{path}'")
```

---

## 5. Verification Status
- **Path Traversal Protection**: Verified in `services/test_multiprocess_concurrency.py`.
- **Stream & Byte Retrieval**: Verified in `services/test_multiprocess_concurrency.py`.
- **Access Permission Matrix**: Verified in `services/test_multiprocess_concurrency.py`.
- **Preserved Existing Data**: All existing uploads in `MEDIA_ROOT` remain accessible.
