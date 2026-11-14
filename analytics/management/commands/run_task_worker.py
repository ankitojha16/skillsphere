import os
import sys
import time
import signal
import socket
import uuid
import logging
from django.core.management.base import BaseCommand
from services.task_queue import (
    process_next_job,
    recover_expired_leases,
    get_queue_health,
)

logger = logging.getLogger('skillsphere.tasks.worker')


class Command(BaseCommand):
    help = 'Runs the SkillSphere durable background task queue worker daemon'

    def add_arguments(self, parser):
        parser.add_argument(
            '--worker-id',
            type=str,
            default=None,
            help='Explicit identifier for this worker instance (default: auto-generated)'
        )
        parser.add_argument(
            '--poll-interval',
            type=float,
            default=0.5,
            help='Sleep interval in seconds when queue has active work (default: 0.5s)'
        )
        parser.add_argument(
            '--idle-interval',
            type=float,
            default=2.0,
            help='Sleep interval in seconds when queue is empty (default: 2.0s)'
        )
        parser.add_argument(
            '--max-tasks',
            type=int,
            default=0,
            help='Maximum number of tasks to process before exiting (0 for indefinite)'
        )

    def handle(self, *args, **options):
        # Determine worker identity
        hostname = socket.gethostname()
        worker_id = options.get('worker_id') or os.getenv('WORKER_ID') or f"worker_{hostname}_{uuid.uuid4().hex[:8]}"
        poll_interval = options['poll_interval']
        idle_interval = options['idle_interval']
        max_tasks = options['max_tasks']

        self.stdout.write(self.style.SUCCESS(
            f"[*] Starting SkillSphere Task Worker [{worker_id}] (PID: {os.getpid()})"
        ))
        logger.info(f"[TaskWorker] Initializing worker [{worker_id}] on host {hostname}")

        # Graceful shutdown handler
        stop_requested = [False]

        def handle_signal(sig, frame):
            sig_name = 'SIGTERM' if sig == signal.SIGTERM else 'SIGINT'
            self.stdout.write(self.style.WARNING(
                f"\n[!] Received {sig_name}. Initiating graceful shutdown for [{worker_id}]..."
            ))
            logger.info(f"[TaskWorker] Received {sig_name}. Finishing current job before stopping.")
            stop_requested[0] = True

        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

        # Initial queue health check
        health = get_queue_health()
        logger.info(f"[TaskWorker] Initial queue health: {health}")

        tasks_processed = 0
        last_recovery_time = time.monotonic()

        while not stop_requested[0]:
            try:
                # Periodically recover expired leases from dead/preempted workers (every 60s)
                now = time.monotonic()
                if now - last_recovery_time >= 60.0:
                    recovered = recover_expired_leases(lease_grace_seconds=30)
                    if recovered > 0:
                        logger.warning(f"[TaskWorker] Recovered {recovered} orphaned tasks from dead workers.")
                    last_recovery_time = now

                # Claim and process the next pending job atomically
                processed = process_next_job(worker_id=worker_id)
                if processed:
                    tasks_processed += 1
                    if max_tasks > 0 and tasks_processed >= max_tasks:
                        logger.info(f"[TaskWorker] Reached maximum task budget of {max_tasks}. Exiting cleanly.")
                        break
                    time.sleep(poll_interval)
                else:
                    # Queue is empty, back off to reduce database polling load
                    time.sleep(idle_interval)

            except Exception as e:
                logger.error(f"[TaskWorker] Unexpected error in polling loop: {e}", exc_info=True)
                time.sleep(idle_interval)

        self.stdout.write(self.style.SUCCESS(
            f"[+] Worker [{worker_id}] stopped cleanly. Processed {tasks_processed} tasks."
        ))
        logger.info(f"[TaskWorker] Worker [{worker_id}] terminated gracefully. Total processed: {tasks_processed}")
