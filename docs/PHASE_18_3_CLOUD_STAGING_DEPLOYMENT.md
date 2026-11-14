# SkillSphere Phase 18.3 — Cloud Staging Deployment & Infrastructure Topology

## 1. Staging Architecture Overview & Multi-AZ Topology

The SkillSphere cloud staging environment is deployed to **AWS Region `ap-south-1`** across three Availability Zones (`ap-south-1a`, `ap-south-1b`, `ap-south-1c`). 

It provides an isolated pre-production environment strictly segregated from live production traffic, production databases, and user credentials.

```
                                  [ Internet / Public Ingress ]
                                                │
                                                ▼
                   +──────────────────────────────────────────────────────────+
                   |           Application Load Balancer (ALB)                |
                   |   - Public Subnets across AZ-1a, AZ-1b, AZ-1c            |
                   |   - TLS 1.3 / HTTP to HTTPS Redirection                  |
                   |   - Health check: /health/live/                          |
                   +────────────────────────────┬─────────────────────────────+
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 │                                                             │
                 ▼                                                             ▼
  +─────────────────────────────+                               +─────────────────────────────+
  |  Private App Subnet (AZ-1a) |                               |  Private App Subnet (AZ-1b) |
  |  ├── ECS Fargate: Web Task 1|                               |  ├── ECS Fargate: Web Task 2|
  |  └── ECS Fargate: Worker 1  |                               |  └── ECS Fargate: Worker 2  |
  +──────────────┬──────────────+                               +──────────────┬──────────────+
                 │                                                             │
                 └──────────────────────────────┬──────────────────────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 │                                                             │
                 ▼                                                             ▼
  +─────────────────────────────────────────────+               +─────────────────────────────+
  |        Private Data Subnets (No IGW)        |               |       Object Storage        |
  |  ├── Amazon RDS PostgreSQL 17 (Multi-AZ)    |               |  ├── Amazon S3 Staging      |
  |  │   └── PgBouncer Connection Pooler        |               |  │   (Encrypted / Private)  |
  |  └── Amazon ElastiCache Redis Replication   |               |  └── CloudFront CDN OAC     |
  +─────────────────────────────────────────────+               +─────────────────────────────+
```

---

## 2. Infrastructure Inventory & Staging Topology

| Tier / Component | Cloud Resource Type | Sizing & Allocation | Availability & Redundancy |
| :--- | :--- | :--- | :--- |
| **Ingress Load Balancer** | AWS Application Load Balancer | Dual-stack IPv4/IPv6, 3 subnets | Cross-zone load balancing enabled |
| **Web Application Fleet** | AWS ECS Fargate Tasks | 2 Tasks (1 vCPU, 2 GB RAM per task) | Multi-AZ (AZ-1a and AZ-1b) |
| **Background Worker Fleet**| AWS ECS Fargate Tasks | 2 Tasks (1 vCPU, 2 GB RAM per task) | Multi-AZ (AZ-1a and AZ-1b) |
| **Staging Relational DB** | Amazon RDS for PostgreSQL 17 | `db.t4g.medium` (2 vCPU, 4 GB RAM) | Multi-AZ failover enabled |
| **Database Pooler** | PgBouncer Container / RDS Proxy| `max_client_conn=500`, pool=40 | Transaction-mode multiplexing |
| **Distributed Cache** | Amazon ElastiCache Redis | `cache.t4g.small` (1.37 GB RAM) | Multi-AZ with automatic failover |
| **Object Storage** | Amazon S3 Bucket | `skillsphere-staging-media` | Versioning enabled, AES256 SSE |
| **Observability** | CloudWatch Logs & Metrics | `/ecs/skillsphere-staging-*` | 14-day retention, Container Insights |

---

## 3. Strict Staging Isolation Guarantees

To ensure complete safety and prevent staging operations from compromising production data:
1. **Network Boundary**: Staging runs inside an independent VPC CIDR (`10.1.0.0/16`) separate from production (`10.0.0.0/16`).
2. **Authoritative Database Separation**: Staging utilizes an isolated PostgreSQL instance (`skillsphere_staging`). Under no circumstances is staging connected to the production Supabase database.
3. **Synthetic Student Accounts**: Staging is pre-seeded with synthetic test profiles (`staging_student_alice`, `staging_student_bob`) with randomized hashes.
4. **Isolated S3 Storage**: All file uploads target `skillsphere-staging-media`. Cross-bucket IAM policies block access to production assets.

---

## 4. Turnkey Deployment Sequence

The cloud staging environment is deployed via [`scripts/deploy_cloud_staging.sh`](file:///Users/ankitkumar/Desktop/wealthtrack/AnkitPortfolio/skill%20sphare/scripts/deploy_cloud_staging.sh):

```bash
# 1. Provision staging environment variables template:
cp .env.staging.example .env.staging

# 2. Run pre-flight verification & dry-run audit:
./scripts/deploy_cloud_staging.sh

# 3. When authorized by project owner, apply infrastructure changes:
./scripts/deploy_cloud_staging.sh --apply
```
