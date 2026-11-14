# SkillSphere Phase 18.3 — Cloud Cost & Capacity Model

## 1. Cost Architecture & Modeling Principles

SkillSphere's infrastructure cost model is engineered to scale proportionally with active student engagement while establishing strict fixed-baseline budget boundaries:

1. **Fixed Infrastructure**: Dedicated Multi-AZ database, managed Redis cache, and baseline compute tasks guarantee five-nines availability regardless of traffic dips.
2. **Variable Infrastructure**: ECS Fargate autoscaling, S3 object storage bytes, CDN egress, and AI API tokens scale dynamically with student concurrency.
3. **Region Baseline**: Pricing modeled for **AWS Region `ap-south-1` (Mumbai)** based on official AWS Pricing Calculator figures (Q4 2026).

---

## 2. Monthly Cost Estimates Across Operational Tiers

| Cloud Component | Tier 1: Staging / Dev | Tier 2: 1,000 CCU | Tier 3: 5,000 CCU | Tier 4: 10,000 CCU (Peak Target) | Cost Type |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Compute: Web Tasks (Fargate)** | $30 / mo (2 tasks, 1vCPU/2GB) | $60 / mo (4 tasks) | $150 / mo (10 tasks) | $300 / mo (20 tasks) | Variable |
| **Compute: Worker Tasks (Fargate)**| $30 / mo (2 tasks, 1vCPU/2GB) | $30 / mo (2 tasks) | $60 / mo (4 tasks) | $150 / mo (10 tasks) | Variable |
| **Application Load Balancer** | $25 / mo + $5 LCU | $25 / mo + $12 LCU | $25 / mo + $35 LCU | $25 / mo + $70 LCU | Fixed + Variable |
| **Database: RDS PostgreSQL** | $45 / mo (`db.t4g.medium`) | $75 / mo (`db.r6g.large`) | $155 / mo (`db.r6g.xlarge`) | $310 / mo (`db.r6g.2xlarge`) | Fixed |
| **Cache: ElastiCache Redis** | $25 / mo (`cache.t4g.small`)| $45 / mo (`cache.t4g.med`) | $90 / mo (`cache.r6g.large`) | $180 / mo (`cache.r6g.xlarge`) | Fixed |
| **Object Storage (S3 & Requests)** | $5 / mo (50 GB storage) | $15 / mo (200 GB) | $50 / mo (1 TB) | $120 / mo (3 TB + Put/Get) | Variable |
| **CDN & Data Transfer (CloudFront)**| $5 / mo (50 GB egress) | $20 / mo (300 GB) | $90 / mo (2 TB) | $180 / mo (5 TB egress) | Variable |
| **Observability (CloudWatch Logs)**| $5 / mo (Basic retention) | $15 / mo | $35 / mo | $65 / mo | Variable |
| **AI LLM API Tokens (Tutoring)** | $10 / mo (Synthetic testing)| $45 / mo | $235 / mo | $470 / mo | Variable |
| **ESTIMATED MONTHLY TOTAL** | **~$180 / month** | **~$342 / month** | **~$890 / month** | **~$1,870 / month** | — |

---

## 3. Workload Assumptions & Unit Economics

- **Compute Unit Cost**: AWS Fargate pricing: $0.04048 per vCPU-hour, $0.004445 per GB-hour in `ap-south-1`.
- **Database Multiplexing**: PgBouncer ensures `db.r6g.2xlarge` supports 10,000 CCU by maintaining active connections $\le 80$.
- **Bandwidth Optimization**: Static assets and video content are cached at CloudFront edge POPs, reducing origin egress costs by $\approx 78\%$.
- **Cost per Concurrent Student**:
  - At 1,000 CCU: **$0.34 per CCU / month**.
  - At 10,000 CCU: **$0.19 per CCU / month** (demonstrating strong positive economies of scale).

---

## 4. Cost Governance & Budget Alerting

To prevent unexpected billing spikes:
1. **AWS Budgets Alert**: Configured at $250/mo for staging and $1,200/mo for production, dispatching SNS email alerts at 85% forecast.
2. **S3 Lifecycle Rules**: Incomplete multipart uploads are aborted automatically after 7 days; non-current versions transition to S3 Glacier after 30 days.
3. **Fargate Max Capacity Caps**: Hard limits (`web_max_capacity = 20`, `worker_max_capacity = 10`) prevent runaway compute autoscaling.
