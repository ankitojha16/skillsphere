# SkillSphere Phase 18.1 — Staging Cluster Execution & Host Audit

## 1. Executive Summary & Host Environment Audit

Phase 18.1 conducts an independent engineering audit and verification of the staging cluster deployment artifacts prepared in Phase 18.

### 1.1 Host Environment Findings
- **Host OS**: macOS Darwin 24.1.0 (Apple Silicon arm64)
- **Container Runtime Audit**: `docker` CLI and daemon are not installed on the local developer host system (`zsh: command not found: docker`).
- **IaC Tooling Audit**: `terraform` and `opentofu` are not installed locally (`terraform: command not found`).
- **Python Virtualenv**: Python 3.9.6 / Django 4.2.29 with PostgreSQL, Redis, ReportLab, and `locust-2.34.0` installed.

> [!IMPORTANT]
> In accordance with Phase 18.1 core instructions ("Never invent results. Distinguish executed tests from prepared scripts and mocked tests"), this report explicitly documents that Docker container execution on the local host is constrained by the host machine's missing Docker daemon. All container specifications, volume mappings, and process models are validated through static configuration analysis, live Gunicorn execution, and Python-level multi-instance simulation test suites (`services/test_phase_18_1_validation.py` and `services/test_phase_18_staging.py`).

---

## 2. Staging Cluster Topology & Defect Rectification

### 2.1 Confirmed Architectural Defect & Fix: Shared Media Volume
- **Defect Identified**: In the initial `docker-compose.staging.yml`, `web_instance_1` and `web_instance_2` ran with `STORAGE_BACKEND=local` without mounting a shared volume for `/app/media`. As a result, files uploaded to Web Instance 1 were written to its isolated container disk and were completely inaccessible to Web Instance 2.
- **Rectification**: Added a named shared volume `staging_media:/app/media` across all web and worker containers:
  ```yaml
  volumes:
    - staging_media:/app/media
  ```
  This guarantees that all container instances share the same physical filesystem volume when operating with local storage.

### 2.2 Staging Services Specification (`docker-compose.staging.yml`)
1. **`lb` (Reverse Proxy Load Balancer)**: Nginx 1.27 distributing HTTP traffic round-robin across web instances with rate limiting (60 req/s), connection limits (50 conns), and trusted proxy headers.
2. **`web_instance_1` & `web_instance_2`**: Independent Django Gunicorn application containers running 2 workers and 4 threads each ($16\text{ total web threads}$), tagged with distinct instance IDs (`staging_web_node_1`, `staging_web_node_2`).
3. **`worker_instance_1` & `worker_instance_2`**: Independent background task workers executing `python manage.py run_task_worker` with unique worker IDs (`staging_worker_pod_1`, `staging_worker_pod_2`).
4. **`db`**: PostgreSQL 17 with healthcheck (`pg_isready -U postgres -d skillsphere_staging`).
5. **`redis`**: Redis 7 alpine with healthcheck (`redis-cli ping`).

---

## 3. Container Lifecycle & Graceful Termination

### 3.1 PID 1 Init Management (`tini`)
The `Dockerfile` employs `/usr/bin/tini --` as the container entrypoint. This guarantees:
- Zombie child process reaping (prevents defunct process table exhaustion).
- Transparent `SIGTERM` forwarding to Gunicorn worker processes and background worker loops.

### 3.2 Worker Graceful Shutdown Verification
The worker daemon `analytics/management/commands/run_task_worker.py` binds signal handlers for `SIGTERM` and `SIGINT`:
- Flushes the active in-flight task to completion.
- Disables further queue polling.
- Exits cleanly with return code 0, emitting structured shutdown telemetry.
