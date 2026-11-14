# SkillSphere Phase 17.2 — State Management & Process-Local Inventory Audit

## 1. Audit Overview & Objectives

In a multi-instance production environment, application state must be categorized by scope to ensure data consistency, prevent lost updates, and eliminate memory leaks.

This audit inspects every Django application, service, middleware, model, view, and task in the SkillSphere repository. Every identified stateful construct is classified into one of four action categories:
1. **Safe Process-Local**: State that protects or measures only local worker threads, has no cross-process correctness implications, and is safe across independent instances.
2. **Must Use Shared Storage**: Persistent data or binary artifacts that must be accessible by all nodes regardless of which instance serviced the initial request.
3. **Must Use Distributed Coordination**: Operations where race conditions across multiple instances could cause double execution, over-allocation, or data inconsistency.
4. **Must Be Redesigned**: Inadequate single-process constructs replaced with resilient, crash-safe patterns.

---

## 2. Complete Inventory of Stateful Constructs

| Location | Construct | Current Nature | Classification | Multi-Instance Behavior & Resolution |
| :--- | :--- | :--- | :--- | :--- |
| `services/resilience.py` | `Bulkhead._semaphore` | `threading.BoundedSemaphore` | **Safe Process-Local** | Protects individual worker thread pool from starvation. For fleet limits, `DistributedBulkhead` is provided. |
| `services/resilience.py` | `CircuitBreaker._lock` | `threading.Lock` | **Safe Process-Local** | Protects internal state transitions within a single worker process; shared state is synced to Redis. |
| `services/resilience.py` | `CircuitBreaker` state | In-memory + Cache key | **Hybrid / Distributed** | Shared cache key coordinates fleet tripping. Fallback to process-local memory if Redis drops. |
| `services/observability.py` | `_local_requests`, `_local_errors` | In-memory integer counters | **Safe Process-Local** | Worker-local monotonic counters. Scraped by Prometheus and aggregated via PromQL (`sum(rate(...))`). |
| `services/observability.py` | `_local_latencies` | `collections.deque(maxlen=1000)` | **Safe Process-Local** | Bounded rolling sample per process. Eliminates cross-instance lock contention for high-frequency telemetry. |
| `services/observability.py` | `_local_histogram` | In-memory dictionary | **Safe Process-Local** | Local bucket counter tagged with `instance="{id}"` during Prometheus scrape. |
| `services/observability.py` | Minute-bucket metrics | `cache.incr()` | **Distributed Coordination** | Atomic Redis increments aggregate fleet-wide throughput without read-modify-write lost updates. |
| `services/task_queue.py` | `TASK_HANDLERS` | Global dictionary | **Safe Process-Local** | Read-only dispatch registry populated at boot time during Django application initialization. |
| `services/task_queue.py` | `DurableTaskJob` | PostgreSQL database table | **Shared Storage** | Jobs stored in PostgreSQL with `select_for_update(skip_locked=True)` for atomic cross-worker claiming. |
| `services/task_queue.py` | Worker Leases | `job.started_at` & `timeout` | **Must Be Redesigned (Done)** | Replaced static 10m timeout with per-job lease expiry in `recover_expired_leases()` to survive node crashes. |
| `services/storage_service.py`| File storage | `BaseStorageService` | **Must Use Shared Storage (Done)** | Replaced bare filesystem writes with provider-independent cloud storage abstraction (`S3CompatibleStorageService`). |
| `config/middleware.py` | `_thread_locals` | `threading.local()` | **Safe Process-Local** | Stores correlation ID for the duration of a single HTTP request thread. Cleaned up at response time. |
| `django.contrib.sessions` | User Sessions | Database (`django_session`) | **Shared Storage** | Session state is shared across all nodes via database backed session engine. |
| `courses/views.py` | Assessment Idempotency | DB-backed attempt lookup | **Distributed Coordination** | 5s submission replay window and atomic attempt count inside `transaction.atomic()`. |
| `gamification/services.py` | XP Awards | `XPTransaction` (Unique Key) | **Distributed Coordination** | Database unique constraint on `(user_id, activity_key)` prevents double awards across parallel requests. |
| `learning/views.py` | Lesson Toggle | `LessonProgress` (Unique Key) | **Distributed Coordination** | Explicit desired state with inner atomic savepoint catching `IntegrityError`. |
| `courses/models.py` | Enrollment | `UniqueConstraint(user, course)` | **Distributed Coordination** | Strict database uniqueness prevents double-enrollment under concurrent HTTP requests. |

---

## 3. Analysis of Critical State Boundaries

### 3.1 Circuit Breaker Multi-Instance Independence vs Coordination
In SkillSphere, a circuit breaker for an external dependency (such as Gemini AI) operates in a **hybrid model**:
- **Why Process-Local Protection is Retained**: If an instance loses network connectivity to Redis, the circuit breaker must not throw an unhandled exception or disable fault tolerance. It degrades seamlessly to its in-memory state.
- **Why Distributed State is Synchronized**: When Redis is available, failure events increment a shared key (`circuit_breaker:gemini_api:failures`). When the threshold is reached by any combination of nodes, all nodes reading the shared cache see `OPEN` state, shielding the wounded dependency fleet-wide.
- **Probe Permitting in HALF_OPEN**: When transitioning from `OPEN` to `HALF_OPEN`, only a single trial request is permitted per instance (`_trial_in_progress = True`). If multiple instances probe simultaneously, the external dependency receives at most $N_{\text{instances}}$ probes, well within upstream recovery thresholds.

### 3.2 Bulkhead Capacity Accounting
A process-local `Bulkhead` controls concurrency per Python process. 
- In an architecture with $N$ instances each running $W$ worker processes, the total maximum concurrency is:
  $$C_{\text{total}} = N \times W \times C_{\text{local}}$$
- For strict fleet-wide concurrency ceilings (e.g. rate-limited external partners permitting at most 50 concurrent connections globally), `DistributedBulkhead` (`services/resilience.py`) coordinates atomic token sets in Redis with lease timeouts (TTL 30s) to prevent permit leaks if a worker terminates abruptly.

### 3.3 Task Queue Worker Safety
Background processing does not rely on an in-memory queue.
- Jobs are persisted to `analytics_durabletaskjob` in PostgreSQL.
- Parallel worker processes claim jobs using `select_for_update(skip_locked=True)`, which is fully concurrency-safe in PostgreSQL.
- Stalled jobs resulting from crashed nodes (e.g., Kubernetes eviction, SIGKILL) are detected by `recover_expired_leases()` and safely re-queued with exponential backoff and randomized jitter.

---

## 4. Verification & Audit Outcome
All identified stateful components have been audited, classified, and refactored where necessary. No undocumented global mutable state remains that would cause data corruption or inconsistencies when running multiple application instances.
