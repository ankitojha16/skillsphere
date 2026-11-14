# SkillSphere Phase 18 — Comprehensive Cost & Operational Planning

## 1. Executive Summary & Cost Modeling Methodology

This document provides itemized monthly cost projections for operating SkillSphere across development, staging, and production tiers from **1,000 to 10,000 concurrent active users (CCU)**.

### Pricing Baseline:
- Region: AWS `ap-south-1` (Mumbai)
- Fargate vCPU: \$0.04048 per vCPU-hour
- Fargate Memory: \$0.004445 per GB-hour
- RDS PostgreSQL: Multi-AZ on gp3 SSD storage
- ElastiCache Redis: Multi-AZ replication group
- CloudFront CDN: Outbound egress to Internet

---

## 2. Workload & Operational Parameters

| Parameter | 1,000 CCU | 5,000 CCU | 10,000 CCU |
| :--- | :---: | :---: | :---: |
| **Average Daily Active Users (DAU)** | 15,000 | 75,000 | 150,000 |
| **Average Session Duration** | 20 minutes | 20 minutes | 20 minutes |
| **Requests Per User Session** | 60 requests | 60 requests | 60 requests |
| **Total Daily HTTP Requests** | 900,000 | 4,500,000 | 9,000,000 |
| **Peak Total RPS (Edge)** | 215 RPS | 1,070 RPS | 2,140 RPS |
| **Peak Dynamic RPS (Django Fleet)** | 85 RPS | 425 RPS | 855 RPS |
| **Monthly Outbound CDN Egress** | 450 GB | 2.25 TB | 4.5 TB |
| **Object Storage (PDFs/Resumes)** | 50 GB | 250 GB | 750 GB |
| **AI Assistant Prompts / Day** | 1,500 | 7,500 | 15,000 |

---

## 3. Itemized Monthly Cost Breakdown

### 3.1 Development & Staging Tier (Local / Docker Compose / Minimal Cloud)
- **ECS Fargate**: 1 Web + 1 Worker task (1 vCPU, 2 GB) = \$65/mo
- **RDS PostgreSQL**: db.t4g.small (Single AZ) = \$28/mo
- **ElastiCache Redis**: cache.t4g.micro = \$14/mo
- **NAT Gateway & Networking**: \$35/mo
- **Total Staging Cost**: **~\$142 / month**

---

### 3.2 Tier 1: 1,000 Concurrent Active Users
| Service Component | Sizing & Specifications | Fixed Cost | Variable Cost | Total Monthly |
| :--- | :--- | :---: | :---: | :---: |
| **ECS Web Service** | 2 tasks (1 vCPU, 2 GB) Multi-AZ | \$65 | — | \$65 |
| **ECS Worker Service** | 2 tasks (1 vCPU, 2 GB) Multi-AZ | \$65 | — | \$65 |
| **Amazon RDS PostgreSQL**| db.t4g.medium Multi-AZ (100 GB gp3) | \$72 | — | \$72 |
| **ElastiCache Redis** | cache.t4g.medium Multi-AZ | \$38 | — | \$38 |
| **Application Load Balancer**| 1 ALB + LCU processing charges | \$22 | \$8 | \$30 |
| **CloudFront CDN Egress**| 450 GB data transfer out | — | \$38 | \$38 |
| **Amazon S3 Storage** | 50 GB standard storage + PUT/GET | \$1 | \$2 | \$3 |
| **CloudWatch Logs & Metrics**| Log ingestion & 10 custom metrics | \$10 | \$5 | \$15 |
| **Gemini AI API Costs** | 45,000 prompts/mo (Flash Lite) | — | \$12 | \$12 |
| **TOTAL TIER 1** | | **\$273** | **\$65** | **~\$338 / month** |

---

### 3.3 Tier 2: 5,000 Concurrent Active Users
| Service Component | Sizing & Specifications | Fixed Cost | Variable Cost | Total Monthly |
| :--- | :--- | :---: | :---: | :---: |
| **ECS Web Service** | 6 tasks (2 vCPU, 4 GB) Multi-AZ | \$390 | — | \$390 |
| **ECS Worker Service** | 4 tasks (1 vCPU, 2 GB) Multi-AZ | \$130 | — | \$130 |
| **Amazon RDS PostgreSQL**| db.r6g.large Multi-AZ (250 GB gp3) | \$260 | — | \$260 |
| **ElastiCache Redis** | cache.r6g.large Multi-AZ | \$155 | — | \$155 |
| **Application Load Balancer**| 1 ALB + LCU processing charges | \$25 | \$35 | \$60 |
| **CloudFront CDN Egress**| 2.25 TB data transfer out | — | \$185 | \$185 |
| **Amazon S3 Storage** | 250 GB standard storage | \$6 | \$5 | \$11 |
| **CloudWatch Logs & Metrics**| Log ingestion & metrics retention | \$20 | \$15 | \$35 |
| **Gemini AI API Costs** | 225,000 prompts/mo | — | \$55 | \$55 |
| **TOTAL TIER 2** | | **\$986** | **\$295** | **~\$1,281 / month** |

---

### 3.4 Tier 3: 10,000 Concurrent Active Users (Peak Target)
| Service Component | Sizing & Specifications | Fixed Cost | Variable Cost | Total Monthly |
| :--- | :--- | :---: | :---: | :---: |
| **ECS Web Service** | 12 tasks (2 vCPU, 4 GB) Multi-AZ | \$780 | — | \$780 |
| **ECS Worker Service** | 6 tasks (2 vCPU, 4 GB) Multi-AZ | \$390 | — | \$390 |
| **Amazon RDS PostgreSQL**| db.r6g.xlarge Multi-AZ + Read Replica | \$520 | — | \$520 |
| **ElastiCache Redis** | cache.r6g.large Multi-AZ | \$155 | — | \$155 |
| **Application Load Balancer**| 1 ALB + high LCU throughput | \$25 | \$85 | \$110 |
| **CloudFront CDN Egress**| 4.5 TB data transfer out | — | \$365 | \$365 |
| **Amazon S3 Storage** | 750 GB storage + lifecycle rules | \$18 | \$12 | \$30 |
| **CloudWatch & Telemetry** | High-throughput logging & alarms | \$30 | \$35 | \$65 |
| **Gemini AI API Costs** | 450,000 prompts/mo | — | \$110 | \$110 |
| **TOTAL TIER 3** | | **\$1,918** | **\$607** | **~\$2,525 / month** |

---

## 4. Cost Optimization & Risk Mitigation

1. **AWS Compute Savings Plans**: Committing to a 1-year Compute Savings Plan reduces Fargate compute expenses by up to **$28\%$**, lowering Tier 3 ECS costs from \$1,170 to ~\$842/mo.
2. **CDN Offloading Efficiency**: Increasing static cache TTL and caching public course catalog fragments in CloudFront saves up to \$180/mo in dynamic compute and database read load.
3. **Database Idle Connection Savings**: PgBouncer transaction pooling prevents over-provisioning RDS RAM solely for idle connection memory buffers.
