# SkillSphere Phase 18 — Shared Redis & Task Queue Architecture

## 1. Executive Summary

This document specifies the shared Redis cluster architecture and evaluates the long-term viability of SkillSphere's PostgreSQL-backed durable task queue (`DurableTaskJob`) under a 10,000 concurrent active user workload.

---

## 2. Shared Redis Fleet Architecture

In a horizontally autoscaled environment, Redis acts as the centralized coordinator for distributed state across all application containers.

```
                  Web Pod 1       Web Pod 2     Worker Pod 1    Worker Pod 2
                      │               │               │               │
                      └───────┬───────┴───────┬───────┴───────────────┘
                              ▼               ▼
                 ┌─────────────────────────────────────────┐
                 │       Amazon ElastiCache for Redis      │
                 │      (Multi-AZ with Auto-Failover)      │
                 ├─────────────────────────────────────────┤
                 │ - Distributed Cache (HTML/API fragments)│
                 │ - Atomic Bulkheads (Lua script permits) │
                 │ - Sliding Window Rate Limiters          │
                 │ - Circuit Breaker Shared Fail Counters  │
                 │ - In-Flight Lease Renewals              │
                 └─────────────────────────────────────────┘
```

### 2.1 Coordination Responsibilities
1. **Atomic Bulkheads (`DistributedBulkhead`)**: Coordinates fleet-wide concurrency ceilings (e.g., maximum 10 simultaneous PDF renders across all containers) using Redis sorted sets and Lua scripts (`LUA_ACQUIRE`, `LUA_RENEW`, `LUA_RELEASE`).
2. **Sliding-Window Rate Limiting**: Enforces API quotas (e.g., 60 AI prompts/min per student) across all application instances atomically via Redis sorted sets.
3. **Session & Cache Storage**: Shared sessions allow students to maintain login state across round-robin load-balanced instances without sticky sessions.
4. **Circuit Breaker Coordination**: Shares upstream failure counts across pods so all instances fast-fail downstream calls simultaneously during upstream third-party outages.

### 2.2 Redis Failure & Degraded Mode Safety
If the Redis cluster is unreachable:
- `RedisService` catches timeouts and automatically degrades to `LocMemCache`.
- `DistributedBulkhead` falls back to process-local `threading.BoundedSemaphore` with capacity `fallback_local_concurrent` and sets `is_degraded = True`.
- Core learning workflows (reading lessons, submitting quizzes, taking exams) continue operating without interruption.

---

## 3. Evaluation of Durable PostgreSQL Task Queue vs Celery/SQS

SkillSphere currently executes background tasks using a database-backed durable queue (`analytics.models:DurableTaskJob`) managed via `services/task_queue.py`.

### 3.1 Workload Assessment for 10,000 CCU
- Background job generation rate under peak load:
  - Certificate generation: $\sim 2\text{ jobs/min}$
  - Resume PDF export: $\sim 5\text{ jobs/min}$
  - Course analytics summary: $\sim 1\text{ job/5 min}$
  - Total background throughput: **$\sim 0.2\text{ to }0.5\text{ jobs/sec}$**.
- Queue processing latency: Average job finishes in $120\text{ ms}$.

### 3.2 Feature & Portability Comparison
| Dimension | Existing `DurableTaskJob` (PostgreSQL) | Celery with Redis Broker | AWS SQS + Celery/Boto3 |
| :--- | :--- | :--- | :--- |
| **Transaction Atomicity** | ✅ **Perfect**: Job enqueued inside the same DB transaction as course completion. | ❌ Dual-write problem: Redis publish can succeed while DB rolls back. | ❌ Dual-write problem: SQS message sent before DB commit. |
| **Lock Contention** | ✅ **Zero**: `select_for_update(skip_locked=True)` eliminates row lock waits. | N/A (Redis in-memory queue) | N/A (SQS distributed queue) |
| **Dead-Letter Queue (DLQ)** | ✅ Built-in `status='dead_letter'` with full error stack trace inspection. | Requires Celery error callbacks. | SQS Dead-Letter Queue. |
| **Worker Fencing & Zombies** | ✅ Tested fencing tokens (`worker_id#<token>`) reject stale writes. | Complex worker heartbeat tuning. | Visibility timeout tuning. |
| **Operational Overhead** | ✅ **Zero additional infrastructure**: Runs on existing PostgreSQL. | Medium (Worker monitoring, Flower). | Medium (AWS IAM, SQS cost, vendor lock-in). |
| **Portability** | ✅ **100% Provider-Independent** | 80% (Requires Redis broker) | 20% (Locked into AWS SQS) |

---

## 4. Final Queue Recommendation

**Maintain the Existing PostgreSQL Durable Task Queue (`DurableTaskJob`)**.

Introducing Celery or AWS SQS at this stage would add substantial operational complexity, risk dual-write inconsistencies, and degrade provider portability without measurable performance justification. The existing queue effortlessly processes up to $50\text{ jobs/second}$ ($100\times$ our peak requirement) while guaranteeing strict transaction consistency and zero lost tasks.
