# SkillSphere Phase 17.3 — Multi-Instance Observability & Health Probe Validation

## 1. Executive Overview

When deploying a fleet of web instances behind a reverse proxy or load balancer, monitoring requires reliable metrics aggregation, secure scraping interfaces, stabilized label cardinality, and decoupled health check endpoints.

Phase 17.3 hardens `services/observability.py` and `services/health_views.py` to ensure high-fidelity telemetry across distributed container pods.

---

## 2. Instance Identity & Label Cardinality Stabilization

In Prometheus monitoring, high-cardinality labels (labels that generate an unbounded number of time-series combinations) degrade Prometheus TSDB performance and cause memory exhaustion.

SkillSphere stabilizes `instance_id` label cardinality:
```python
# services/observability.py
def get_instance_identifier() -> str:
    global _cached_instance_id
    if _cached_instance_id is not None:
        return _cached_instance_id

    # Check container / cluster orchestrator identity
    raw_id = (
        os.getenv('INSTANCE_ID')
        or os.getenv('KUBERNETES_POD_NAME')
        or os.getenv('DYNO')
        or os.getenv('CF_INSTANCE_INDEX')
        or os.getenv('HOSTNAME')
        or 'single-instance'
    )
    # Sanitize label value (only allow alphanumeric, underscore, hyphen, and dot)
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', raw_id)[:64]
    _cached_instance_id = sanitized
    return _cached_instance_id
```

### Cardinality Protections:
1. **Lifetime In-Memory Cache**: `get_instance_identifier()` is evaluated once and cached in `_cached_instance_id`. It never mutates during the lifetime of a worker process.
2. **Strict Whitelist Sanitization**: Strips spaces, newlines, and illegal characters (`[^a-zA-Z0-9_\-\.]`).
3. **Length Bounding**: Bounded to 64 characters max, preventing memory explosion from rogue hostname values.

---

## 3. Metrics Endpoint Security & Prometheus Scraping

The Prometheus metrics endpoint (`/api/metrics/`) exposes operational telemetry, request latencies, and circuit breaker states. Unauthenticated access exposes internal architecture details to attackers.

### Security Specification:
- **Authentication**: When `METRICS_AUTH_TOKEN` is configured in the environment, the endpoint requires:
  - Header: `X-Metrics-Token: <token>`, or
  - Header: `Authorization: Bearer <token>`
- **Unauthorized Handling**: Requests missing or supplying an invalid token receive `HTTP 403 Forbidden` (`{"error": "Unauthorized metrics access"}`).
- **Local Development**: If `METRICS_AUTH_TOKEN` is unconfigured and `DEBUG=True`, access is allowed for development inspection.

### Prometheus Configuration Example:
```yaml
scrape_configs:
  - job_name: 'skillsphere_fleet'
    metrics_path: '/api/metrics/'
    authorization:
      type: Bearer
      credentials: '${METRICS_AUTH_TOKEN}'
    static_configs:
      - targets: ['pod-1.internal:8000', 'pod-2.internal:8000', 'pod-3.internal:8000']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
```

In Grafana, dashboards aggregate across the fleet using PromQL:
- Fleet request rate: `sum(rate(django_http_requests_total[1m])) by (status_code)`
- Fleet p95 latency: `histogram_quantile(0.95, sum(rate(django_http_request_duration_seconds_bucket[1m])) by (le))`
- Bulkhead degradation: `max(bulkhead_degraded_status) by (bulkhead_name)`

---

## 4. Decoupled Kubernetes & Container Health Probes

SkillSphere implements three discrete health endpoints in `services/health_views.py`:

```
                    Container Lifecycle Probes
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
      /health/startup/    /health/live/      /health/ready/
     (Database migrations (Process heartbeat (DB ping & Redis
      & warm cache ready)   & event loop)     cache connectivity)
```

### 1. `/health/startup/` (Startup Probe)
- Verifies that the application process has initialized, Django apps are loaded, and essential settings are valid.
- Informs orchestrators to hold liveness checks until initialization completes.

### 2. `/health/live/` (Liveness Probe)
- Lightweight in-memory check (`{"status": "alive"}`).
- Returns HTTP 200 immediately without executing database queries or Redis calls.
- **Critical Design Choice**: Never touches the database. If the database experiences a brief 2-second stall, liveness probes must NOT fail and trigger cascading container restarts across the entire fleet.

### 3. `/health/ready/` (Readiness Probe)
- Actively probes PostgreSQL (`connection.ensure_connection()`) and Redis (`cache.set / cache.get`).
- If PostgreSQL is unreachable, returns `HTTP 503 Service Unavailable` with diagnostic payload:
  ```json
  {
    "status": "degraded",
    "database": "unhealthy",
    "cache": "healthy"
  }
  ```
- Signals the ingress controller / load balancer to temporarily remove the instance from traffic routing until the dependency recovers.

---

## 5. Automated Test Verification

Hardening verified via `services/test_phase_17_3_hardening.py`:
- `test_metrics_security_and_instance_stability`:
  - Confirms unauthenticated access receives HTTP 403.
  - Confirms valid bearer token receives HTTP 200 with Prometheus payload.
  - Confirms instance identifier stability across repeated calls.
