# SkillSphere Phase 17.1 — Telemetry & Metrics Mathematical Validation

---

## 1. Mathematical Grounding & Statistical Principles

To prevent statistical distortions across distributed application workers, SkillSphere’s telemetry layer strictly distinguishes three metric concepts:

1. **Distributed Atomic Counters (`cache.incr`)**:
   - Used for cumulative request counts (`requests_total`) and error counts (`errors_total`).
   - Atomic increments eliminate check-then-act read-modify-write race conditions.
2. **Prometheus Histogram Buckets (`skillsphere_http_request_duration_ms_bucket`)**:
   - Aggregatable across multiple application instances without storing raw latency arrays.
   - Buckets: `[10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, +Inf]`.
3. **Rolling Recent-Request Window**:
   - Implemented via a thread-safe bounded in-memory ring buffer (`collections.deque(maxlen=1000)`) per worker process.
   - Calculates exact rolling p50, p95, and p99 percentiles over the most recent 1,000 requests served by that worker.
   - Explicitly documented as a **rolling recent-request sample**, NOT a lifetime reservoir sample.

---

## 2. Cardinality Protection & Label Sanitization

- **Vulnerability**: In naive implementations, recording `request.path` (e.g. `/courses/python-1234/lessons/5678/`) generates unbounded unique metric labels ($O(U \times L)$ cardinality), exhausting Prometheus server memory.
- **Remediation**:
  - `PerformanceMonitoringMiddleware` normalizes paths using Django's URL resolver view name:
    ```python
    route_name = getattr(getattr(request, 'resolver_match', None), 'view_name', None)
    if not route_name:
        route_name = '/' + request.path.strip('/').split('/')[0] if request.path.strip('/') else '/'
    ```
  - Yields predictable, bounded cardinality: e.g. `courses:detail`, `learning:lesson_detail`, `dashboard:index`.

---

## 3. Sample Prometheus Exposition Format (`/api/metrics/`)

```
# HELP skillsphere_requests_total Total HTTP requests in 5m window
# TYPE skillsphere_requests_total counter
skillsphere_requests_total 1284
# HELP skillsphere_errors_total Total HTTP errors in 5m window
# TYPE skillsphere_errors_total counter
skillsphere_errors_total 2
# HELP skillsphere_latency_p50_ms 50th percentile latency in ms
# TYPE skillsphere_latency_p50_ms gauge
skillsphere_latency_p50_ms 24.50
# HELP skillsphere_latency_p95_ms 95th percentile latency in ms
# TYPE skillsphere_latency_p95_ms gauge
skillsphere_latency_p95_ms 112.30
# HELP skillsphere_latency_p99_ms 99th percentile latency in ms
# TYPE skillsphere_latency_p99_ms gauge
skillsphere_latency_p99_ms 245.80
# HELP skillsphere_db_latency_ms Database probe latency in ms
# TYPE skillsphere_db_latency_ms gauge
skillsphere_db_latency_ms 4.20
# HELP skillsphere_queue_pending_tasks Tasks currently waiting in queue
# TYPE skillsphere_queue_pending_tasks gauge
skillsphere_queue_pending_tasks 0
# HELP skillsphere_queue_dead_letter_tasks Dead letter tasks total
# TYPE skillsphere_queue_dead_letter_tasks gauge
skillsphere_queue_dead_letter_tasks 0
# HELP skillsphere_cache_hits_total Total distributed cache hits
# TYPE skillsphere_cache_hits_total counter
skillsphere_cache_hits_total 5420
# HELP skillsphere_cache_misses_total Total distributed cache misses
# TYPE skillsphere_cache_misses_total counter
skillsphere_cache_misses_total 180
# HELP skillsphere_http_request_duration_ms HTTP request duration histogram
# TYPE skillsphere_http_request_duration_ms histogram
skillsphere_http_request_duration_ms_bucket{le="10.0"} 412
skillsphere_http_request_duration_ms_bucket{le="25.0"} 780
skillsphere_http_request_duration_ms_bucket{le="50.0"} 1050
skillsphere_http_request_duration_ms_bucket{le="100.0"} 1210
skillsphere_http_request_duration_ms_bucket{le="250.0"} 1260
skillsphere_http_request_duration_ms_bucket{le="500.0"} 1275
skillsphere_http_request_duration_ms_bucket{le="1000.0"} 1282
skillsphere_http_request_duration_ms_bucket{le="2500.0"} 1284
skillsphere_http_request_duration_ms_bucket{le="5000.0"} 1284
skillsphere_http_request_duration_ms_bucket{le="+Inf"} 1284
```

---

## 4. Multi-Instance Prometheus Scraping Architecture

In a production Kubernetes or ECS cluster:
1. Each application pod exposes `/api/metrics/` on port 8000.
2. Prometheus scrapes each pod target directly using pod annotations (`prometheus.io/scrape: "true"`).
3. Prometheus server aggregates counters (`sum(rate(skillsphere_requests_total[5m]))`) and computes fleet-wide percentiles using standard PromQL histogram quantiles:
   ```promql
   histogram_quantile(0.95, sum(rate(skillsphere_http_request_duration_ms_bucket[5m])) by (le))
   ```
4. This avoids single-point-of-failure centralized metrics aggregation while guaranteeing statistical validity across any number of replicas.
