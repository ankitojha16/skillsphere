# SkillSphere Phase 18 — Production Container & Deployment Architecture

## 1. Executive Summary

This document specifies the enterprise container architecture for SkillSphere, detailing the multi-stage Docker build, non-root security enforcement, PID 1 signal management, decoupled entrypoints, and graceful lifecycle handling.

---

## 2. Container Build Specification (`Dockerfile`)

### 2.1 Multi-Stage Compilation
```dockerfile
# Stage 1: Build & Python Wheel Compilation
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final Minimal Runtime Image
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PATH="/home/skillsphere/.local/bin:$PATH" PORT=8000
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl tini && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1001 -s /bin/bash skillsphere
COPY --from=builder /root/.local /home/skillsphere/.local
COPY --chown=skillsphere:skillsphere . .
USER skillsphere
RUN python manage.py collectstatic --noinput --clear || true
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/live/ || exit 1
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "config.wsgi:application"]
```

### 2.2 Security Hardening Attributes
1. **Unprivileged Execution**: The container runs under UID `1001` (`skillsphere`), strictly preventing root escalation or container breakout exploits.
2. **Minimal Attack Surface**: Compiler toolchains (`gcc`, `g++`, `build-essential`) exist only in the temporary `builder` stage and are absent from the runtime image.
3. **No Embedded Credentials**: All configuration is injected at runtime via environment variables or AWS Secrets Manager. No passwords or API keys are baked into container filesystem layers.
4. **PID 1 Signal Forwarding (`tini`)**: Python interpreters running as PID 1 often fail to reap orphaned zombie child processes or respond properly to `SIGTERM`. Prepending `/usr/bin/tini --` ensures proper signal trapping and immediate process termination upon container stop.

---

## 3. Decoupled Process Entrypoints

The same hardened container image serves both Web and Background Worker roles, guaranteeing code parity:

### 3.1 Web Service Entrypoint
```bash
gunicorn -c gunicorn.conf.py config.wsgi:application
```
- **Concurrency**: Gunicorn with threaded workers (`worker_class = 'gthread'`).
- **Dynamic Workers**: Configured via `WEB_CONCURRENCY` and `GUNICORN_THREADS`.
- **Preload App**: `preload_app = True` minimizes memory duplication via copy-on-write.

### 3.2 Background Worker Entrypoint
```bash
python manage.py run_task_worker --worker-id=worker_fargate_node_1 --poll-interval=0.5
```
- **Signal Handling**: Traps `SIGTERM` and `SIGINT`, finishing any active job before exiting.
- **Lease Expiry Recovery**: Periodically sweeps the database for abandoned jobs from crashed workers.
- **Non-blocking Polling**: Uses `select_for_update(skip_locked=True)` so multiple worker pods run concurrently without thread contention.

---

## 4. Graceful Shutdown & Zero-Downtime Deployments

During container rolling updates (ECS deployments or Kubernetes rolling updates):
1. The load balancer receives a de-registration event and stops routing new connections to the retiring task.
2. Container runtime sends `SIGTERM` to `tini`.
3. Gunicorn/Worker catches `SIGTERM`:
   - Gunicorn enters graceful shutdown mode: waits up to `GUNICORN_GRACEFUL_TIMEOUT` (30s) for active requests to finish before closing connections.
   - Worker daemon finishes processing its current task and exits without picking up new jobs.
4. If processes do not terminate within 35 seconds, container runtime issues `SIGKILL`.
