# SkillSphere Phase 17.2 — Horizontal Scalability & Multi-Instance Architecture

## 1. Executive Summary & Architectural Scope

SkillSphere Phase 17.2 establishes the architectural foundation enabling multiple independent application nodes to run concurrently across autoscaling container clusters, serverless environments, or hybrid edge networks.

Prior to Phase 17.2, several application layers relied on single-process memory, local filesystem storage, or static assumptions about process boundaries. Phase 17.2 formalizes **server and provider independence**, decoupling the application tier from local host state and ensuring consistent behavior whether deployed as 1, 10, or 100 instances.

```
                                  [ Global Edge / CDN / Anycast DNS ]
                                                   │
                                                   ▼
                                 [ Layer 7 Load Balancer / Ingress ]
                                      (Round-Robin / Least-Conn)
                                                   │
                     ┌─────────────────────────────┼─────────────────────────────┐
                     ▼                             ▼                             ▼
           [ App Instance 1 ]            [ App Instance 2 ]            [ App Instance N ]
             (Gunicorn/Uvicorn)            (Gunicorn/Uvicorn)            (Gunicorn/Uvicorn)
             ├─ Local Bulkhead             ├─ Local Bulkhead             ├─ Local Bulkhead
             ├─ Circuit Breakers           ├─ Circuit Breakers           ├─ Circuit Breakers
             ├─ Monotonic Counter          ├─ Monotonic Counter          ├─ Monotonic Counter
             └─ Prometheus /metrics        └─ Prometheus /metrics        └─ Prometheus /metrics
                     │                             │                             │
                     ├─────────────────────────────┼─────────────────────────────┘
                     │                             │
                     ▼                             ▼
       [ Distributed State Layer ]   [ Object Storage Service ]   [ Managed PostgreSQL Pool ]
       ┌─────────────────────────┐   ┌────────────────────────┐   ┌─────────────────────────┐
       │   Redis Cache / Locks   │   │ S3 / R2 / Supabase     │   │ PgBouncer (Port 6543)   │
       │   Atomic Counters       │   │ Local Filesystem       │   │ Row-Level Locks         │
       │   Token Rate Limiter    │   │ Presigned URL Engine   │   │ Unique Constraints      │
       └─────────────────────────┘   └────────────────────────┘   └─────────────────────────┘
```

---

## 2. Multi-Instance Architecture Principles

### 2.1 Stateless Application Tier
Every web worker and background task runner is fully stateless:
- **No In-Memory Session Storage**: User authentication sessions are stored in the shared database or signed client cookies (`django.contrib.sessions.backends.db` or `cached_db`).
- **No Local File State Assumptions**: User avatars, resume exports, certificates, and portfolio attachments are managed through `BaseStorageService`, directing writes to S3-compatible cloud object storage (or mountable network storage).
- **Process Crash Survival**: If an instance crashes abruptly, no state is trapped in its local memory; in-flight background tasks are reclaimed automatically via lease expiry.

### 2.2 Provider Independence
SkillSphere avoids proprietary vendor locks (such as AWS-specific or GCP-specific libraries in business logic):
- Storage uses standard S3-compatible REST interfaces supported identically by AWS S3, Cloudflare R2, MinIO, and Supabase Storage.
- Caching uses standard Redis protocol with seamless failover to `LocMemCache` for zero-crash developer simplicity.
- Concurrency control uses ANSI-SQL PostgreSQL semantics (`transaction.atomic()`, `select_for_update(skip_locked=True)`).

---

## 3. Implementation Status Matrix

| Component | Scope | Implementation File | Status | Multi-Instance Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Object Storage Abstraction** | Distributed | `services/storage_service.py` | **Implemented & Tested** | Uniform storage across cloud providers with IDOR access validation. |
| **Fleet-Wide Bulkhead** | Hybrid | `services/resilience.py` | **Implemented & Tested** | Redis atomic tokens with lease TTL; fail-open to local `BoundedSemaphore`. |
| **Circuit Breaker** | Hybrid | `services/resilience.py` | **Implemented & Tested** | Thread-safe per process; shared state via Redis with graceful in-process fallback. |
| **Background Lease Recovery** | Distributed | `services/task_queue.py` | **Implemented & Tested** | Reclaims orphaned running jobs from crashed instances; jittered backoff. |
| **Prometheus Exporter** | Distributed Scrape | `services/observability.py` | **Implemented & Tested** | Instance labeling (`instance="{id}"`), monotonic counters, histogram buckets. |
| **PgBouncer Pooling** | Distributed DB | `config/settings.py` | **Implemented & Tested** | `DISABLE_SERVER_SIDE_CURSORS = True`, bounded connect & statement timeouts. |
| **Cache Stampede & Isolation** | Distributed | `config/cache.py` | **Implemented & Tested** | Versioned keys, fault-tolerant Redis backend with `LocMemCache` fallback. |
| **Physical Multi-Node Cluster** | Infrastructure | Hosting / Kubernetes | **Blocked / External** | Application code is 100% ready; multi-node hardware deployment configured separately. |

---

## 4. Multi-Instance Deployment Topology

### 4.1 Ingress & Load Balancing
- **Load Balancing Strategy**: Layer 7 round-robin or least-connections without sticky sessions required.
- **SSL Termination**: Terminated at edge/load balancer; `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` ensures Django handles HTTPS requests transparently.
- **Request Tracing**: `RequestCorrelationMiddleware` extracts or generates `X-Request-ID` (validated against `^[a-zA-Z0-9_-]{8,64}$`), propagating it across all logs, DB queries, and downstream calls.

### 4.2 Health Checks & Autoscaling Signals
- **Liveness Probe** (`/health/live/`): Returns HTTP 200 immediately with `X-Request-ID`. Used by Kubernetes or container orchestrator to restart dead workers.
- **Readiness Probe** (`/health/ready/`): Verifies database connectivity and cache responsiveness within a 2-second timeout budget. If database connections fail, node is temporarily taken out of the ingress pool without crashing.

---

## 5. Capacity & Sizing Guidelines for Autoscaling Clusters

When scaling from 1 to $N$ instances:

1. **Total HTTP Throughput**:
   $$RPS_{\text{total}} = N \times RPS_{\text{per\_instance}}$$
2. **Database Connection Allocation**:
   $$Connections_{\text{total}} = N \times Workers_{\text{per\_instance}} \times Conns_{\text{per\_worker}}$$
   To prevent exhausting PostgreSQL connection limits ($Max_{\text{db}} = 60$ on Supabase free tier, $Max_{\text{db}} = 300$ on Pro), **PgBouncer transaction mode** (port 6543) is mandatory with `CONN_MAX_AGE = 0` (serverless) or `60` (persistent container).
3. **Bulkhead Capacity Sizing**:
   To enforce an upstream rate limit of $L_{\text{upstream}}$ across $N$ instances:
   $$C_{\text{local}} = \max\left(1, \left\lfloor \frac{L_{\text{upstream}}}{N_{\text{max}}} \right\rfloor\right)$$
   Alternatively, use `DistributedBulkhead` which coordinates a global capacity ceiling of $L_{\text{upstream}}$ across all instances via Redis atomic sets.
