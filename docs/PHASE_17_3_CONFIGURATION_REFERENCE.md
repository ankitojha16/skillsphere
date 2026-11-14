# SkillSphere Phase 17.3 — Multi-Instance Production Configuration Reference

## 1. Executive Overview

This reference document defines all environment variables required for running SkillSphere reliably across multi-instance container environments (Kubernetes, AWS ECS, GCP Cloud Run, Render, Heroku).

---

## 2. Environment Variables Specification

### 2.1 Object Storage Configuration
| Variable | Required | Default | Allowed Values | Description & Validation Rules |
| :--- | :---: | :---: | :---: | :--- |
| `STORAGE_BACKEND` | Optional | `local` | `local`, `s3`, `r2`, `spaces` | Storage backend driver. In production (`DEBUG=False`), setting `s3` requires S3 credentials. |
| `STORAGE_ACCESS_KEY` | Conditional | `None` | String | S3 / R2 access key ID. Required if `STORAGE_BACKEND=s3`. |
| `STORAGE_SECRET_KEY` | Conditional | `None` | String | S3 / R2 secret access key. Required if `STORAGE_BACKEND=s3`. |
| `STORAGE_BUCKET_NAME`| Conditional | `None` | String | S3 / R2 bucket name. Required if `STORAGE_BACKEND=s3`. |
| `STORAGE_REGION` | Optional | `us-east-1` | AWS Region String | AWS Region for S3 bucket. |
| `STORAGE_ENDPOINT_URL`| Optional | `None` | Valid URI | S3-compatible custom endpoint URL (e.g., Cloudflare R2, MinIO, Supabase S3). |
| `ALLOW_LOCAL_STORAGE_IN_PRODUCTION` | Optional | `False` | `True`, `False`, `1`, `0` | Explicit override allowing local disk in production if using a shared NFS volume. |

---

### 2.2 Redis & Caching Configuration
| Variable | Required | Default | Description & Validation Rules |
| :--- | :---: | :---: | :--- |
| `REDIS_URL` | Recommended | `None` | Connection string for Redis cluster/instance (`redis://:password@host:port/0` or `rediss://...` for TLS). |
| `CACHE_URL` / `REDIS_CACHE_URL` | Optional | `None` | Alternative connection string fallback if `REDIS_URL` is omitted. |
| `CACHE_PREFIX` | Optional | `skillsphere` | Key prefix in Redis to prevent key collision across environments. |
| `CACHE_DEFAULT_TIMEOUT` | Optional | `300` | Default cache TTL in seconds. |

---

### 2.3 PostgreSQL Database Configuration
| Variable | Required | Default | Description & Validation Rules |
| :--- | :---: | :---: | :--- |
| `DATABASE_URL` | **Yes** | `None` | PostgreSQL connection string (`postgresql://user:pass@host:port/dbname`). |
| `DB_CONN_MAX_AGE` | Optional | `60` | Persistent DB connection lifetime in seconds. Set to `0` if using PgBouncer in transaction mode. |
| `DB_SSLMODE` | Optional | `require` | SSL mode for Supabase / RDS connection (`require`, `verify-full`). |

---

### 2.4 Security & Core Django Settings
| Variable | Required | Default | Description & Validation Rules |
| :--- | :---: | :---: | :--- |
| `DEBUG` | **Yes** | `False` | Must be `False` in all staging and production deployments. |
| `SECRET_KEY` | **Yes** | `None` | Cryptographic signing key (minimum 50 random characters). |
| `ALLOWED_HOSTS` | **Yes** | `localhost` | Comma-delimited list of valid domain names (e.g., `skillsphere.com,*.skillsphere.com`). |
| `CSRF_TRUSTED_ORIGINS`| **Yes** | `None` | Comma-delimited origins (e.g., `https://skillsphere.com`). |
| `SECURE_SSL_REDIRECT` | Optional | `True` | Forces HTTPS redirection behind TLS termination load balancers. |
| `SECURE_PROXY_SSL_HEADER`| Optional | `HTTP_X_FORWARDED_PROTO,https` | Header indicating HTTPS termination at proxy/load balancer. |

---

### 2.5 Observability & Metrics Configuration
| Variable | Required | Default | Description & Validation Rules |
| :--- | :---: | :---: | :--- |
| `METRICS_AUTH_TOKEN` | Recommended | `None` | Secret bearer token required to access `/api/metrics/`. If unset in production, access is restricted. |
| `INSTANCE_ID` | Optional | Auto-detected | Unique instance identifier. Auto-detects `KUBERNETES_POD_NAME`, `DYNO`, `CF_INSTANCE_INDEX`, or `HOSTNAME`. |

---

### 2.6 Resilience & Distributed Bulkheads
| Variable | Required | Default | Description & Validation Rules |
| :--- | :---: | :---: | :--- |
| `BULKHEAD_AI_LIMIT` | Optional | `5` | Maximum concurrent fleet requests to external AI APIs. |
| `BULKHEAD_PDF_LIMIT` | Optional | `4` | Maximum concurrent ReportLab PDF generation renders across fleet. |
| `BULKHEAD_EXPORT_LIMIT`| Optional | `3` | Maximum concurrent data export operations across fleet. |
| `CIRCUIT_BREAKER_FAIL_THRESHOLD` | Optional | `5` | Consecutive failures before tripping a circuit breaker to OPEN. |
| `CIRCUIT_BREAKER_RESET_TIMEOUT` | Optional | `30.0` | Seconds to hold circuit OPEN before attempting a HALF_OPEN trial. |

---

### 2.7 Background Task Queue Configuration
| Variable | Required | Default | Description & Validation Rules |
| :--- | :---: | :---: | :--- |
| `TASK_QUEUE_WORKER_ID` | Optional | `worker_<uuid>` | Base identifier for this background worker instance. |
| `TASK_QUEUE_LEASE_SECONDS` | Optional | `60` | Default duration of job execution lease before considered stalled. |
| `TASK_QUEUE_LEASE_GRACE_SECONDS`| Optional | `30` | Grace period added to timeout before recovery triggers. |
| `TASK_QUEUE_MAX_RETRIES` | Optional | `3` | Maximum retry attempts before moving a task to `dead_letter`. |

---

## 3. Production Configuration Template (`.env.production.example`)

```bash
# Core Environment
DEBUG=False
SECRET_KEY=change-this-to-a-cryptographically-secure-random-string-at-least-50-chars
ALLOWED_HOSTS=skillsphere-cyan.vercel.app,skillsphere.com,*.skillsphere.com
CSRF_TRUSTED_ORIGINS=https://skillsphere-cyan.vercel.app,https://skillsphere.com

# PostgreSQL via Supabase Connection Pool
DATABASE_URL=postgresql://postgres.xxx:yyy@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
DB_CONN_MAX_AGE=0

# Redis Fleet Cache & Bulkhead Backend
REDIS_URL=rediss://default:secret@redis-cluster.internal:6379/0

# Cloudflare R2 / AWS S3 Object Storage
STORAGE_BACKEND=s3
STORAGE_ACCESS_KEY=your_access_key_id
STORAGE_SECRET_KEY=your_secret_access_key
STORAGE_BUCKET_NAME=skillsphere-production-assets
STORAGE_REGION=auto
STORAGE_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com

# Fleet Observability
METRICS_AUTH_TOKEN=super-secret-prometheus-token-xyz123

# Distributed Bulkheads
BULKHEAD_AI_LIMIT=10
BULKHEAD_PDF_LIMIT=5
```
