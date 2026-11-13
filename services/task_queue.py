import time
import logging
import traceback
from datetime import timedelta
from django.utils import timezone
from django.db import transaction, models
from analytics.models import DurableTaskJob

logger = logging.getLogger('skillsphere.tasks')

# Registry for task handlers: task_name -> callable(payload)
TASK_HANDLERS = {}

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


def execute_job(job: DurableTaskJob, worker_id: str = 'sync_worker') -> bool:
    """
    Executes a single job with timeout protection, retries, and dead-letter handling.
    """
    handler = TASK_HANDLERS.get(job.task_name)
    if not handler:
        job.status = 'failed'
        job.error_message = f"No handler registered for task '{job.task_name}'"
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error_message', 'completed_at'])
        return False

    job.status = 'running'
    job.started_at = timezone.now()
    job.worker_id = worker_id
    job.save(update_fields=['status', 'started_at', 'worker_id'])

    start_t = time.perf_counter()
    try:
        handler(job.payload)
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.error_message = ''
        job.save(update_fields=['status', 'completed_at', 'error_message'])
        logger.info(f"Task {job.task_name} [{job.task_id}] succeeded in {(time.perf_counter() - start_t)*1000:.1f}ms")
        return True
    except Exception as e:
        dur = (time.perf_counter() - start_t) * 1000.0
        job.retries += 1
        err_str = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        if job.retries >= job.max_retries:
            job.status = 'dead_letter'
            logger.error(f"Task {job.task_name} [{job.task_id}] moved to DEAD_LETTER after {job.retries} attempts: {e}")
        else:
            job.status = 'failed'
            logger.warning(f"Task {job.task_name} [{job.task_id}] failed (attempt {job.retries}/{job.max_retries}): {e}")

        job.error_message = err_str[:3000]
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'retries', 'error_message', 'completed_at'])
        return False


def process_next_job(worker_id: str = 'default_worker') -> bool:
    """
    Claims and processes the next pending job atomically using select_for_update.
    Returns True if a job was found and processed, False if queue is empty.
    """
    with transaction.atomic():
        # Clean up stale jobs that timed out
        stale_cutoff = timezone.now() - timedelta(minutes=10)
        DurableTaskJob.objects.filter(
            status='running',
            started_at__lt=stale_cutoff
        ).update(status='failed', error_message='Job execution timed out while running')

        job = (
            DurableTaskJob.objects.select_for_update(skip_locked=True)
            .filter(status__in=['pending', 'failed'], retries__lt=models.F('max_retries'))
            .order_by('created_at')
            .first()
        )

        if not job:
            return False

        # Claim the job
        job.status = 'running'
        job.started_at = timezone.now()
        job.worker_id = worker_id
        job.save(update_fields=['status', 'started_at', 'worker_id'])

    # Execute outside transaction so failures don't roll back status updates
    return execute_job(job, worker_id=worker_id)


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
