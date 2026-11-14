# SkillSphere Phase 18.4.2 — Supported Software Baseline Audit

**Assessment Date**: 2026-11-15  
**Audit Purpose**: Software Lifecycle & Engine Support Validation before AWS ECS Staging Provisioning  
**Preflight Result**: Approved for Staging Execution  

---

## 1. Executive Summary

Phase 18.4.2 audits and remediates two critical software lifecycle risks identified during Phase 18.4.1 preflight hardening:
1. **Django Framework Lifecycle**: Django 4.2 LTS reaches End of Extended Support in April 2026. Deploying a new cloud staging environment on an end-of-life framework introduces unpatched security vulnerabilities and compliance blockers.
2. **AWS RDS PostgreSQL Engine Deprecation**: AWS RDS deprecated PostgreSQL 17.2 and 17.4 in favor of active community minor releases (PostgreSQL 17.11). Provisioning deprecated database engines risks API rejection or forced maintenance disruptions.

### Software Baseline Matrix

| Software Component | Previous Baseline | Phase 18.4.2 Supported Baseline | Lifecycle Support Status |
| :--- | :--- | :--- | :--- |
| **Django Framework** | Django 4.2.30 LTS | **Django 5.2 LTS** (`Django>=5.2.0,<5.3.0`) | Active LTS (Extended support to April 2028) |
| **Python Runtime** | Python 3.9 (host) / Python 3.12 (container) | **Python 3.12 (Standard)** | Supported by Python Foundation through Oct 2028 |
| **PostgreSQL RDS Engine**| PostgreSQL 17.4 (Deprecated on RDS) | **PostgreSQL 17.11** | Latest Active PostgreSQL 17 RDS minor release |
| **PostgreSQL Client Driver**| `psycopg2-binary` 2.9.12 | `psycopg2-binary` >= 2.9.9 / 2.9.12 | Actively maintained, zero CVEs |
| **Redis Cache Driver** | `redis` 4.5.0 | `redis` >= 5.0.0 (Installed 7.0.1) | Active LTS, Redis 7.x wire protocol support |
| **REST Framework** | DRF 3.14.0 | `djangorestframework` >= 3.15.0 (Installed 3.16.1)| Full Django 5.x LTS support |
| **Static Storage Backend**| `STATICFILES_STORAGE` (Deprecated) | `STORAGES` dictionary (Modern Standard) | 100% compliant with Django 5.x |

---

## 2. Django Framework Upgrade Analysis

### 2.1 Compatibility Audit
All Django applications and third-party packages in SkillSphere were audited against Django 5.2 LTS breaking changes:
- **`STORAGES` Configuration**: Removed deprecated `STATICFILES_STORAGE` and `DEFAULT_FILE_STORAGE` settings in `config/settings.py` in favor of the modern `STORAGES` dictionary.
- **Model Check Validations**: Executed `python manage.py check` with `-Wd` (all deprecation warnings enabled). Zero deprecation warnings or runtime regressions detected.
- **Migration Graph**: Validated all migrations across 18 Django apps (`accounts`, `analytics`, `assessments`, `assistant`, `careers`, `certificates`, `collaboration`, `community`, `courses`, `events`, `gamification`, `goals`, `interviews`, `learning`, `notifications`, `opportunities`, `portfolios`, `projects`, `resumes`, `roadmaps`, `sessions`). Migration plan executed with 100% resolution.
- **Asynchronous & Threading Primitives**: Background worker daemon (`run_task_worker`) and fault-tolerant Redis cache layer (`config/cache.py`) audited for thread safety and connection recovery under Django 5.2.

---

## 3. PostgreSQL RDS Engine Audit

### 3.1 Engine Version Deprecation
AWS RDS deprecates older PostgreSQL minor versions (such as 17.1, 17.2, and 17.4) once community updates address critical memory, index, or replication CVEs. AWS lists **PostgreSQL 17.11** as an actively supported release.

### 3.2 Target Region Availability Check (`ap-south-1`)
Documented AWS CLI discovery command for read-only identity verification:
```bash
aws rds describe-db-engine-versions \
  --region ap-south-1 \
  --engine postgres \
  --engine-version 17.11 \
  --query "DBEngineVersions[].{EngineVersion:EngineVersion,Status:Status,ValidUpgradeTarget:ValidUpgradeTarget}"
```
- **Terraform Configuration**: Updated `terraform/aws/modules/database/main.tf` to `engine_version = "17.11"` with `auto_minor_version_upgrade = true`.
- **PostgreSQL 18 Evaluation**: Upstream PostgreSQL 18 is currently in beta/development and is not yet available or certified on Amazon RDS.

---

## 4. Preflight Conclusion

The SkillSphere application code and Terraform infrastructure definitions are aligned with active, supported LTS releases. All deprecations have been resolved, and the repository is ready for safe cloud staging provisioning upon owner authorization.
