# SkillSphere Phase 17.2 — Database Capacity & Connection Pool Engineering

## 1. Executive Summary & Production Baseline

SkillSphere uses PostgreSQL (hosted on Supabase) with **PgBouncer** connection pooling in transaction mode.

When scaling horizontally across multiple independent application instances, database connection exhaustion is the primary failure mode if connection lifecycles are unmanaged. Phase 17.2 establishes connection budgets, statement timeouts, query boundary guidelines, and PgBouncer compatibility rules.

### Current Production Data Baseline (Zero Data Loss Verified)
- **Users**: 3
- **Student Profiles**: 3
- **Courses**: 69
- **Course Modules**: 276
- **Lessons**: 1,104
- **Enrollments**: 17
- **Assessments**: 131
- **Assessment Questions**: 775
- **Lesson Progress Records**: 84
- **Certificates**: 6
- **XP Transactions**: 84

---

## 2. Connection Pool Architecture & PgBouncer Optimization

```
     [ App Instance 1 ]      [ App Instance 2 ]     ...     [ App Instance N ]
       (4 WSGI Workers)        (4 WSGI Workers)               (4 WSGI Workers)
              │                       │                              │
              └───────────────────────┼──────────────────────────────┘
                                      │
                                      ▼
                        [ PgBouncer Connection Pooler ]
                             (Port 6543, Transaction Mode)
                                      │ (Max Pool: 25 - 60)
                                      ▼
                       [ PostgreSQL Database Engine ]
                            (Managed Supabase Server)
```

### 2.1 PgBouncer Transaction Pooling Compatibility
In PgBouncer transaction mode (`port 6543`), a server connection is assigned to a client only for the duration of a single database transaction or query. As soon as the transaction commits or aborts, the connection returns to the pool.
- **Server-Side Cursors Disabled**: Django normally attempts to create named server-side cursors for large querysets. In transaction pooling mode, named cursors persist beyond transaction boundaries and cause `psycopg2.OperationalError: prepared statement does not exist`.
  - **Resolution (`config/settings.py`)**:
    ```python
    default_db['DISABLE_SERVER_SIDE_CURSORS'] = True
    ```
- **Connection Max Age**:
  - In serverless/stateless environments: `CONN_MAX_AGE = 0` ensures sockets are closed cleanly after each request cycle, preventing connection pileups.
  - In containerized deployments (Docker/K8s): `CONN_MAX_AGE = 60` with `conn_health_checks=True` allows connection reuse without lingering stale sockets.

### 2.2 Connection Timeout & Defense-in-Depth
To guarantee that a slow query or network glitch cannot tie up connection slots:
1. **Connect Timeout**: `connect_timeout = 5s` (fast failure if database or pooler is unreachable).
2. **Statement Timeout**: `-c statement_timeout=10000` (hard 10-second ceiling on any single SQL execution). Any runaway query is terminated by PostgreSQL before exhausting worker threads.

---

## 3. Mathematical Connection Budget & Sizing Model

Let:
- $N$ = Number of application instances.
- $W$ = Number of worker processes per instance (e.g. 4 Gunicorn workers).
- $P_{\text{server}}$ = PostgreSQL maximum server connections (e.g. 60 on Supabase Small, 300 on Pro).
- $P_{\text{pool}}$ = PgBouncer pool capacity.

### Without PgBouncer (Session Mode)
Each worker holds an open connection:
$$Connections_{\text{needed}} = N \times W$$
With $N = 20$ instances and $W = 4$ workers:
$$Connections = 20 \times 4 = 80 > 60 \implies \text{Database Connection Starvation (HTTP 500)}$$

### With PgBouncer (Transaction Mode)
Connections are only occupied during active query execution ($T_{\text{query}} \approx 2\text{ms}$ to $15\text{ms}$).
For throughput of $R$ total requests per second, the average number of active database connections required is:
$$Conns_{\text{active}} = R \times T_{\text{query}}$$
At $R = 500\text{ RPS}$ with average query duration $T_{\text{query}} = 5\text{ms} = 0.005\text{s}$:
$$Conns_{\text{active}} = 500 \times 0.005 = 2.5\text{ active connections!}$$
With a pool size of $P_{\text{pool}} = 25$, PgBouncer easily handles 500+ dynamic RPS across dozens of app instances.

---

## 4. Query Efficiency & N+1 Prevention

| Endpoint / Model | Query Optimization Applied | Index Protection |
| :--- | :--- | :--- |
| **Course Catalogue** | `Course.objects.filter(is_published=True).select_related('category')` | `course_pub_created_idx`, `course_cat_pub_idx` |
| **Course Detail** | `prefetch_related('modules__lessons', 'assessments')` | `module_course_order_idx`, `lesson_course_order_idx` |
| **Student Dashboard** | `Enrollment.objects.select_related('course').prefetch_related('user__lesson_progress')` | `enrollment_user_course_idx` |
| **Task Queue Claim** | `DurableTaskJob.objects.select_for_update(skip_locked=True)` | `task_status_sched_idx` |
| **Certificate View** | `Certificate.objects.select_related('user', 'course')` | `cert_user_course_idx` |

---

## 5. Migration Safety Policy
No destructive migrations were introduced during Phase 17.2. All existing schema structures, column constraints, and foreign key relations are intact and backward-compatible.
