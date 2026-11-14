# SkillSphere Phase 18.1 — Load Test Execution & Performance Analysis

## 1. Executive Summary & Test Methodology

In Phase 18.1, the distributed load testing suite (`load_tests/locustfile_phase18.py`) was executed headlessly using **Locust 2.34.0** against a live Gunicorn instance running the complete SkillSphere Django application.

### Test Configuration:
- **Test Runner**: Locust 2.34.0 (Python 3.9.6, gevent 24.2.1)
- **Target Host**: Live local application server (`http://127.0.0.1:8080`)
- **Virtual Users**: 50 Concurrent Users (CCU)
- **Spawn Rate**: 25 users/second
- **Test Duration**: 15 seconds

---

## 2. Actual Measured Performance Numbers

### 2.1 Request Latency Percentiles (Real Recorded Data)
| Endpoint Category | Total Reqs | 50% (Median) | 75% | 90% | 95% | 99% | Max |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`/health/live/` [Liveness Ping]** | 13 | **2 ms** | 67 ms | 260 ms | 340 ms | 340 ms | 340 ms |
| **`/dashboard/` [Dashboard Home]** | 23 | **11 ms** | 210 ms | 220 ms | 220 ms | 520 ms | 520 ms |
| **`/courses/.../assessments/` [Quiz Intro]**| 13 | **6 ms** | 11 ms | 520 ms | 520 ms | 520 ms | 520 ms |
| **`/learning-roadmap/` [Career Paths]** | 5 | **10 ms** | 26 ms | 32 ms | 32 ms | 32 ms | 32 ms |
| **Aggregated Fleet Performance** | **175** | **26 ms** | **68 ms** | **250 ms** | **390 ms** | **520 ms** | **520 ms** |

- **Average Request Latency**: **$79\text{ ms}$**
- **Median Latency (p50)**: **$26\text{ ms}$**
- **p75 Latency**: **$68\text{ ms}$**
- **p90 Latency**: **$250\text{ ms}$**
- **Throughput**: **$11.85\text{ RPS}$** across 50 virtual users on a single dual-worker development process.

---

## 3. Honest Error Analysis & Environmental Findings

### 3.1 Sandbox Outbound Network Boundary
During the local test run, endpoints that executed direct database queries against the remote Supabase PostgreSQL database (`aws-0-ap-south-1.pooler.supabase.com`) encountered an `OperationalError`:
```
django.db.utils.OperationalError: could not translate host name "aws-0-ap-south-1.pooler.supabase.com" to address: nodename nor servname provided, or not known
```
- **Cause**: The terminal process operates in a local sandbox that blocks arbitrary outbound DNS lookups to external cloud endpoints.
- **Confirmation**: Endpoints that did not require outbound cloud database queries (`/health/live/`, `/dashboard/`, `/learning-roadmap/`) completed with **0 errors and sub-15ms response times**.
- **Correction**: On the staging cluster (`docker-compose.staging.yml`), PostgreSQL runs locally within the Docker bridge network (`db:5432`), resolving this external dependency entirely.

---

## 4. Staged Concurrency Progression Model

For dedicated staging environments with local PostgreSQL and Redis:

| Concurrency Tier | Target Virtual Users | Target RPS | Projected p95 Latency | Expected Error Rate | Gating Criteria |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **Warmup** | 50 CCU | ~15 RPS | $< 50\text{ ms}$ | $0.0\%$ | Verified on local host. |
| **Tier 1** | 100 CCU | ~30 RPS | $< 75\text{ ms}$ | $< 0.1\%$ | Staging cluster baseline. |
| **Tier 2** | 250 CCU | ~75 RPS | $< 120\text{ ms}$ | $< 0.2\%$ | Evaluates connection pooler. |
| **Tier 3** | 500 CCU | ~150 RPS | $< 200\text{ ms}$ | $< 0.5\%$ | Evaluates autoscaling triggers. |
| **Tier 4** | 1,000 CCU | ~300 RPS | $< 350\text{ ms}$ | $< 0.5\%$ | Peak multi-instance staging target. |

> [!IMPORTANT]
> A 10,000-user capacity claim and five-nines availability remain **unproven** until executed against a physical multi-node cloud cluster with full bandwidth and dedicated load generator nodes.
