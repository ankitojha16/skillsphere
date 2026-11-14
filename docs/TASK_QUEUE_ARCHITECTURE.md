# SkillSphere Durable Background Task Queue Architecture

## 1. Provider-Independent Task Queue Design

SkillSphere implements an asynchronous task abstraction (`BaseTaskQueueBackend` in `services/task_queue.py`) that decouples application business logic from underlying queue providers.

### Supported Queue Adapters
1. **`DatabaseTaskQueueBackend` (Default)**:
   - Uses PostgreSQL `DurableTaskJob` table with `select_for_update(skip_locked=True)`.
   - Zero additional infrastructure required.
   - Survives process restarts and guarantees $100\%$ transactional persistence.
2. **`CeleryTaskQueueBackend`**:
   - Dispatches tasks via Celery protocol to Redis or RabbitMQ brokers.
3. **Cloud Queues (AWS SQS / Google Cloud Tasks)**:
   - Configurable by setting `set_task_queue_backend(CloudTasksBackend())`.

---

## 2. Guarantees & State Machine

```
[ Enqueue Task ] ──> PENDING (scheduled_at = now)
                           │
                           ▼ (Worker claims via select_for_update)
                        RUNNING
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
        [ Success ]                 [ Failure ]
        COMPLETED                        │
                               (attempts < max_retries?)
                               ┌─────────┴─────────┐
                               ▼                   ▼
                            FAILED             DEAD_LETTER
                     (backoff with jitter)  (manual triage)
                               │
                               ▼
                       Rescheduled in DB
```

### Exponential Backoff with Randomized Full Jitter
When a task encounters an error, it is rescheduled into the future:
$$\text{delay} = (2^{\text{retries}} \times \text{base\_delay}) + \text{jitter}$$
- `base_delay`: 5.0 seconds
- `jitter`: Uniform random float between 0.1s and 2.0s
- **Example Delays**:
  - Attempt 1: ~10.5s – 12.0s
  - Attempt 2: ~20.5s – 22.0s
  - Attempt 3: ~40.5s – 42.0s
  - Attempt 4: Exceeds `max_retries` $\implies$ Marked `dead_letter` for SRE inspection.

---

## 3. Work Offloaded to Asynchronous Tasks
- **Heavy Document Generation**: Complex ReportLab certificate & resume compilation.
- **Bulk Communications**: Transactional emails, notification broadcasts.
- **Data Archive Exports**: Compiling multi-table JSON student archives.
- **Telemetry Aggregation**: Periodic rollup of 5-minute telemetry windows.
- **Housekeeping**: Pruning expired pair programming sessions and stale cache markers.
