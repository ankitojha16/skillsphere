# SkillSphere Phase 18.3 — Cloud Provider Decision & Architecture Evaluation

## 1. Architectural Mandate & Evaluation Objective

To achieve high availability across multiple availability zones and support horizontal autoscaling targeting 10,000 concurrently active students, SkillSphere evaluated two primary cloud deployment architectures:
- **Option A**: **AWS ECS Fargate** (Container orchestration within an Amazon VPC)
- **Option B**: **Google Cloud Run** (Serverless container execution)

This document provides a comprehensive technical comparison based on current official cloud documentation, real application workloads, and pricing models.

---

## 2. In-Depth Architectural Comparison

| Evaluation Criterion | AWS ECS Fargate (Selected Primary) | Google Cloud Run (Documented Alternative) | Architectural Advantage |
| :--- | :--- | :--- | :--- |
| **Independent Web Application Instances** | True long-running container tasks running Gunicorn in an isolated `awsvpc` network namespace across multiple AZs. | Ephemeral container instances spun up per request concurrency. Instance lifetimes are managed dynamically by GCP. | **AWS ECS Fargate**: Predictable network topology, stable IP addresses in private subnets, deterministic lifecycle. |
| **Autoscaling Mechanics** | Target tracking scaling policies on CPU / Memory (70% target) or ALB `RequestCountPerTarget`. Scales smoothly over 1–2 minutes. | Instant request-concurrency autoscaling (scales up in seconds based on max concurrent requests per instance). | **GCP Cloud Run**: Faster scale-from-zero reaction time, but prone to sudden container burst surges. |
| **Multi-Zone Availability** | Native task placement across $\ge 3$ distinct Availability Zones (`ap-south-1a`, `ap-south-1b`, `ap-south-1c`). | Inherently regional service spread across multiple zones within the selected GCP region. | **TIE**: Both support multi-zone resilience. |
| **Managed Relational Database** | Amazon RDS for PostgreSQL with Multi-AZ automated failover and native RDS Proxy / PgBouncer multiplexing. | Cloud SQL for PostgreSQL with High Availability regional failover and Cloud SQL Auth Proxy. | **TIE**: Both offer enterprise-grade managed PostgreSQL 17. |
| **Distributed Cache & Session Store** | Amazon ElastiCache for Redis (Valkey) Multi-AZ replication group with automatic failover. | Google Cloud Memorystore for Redis Standard Tier with automated cross-zone failover. | **TIE**: Both provide sub-millisecond in-memory caching. |
| **Object Storage Integration** | Amazon S3 with CloudFront Origin Access Control (OAC), versioning, and lifecycle policies. | Google Cloud Storage with Cloud Storage XML / S3 interoperability API. | **AWS ECS Fargate**: S3 is the native standard; direct pre-signed URL compatibility with `services/storage_service.py`. |
| **Continuous Background Worker Daemons** | **Native Support**: Worker containers run `python manage.py run_task_worker` continuously, polling tasks, renewing leases, and recovering orphaned jobs. | **Architectural Impediment**: Cloud Run is designed for request-response HTTP workloads. Running continuous daemon workers requires Cloud Run Jobs (batch) or `cpu-always-allocated` with artificial keepalive pings. | **AWS ECS Fargate (Decisive Advantage)**: Seamlessly decouples long-running workers from HTTP endpoints. |
| **WebSocket Support (`/ws/`)** | Application Load Balancer natively terminates WebSockets with configurable timeouts up to 4,000 seconds. | Supported with up to 60-minute streaming request duration. | **AWS ECS Fargate**: Higher timeout ceiling and integrated stickiness options. |
| **Network Latency & VPC Topology** | Direct intra-VPC routing. Sub-millisecond latency between ECS containers, RDS, and ElastiCache. | Serverless VPC Access connector introduces an extra proxy hop (~1–2 ms latency penalty) to access Cloud SQL. | **AWS ECS Fargate**: Lower latency, simpler direct private subnet peering. |
| **Security & Isolation** | Granular AWS IAM Task Execution Roles vs Task Roles. Isolated private subnets without public IPs. | Google Service Accounts with IAM roles; VPC Service Controls. | **TIE**: Both support strict least-privilege security. |
| **Operational Complexity** | Moderate: Managed via modular Terraform (`terraform/aws/modules/`). Familiar enterprise pattern. | Low to Moderate: Fewer infrastructure components, but higher friction for worker daemons. | **AWS ECS Fargate**: Standard enterprise pattern for containerized Django fleets. |
| **Expected Monthly Staging Cost** | ~$135 / month (Fixed baseline across Multi-AZ RDS, Redis, and 2 Fargate tasks). | ~$95 / month (Lower due to aggressive idle scale-down). | **GCP Cloud Run**: Marginally cheaper for idle staging; comparable at scale. |

---

## 3. Final Recommendation & Strategic Decision

### Selected Primary Architecture: **AWS ECS Fargate**
**Rationale**:
1. **Continuous Queue Worker Affinity**: SkillSphere relies on continuous background worker loops ([`analytics/management/commands/run_task_worker.py`](file:///Users/ankitkumar/Desktop/wealthtrack/AnkitPortfolio/skill%20sphare/analytics/management/commands/run_task_worker.py)) with fencing tokens and atomic lease renewals (`SELECT FOR UPDATE SKIP LOCKED`). Running continuous daemons on AWS ECS Fargate is a native, battle-tested architectural pattern.
2. **Deterministic Database Multiplexing**: Fargate tasks maintain stable, persistent client connection pools to PgBouncer. Cloud Run's rapid cold-start container bursting can spike client connections unpredictably.
3. **Direct S3 Ecosystem Alignment**: SkillSphere's `S3CompatibleStorageService` and pre-signed URL security integrate natively with AWS S3 and CloudFront OAC.

### Documented Alternative: **Google Cloud Run**
GCP Cloud Run remains fully supported via `terraform/gcp/` for organizations seeking a fully serverless environment where background queues are offloaded to Cloud Tasks or Google Pub/Sub.
