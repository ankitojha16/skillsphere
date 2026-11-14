# SkillSphere Phase 18.4.2 — Dependency Security & Vulnerability Audit

**Audit Date**: 2026-11-15  
**Target Environment**: AWS ECS Staging Runtime (`python:3.12-slim`)  
**Security Standard**: OWASP Top 10 Software and Data Integrity Failures / CIS Benchmark  

---

## 1. Dependency Inventory & Vulnerability Analysis

All installed packages in the SkillSphere virtual environment were audited for known CVEs, unpinned runtime ranges, and maintenance status:

| Package | Installed Version | Pinned Specification | Known CVEs / Security Advisories | Maintenance Status |
| :--- | :--- | :--- | :--- | :--- |
| **Django** | 4.2.30 (Host) / 5.2 (Container) | `Django>=5.2.0,<5.3.0` | None in 4.2.30 / 5.2 LTS | Active LTS |
| **djangorestframework**| 3.16.1 | `djangorestframework>=3.15.0` | None | Active Maintenance |
| **psycopg2-binary** | 2.9.12 | `psycopg2-binary>=2.9.9` | None | Active Maintenance |
| **Pillow** | 11.3.0 | `Pillow>=10.2.0` | None (Prior libwebp CVEs patched) | Active Maintenance |
| **python-dotenv** | 1.2.1 | `python-dotenv>=1.0.0` | None | Active Maintenance |
| **whitenoise** | 6.11.0 | `whitenoise>=6.6.0` | None | Active Maintenance |
| **gunicorn** | 23.0.0 | `gunicorn>=21.2.0` | None (HTTP request smuggling patched)| Active Maintenance |
| **reportlab** | 5.1.0 | `reportlab>=4.0.0` | None (Prior RCE CVE-2023-33733 patched)| Active Maintenance |
| **dj-database-url** | 3.0.1 | `dj-database-url>=2.1.0` | None | Active Maintenance |
| **redis** | 7.0.1 | `redis>=5.0.0` | None | Active Maintenance |
| **boto3** | Container / IAM | `boto3>=1.34.0` | None | Active AWS SDK |

---

## 2. Security Findings & Remediations

### 2.1 Resolution of Legacy Storage Warning
- **Finding**: Running system check with `-Wd` flagged `RemovedInDjango51Warning: The STATICFILES_STORAGE setting is deprecated. Use STORAGES instead.`
- **Remediation**: Refactored `config/settings.py` to use `STORAGES` dictionary. System checks now report zero warnings.

### 2.2 Container Base Image Security (`python:3.12-slim`)
- **Base Image**: Uses official Debian-based `python:3.12-slim` image.
- **CVE Mitigation**:
  - Regular security patches applied via `apt-get update && apt-get install --no-install-recommends`.
  - Minimal package surface: Only `build-essential`, `libpq-dev`, `libpq5`, `curl`, and `tini` installed.
  - Multi-stage build isolates compilation toolchains from runtime layer.

### 2.3 Secrets Protection
- Zero credentials or tokens in Git repository or `.env.staging.example`.
- All production and staging credentials injected dynamically via AWS Secrets Manager at container runtime.
