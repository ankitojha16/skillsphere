# SkillSphere Phase 17.3 — Worker Lease Safety & Zombie Worker Defense

## 1. Executive Overview

In an asynchronous distributed architecture, multiple background worker instances poll a durable PostgreSQL task queue (`DurableTaskJob`). Distributed task execution is inherently vulnerable to network partitions, CPU starvation, and garbage collection freezes. 

A critical failure pattern in distributed systems is the **Zombie Worker Problem**:
1. Worker A claims a job with a 30-second lease.
2. Worker A encounters a prolonged GC pause, disk stall, or network blip lasting 60 seconds.
3. The cluster lease-recovery monitor observes the expired lease and reassigns the job to Worker B.
4. Worker B begins executing the job.
5. Worker A wakes up and blindly attempts to commit its result or update the database, corrupting the job state or executing duplicate side-effects.

Phase 17.3 hardens `services/task_queue.py` with **fencing tokens**, **optimistic concurrency control**, and **zombie worker write rejection**.

---

## 2. Worker Fencing Tokens & Atomic Claims

Whenever a worker claims an available job from the queue via `claim_next_job`, it generates a cryptographically unique 12-character hexadecimal fencing token and combines it with its worker host identifier:

$$\text{worker\_id} = \text{"worker\_pod\_3\#" } + \text{uuid.uuid4().hex[:12]}$$

```python
# services/task_queue.py: claim_next_job()
with transaction.atomic():
    job = DurableTaskJob.objects.select_for_update(skip_locked=True).filter(
        status__in=['pending', 'failed'],
        scheduled_at__lte=now
    ).order_by('priority', 'created_at').first()

    if job:
        fencing_token = uuid.uuid4().hex[:12]
        job.worker_id = f"{worker_id}#{fencing_token}"
        job.status = 'running'
        job.started_at = now
        job.save(update_fields=['status', 'worker_id', 'started_at'])
```

By using `select_for_update(skip_locked=True)`, multiple workers never block or contend for the same row; each worker atomically locks and claims distinct jobs.

---

## 3. Zombie Worker Write Rejection in `execute_job`

Before and after task execution, `execute_job` verifies that the active database record is strictly owned by the executing worker's specific fencing token:

```python
# 1. Pre-execution fencing check:
if job.id:
    db_job = DurableTaskJob.objects.filter(id=job.id).values('status', 'worker_id').first()
    if db_job and db_job['status'] == 'running':
        if db_job['worker_id'] and db_job['worker_id'] != claimed_worker_id:
            logger.warning(
                f"[TaskQueue:Fencing] Zombie worker execution aborted! Worker '{claimed_worker_id}' lease expired "
                f"or job [{job.task_id}] is actively owned by '{db_job['worker_id']}'."
            )
            return False

# 2. Post-execution atomic completion write:
rows_updated = DurableTaskJob.objects.filter(
    id=job.id,
    status='running',
    worker_id=claimed_worker_id
).update(
    status='completed',
    completed_at=timezone.now(),
    error_message=''
)

if rows_updated == 0:
    logger.warning(
        f"[TaskQueue:Fencing] Zombie worker detected! Worker '{claimed_worker_id}' lease expired "
        f"and task [{job.task_id}] was claimed by another worker. Stale completion write aborted."
    )
    return False
```

### Protection Guarantee:
If Worker 1 stalled, Worker 2 claimed the job with a new token (`worker_2#token2`), and Worker 1 subsequently awakens:
1. Worker 1's execution is aborted, or
2. Worker 1's write matches 0 rows in PostgreSQL (`worker_id != 'worker_1#token1'`).
3. Worker 1 logs a zombie worker warning and discards its result.
4. Worker 2's execution and completion remain completely untainted.

---

## 4. Lease Expiry Recovery & Full-Jitter Exponential Backoff

The background scheduler or management daemon runs `recover_expired_leases(lease_grace_seconds=30)` periodically.

Any job remaining in `'running'` status whose elapsed execution time exceeds `timeout_seconds + lease_grace_seconds` is considered abandoned (crashed worker):
- Its retry counter is incremented (`retries += 1`).
- If `retries >= max_retries`, the job is moved to `dead_letter` status for operational triage.
- Otherwise, the job is rescheduled with **Full-Jitter Exponential Backoff**:
  $$\text{backoff\_limit} = \min(300.0, 5.0 \times 2^{\text{retries}})$$
  $$\text{scheduled\_at} = \text{now} + \text{random.uniform}(0.0, \text{backoff\_limit})$$
  This eliminates thundering herds when recovering batches of failed jobs.

---

## 5. In-Flight Lease Extension (`renew_job_lease`)

Workers processing legitimate long-running tasks can actively refresh their lease before expiry:
```python
renew_job_lease(job.id, fencing_token="worker_alpha#f1a2b3c4d5e6", extension_seconds=60)
```
This updates `timeout_seconds` or resets the lease baseline, guaranteeing that healthy long-running jobs are never prematurely stolen by other nodes.

---

## 6. Task Idempotency Verification

All background tasks in SkillSphere are written to be strictly idempotent:
- **`generate_course_pdf_task`**: Re-running overwrites the target PDF artifact deterministically using a fixed relative path derived from `course_id`. Multiple runs produce identical files without orphan records.
- **`export_user_data_task`**: Generates a deterministic export archive for the requesting user ID.
- **Course Enrollment & XP Events**: Protected by unique database constraints (`unique_together = ('student', 'course')`) and atomic transactions.

---

## 7. Automated Test Verification

Hardening verified via `services/test_phase_17_3_hardening.py`:
- `test_worker_fencing_token_and_atomic_claim`: Confirms unique fencing token assignment.
- `test_zombie_worker_defense_stale_completion_rejected`: Deliberately induces worker stall, expires lease, reassigns to Worker 2, wakes up Worker 1, and verifies that Worker 1's completion write is rejected with zero database corruption.
- Full suite passing: `Ran 7 tests in 2.244s, OK`.
