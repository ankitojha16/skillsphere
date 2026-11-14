"""
SkillSphere Enterprise Observability & Site Reliability Engineering (SRE) Service
Provider-independent telemetry, APM metrics, latency percentiles, and OpenTelemetry/Prometheus exporters.
"""

import time
import os
import math
import logging
from typing import Dict, Any, List
from django.core.cache import cache
from django.utils import timezone
from django.db import connection

logger = logging.getLogger('skillsphere.observability')

class MetricsCollector:
    """
    Distributed telemetry collector tracking throughput, status codes,
    p50/p95/p99 latency percentiles, cache hit-rates, and database pool health.
    Compatible with OpenTelemetry and Prometheus standards.
    """
    METRICS_PREFIX = 'metrics:v1'

    @classmethod
    def record_request(cls, method: str, path_prefix: str, status_code: int, duration_ms: float):
        """Records an HTTP request event for telemetry aggregation."""
        try:
            minute_bucket = int(time.time() // 60)
            key = f"{cls.METRICS_PREFIX}:{minute_bucket}"

            # Aggregate counters in cache
            stats = cache.get(key, {'requests': 0, 'errors': 0, 'latencies': []})
            stats['requests'] += 1
            if status_code >= 400:
                stats['errors'] += 1

            # Sample latencies (keep up to 200 samples per minute for fast percentile computation)
            if len(stats['latencies']) < 200:
                stats['latencies'].append(duration_ms)

            cache.set(key, stats, timeout=3600)  # Retain 1 hour of rolling minute stats
        except Exception:
            pass

    @classmethod
    def record_cache_hit(cls):
        try:
            cache.incr(f"{cls.METRICS_PREFIX}:cache_hits")
        except Exception:
            pass

    @classmethod
    def record_cache_miss(cls):
        try:
            cache.incr(f"{cls.METRICS_PREFIX}:cache_misses")
        except Exception:
            pass

    @classmethod
    def get_system_metrics(cls) -> Dict[str, Any]:
        """Collects real-time system, database, cache, and task queue health."""
        now = time.time()
        minute_bucket = int(now // 60)

        # 1. Aggregate last 5 minutes of request traffic
        total_requests = 0
        total_errors = 0
        latencies = []

        for b in range(minute_bucket - 4, minute_bucket + 1):
            stats = cache.get(f"{cls.METRICS_PREFIX}:{b}")
            if stats:
                total_requests += stats.get('requests', 0)
                total_errors += stats.get('errors', 0)
                latencies.extend(stats.get('latencies', []))

        latencies.sort()
        n = len(latencies)
        p50 = round(latencies[int(n * 0.50)], 2) if n else 0.0
        p95 = round(latencies[int(n * 0.95)], 2) if n else 0.0
        p99 = round(latencies[int(n * 0.99)], 2) if n else 0.0
        error_rate = round((total_errors / total_requests * 100.0), 2) if total_requests else 0.0

        # 2. Database Probe & Latency
        db_ok = True
        db_latency_ms = 0.0
        try:
            t0 = time.perf_counter()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        except Exception as e:
            db_ok = False
            logger.error(f"[Observability] DB probe error: {e}")

        # 3. Cache Metrics
        cache_hits = cache.get(f"{cls.METRICS_PREFIX}:cache_hits", 0)
        cache_misses = cache.get(f"{cls.METRICS_PREFIX}:cache_misses", 0)
        total_cache_ops = cache_hits + cache_misses
        hit_ratio = round((cache_hits / total_cache_ops * 100.0), 2) if total_cache_ops else 100.0

        # 4. Background Task Queue Health
        from services.task_queue import get_queue_health
        queue_health = get_queue_health()

        return {
            'timestamp': timezone.now().isoformat(),
            'window_minutes': 5,
            'traffic': {
                'requests_last_5m': total_requests,
                'errors_last_5m': total_errors,
                'error_rate_percent': error_rate,
                'rps_rolling': round(total_requests / 300.0, 2),
            },
            'latency_percentiles_ms': {
                'p50': p50,
                'p95': p95,
                'p99': p99,
            },
            'database': {
                'connected': db_ok,
                'probe_latency_ms': db_latency_ms,
                'vendor': connection.vendor,
            },
            'cache': {
                'hits': cache_hits,
                'misses': cache_misses,
                'hit_ratio_percent': hit_ratio,
            },
            'queue': queue_health,
            'alerts': cls._evaluate_alerts(error_rate, p95, db_ok, queue_health)
        }

    @classmethod
    def _evaluate_alerts(cls, error_rate: float, p95_latency: float, db_ok: bool, queue_health: dict) -> List[Dict[str, str]]:
        alerts = []
        if not db_ok:
            alerts.append({'severity': 'CRITICAL', 'name': 'DatabaseUnreachable', 'message': 'Primary database probe failed.'})
        if error_rate > 2.0:
            alerts.append({'severity': 'WARNING', 'name': 'HighErrorRate', 'message': f'Error rate is {error_rate}% (>2.0%).'})
        if p95_latency > 800.0:
            alerts.append({'severity': 'WARNING', 'name': 'HighLatencyP95', 'message': f'p95 latency is {p95_latency}ms (>800ms).'})
        if queue_health.get('pending', 0) > 1000:
            alerts.append({'severity': 'WARNING', 'name': 'QueueBacklogHigh', 'message': 'Over 1,000 pending tasks in queue.'})
        if queue_health.get('dead_letter', 0) > 20:
            alerts.append({'severity': 'WARNING', 'name': 'DeadLetterHigh', 'message': 'Over 20 tasks moved to dead letter.'})
        return alerts

    @classmethod
    def to_prometheus_format(cls) -> str:
        """Exports metrics in OpenMetrics / Prometheus exposition format."""
        m = cls.get_system_metrics()
        lines = [
            "# HELP skillsphere_requests_total Total HTTP requests in 5m window",
            "# TYPE skillsphere_requests_total counter",
            f"skillsphere_requests_total {m['traffic']['requests_last_5m']}",
            "# HELP skillsphere_errors_total Total HTTP errors in 5m window",
            "# TYPE skillsphere_errors_total counter",
            f"skillsphere_errors_total {m['traffic']['errors_last_5m']}",
            "# HELP skillsphere_latency_p50_ms 50th percentile latency in ms",
            "# TYPE skillsphere_latency_p50_ms gauge",
            f"skillsphere_latency_p50_ms {m['latency_percentiles_ms']['p50']}",
            "# HELP skillsphere_latency_p95_ms 95th percentile latency in ms",
            "# TYPE skillsphere_latency_p95_ms gauge",
            f"skillsphere_latency_p95_ms {m['latency_percentiles_ms']['p95']}",
            "# HELP skillsphere_latency_p99_ms 99th percentile latency in ms",
            "# TYPE skillsphere_latency_p99_ms gauge",
            f"skillsphere_latency_p99_ms {m['latency_percentiles_ms']['p99']}",
            "# HELP skillsphere_db_latency_ms Database probe latency in ms",
            "# TYPE skillsphere_db_latency_ms gauge",
            f"skillsphere_db_latency_ms {m['database']['probe_latency_ms']}",
            "# HELP skillsphere_queue_pending_tasks Tasks currently waiting in queue",
            "# TYPE skillsphere_queue_pending_tasks gauge",
            f"skillsphere_queue_pending_tasks {m['queue']['pending']}",
            "# HELP skillsphere_queue_dead_letter_tasks Dead letter tasks total",
            "# TYPE skillsphere_queue_dead_letter_tasks gauge",
            f"skillsphere_queue_dead_letter_tasks {m['queue']['dead_letter']}",
        ]
        return "\n".join(lines) + "\n"
