# SkillSphere Phase 18.4.2 — Container Architecture & Deployment Validation

**Container Specification**: Docker Multi-Stage Build (`Dockerfile`)  
**Base Image**: `python:3.12-slim`  
**Execution Privilege**: Unprivileged User (`skillsphere` UID 1001)  
**Process Manager**: `tini` (PID 1 Init System)  

---

## 1. Container Architectural Verification

SkillSphere utilizes an enterprise-grade multi-stage container architecture designed for high-concurrency cloud environments (AWS ECS Fargate):

```
[ Stage 1: Builder (python:3.12-slim) ]
  ├── Install build-essential, libpq-dev
  ├── Compile native C wheels (psycopg2, Pillow)
  └── Install dependencies to /root/.local

                    │
                    ▼ (Copy artifacts)

[ Stage 2: Runtime (python:3.12-slim) ]
  ├── Install runtime libraries: libpq5, curl, tini
  ├── Create unprivileged user: skillsphere (UID 1001)
  ├── Copy compiled wheels to /home/skillsphere/.local
  ├── Copy application source code (ownership: skillsphere:skillsphere)
  ├── Execute collectstatic for static assets
  ├── Set unprivileged USER skillsphere
  ├── Configure PID 1 ENTRYPOINT: ["/usr/bin/tini", "--"]
  └── Default CMD: ["gunicorn", "-c", "gunicorn.conf.py", "config.wsgi:application"]
```

---

## 2. Multi-Role Execution in ECS Fargate

The same single production container image powers both web application tasks and background worker tasks, ensuring 100% code and dependency parity:

### 2.1 Web Application Task
- **Command**: Default `gunicorn` entrypoint.
- **Concurrency**: 2 Gunicorn worker processes with 4 threads per worker (`8 threads total per task`).
- **Healthcheck**: Evaluates decoupled `/health/live/` probe every 20 seconds.
- **Port**: Listens on TCP port 8000, mapped to ALB target group.

### 2.2 Background Task Worker Daemon
- **Command**: Overridden in ECS task definition:
  ```json
  ["python", "manage.py", "run_task_worker", "--poll-interval=0.5"]
  ```
- **Lifecycle**: Runs continuously under `tini` management.
- **Signal Handling**: Listens for SIGTERM / SIGINT for graceful job completion.
- **Fencing & Recovery**: Implements distributed task queue fencing tokens and lease heartbeats.
- **Zero Open Ports**: Runs in private application subnets with zero inbound open ports.

---

## 3. Security & Operational Hardening Checklist

- [x] **Non-Root Execution**: Container runs strictly under `USER skillsphere` (UID 1001).
- [x] **Zombie Process Reaping**: `tini` installed as PID 1 to reap orphaned child processes and properly forward POSIX termination signals.
- [x] **Zero Secrets in Image**: Build arguments, Dockerfile, and image layers contain zero credentials. All secrets are mounted dynamically via AWS Secrets Manager.
- [x] **Minimal Attack Surface**: Compiler toolchains (`gcc`, `build-essential`) are discarded in the builder stage and absent from the final runtime image.
- [x] **Reproducible Build**: Dependency versions governed deterministically by `requirements.txt`.
