# SkillSphere Production Container Dockerfile (Option B Architecture)
# Multi-stage, unprivileged, enterprise-hardened container image

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

# Final Runtime Stage
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/skillsphere/.local/bin:$PATH" \
    PORT=8000

# Install runtime PostgreSQL client library
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN useradd -m -u 1001 -s /bin/bash skillsphere

# Copy dependencies and application code
COPY --from=builder /root/.local /home/skillsphere/.local
COPY --chown=skillsphere:skillsphere . .

USER skillsphere

# Collect static assets during image build
RUN python manage.py collectstatic --noinput --clear || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "config.wsgi:application"]
