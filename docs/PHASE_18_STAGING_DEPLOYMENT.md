# SkillSphere Phase 18 — Staging Deployment & Multi-Instance Validation Guide

## 1. Executive Summary

This guide details how to stand up, operate, and validate the SkillSphere multi-instance staging environment (`docker-compose.staging.yml`), simulating a real multi-node production cluster on a local or dedicated staging host.

---

## 2. Multi-Instance Staging Topology

The staging environment mirrors a production multi-AZ cluster with full process isolation:

```
                            [Public Port 8000]
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │    Nginx Load Balancer    │
                      │   (skillsphere_staging_lb)│
                      └─────────────┬─────────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 ▼                                     ▼
      ┌──────────────────────┐              ┌──────────────────────┐
      │  Staging Web Node 1  │              │  Staging Web Node 2  │
      │   (Port 8000 Int)    │              │   (Port 8000 Int)    │
      └──────────┬───────────┘              └──────────┬───────────┘
                 │                                     │
                 └──────────────────┬──────────────────┘
                                    ▼
      ┌────────────────────────────────────────────────────────────┐
      │          Shared Infrastructure (PostgreSQL & Redis)         │
      │  - skillsphere_staging_db (PostgreSQL 17 on Port 5432)     │
      │  - skillsphere_staging_redis (Redis 7 on Port 6379)        │
      └─────────────────────────────┬──────────────────────────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 ▼                                     ▼
      ┌──────────────────────┐              ┌──────────────────────┐
      │ Staging Worker Pod 1 │              │ Staging Worker Pod 2 │
      │ (run_task_worker 1)  │              │ (run_task_worker 2)  │
      └──────────────────────┘              └──────────────────────┘
```

---

## 3. Step-by-Step Staging Launch Instructions

### Step 1: Start the Multi-Instance Fleet
```bash
docker compose -f docker-compose.staging.yml up -d --build
```
This starts:
- 2 independent Django Gunicorn web instances
- 2 independent background task workers
- 1 Nginx round-robin reverse proxy load balancer
- 1 PostgreSQL 17 database container
- 1 Redis 7 cache/bulkhead container

### Step 2: Apply Migrations & Seed Baseline Data
```bash
docker compose -f docker-compose.staging.yml exec web_instance_1 python manage.py migrate
```

### Step 3: Verify Container Health
```bash
docker compose -f docker-compose.staging.yml ps
```
All containers should report `healthy` or `running`.

### Step 4: Verify Multi-Instance Load Balancing
Query the Nginx load balancer port multiple times to verify traffic alternates across independent web nodes:
```bash
curl -i http://localhost:8000/health/live/
```

---

## 4. Multi-Instance Integration Test Verification

The automated multi-instance integration suite `services/test_phase_18_staging.py` runs against the application logic to verify cross-instance safety:

```bash
./.venv/bin/python manage.py test services.test_phase_18_staging
```

### Verified Scenarios:
1. **Multi-Worker Queue Consumption (`test_multi_worker_independent_queue_consumption`)**:
   - Enqueued 6 distinct background jobs.
   - Worker 1 and Worker 2 claimed distinct batches without double-execution or locking races.
   - All 6 jobs completed cleanly with unique worker fencing tokens attached (`staging_worker_node_1#...` and `staging_worker_node_2#...`).
2. **Worker Lease Renewal (`test_worker_lease_renewal_during_long_operation`)**:
   - Simulated active lease extension via `renew_job_lease()`.
   - Confirmed expired lease recovery scanner leaves active jobs untouched.
3. **Distributed Bulkhead Capacity (`test_distributed_bulkhead_multithread_capacity`)**:
   - Concurrently invoked 5 worker threads against a 2-permit bulkhead.
   - Confirmed excess requests are rejected or timed out while active permits execute safely.
4. **Decoupled Health Probes (`test_decoupled_health_probes`)**:
   - Confirmed `/health/live/`, `/health/ready/`, and `/health/startup/` return HTTP 200.
5. **Storage Streaming & Path Security (`test_storage_streaming_and_path_security`)**:
   - Confirmed memory-safe binary chunk streaming and path traversal rejection.

**Test Run Summary**:
`Ran 5 tests in 0.146s. OK (100% Passing)`.
