# SkillSphere Enterprise Production Container Image
# Multi-stage, unprivileged, PID 1 signal-managed (tini) container

# -------------------------------------------------------------
# Stage 1: Build & Python Wheel Compilation
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
