"""
SkillSphere Enterprise Observability & Site Reliability Engineering (SRE) Service
Provider-independent telemetry, APM metrics, latency percentiles, and OpenTelemetry/Prometheus exporters.

SCOPE & ARCHITECTURAL CLARITY:
- Counters: Distributed via atomic cache increments (`cache.incr`) with thread-safe process-local fallback.
  Multiple workers update independent atomic keys, eliminating read-modify-write lost updates.
- Histogram Buckets: Distributed aggregatable Prometheus histogram buckets (10ms to 5000ms).
- Rolling Latencies: Thread-safe bounded in-memory ring buffer (1,000 samples) per worker process for rolling percentiles.
- Resilience: If Redis or database fails, metrics collection degrades to local in-memory structures without failing user requests.
"""

import time
import os
import math
import socket
import logging
import threading
from collections import deque
from typing import Dict, Any, List
from django.core.cache import cache
from django.utils import timezone
from django.db import connection

logger = logging.getLogger('skillsphere.observability')

# Standard Prometheus latency buckets in milliseconds
LATENCY_BUCKETS = [10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0]

class MetricsCollector:
    """
    SRE Telemetry collector tracking throughput, status codes,
    rolling p50/p95/p99 latency percentiles, cache hit-rates, and database pool health.
    Compatible with OpenTelemetry and Prometheus standards.
    """
    METRICS_PREFIX = 'metrics:v2'
    _lock = threading.Lock()
    _local_requests = 0
    _local_errors = 0
    _local_latencies = deque(maxlen=1000)
    _local_histogram = {b: 0 for b in LATENCY_BUCKETS}
    _local_histogram['+Inf'] = 0

    @classmethod
    def record_request(cls, method: str, path_prefix: str, status_code: int, duration_ms: float):
        """
        Records an HTTP request event using atomic increments to prevent read-modify-write races.
        Records into Prometheus histogram buckets and bounded in-memory rolling sample.
        """
        minute_bucket = int(time.time() // 60)

        # 1. Process-local thread-safe recording (guaranteed to succeed)
        with cls._lock:
            cls._local_requests += 1
            if status_code >= 400:
                cls._local_errors += 1
            cls._local_latencies.append(duration_ms)

            # Histogram bucket increment
            bucket_matched = False
            for b in LATENCY_BUCKETS:
                if duration_ms <= b:
                    cls._local_histogram[b] += 1
                    bucket_matched = True
                    break
            if not bucket_matched:
                cls._local_histogram['+Inf'] += 1

        # 2. Distributed atomic cache recording (if Redis available)
        try:
            req_key = f"{cls.METRICS_PREFIX}:{minute_bucket}:requests"
            cache.incr(req_key)
        except ValueError:
            # Key does not exist yet; initialize with 1 and 1-hour TTL
            try:
                cache.set(req_key, 1, timeout=3600)
            except Exception:
                pass
        except Exception:
            pass

        if status_code >= 400:
            try:
                err_key = f"{cls.METRICS_PREFIX}:{minute_bucket}:errors"
                cache.incr(err_key)
            except ValueError:
                try:
                    cache.set(err_key, 1, timeout=3600)
                except Exception:
                    pass
            except Exception:
                pass

    @classmethod
    def record_cache_hit(cls):
        """Records cache hit via atomic increment."""
        try:
            cache.incr(f"{cls.METRICS_PREFIX}:cache_hits")
        except ValueError:
            try:
                cache.set(f"{cls.METRICS_PREFIX}:cache_hits", 1, timeout=86400)
            except Exception:
                pass
        except Exception:
            pass

    @classmethod
    def record_cache_miss(cls):
        """Records cache miss via atomic increment."""
        try:
            cache.incr(f"{cls.METRICS_PREFIX}:cache_misses")
        except ValueError:
            try:
                cache.set(f"{cls.METRICS_PREFIX}:cache_misses", 1, timeout=86400)
            except Exception:
                pass
        except Exception:
            pass

    @classmethod
    def get_system_metrics(cls) -> Dict[str, Any]:
        """Collects real-time system, database, cache, and task queue health."""
        now = time.time()
        minute_bucket = int(now // 60)

        # 1. Aggregate request counts across last 5 minute buckets
        total_requests = 0
        total_errors = 0

        for b in range(minute_bucket - 4, minute_bucket + 1):
            try:
                reqs = cache.get(f"{cls.METRICS_PREFIX}:{b}:requests")
                if reqs is not None:
                    total_requests += int(reqs)
                errs = cache.get(f"{cls.METRICS_PREFIX}:{b}:errors")
                if errs is not None:
                    total_errors += int(errs)
            except Exception:
                pass

        # Fallback to local worker metrics if cache was empty or down
        if total_requests == 0:
            with cls._lock:
                total_requests = cls._local_requests
                total_errors = cls._local_errors

        # 2. Rolling latency percentiles from bounded ring buffer
        with cls._lock:
            samples = sorted(list(cls._local_latencies))

        n = len(samples)
        p50 = round(samples[int(n * 0.50)], 2) if n else 0.0
        p95 = round(samples[int(n * 0.95)], 2) if n else 0.0
        p99 = round(samples[int(n * 0.99)], 2) if n else 0.0
        error_rate = round((total_errors / total_requests * 100.0), 2) if total_requests else 0.0

        # 3. Database Probe & Latency
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

        # 4. Cache Hit/Miss Metrics
        cache_hits = 0
        cache_misses = 0
        try:
            cache_hits = int(cache.get(f"{cls.METRICS_PREFIX}:cache_hits") or 0)
            cache_misses = int(cache.get(f"{cls.METRICS_PREFIX}:cache_misses") or 0)
        except Exception:
            pass

        total_cache_ops = cache_hits + cache_misses
        hit_ratio = round((cache_hits / total_cache_ops * 100.0), 2) if total_cache_ops else 100.0

        # 5. Background Task Queue Health
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
                'sample_size': n,
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
    def get_instance_id(cls) -> str:
        """
        Returns stable unique instance identifier for multi-instance Prometheus scraping.
        Uses SKILLSPHERE_INSTANCE_ID if set, else hostname_pid.
        """
        return os.environ.get('SKILLSPHERE_INSTANCE_ID') or f"{socket.gethostname()}_{os.getpid()}"

    @classmethod
    def to_prometheus_format(cls) -> str:
        """
        Exports metrics in OpenMetrics / Prometheus exposition format with histograms
        and instance labels to support multi-node scraping and fleet aggregation.
        """
        m = cls.get_system_metrics()
        inst = cls.get_instance_id()

        lines = [
            "# HELP skillsphere_instance_info Metadata about application instance",
            "# TYPE skillsphere_instance_info gauge",
            f'skillsphere_instance_info{{instance="{inst}"}} 1',
            "# HELP skillsphere_requests_total Total HTTP requests in 5m window",
            "# TYPE skillsphere_requests_total counter",
            f'skillsphere_requests_total{{instance="{inst}"}} {m["traffic"]["requests_last_5m"]}',
            "# HELP skillsphere_instance_requests_cumulative Monotonic cumulative HTTP requests for this process",
            "# TYPE skillsphere_instance_requests_cumulative counter",
            f'skillsphere_instance_requests_cumulative{{instance="{inst}"}} {cls._local_requests}',
            "# HELP skillsphere_errors_total Total HTTP errors in 5m window",
            "# TYPE skillsphere_errors_total counter",
            f'skillsphere_errors_total{{instance="{inst}"}} {m["traffic"]["errors_last_5m"]}',
            "# HELP skillsphere_instance_errors_cumulative Monotonic cumulative HTTP errors for this process",
            "# TYPE skillsphere_instance_errors_cumulative counter",
            f'skillsphere_instance_errors_cumulative{{instance="{inst}"}} {cls._local_errors}',
            "# HELP skillsphere_latency_p50_ms 50th percentile latency in ms",
            "# TYPE skillsphere_latency_p50_ms gauge",
            f'skillsphere_latency_p50_ms{{instance="{inst}"}} {m["latency_percentiles_ms"]["p50"]}',
            "# HELP skillsphere_latency_p95_ms 95th percentile latency in ms",
            "# TYPE skillsphere_latency_p95_ms gauge",
            f'skillsphere_latency_p95_ms{{instance="{inst}"}} {m["latency_percentiles_ms"]["p95"]}',
            "# HELP skillsphere_latency_p99_ms 99th percentile latency in ms",
            "# TYPE skillsphere_latency_p99_ms gauge",
            f'skillsphere_latency_p99_ms{{instance="{inst}"}} {m["latency_percentiles_ms"]["p99"]}',
            "# HELP skillsphere_db_latency_ms Database probe latency in ms",
            "# TYPE skillsphere_db_latency_ms gauge",
            f'skillsphere_db_latency_ms{{instance="{inst}"}} {m["database"]["probe_latency_ms"]}',
            "# HELP skillsphere_queue_pending_tasks Tasks currently waiting in queue",
            "# TYPE skillsphere_queue_pending_tasks gauge",
            f"skillsphere_queue_pending_tasks {m['queue']['pending']}",
            "# HELP skillsphere_queue_dead_letter_tasks Dead letter tasks total",
            "# TYPE skillsphere_queue_dead_letter_tasks gauge",
            f"skillsphere_queue_dead_letter_tasks {m['queue']['dead_letter']}",
            "# HELP skillsphere_cache_hits_total Total distributed cache hits",
            "# TYPE skillsphere_cache_hits_total counter",
            f"skillsphere_cache_hits_total {m['cache']['hits']}",
            "# HELP skillsphere_cache_misses_total Total distributed cache misses",
            "# TYPE skillsphere_cache_misses_total counter",
            f"skillsphere_cache_misses_total {m['cache']['misses']}",
        ]

        # Prometheus histogram buckets with instance tags
        with cls._lock:
            hist_copy = dict(cls._local_histogram)
        cumulative = 0
        lines.append("# HELP skillsphere_http_request_duration_ms HTTP request duration histogram")
        lines.append("# TYPE skillsphere_http_request_duration_ms histogram")
        for b in LATENCY_BUCKETS:
            cumulative += hist_copy.get(b, 0)
            lines.append(f'skillsphere_http_request_duration_ms_bucket{{instance="{inst}",le="{b}"}} {cumulative}')
        cumulative += hist_copy.get('+Inf', 0)
        lines.append(f'skillsphere_http_request_duration_ms_bucket{{instance="{inst}",le="+Inf"}} {cumulative}')

        return "\n".join(lines) + "\n"
