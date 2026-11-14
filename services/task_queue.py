import time
import uuid
import random
import logging
import traceback
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import timedelta
from django.utils import timezone
from django.db import transaction, models
from analytics.models import DurableTaskJob

logger = logging.getLogger('skillsphere.tasks')

# Registry for task handlers: task_name -> callable(payload)
TASK_HANDLERS = {}

class BaseTaskQueueBackend(ABC):
    """Abstract provider-independent background task queue interface."""
    @abstractmethod
    def enqueue(
        self,
        task_name: str,
        payload: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: int = 60,
        execute_now: bool = False
    ) -> Any:
        pass


class DatabaseTaskQueueBackend(BaseTaskQueueBackend):
    """PostgreSQL-backed transactional task queue for zero-dependency persistence."""
    def enqueue(
        self,
        task_name: str,
        payload: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: int = 60,
        execute_now: bool = False
    ) -> Any:
        return enqueue_task(
            task_name=task_name,
            payload=payload,
            idempotency_key=idempotency_key,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            execute_now=execute_now
        )


_ACTIVE_BACKEND: BaseTaskQueueBackend = DatabaseTaskQueueBackend()

def get_task_queue_backend() -> BaseTaskQueueBackend:
    """Returns active provider-independent task queue backend."""
    return _ACTIVE_BACKEND

def set_task_queue_backend(backend: BaseTaskQueueBackend):
    """Configures active backend (e.g. for Celery, Redis RQ, SQS, or Cloud Tasks)."""
    global _ACTIVE_BACKEND
    _ACTIVE_BACKEND = backend

def register_task(task_name):
    """Decorator to register a function as a durable task handler."""
    def decorator(fn):
        TASK_HANDLERS[task_name] = fn
        return fn
    return decorator


def enqueue_task(
    task_name: str,
    payload: dict = None,
    idempotency_key: str = None,
    max_retries: int = 3,
    timeout_seconds: int = 60,
    execute_now: bool = False
) -> DurableTaskJob:
    """
    Durable, idempotent background task enqueuer.
    Guarantees persistence in PostgreSQL, surviving application crashes or worker restarts.
    """
    if payload is None:
        payload = {}

    if idempotency_key:
        existing = DurableTaskJob.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            if existing.status == 'failed' and existing.retries < existing.max_retries:
                # Allow re-triggering failed task
                existing.status = 'pending'
                existing.error_message = ''
                existing.save(update_fields=['status', 'error_message'])
            return existing

    job = DurableTaskJob.objects.create(
        task_name=task_name,
        payload=payload,
        idempotency_key=idempotency_key or '',
        status='pending',
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
    )

    if execute_now:
        execute_job(job)

    return job


def execute_job(job: DurableTaskJob, worker_id: Optional[str] = None) -> bool:
    """
    Executes a single job with timeout protection, retries, and dead-letter handling.
    Enforces atomic worker fencing: stale or zombie workers cannot overwrite results
    if their lease expired and the job was reassigned to another worker.
    """
    handler = TASK_HANDLERS.get(job.task_name)
    if not handler:
        job.status = 'failed'
        job.error_message = f"No handler registered for task '{job.task_name}'"
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error_message', 'completed_at'])
        return False

    claimed_worker_id = worker_id or job.worker_id
    if not claimed_worker_id:
        fencing_token = uuid.uuid4().hex[:12]
        claimed_worker_id = f"sync_worker#{fencing_token}"

    if job.id:
        db_job = DurableTaskJob.objects.filter(id=job.id).values('status', 'worker_id').first()
        if db_job:
            if db_job['status'] == 'running':
                if db_job['worker_id'] and db_job['worker_id'] != claimed_worker_id:
                    logger.warning(
                        f"[TaskQueue:Fencing] Zombie worker execution aborted! Worker '{claimed_worker_id}' lease expired "
                        f"or job [{job.task_id}] is actively owned by '{db_job['worker_id']}'."
                    )
                    return False
            else:
                rows = DurableTaskJob.objects.filter(id=job.id, status=db_job['status']).update(
                    status='running',
                    started_at=timezone.now(),
                    worker_id=claimed_worker_id
                )
                if rows == 0:
                    logger.warning(f"[TaskQueue:Fencing] Failed to transition job [{job.task_id}] to running.")
                    return False
                job.status = 'running'
                job.worker_id = claimed_worker_id
        else:
            job.status = 'running'
            job.started_at = timezone.now()
            job.worker_id = claimed_worker_id
            job.save(update_fields=['status', 'started_at', 'worker_id'])
    else:
        job.status = 'running'
        job.started_at = timezone.now()
        job.worker_id = claimed_worker_id
        job.save()

    start_t = time.perf_counter()
    try:
        handler(job.payload)
        now = timezone.now()

        # Atomic fencing verification: update status ONLY if this worker still owns the running lease
        rows_updated = DurableTaskJob.objects.filter(
            id=job.id,
            status='running',
            worker_id=claimed_worker_id
        ).update(
            status='completed',
            completed_at=now,
            error_message=''
        )
        if rows_updated == 0:
            logger.warning(
                f"[TaskQueue:Fencing] Zombie worker detected! Worker '{claimed_worker_id}' lease expired "
                f"and task [{job.task_id}] was claimed by another worker. Stale completion write aborted."
            )
            return False

        # Synchronize in-memory job object
        job.status = 'completed'
        job.completed_at = now
        job.error_message = ''

        logger.info(f"Task {job.task_name} [{job.task_id}] succeeded in {(time.perf_counter() - start_t)*1000:.1f}ms")
        return True
    except Exception as e:
        dur = (time.perf_counter() - start_t) * 1000.0
        err_str = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        now = timezone.now()

        # Check if this worker still holds the lease before updating failure/retries
        current = DurableTaskJob.objects.filter(id=job.id, status='running', worker_id=claimed_worker_id).first()
        if not current:
            logger.warning(
                f"[TaskQueue:Fencing] Zombie worker failure write rejected for task [{job.task_id}]. "
                f"Ownership has been reassigned to a newer worker."
            )
            return False

        current.retries += 1
        if current.retries >= current.max_retries:
            current.status = 'dead_letter'
            logger.error(f"Task {current.task_name} [{current.task_id}] moved to DEAD_LETTER after {current.retries} attempts: {e}")
        else:
            current.status = 'failed'
            # Canonical full-jitter exponential backoff:
            base_delay = 5.0
            cap = 300.0
            backoff_limit = min(cap, base_delay * (2 ** current.retries))
            backoff_delay = random.uniform(0.0, backoff_limit)
            current.scheduled_at = now + timedelta(seconds=backoff_delay)
            logger.warning(
                f"Task {current.task_name} [{current.task_id}] failed (attempt {current.retries}/{current.max_retries}). "
                f"Rescheduled with full-jitter backoff in {backoff_delay:.1f}s (cap={backoff_limit:.1f}s): {e}"
            )

        current.error_message = err_str[:3000]
        current.completed_at = now
        current.save(update_fields=['status', 'retries', 'error_message', 'completed_at', 'scheduled_at'])

        # Synchronize in-memory job object
        job.status = current.status
        job.retries = current.retries
        job.completed_at = current.completed_at
        job.scheduled_at = current.scheduled_at
        job.error_message = current.error_message
        return False


def renew_job_lease(job_id: Any, fencing_token: str, extension_seconds: int = 60) -> bool:
    """
    Extends the lease duration for an in-flight job, preventing another worker
    from reclaiming the job while a long-running task is still actively making progress.
    """
    now = timezone.now()
    rows = DurableTaskJob.objects.filter(
        id=job_id,
        status='running'
    ).filter(
        models.Q(worker_id=fencing_token) | models.Q(worker_id__endswith=f"#{fencing_token}")
    ).update(started_at=now)
    return rows > 0


def recover_expired_leases(lease_grace_seconds: int = 30) -> int:
    """
    Recovers orphaned jobs from crashed workers or terminated containers.
    Inspects running jobs whose started_at exceeds their individual timeout_seconds + grace.
    Atomically increments retries, schedules full-jitter exponential backoff, or moves
    to dead_letter if max_retries has been reached. Never loses a job permanently.
    Returns count of recovered jobs.
    """
    recovered_count = 0
    now = timezone.now()

    # Find running jobs whose execution lease has expired
    running_jobs = list(
        DurableTaskJob.objects.filter(
            status='running',
            started_at__isnull=False
        ).select_for_update(skip_locked=True)
    )

    for job in running_jobs:
        lease_duration = timedelta(seconds=max(30, job.timeout_seconds + lease_grace_seconds))
        if job.started_at and (now - job.started_at) > lease_duration:
            job.retries += 1
            if job.retries >= job.max_retries:
                job.status = 'dead_letter'
                job.error_message = (
                    f"Worker lease expired (worker '{job.worker_id}' crashed or terminated). "
                    f"Job exceeded max retries ({job.retries}/{job.max_retries})."
                )
                logger.error(f"[TaskQueue:Recovery] Job {job.task_name} [{job.task_id}] moved to DEAD_LETTER after lease expiry.")
            else:
                job.status = 'failed'
                base_delay = 5.0
                cap = 300.0
                backoff_limit = min(cap, base_delay * (2 ** job.retries))
                backoff_delay = random.uniform(0.0, backoff_limit)
                job.scheduled_at = now + timedelta(seconds=backoff_delay)
                job.error_message = (
                    f"Worker lease expired (worker '{job.worker_id}' timed out or crashed). "
                    f"Attempt {job.retries}/{job.max_retries}. Rescheduled in {backoff_delay:.1f}s."
                )
                logger.warning(
                    f"[TaskQueue:Recovery] Recovered stalled job {job.task_name} [{job.task_id}] "
                    f"from worker '{job.worker_id}'. Rescheduled with jitter."
                )

            job.completed_at = now
            job.save(update_fields=['status', 'retries', 'error_message', 'completed_at', 'scheduled_at'])
            recovered_count += 1

    return recovered_count


def process_next_job(worker_id: str = 'default_worker') -> bool:
    """
    Claims and processes the next pending job atomically using select_for_update(skip_locked=True).
    Attaches a unique fencing token on claim to guard against zombie worker overwrites.
    Honors scheduled_at timestamps with exponential backoff and jitter.
    Automatically recovers orphaned jobs from crashed workers prior to claiming.
    Returns True if a job was found and processed, False if queue is empty.
    """
    with transaction.atomic():
        # 1. Recover any expired leases from crashed workers
        recover_expired_leases(lease_grace_seconds=30)

        # 2. Claim next available job atomically across parallel workers
        job = (
            DurableTaskJob.objects.select_for_update(skip_locked=True)
            .filter(
                status__in=['pending', 'failed'],
                retries__lt=models.F('max_retries'),
                scheduled_at__lte=timezone.now()
            )
            .order_by('scheduled_at', 'created_at')
            .first()
        )

        if not job:
            return False

        # Claim the job with unique worker fencing token
        fencing_token = uuid.uuid4().hex[:12]
        claimed_worker_id = f"{worker_id}#{fencing_token}"
        job.status = 'running'
        job.started_at = timezone.now()
        job.worker_id = claimed_worker_id
        job.save(update_fields=['status', 'started_at', 'worker_id'])

    # Execute outside transaction so failures don't roll back status updates
    return execute_job(job, worker_id=claimed_worker_id)


def get_queue_health() -> dict:
    """Returns queue telemetry and health metrics."""
    counts = dict(
        DurableTaskJob.objects.values('status')
        .annotate(cnt=models.Count('id'))
        .values_list('status', 'cnt')
    )
    oldest_pending = DurableTaskJob.objects.filter(status='pending').order_by('created_at').first()
    oldest_age_seconds = None
    if oldest_pending:
        oldest_age_seconds = int((timezone.now() - oldest_pending.created_at).total_seconds())

    return {
        'pending': counts.get('pending', 0),
        'running': counts.get('running', 0),
        'completed': counts.get('completed', 0),
        'failed': counts.get('failed', 0),
        'dead_letter': counts.get('dead_letter', 0),
        'total': sum(counts.values()),
        'oldest_pending_age_seconds': oldest_age_seconds,
        'healthy': (counts.get('pending', 0) < 5000 and (oldest_age_seconds or 0) < 300),
    }


def cleanup_completed_jobs(retention_days: int = 7, batch_size: int = 500) -> dict:
    """
    Cleans up eligible completed jobs older than retention_days in bounded batches.
    PRESERVES:
    - Pending and scheduled jobs (NEVER deleted).
    - Running jobs (NEVER deleted).
    - Failed and dead_letter jobs (preserved for debugging/telemetry).
    - Idempotency records within retention window.
    Avoids long-running table locks by deleting in chunks of batch_size.
    Returns summary dict with total cleaned and batch count.
    """
    cutoff = timezone.now() - timedelta(days=retention_days)
    total_cleaned = 0
    batches = 0

    while True:
        # Fetch chunk of IDs to avoid locking large tables
        ids_to_delete = list(
            DurableTaskJob.objects.filter(
                status='completed',
                completed_at__lt=cutoff
            ).values_list('id', flat=True)[:batch_size]
        )

        if not ids_to_delete:
            break

        deleted_count, _ = DurableTaskJob.objects.filter(id__in=ids_to_delete).delete()
        total_cleaned += deleted_count
        batches += 1

        if len(ids_to_delete) < batch_size:
            break

    logger.info(f"[TaskQueue:Cleanup] Removed {total_cleaned} completed jobs older than {retention_days} days in {batches} batches.")
    return {
        'cleaned_completed': total_cleaned,
        'batches': batches,
        'retention_days': retention_days
    }

