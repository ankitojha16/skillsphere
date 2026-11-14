# SkillSphere Ultra-Scale Architecture (10,000 Concurrent Active Users)

## 1. System Topology & Architectural Philosophy
SkillSphere is an autonomous career and technical education platform engineered to support **10,000 simultaneously active learners** with sub-second API latencies and resilient fault tolerance.

### Core Architectural Principles
1. **Hosting Provider Independence**: Zero vendor lock-in. The application layer runs as stateless containers or serverless workers without hardcoded dependencies on Vercel, AWS, GCP, or Azure SDKs. All infrastructure coordination is handled through abstract interfaces and environment variables.
2. **Stateless Compute**: Any web process can handle any request. Sessions are backed by cached PostgreSQL (`django.contrib.sessions.backends.cached_db`) with distributed Redis caching, eliminating local memory dependencies.
3. **Architectural Workload Offloading**:
   - **Video Streaming**: 100% offloaded to YouTube Global CDN (`youtube-nocookie.com`). Zero video streaming bytes pass through Django workers.
   - **Interactive Code Execution**: 100% offloaded to the student browser's WebAssembly engine (Pyodide). Server-side code execution via `exec()` is strictly forbidden.
   - **Static & Media Assets**: Edge-cached for 1 year immutable (`max-age=31536000, immutable`).

---

## 2. 10,000 Concurrent User Workload Model

| Learner Persona | Traffic Share | Primary Endpoints | Think Time | Dynamic RPS Contribution |
|---|---|---|---|---|
| **Deep Learning & Video** | 45% (4,500 users) | `/learn/<slug>/<id>/`, video progress heartbeats | 25s–45s | ~187.5 RPS |
| **Course Discovery & Search** | 25% (2,500 users) | `/courses/`, autocomplete, category filters | 8s–15s | ~125.0 RPS (mostly cached) |
| **Learner Dashboard & Progress** | 15% (1,500 users) | `/dashboard/`, `/goals/`, profile | 15s–30s | ~75.0 RPS |
| **Assessment & Sandbox** | 10% (1,000 users) | Assessments, coding checks | 30s–60s | ~33.3 RPS |
| **Collaboration & Community** | 5% (500 users) | Pair Lounge, forums, project reviews | 20s–40s | ~25.0 RPS |
| **TOTALS** | **100% (10,000 users)** | Full Platform Funnel | **~25s avg** | **~445.8 – 639.2 RPS** |

- **Nominal Dynamic Backend RPS**: ~357.5 RPS (accounting for 44% edge and Redis cache absorption).
- **Peak Dynamic Backend RPS (1.5× surge)**: ~536.2 RPS.
- **Burst Dynamic Backend RPS (2.5× surge)**: ~893.7 RPS.

---

## 3. High-Level Component Architecture

```
[ Global Users (10,000 Active) ]
              │
              ▼
[ Global Anycast CDN & WAF (Cloudflare / Edge CDN) ]
  ├── Static Assets (/static/*) ──> 1-Year Immutable Edge Cache
  ├── Video Streams ──────────────> YouTube CDN (Direct Stream)
  └── Dynamic API / Pages ────────> Load Balancer / Ingress
                                           │
                                           ▼
                       [ Stateless Django Web App Cluster ]
                       (AWS ECS Fargate / GCP Cloud Run / K8s)
                       (Gunicorn gthread: 5 workers, 4 threads)
                                     │         │
                    ┌────────────────┘         └────────────────┐
                    ▼                                           ▼
      [ Distributed Redis Cluster ]              [ Supabase PgBouncer Pooler ]
      - Versioned Catalogue Cache                (Port 6543, Transaction Mode)
      - Distributed Token Locks                                 │
      - Sliding-Window Rate Limiters                            ▼
      - Circuit Breaker Telemetry                 [ PostgreSQL 17 Primary ]
                                                  - Composite B-Tree Indexes
                                                  - 10s Statement Timeout
                                                  - DurableTaskJob Queue
```

---

## 4. Portability & Migration Readiness
SkillSphere exposes standard POSIX and HTTP interfaces:
- **Container Artifacts**: Fully containerized via multi-stage `Dockerfile`, `gunicorn.conf.py`, and `docker-compose.yml`.
- **Health Probes**: Standard Kubernetes/ALB endpoints:
  - `GET /health/live/`: Fast process liveness.
  - `GET /health/ready/`: Dependency readiness probe.
- **Observability**: Prometheus metrics exported at `GET /api/metrics/`.
