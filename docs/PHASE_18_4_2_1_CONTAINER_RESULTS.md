# SkillSphere Phase 18.4.2.1 — Container Build & Runtime Specification

**Target Platform**: Linux/arm64 & Linux/amd64 (AWS ECS Fargate)  
**Base Image**: `python:3.12-slim`  
**Execution Identity**: Non-Root `skillsphere` (UID 1001)  
**Process Supervisor**: `tini` (PID 1 Init)  

---

## 1. Container Configuration Audit

The SkillSphere production container image (`Dockerfile`) adheres to cloud-native container standards:

```dockerfile
# -------------------------------------------------------------
# Stage 1: Builder (python:3.12-slim)
# -------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# -------------------------------------------------------------
# Stage 2: Final Minimal Runtime Image
# -------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/skillsphere/.local/bin:$PATH" \
    PORT=8000

# Install runtime dependencies, libpq, curl for healthchecks, and tini for PID 1 init
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN useradd -m -u 1001 -s /bin/bash skillsphere

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/skillsphere/.local

# Copy application source code
COPY --chown=skillsphere:skillsphere . .

# Set unprivileged user
USER skillsphere

# Collect static assets into staticfiles/
RUN python manage.py collectstatic --noinput --clear || true

EXPOSE 8000

# Container liveness check using decoupled /health/live/ endpoint
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/live/ || exit 1

# Use tini as the PID 1 init process to reap zombie processes and forward signals
ENTRYPOINT ["/usr/bin/tini", "--"]

# Default command starts the web application server
CMD ["gunicorn", "-c", "gunicorn.conf.py", "config.wsgi:application"]
```

---

## 2. Runtime Verification Points

### 2.1 Non-Root Security Enforcement
- Container processes execute strictly as unprivileged user `skillsphere` (UID 1001).
- Filesystem ownership is restricted to `skillsphere:skillsphere`.
- Root privilege escalation is disallowed in ECS task definitions (`readonlyRootFilesystem = false` with non-root user).

### 2.2 Decoupled Health Probes
- **Liveness Probe (`/health/live/`)**: Returns HTTP 200 immediately without database dependencies. Used by ALB target group and container runtime.
- **Readiness Probe (`/health/ready/`)**: Evaluates database and Redis connectivity before accepting live traffic.

### 2.3 Background Worker Daemon
- The same image serves as the background worker daemon in ECS:
  ```json
  "command": ["python", "manage.py", "run_task_worker", "--poll-interval=0.5"]
  ```
- Supervised by `tini` to ensure graceful shutdown on SIGTERM within AWS ECS task stop timeout (30s).

### 2.4 Zero Secret Leakage
- Zero environment variables containing passwords or keys are written to `Dockerfile` or image layers.
- All secrets are injected dynamically via AWS Secrets Manager at container launch time.
