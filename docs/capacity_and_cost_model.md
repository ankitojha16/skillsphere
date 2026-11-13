# SkillSphere Phase 16: Enterprise Architecture Evaluation, Capacity & Cost Model

## 1. Hosting Architecture Comparison: Option A vs. Option B

### Executive Summary
To support 10,000 concurrent active users generating 500–833 dynamic requests per second (RPS), we evaluate two production deployment architectures:
- **Option A**: Optimized Vercel Serverless + Supabase PgBouncer + Cloudflare/Vercel Edge CDN + Shared Redis.
- **Option B**: Containerized Horizontal Autoscaling (GCP Cloud Run / AWS ECS Fargate) behind an Application Load Balancer + Supabase PgBouncer.

---

### Detailed Architecture Comparison Matrix

| Evaluation Dimension | Option A: Optimized Vercel Serverless | Option B: Managed Containers (Cloud Run / ECS) |
|---|---|---|
| **Architecture Model** | Serverless functions (`@vercel/python` on AWS Lambda, region `bom1`) with Edge CDN | Stateless container tasks running Gunicorn with `gthread` workers behind ALB |
| **Max Concurrency** | 1,000 concurrent executions (Vercel Pro default). Spike traffic risks execution throttling. | Autoscales from 2 to 30 tasks seamlessly based on CPU/concurrency targets (100 req/task). |
| **Database Connections** | Serverless functions create transient connections. **Requires PgBouncer Transaction Pooler** (port 6543) with `CONN_MAX_AGE=0` to prevent exhausting Supabase's 60-connection pool limit. | Persistent connection pool (`CONN_MAX_AGE=60`). 10 container tasks with 5 workers each hold a predictable, bounded pool of 50 connections to PgBouncer. |
| **Cold Starts & Latency** | 250ms–700ms cold starts when scaling up from 0 to hundreds of lambda instances during sudden traffic bursts. | Zero cold starts for warm tasks; minimum 2 active tasks always running. Sub-10ms intra-VPC latency. |
| **Long-Running / Background Tasks** | Execution timeout hard capped at 60s (Pro). Cannot run long-running daemon workers on Vercel without external service. | Can run dedicated Celery / durable worker containers with arbitrary timeouts (10–30 mins for batch exports). |
| **WebSockets & Collaboration** | WSGI lambdas cannot maintain stateful WebSocket connections (requires external WebSocket service like Pusher/Supabase Realtime). | Native ASGI support (Uvicorn / Daphne) for persistent WebSockets in 1v1 Arena and Pair Lounge. |
| **Deployment Complexity** | **Very Low**: Git push to `main` triggers automated build and atomic edge aliasing. Zero infrastructure management. | **Moderate**: Requires Docker container registry, Terraform/CloudFormation, ALB SSL certs, VPC networking, and autoscaling policies. |
| **Operational Reliability** | High for standard web traffic; dependent on Vercel platform limits during extreme 10K concurrency spikes. | Very High: Enterprise SLA, dedicated resource guarantees, independent memory and CPU isolation. |
| **Monthly Operating Cost (10K Users)** | **\$380 – \$550 / month** (driven by function invocation count and duration: ~45M invocations/mo). | **\$220 – \$340 / month** (fixed vCPU/RAM container hours; significantly cheaper at sustained high RPS). |
| **Migration Risk** | **Zero Risk**: Current proven deployment platform, zero migration downtime. | **Moderate Risk**: Requires DNS migration, secret re-provisioning, and CI/CD pipeline overhaul. |

---

### Evidence-Based Hosting Recommendation
- **Current Production Recommendation**: **Retain and Optimize Option A (Vercel Serverless + Supabase PgBouncer)** for current operations and initial scaling. With our Phase 16 optimizations (parameterized catalogue caching, 1-year immutable static assets, `DISABLE_SERVER_SIDE_CURSORS`, 10s statement timeouts, and cached sessions), Vercel + Supabase handles up to **2,500–5,000 concurrent active users** cleanly.
- **Strategic Evolution Threshold**: If sustained platform concurrency exceeds **5,000 active users** or monthly traffic exceeds **50 million function invocations**, migrate the web tier to **Option B (GCP Cloud Run or AWS ECS Fargate)** to achieve lower unit costs (\$0.000008 per request vs. \$0.00004 on serverless) and native persistent WebSocket support.

---

## 2. Gunicorn Worker Sizing & Benchmarking (For Containerized Deployment)

### Resource Formula:
$$\text{Workers} = (2 \times \text{vCPUs}) + 1$$
$$\text{Threads per Worker} = 4 \text{ to } 8 \text{ (gthread worker class)}$$

### Benchmark Parameters (per 2 vCPU, 2GB RAM Container Instance):
- **Gunicorn Workers**: $2 \times 2 + 1 = \mathbf{5\text{ workers}}$
- **Worker Class**: `gthread` (Threaded worker model ideal for mixed I/O and DB queries)
- **Threads per Worker**: 4 threads $\implies$ $5 \times 4 = \mathbf{20\text{ concurrent requests per container task}}$
- **Memory Footprint**:
  - Base Django + dependencies: ~85 MB
  - Active worker process footprint: ~35 MB
  - Total per container task: $85\text{ MB} + (5 \times 35\text{ MB}) \approx \mathbf{260\text{ MB RAM}}$ (well within 2GB allocation)
- **Cluster Capacity**:
  - 10 container tasks: $10 \times 20 = 200\text{ concurrent threads} \implies$ **1,000+ RPS sustained** at average 200ms latency.
  - Autoscaling trigger: Average CPU utilization $> 65\%$ or Request Count $> 150\text{ req/min/task}$.

---

## 3. Infrastructure Cost Model (1,000 / 5,000 / 10,000 Concurrent Users)

### Cost Assumptions:
- **Active Hours**: 16 peak hours/day, 8 off-peak hours/day.
- **Workload**: 10,000 active users $\implies$ 500 average dynamic RPS, ~45 million dynamic requests/month.
- **Static Assets**: 90% served from CDN edge cache at \$0.085/GB.
- **AI Integrations**: Gemini 3.8 Flash cascade with aggressive Knowledge Engine offline fallback.

| Infrastructure Component | 1,000 Concurrent Users (50 RPS) | 5,000 Concurrent Users (250 RPS) | 10,000 Concurrent Users (500 RPS) | Cost Driver & Sizing Notes |
|---|---|---|---|---|
| **Web & API Hosting** | \$20 / mo (Vercel Pro) | \$150 / mo (Vercel overages or Cloud Run) | \$280 / mo (Cloud Run: 8–16 tasks or Vercel Pro invocations) | Dynamic HTTP requests & CPU duration |
| **PostgreSQL Database** | \$25 / mo (Supabase Pro) | \$25 / mo (Supabase Pro with PgBouncer) | \$60 / mo (Supabase Pro + Compute Add-on 4 vCPU) | Connection pooling on port 6543 handles all connections |
| **Shared Redis Cache** | \$0 / mo (Upstash Free tier) | \$20 / mo (Upstash Redis Pro) | \$40 / mo (Upstash Redis 100K commands/day) | Session caching, catalogue caching, rate limiting |
| **Object Storage (Media/Uploads)** | \$5 / mo (AWS S3 / Supabase) | \$15 / mo (Supabase Storage 50GB) | \$30 / mo (AWS S3 / Cloudflare R2 100GB) | Resumes, avatar uploads, bug report screenshots |
| **CDN & Network Egress** | \$10 / mo | \$35 / mo | \$65 / mo | Cloudflare / Vercel Edge CDN egress (~600 GB/mo) |
| **Background Task Workers** | Included in web tier | \$15 / mo (Durable queue worker) | \$35 / mo (Dedicated worker task) | PDF compilation, email dispatch, data exports |
| **Application Monitoring** | \$0 / mo (Sentry Developer) | \$29 / mo (Sentry Team plan) | \$65 / mo (Sentry Business + Datadog APM) | Error tracking, distributed tracing, performance alerts |
| **Transactional Email** | \$0 / mo (SendGrid Free 100/day)| \$15 / mo (SendGrid Essentials 50K/mo) | \$35 / mo (SendGrid Pro 100K/mo) | Password resets, certificate notifications |
| **AI API Usage (Gemini)** | \$10 / mo | \$35 / mo | \$70 / mo (Gemini 3.8 Flash + Knowledge Engine fallback) | Token usage capped by rate limits (20 req/min/user) |
| **Backup & Disaster Recovery** | Included in Supabase Pro | Included in Supabase Pro | \$15 / mo (Daily S3 WAL snapshot archiving) | Offsite Point-in-Time Recovery (PITR) |
| **TOTAL ESTIMATED MONTHLY COST** | **\$70 / month** | **\$339 / month** | **\$695 / month** | Complete enterprise platform cost |

---

### Budget Alerts & Cost Control Policies:
1. **Vercel Spend Alerts**: Configure soft alert at \$200/mo and hard budget alert at \$400/mo in Vercel Billing Settings.
2. **Supabase Compute Threshold**: Set Supabase alerts for CPU utilization $> 80\%$ sustained over 15 minutes.
3. **AI Cost Cap**: Enforce `AI_RATE_LIMIT_PER_MINUTE = 20` and 1ms fast-fail to the local Knowledge Engine if Gemini API costs exceed \$100/mo.
4. **Upstash Redis Capping**: Set daily spend cap of \$5/day on Redis command invocations.
