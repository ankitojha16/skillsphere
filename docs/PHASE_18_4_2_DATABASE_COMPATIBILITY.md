# SkillSphere Phase 18.4.2 — Database Driver & RDS PostgreSQL Compatibility Specification

**Target Database**: Amazon RDS for PostgreSQL  
**Engine Version**: `17.11` (Multi-AZ DB Instance Deployment)  
**Database Driver**: `psycopg2-binary` 2.9.12 (`psycopg2-binary>=2.9.9`)  
**Pooling Strategy**: PgBouncer / RDS Proxy Compatible (`DISABLE_SERVER_SIDE_CURSORS = True`)  

---

## 1. Database Driver Compatibility Audit

SkillSphere utilizes `psycopg2-binary` (installed version: `2.9.12`), which is actively maintained and certified for PostgreSQL 12 through 17+ and Django 4.2/5.x.

### Driver Functional Validation Matrix

| Database Operation | Architectural Implementation | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **Connection Pooling** | `conn_max_age = 60` with `conn_health_checks = True` | Unit tests & settings audit | ✅ Verified |
| **Atomic Transactions** | `transaction.atomic()` context managers | XP transaction & enrollment tests | ✅ Verified |
| **Row Locking (`select_for_update`)** | Used in `TaskQueue.claim_job` and assessment attempts | Task queue concurrency tests | ✅ Verified |
| **Savepoint Handling** | Nested atomic blocks for payment & quiz retry | Error recovery test suite | ✅ Verified |
| **Unique Constraints** | `unique_project_user_request`, `unique_user_activity_xp` | Constraint violation tests | ✅ Verified |
| **PgBouncer Multiplexing**| `DISABLE_SERVER_SIDE_CURSORS = True` configured | Settings verification | ✅ Verified |
| **Connection Timeouts** | `connect_timeout = 5`, `statement_timeout = 10000ms` | Network drop simulation | ✅ Verified |

---

## 2. RDS PostgreSQL 17.11 Engine Verification

### 2.1 Why PostgreSQL 17.11 Was Selected
AWS RDS deprecates older PostgreSQL minor releases once community security advisories (CVEs) and stability fixes are published. PostgreSQL **17.11** is the current active supported release on Amazon RDS within the PostgreSQL 17 major version branch.

### 2.2 Regional Discovery Command (`ap-south-1`)
To query RDS engine version availability in the AWS Asia Pacific (Mumbai) region using a read-only IAM identity:

```bash
aws rds describe-db-engine-versions \
  --region ap-south-1 \
  --engine postgres \
  --engine-version 17.11 \
  --output table
```

Expected response attributes:
- `Engine`: `postgres`
- `EngineVersion`: `17.11`
- `Status`: `available`
- `SupportsMultiAZ`: `true`

---

## 3. PostgreSQL Extension Availability on RDS 17.11

SkillSphere relies on four standard PostgreSQL extensions. All four are verified as natively supported in Amazon RDS PostgreSQL 17.11:

| Extension Name | Extension Purpose in SkillSphere | RDS 17.11 Availability |
| :--- | :--- | :--- |
| **`uuid-ossp`** | Deterministic UUID generation for student certificates and task IDs | Supported |
| **`pgcrypto`** | Cryptographic hash digests for authentication tokens | Supported |
| **`pg_trgm`** | Trigram index matching (`GIN` / `GiST`) for fast skill and course search | Supported |
| **`btree_gist`** | Multicolumn exclusion constraints for schedule reservations | Supported |

### Extension Initialization Script
When the RDS instance is provisioned, Django migrations or an initial DBA script will enable the extensions:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
```

---

## 4. Elimination of Supabase-Specific Assumptions

1. **Host Configuration**: Staging uses a dedicated RDS endpoint injected via AWS Secrets Manager (`DATABASE_URL`), eliminating references to `aws-0-ap-south-1.pooler.supabase.com`.
2. **Port Handling**: Default RDS port `5432` is configured in security groups and connection strings (unlike Supabase PgBouncer pooler port `6543`).
3. **SSL Mode**: Staging enforces `sslmode=require` across all database connections, adhering to AWS RDS SSL/TLS security best practices.
