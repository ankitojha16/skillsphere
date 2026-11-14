# SkillSphere Phase 18.3 — Database & Task Queue Production Validation

## 1. Database Sizing, Multiplexing & Connection Budget

SkillSphere separates client connection concurrency from physical database server connections through **PgBouncer** running in `transaction` pooling mode.

### 1.1 Complete Connection Budget Calculation

| Replica Fleet Tier | Max Replica Count | Threads per Replica | Total Client Connections | PgBouncer Inbound Capacity | Physical Database Server Connections |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Web Service (Fargate)** | 20 tasks | 16 threads (4w $\times$ 4t) | 320 | Accepted (within 500 limit) | Multiplexed into pooled server connections |
| **Worker Daemons (Fargate)** | 10 tasks | 2 threads | 20 | Accepted (within 500 limit) | Multiplexed into pooled server connections |
| **Ad-Hoc / Management** | 2 tasks | 1 thread | 2 | Accepted | Direct / Pooled |
| **Prometheus Exporters** | 2 tasks | 1 thread | 2 | Accepted | Direct / Pooled |
| **TOTAL CLIENT CONNECTIONS**| **34 tasks** | — | **344** | **Max 500 (`max_client_conn`)** | **<= 80 (`max_db_connections`)** |

### 1.2 Mathematical Headroom Proof
- Physical PostgreSQL Server `max_connections`: **100**.
- PgBouncer hard connection cap to PostgreSQL: **80**.
- Guaranteed Dedicated Headroom: $100 - 80 = 20$ connections (**20% safety margin**).
- Dedicated connections are reserved exclusively for superusers (`superuser_reserved_connections = 3`), schema migrations, and autovacuum workers, preventing total database lockout during traffic spikes.

---

## 2. Transaction Management & Query Guardrails

1. **Transaction Pooling Compatibility**:
   Django avoids session-level SQL features (`PREPARE`, temporary tables, or advisory locks across transactions) to ensure full compatibility with PgBouncer's `transaction` pool mode.
2. **Bounded Query Execution**:
   PostgreSQL enforces `statement_timeout = '30000ms'` (30 seconds) on application roles, terminating runaway table scans before they starve connection pools.
3. **Automated Backups & Point-in-Time Recovery (PITR)**:
   - Automated daily snapshots retained for 7 days.
   - Continuous WAL archiving to S3 enables point-in-time recovery to any second within the retention window.

---

## 3. Asynchronous Queue Concurrency & Fault Tolerance

The durable background task queue ([`services/task_queue.py`](file:///Users/ankitkumar/Desktop/wealthtrack/AnkitPortfolio/skill%20sphare/services/task_queue.py) and [`analytics/models.py`](file:///Users/ankitkumar/Desktop/wealthtrack/AnkitPortfolio/skill%20sphare/analytics/models.py)) provides at-least-once processing guarantees:

```
[ Task Enqueued ] ──> [ Status: PENDING ]
                             │
                             ▼ Atomic Lock: SELECT FOR UPDATE SKIP LOCKED
                     [ Status: RUNNING ]
                     Worker receives: worker_pod_X#fencing_token_XYZ
                     Lease valid for 30 seconds
                             │
       ┌─────────────────────┴─────────────────────┐
       ▼                                           ▼
[ Normal Completion ]                     [ Worker SIGKILL Crash ]
Lease token validated.                    Lease expires after 30 seconds.
Result written.                           Sibling worker runs recover_expired_leases().
Status: COMPLETED.                        Attempt count incremented.
                                          Job rescheduled with exponential jitter.
                                          If original worker awakes (Zombie):
                                          Fencing token mismatch -> WRITE REJECTED!
```

### 3.1 Dead-Letter Queue (DLQ) Handling
- When a task fails repeatedly, it backs off exponentially:
  $$\text{Backoff} = \min(300, 2^{\text{attempt}} \times 2) \pm \text{jitter}$$
- After exceeding `max_retries` (default: 3), the task transitions to `status = 'dead_letter'`.
- DLQ alerts are published to CloudWatch / Prometheus for SRE investigation without blocking pending tasks in the queue.
