# Phase 18.1 — SkillSphere Staging Deployment Runbook

## 1. Overview and Operational Purpose

This runbook provides complete, deterministic, step-by-step instructions to deploy, verify, operate, and troubleshoot the **SkillSphere Multi-Instance Staging Cluster** from a fresh repository clone.

The staging environment mirrors production horizontal concurrency using:
- **Reverse Proxy / Load Balancer**: Nginx (`nginx/nginx.staging.conf`) with least-connections load balancing, TLS/SSL termination, and security headers.
- **Web Application Instances**: Multiple independent Gunicorn worker nodes running Django (`web_instance_1`, `web_instance_2`).
- **Background Worker Fleet**: Multi-instance Celery / task queue daemons (`worker_instance_1`, `worker_instance_2`).
- **Shared Object / File Storage**: Shared volume mounted at `/app/media` across all web and worker nodes, or S3/MinIO bucket.
- **Relational Database**: PostgreSQL with PgBouncer connection multiplexing.
- **Distributed Cache & Broker**: Redis cluster/sentinel for session caching, bulkhead concurrency semaphores, and worker leases.
- **Monitoring & Metrics**: Prometheus scraping `/metrics` and Grafana observability dashboards.

---

## 2. Prerequisites & Host Requirements

Before initiating deployment, verify that the host machine meets the following operational prerequisites:

### Hardware Specifications
- **CPU**: 4+ vCPUs recommended for local staging cluster emulation.
- **Memory**: 8 GB RAM minimum (16 GB recommended).
- **Disk**: 20 GB free disk space.

### Software Dependencies
- **Docker Engine**: Version `24.0.0+` or `Podman 4.0+`.
- **Docker Compose**: Version `v2.20.0+`.
- **Python**: Version `3.9+` (for running local load test clients, smoke tests, and operational scripts).
- **cURL / HTTPie**: For health check and probe interrogation.
- **Git**: For source version control.

Verify tooling versions:
```bash
docker --version
docker compose version
python3 --version
curl --version
```

---

## 3. Configuration & Environment Setup

### 3.1 Clone the Repository
```bash
git clone https://github.com/ankitojha16/ankit-kumar-portfolio.git skillsphere
cd skillsphere
```

### 3.2 Environment File Provisioning
Copy the template staging environment file:
```bash
cp .env.staging.example .env.staging
```

Verify and configure required variables within `.env.staging`:

| Variable Name | Required Value / Description | Staging Example |
| :--- | :--- | :--- |
| `DJANGO_SETTINGS_MODULE` | Active Django settings module | `skillsphere.settings_staging` |
| `SECRET_KEY` | High-entropy production/staging secret | `insecure-staging-key-replace-in-prod-xyz123` |
| `DEBUG` | Django debug mode (must be False) | `False` |
| `ALLOWED_HOSTS` | Comma-delimited list of host headers | `localhost,127.0.0.1,staging.skillsphere.internal,web_instance_1,web_instance_2` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://skillsphere_user:staging_secret_pass@db:5432/skillsphere_staging` |
| `REDIS_URL` | Distributed cache and broker URL | `redis://redis:6379/0` |
| `STORAGE_BACKEND` | Storage provider (`local` or `s3`) | `local` |
| `MEDIA_ROOT` | Shared mount point for file uploads | `/app/media` |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket (if STORAGE_BACKEND=s3) | `skillsphere-staging-media` |
| `PGBOUNCER_POOL_MODE` | PgBouncer pooling strategy | `transaction` |
| `PGBOUNCER_MAX_CLIENT_CONN` | Max inbound application connections | `500` |
| `PGBOUNCER_DEFAULT_POOL_SIZE` | Physical server connections per pool | `40` |

---

## 4. Step-by-Step Cluster Deployment Sequence

Follow this exact deterministic execution order to ensure dependent infrastructure services initialize before application instances:

### Step 1: Provision Persistent Volumes & Networks
```bash
# Docker Compose manages volumes and bridge networks automatically
# Verify no conflicting orphaned containers exist:
docker compose -f docker-compose.staging.yml down -v --remove-orphans
```

### Step 2: Build Application Container Images
```bash
docker compose -f docker-compose.staging.yml build --no-cache
```

### Step 3: Start Foundation Infrastructure (DB & Redis)
```bash
docker compose -f docker-compose.staging.yml up -d db redis
```

Wait 10 seconds for database readiness, or verify via healthcheck:
```bash
docker compose -f docker-compose.staging.yml exec db pg_isready -U skillsphere_user -d skillsphere_staging
```

### Step 4: Execute Database Migrations & Static Collection
Run one-shot administrative migration container to initialize database schema:
```bash
docker compose -f docker-compose.staging.yml run --rm web_instance_1 python manage.py migrate --noinput
docker compose -f docker-compose.staging.yml run --rm web_instance_1 python manage.py collectstatic --noinput
```

### Step 5: Start Application Cluster & Worker Fleet
```bash
docker compose -f docker-compose.staging.yml up -d web_instance_1 web_instance_2 worker_instance_1 worker_instance_2
```

### Step 6: Start Edge Ingress Proxy & Monitoring
```bash
docker compose -f docker-compose.staging.yml up -d nginx prometheus grafana
```

### Step 7: Verify Service Status
```bash
docker compose -f docker-compose.staging.yml ps
```
All containers (`nginx`, `web_instance_1`, `web_instance_2`, `worker_instance_1`, `worker_instance_2`, `db`, `redis`, `prometheus`, `grafana`) should show `Up` (healthy).

---

## 5. Post-Deployment Verification & Smoke Probes

### 5.1 Deep Health Check Probe
Query the unified health endpoint through Nginx ingress:
```bash
curl -i http://localhost/health/
```
**Expected Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "storage": "writable"
}
```

### 5.2 Liveness & Readiness Probes
```bash
# Readiness (traffic routing readiness)
curl -i http://localhost/health/ready/
# Status: 200 OK

# Liveness (process health)
curl -i http://localhost/health/live/
# Status: 200 OK
```

### 5.3 Prometheus Metrics Scraping Verification
```bash
curl -s http://localhost/metrics | grep -E "django_http_requests_total|active_requests"
```

### 5.4 Cross-Instance Shared Storage Smoke Test
Verify that an upload handled by instance 1 is readable by instance 2:
```bash
# Upload a file via Web 1
TOKEN=$(curl -s -X POST http://localhost/api/token/ -d "username=admin&password=staging_password" | jq -r .access)
FILE_ID=$(curl -s -X POST http://localhost/api/media/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_cert.png" | jq -r .id)

# Fetch file repeatedly to verify round-robin Nginx hits both instances successfully:
for i in {1..10}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/media/uploads/$FILE_ID)
  echo "Fetch $i: HTTP $STATUS"
  test "$STATUS" -eq 200 || echo "FAILED ON FETCH $i"
done
```

---

## 6. Worker Daemon & Recovery Verification

To verify that background worker leases recover gracefully during node failure:

```bash
# 1. Enqueue long-running task
TASK_ID=$(curl -s -X POST http://localhost/api/tasks/trigger-report/ -H "Authorization: Bearer $TOKEN" | jq -r .task_id)

# 2. Identify which worker claimed the lease:
docker compose -f docker-compose.staging.yml logs worker_instance_1 worker_instance_2 | grep "$TASK_ID"

# 3. Simulate sudden worker crash (SIGKILL worker_instance_1):
docker compose -f docker-compose.staging.yml kill -s SIGKILL worker_instance_1

# 4. Monitor worker_instance_2 adopting the expired lease:
sleep 35
docker compose -f docker-compose.staging.yml logs worker_instance_2 | grep -E "Recovered expired lease|processing task $TASK_ID"

# 5. Bring worker_instance_1 back online:
docker compose -f docker-compose.staging.yml up -d worker_instance_1
```

---

## 7. Staging Load Testing Execution

Execute the Phase 18 Locust load test against the staging cluster:

```bash
# Install Locust in virtualenv
pip install locust==2.34.0

# Run headless load test: 50 concurrent virtual users, spawn rate 5/sec, duration 3 minutes
locust -f load_tests/locustfile_phase18.py \
  --host http://localhost \
  --users 50 \
  --spawn-rate 5 \
  --run-time 3m \
  --headless \
  --html load_test_report_staging.html \
  --csv load_test_staging
```

---

## 8. Rollback & Disaster Recovery Procedures

### 8.1 Rollback Application Code Version
If a newly deployed image exhibits critical regressions:
```bash
# 1. Re-tag or pull prior stable commit:
git checkout <PREVIOUS_STABLE_COMMIT>

# 2. Rebuild and restart web & worker instances:
docker compose -f docker-compose.staging.yml up -d --build --no-deps web_instance_1 web_instance_2 worker_instance_1 worker_instance_2

# 3. Verify health probes:
curl -i http://localhost/health/
```

### 8.2 Database Schema Reversal
```bash
# Run migration rollback on a single instance:
docker compose -f docker-compose.staging.yml run --rm web_instance_1 python manage.py migrate <app_name> <migration_number>
```

### 8.3 Emergency Teardown
```bash
# Stop all services gracefully:
docker compose -f docker-compose.staging.yml down

# Complete wipe (resets all containers, networks, and persistent staging volumes):
docker compose -f docker-compose.staging.yml down -v
```

---

## 9. Security & Hardening Checklist

Prior to promoting staging configurations to production:
1. Ensure all passwords and `SECRET_KEY` in `.env.staging` are replaced with AWS KMS / GCP Secret Manager secrets.
2. Confirm Nginx TLS certificate is signed by Let's Encrypt / DigiCert (no self-signed certificates in public routing).
3. Validate that `DEBUG=False` in all container runtimes.
4. Ensure database and Redis ports are bound strictly to internal Docker bridge networks (`expose:`), never published to host interfaces (`ports:`).
5. Verify PgBouncer connection pool saturation metrics in Grafana under peak load.
