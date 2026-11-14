# SkillSphere Phase 18.4.2 — Django 5.2 LTS Framework Upgrade Specification

**Previous Version**: Django 4.2.30 LTS  
**Target Version**: Django 5.2 LTS (`Django>=5.2.0,<5.3.0`)  
**Target Runtime**: Python 3.12 (AWS ECS Container Runtime)  
**Backward Compatibility**: Preserved via PEP 508 environment markers for local environments  

---

## 1. Upgrade Rationale & Extended Support Lifecycle

Django 4.2 LTS (released April 2023) enters End-of-Life status in April 2026. Upgrading SkillSphere to **Django 5.2 LTS** ensures:
- Upstream security patches and vulnerability mitigation guaranteed through **April 2028**.
- Native support for Python 3.12 and 3.13 performance improvements (specialized adaptive interpreter).
- Native database connection pooling enhancements and improved async ORM query capabilities.
- Deprecation removal of legacy file storage settings (`STATICFILES_STORAGE`).

---

## 2. Component Compatibility Audit & Refactoring

### 2.1 Storage Configuration (`STORAGES` Dictionary)
In Django 5.1+, `STATICFILES_STORAGE` and `DEFAULT_FILE_STORAGE` are removed. The configuration was migrated to the modern `STORAGES` structure in `config/settings.py`:

```python
# Static files and default media storage (Django 4.2+ / Django 5.x STORAGES standard)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedStaticFilesStorage"
        ),
    },
}
```

### 2.2 Database Engine Option Scoping
Django 5.x strictly validates backend-specific options. PostgreSQL-specific connection parameters (`connect_timeout` and `-c statement_timeout`) were updated to only apply when the resolved engine is PostgreSQL:

```python
# Scoped specifically to PostgreSQL backend
if 'postgresql' in default_db.get('ENGINE', ''):
    default_db.setdefault('OPTIONS', {})
    default_db['OPTIONS'].update({
        'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '5')),
        'options': f"-c statement_timeout={os.getenv('DB_STATEMENT_TIMEOUT', '10000')}",
    })
```

### 2.3 Django REST Framework (DRF) Compatibility
- **Installed Version**: DRF `3.16.1`
- **Specification**: `djangorestframework>=3.15.0`
- **Status**: 100% compatible with Django 5.x. All serializer fields, pagination classes, and API viewsets pass validation.

### 2.4 Authentication & Permissions
- Standard `django.contrib.auth` models and custom student profile context processors audited.
- Password hashers (`PBKDF2PasswordHasher`) verified with zero deprecation warnings.

### 2.5 Custom Management Commands
- Audited `run_task_worker` (background worker daemon with recovery and lease fencing).
- Verified signal handling (SIGTERM / SIGINT) and graceful shutdown under Django 5.2.

### 2.6 ReportLab & Certificate Generation
- **Version**: `reportlab>=4.0.0` (Installed `5.1.0`).
- Canvas drawing, PDF stream generation, and memory-safe chunking verified.

### 2.7 AI Gemini Integration & Distributed Resilience
- Circuit breaker state machine, token bucket rate limiters, and distributed Redis bulkheads pass all unit tests without behavioral changes.

---

## 3. Dependency Specification (`requirements.txt`)

To ensure deterministic deployment in production containers while supporting local development machines:

```text
# SkillSphere Production & Staging Dependencies
# Target Cloud Runtime: Python 3.12 (Dockerfile) / Django 5.2 LTS
Django>=5.2.0,<5.3.0; python_version >= '3.10'
Django>=4.2.20,<5.0; python_version < '3.10'
djangorestframework>=3.15.0
psycopg2-binary>=2.9.9
Pillow>=10.2.0
python-dotenv>=1.0.0
whitenoise>=6.6.0
gunicorn>=21.2.0
reportlab>=4.0.0
dj-database-url>=2.1.0
redis>=5.0.0
boto3>=1.34.0
```

---

## 4. Verification Results
- `python manage.py check`: **Passed** (0 issues, 0 silenced).
- `python -Wd manage.py check`: **Passed** (0 deprecation warnings).
- `python manage.py makemigrations --check --dry-run`: **Passed** (No pending migrations).
- `python manage.py migrate --plan`: **Passed** (100% migration plan resolved).
