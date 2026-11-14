# SkillSphere Phase 18.4 — Database Architecture & Validation Specification

**Target Database**: Amazon RDS for PostgreSQL  
**Engine Version**: `17.4`  
**Deployment Model**: RDS Multi-AZ DB Instance Deployment  
**Isolation State**: 100% Isolated from Production Supabase  

---

## 1. PostgreSQL Engine Version Evaluation

### 1.1 Why PostgreSQL 17.2 Was Deprecated
During the Phase 18.4 audit, AWS RDS release advisories confirmed that minor release `17.2` has been deprecated due to critical upstream PostgreSQL community fixes:
- Memory leak in logical replication slot tracking.
- Query planner regression on nested partition indexes.
- Security vulnerabilities addressed in community CVE advisories.

Deploying a deprecated minor version risks unexpected maintenance window upgrades, service interruptions, or provisioning failure from the AWS RDS API.

### 1.2 Selected Version: PostgreSQL 17.4
- **Engine**: `postgres`
- **Version String**: `17.4`
- **Auto Minor Upgrade**: Enabled (`true`) to receive bug and CVE fixes during scheduled maintenance.
- **Django LTS Compatibility**: Django 4.2 LTS natively supports PostgreSQL 12 through 17 via `psycopg2-binary` (>= 2.9.9) and `psycopg3`.
- **PostgreSQL 18 Evaluation**: PostgreSQL 18 is currently in active upstream development (beta expected late 2025/2026) and is **not yet supported or generally available on Amazon RDS**. PostgreSQL 17.4 is the latest, most stable production-grade release available in AWS `ap-south-1`.

### 1.3 PostgreSQL Extensions Verification
SkillSphere utilizes the following extensions, all confirmed supported in RDS PostgreSQL 17.4:
| Extension | Purpose | RDS 17.4 Compatibility |
| :--- | :--- | :--- |
| `uuid-ossp` | Primary key and transaction UUID generation | Supported |
| `pgcrypto` | Secure credential hashing and token digest calculations | Supported |
| `pg_trgm` | Trigram matching for fast course and skill searching | Supported |
| `btree_gist` | Multi-column exclusion constraints for schedule reservations | Supported |

---

## 2. Explicit Database Availability Architecture

To eliminate architectural ambiguity, AWS RDS provides two fundamentally distinct Multi-AZ deployment models. Below is an exhaustive comparison:

### Comparison: RDS Multi-AZ DB Instance vs RDS Multi-AZ DB Cluster

| Architectural Dimension | Model A: Multi-AZ DB Instance Deployment (Selected for Staging) | Model B: Multi-AZ DB Cluster Deployment (Target for Prod 10k CCU) |
| :--- | :--- | :--- |
| **Instance Count** | **2 instances total** (1 Primary + 1 Synchronous Standby) | **3 instances total** (1 Primary + 2 Readable Standbys) |
| **AZ Distribution** | Spans **2 Availability Zones** (e.g. `ap-south-1a`, `ap-south-1b`) | Spans **3 Availability Zones** (`ap-south-1a`, `ap-south-1b`, `ap-south-1c`) |
| **Replication Technology** | Synchronous physical block-level storage replication (EBS level) | PostgreSQL native streaming replication with quorum commit |
| **Read Capabilities of Standby** | **NO READS SERVED.** Standby is completely passive and closed to queries | **READS SERVED.** Both standby instances actively serve read queries |
| **Endpoints Provided** | **1 Endpoint** (Single DNS CNAME pointing to current primary) | **2 Endpoints** (1 Cluster Writer Endpoint + 1 Reader Load-Balanced Endpoint) |
| **Failover Duration** | **60 to 120 seconds** (DNS propagation + crash recovery) | **Sub-35 seconds** (Typically 10–25 seconds fast quorum promotion) |
| **Snapshot / Backup Impact** | Zero I/O suspension on primary (snapshots taken from standby) | Zero I/O suspension on primary (snapshots taken from standby) |
| **Cost Multiplier** | **~2.0x single instance cost** (~$95/mo for `db.t4g.medium`) | **~3.2x single instance cost** (~$380/mo minimum for `db.m6gd.large`) |
| **Read Scaling Capability** | Requires manual external Read Replicas (with distinct endpoints) | Built-in 2x read capacity out-of-the-box via reader endpoint |

### Architectural Decision for Staging:
SkillSphere selects **Model A: RDS Multi-AZ DB Instance Deployment** for staging because:
1. Staging workloads are caching-heavy (read requests are absorbed by ElastiCache Redis).
2. It thoroughly validates automated Multi-AZ failover and zero-downtime snapshots without incurring the substantial 3x compute cost ($380+/mo) of a 3-instance DB cluster.
3. **Standby Behavior Explicitly Acknowledged**: The standby instance does **not** serve read traffic. All web and worker tasks connect to the primary endpoint.

---

## 3. Database Connection Budget & Autoscaling Constraints

### 3.1 RDS Connection Sizing Formula
For an RDS PostgreSQL instance, the default `max_connections` is computed as:
$$\text{max\_connections} = \frac{\text{DBInstanceClassMemory (bytes)}}{9531392}$$
- On `db.t4g.medium` (4,096 MB RAM): $\approx 450$ max connections.
- On `db.r6g.xlarge` (32,768 MB RAM): $\approx 3,600$ max connections.

### 3.2 Connection Allocation Budget

| Service Tier | Task Count | Workers / Concurrency per Task | Connections per Task | Max Total Connections |
| :--- | :--- | :--- | :--- | :--- |
| **ECS Web (Baseline)** | 2 tasks | 2 Gunicorn workers + 4 threads | 8 connections | **16 connections** |
| **ECS Web (Max Autoscaling)** | 20 tasks | 2 Gunicorn workers + 4 threads | 8 connections | **160 connections** |
| **ECS Worker (Baseline)** | 2 tasks | 1 daemon process | 4 connections | **8 connections** |
| **ECS Worker (Max Autoscaling)** | 10 tasks | 1 daemon process | 4 connections | **40 connections** |
| **Admin & Migration Tasks** | 2 tasks | Ad-hoc CLI / migrations | 2 connections | **4 connections** |
| **Safety Reserve Buffer** | N/A | RDS internal processes & superuser | 50 connections | **50 connections** |
| **Peak Total Demand** | **32 tasks** | **Full Capacity Surge** | N/A | **260 connections** |

**Conclusion**: Peak application demand under maximum 20-web / 10-worker autoscaling is **260 connections**, comfortably within the **450 connection limit** of `db.t4g.medium` and well below `db.r6g.xlarge`. No connection saturation or starvation will occur.

---

## 4. Production/Staging Isolation Guarantee

### 4.1 Strict Architectural Separation
1. **Network**: Staging RDS resides in a private VPC subnet (`10.0.96.0/20`) inaccessible from the public internet (`publicly_accessible = false`).
2. **Credentials**: Staging uses an independent database instance (`skillsphere-staging-db`) with credentials managed exclusively in `skillsphere-staging-app-secrets`.
3. **Zero Production Cross-Talk**: Code audit confirmed zero hardcoded references to `aws-0-ap-south-1.pooler.supabase.com` in staging configurations.
4. **Synthetic Data**: Staging will be seeded exclusively with synthetic test accounts (`staging_student_1`, `staging_instructor_1`) and synthetic course fixtures. Under no circumstances will production Supabase records be imported, queried, or modified.
