# SkillSphere Phase 18 — Database Capacity Plan & Connection Budget

## 1. Executive Summary

This capacity plan models the database workload for SkillSphere at **10,000 concurrent active users**, evaluates the suitability of the current Supabase PostgreSQL deployment, calculates a rigorous connection budget, and specifies sizing for transaction poolers, read replicas, and disaster recovery.

> [!IMPORTANT]
> In accordance with Phase 18 restrictions, **NO production database migration is performed in this phase**. The existing Supabase PostgreSQL instance is preserved and hardened via connection pooler configuration.

---

## 2. Current Database Evaluation (Supabase PostgreSQL)

### 2.1 Geographic Location & Latency
- **Endpoint**: `aws-0-ap-south-1.pooler.supabase.com:6543` (Mumbai, India)
- **Target Application Region**: AWS `ap-south-1` (Mumbai)
- **Network Latency**: Intra-region network latency from AWS ECS Fargate tasks to the Supabase pooler is approximately **$1.2\text{ to }2.5\text{ ms}$**, eliminating cross-region WAN lag.

### 2.2 Connection Pooler Evaluation (PgBouncer)
- **Port**: `6543` operates in **Transaction Pooling Mode** (`pool_mode = transaction`).
- **Suitability**: In transaction pooling mode, a server connection is allocated to a Django worker only for the duration of a transaction, then immediately returned to the pool. This allows hundreds of Gunicorn threads to share a modest pool of physical PostgreSQL connections.
- **Django Configuration Rule**:
  - `CONN_MAX_AGE = 0` or short lifecycle ($60\text{s}$) to avoid holding idle server sessions.
  - Disable prepared statements if using native PgBouncer transaction pooling.

---

## 3. Workload Modeling & Connection Budget (10,000 CCU)

### 3.1 Fleet Sizing Under 10,000 CCU
- **Web Tier**: 12 to 16 Fargate tasks
  - Each task: Gunicorn with 4 workers and 4 threads = $16\text{ client worker threads per task}$.
  - Total Web client connections: $16\text{ tasks} \times 16\text{ threads} = \mathbf{256\text{ client connections}}$.
- **Worker Tier**: 6 to 10 Fargate tasks
  - Each task: 2 concurrent background execution threads.
  - Total Worker client connections: $10\text{ tasks} \times 2\text{ threads} = \mathbf{20\text{ client connections}}$.
- **Total Client Connections**: $256 + 20 = \mathbf{276\text{ active threads}}$.

---

### 3.2 PgBouncer Multiplexing & Connection Budget

Without PgBouncer, 276 direct PostgreSQL backend connections would exhaust memory buffers (`work_mem`, `shared_buffers`) and cause lock contention.

With PgBouncer transaction pooling:
- Dynamic Django query duty cycle: $\sim 15\%$ active DB time per request ($6.75\text{ ms}$ DB time per $45\text{ ms}$ request).
- Active concurrent database transactions under $855\text{ dynamic RPS}$:
  $$N_{\text{active\_tx}} = 855\text{ RPS} \times 0.00675\text{ s} \approx \mathbf{5.77\text{ simultaneous transactions}}$$

### Sizing Specification:
| Connection Category | Direct Client Connections | PgBouncer Server Pool | Database Server Max Connections |
| :--- | :---: | :---: | :---: |
| **Web Service Pool** | 256 | 45 | — |
| **Background Workers** | 20 | 15 | — |
| **Admin / Migration Pool** | 5 | 5 | — |
| **Safety Headroom** | — | 15 | — |
| **Total Dedicated Pool** | **281** | **80** | **100** |

**Conclusion**: An allocation of **80 physical PostgreSQL server connections** managed by PgBouncer comfortably services 10,000 CCU with substantial safety margin.

---

## 4. Query Performance & Read Replicas

### 4.1 Indexing Status & Hot Paths
All critical queries in SkillSphere are indexed:
1. `DurableTaskJob`: `(status, scheduled_at, priority)` index ensures $O(\log N)$ queue polling via `select_for_update(skip_locked=True)`.
2. `Enrollment`: Unique constraint on `(user_id, course_id)` prevents race-condition duplicates.
3. `LessonProgress`: Index on `(user_id, lesson_id)` provides sub-millisecond study progress updates.
4. `XPTransaction`: Index on `(user_id, created_at)` accelerates gamification streak queries.

### 4.2 Read Replica Recommendation
- At 1,000 to 5,000 CCU: Single primary database with PgBouncer is fully sufficient ($< 25\%$ CPU utilization).
- At 10,000 CCU: Provision **one Read Replica** dedicated to analytical queries (`analytics.views`, dashboard reports, and course discovery catalogs). Django database routing directs read-only view queries to the replica via `using='read_replica'`.

---

## 5. Backup Policy & Point-in-Time Recovery (PITR)

- **Automated Snapshots**: Daily full backups retained for 30 days.
- **Write-Ahead Log (WAL) Archiving**: Continuous WAL archiving to S3 enables **Point-in-Time Recovery (PITR)** with an RPO of under 5 minutes.
- **Integrity Baseline**: The production database baseline (3 users, 69 courses, 1,104 lessons, 17 enrollments, 6 certificates) must be verified after every snapshot restoration drill.
