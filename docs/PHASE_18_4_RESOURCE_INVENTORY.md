# SkillSphere Phase 18.4 — AWS Staging Resource Inventory

**Target Environment**: AWS Staging (`ap-south-1`)  
**Deployment Identifier**: `skillsphere-staging`  
**State**: Defined & Validated in Terraform (Pending Owner Provisioning Authorization)

---

## 1. Network & VPC Resource Inventory

| Resource Type | Logical Name / Identifier | CIDR / Specification | Placement / Zone | Routing Target |
| :--- | :--- | :--- | :--- | :--- |
| `aws_vpc` | `skillsphere-staging-vpc` | `10.0.0.0/16` | `ap-south-1` (Mumbai) | Default Local |
| `aws_subnet` (Public 1) | `skillsphere-staging-public-1` | `10.0.0.0/20` | `ap-south-1a` | Internet Gateway |
| `aws_subnet` (Public 2) | `skillsphere-staging-public-2` | `10.0.16.0/20` | `ap-south-1b` | Internet Gateway |
| `aws_subnet` (Public 3) | `skillsphere-staging-public-3` | `10.0.32.0/20` | `ap-south-1c` | Internet Gateway |
| `aws_subnet` (Private App 1) | `skillsphere-staging-private-app-1`| `10.0.48.0/20` | `ap-south-1a` | NAT Gateway 1 + S3 GW Endpoint |
| `aws_subnet` (Private App 2) | `skillsphere-staging-private-app-2`| `10.0.64.0/20` | `ap-south-1b` | NAT Gateway 2 + S3 GW Endpoint |
| `aws_subnet` (Private App 3) | `skillsphere-staging-private-app-3`| `10.0.80.0/20` | `ap-south-1c` | NAT Gateway 3 + S3 GW Endpoint |
| `aws_subnet` (Private Data 1)| `skillsphere-staging-private-data-1`| `10.0.96.0/20`| `ap-south-1a` | Local VPC Only (Isolated) |
| `aws_subnet` (Private Data 2)| `skillsphere-staging-private-data-2`| `10.0.112.0/20`| `ap-south-1b`| Local VPC Only (Isolated) |
| `aws_subnet` (Private Data 3)| `skillsphere-staging-private-data-3`| `10.0.128.0/20`| `ap-south-1c`| Local VPC Only (Isolated) |
| `aws_internet_gateway` | `skillsphere-staging-igw` | N/A | VPC-attached | Public Ingress / Egress |
| `aws_eip` (NAT 1..3) | `skillsphere-staging-nat-eip-[1..3]` | 3x Static IPv4 | Public Subnets 1..3 | Attached to NAT Gateways |
| `aws_nat_gateway` (1..3) | `skillsphere-staging-nat-[1..3]` | Managed NAT | Public Subnets 1..3 | Outbound Private App Internet |
| `aws_vpc_endpoint` | `skillsphere-staging-s3-gw-endpoint` | Gateway Type | VPC-wide | Direct S3 route (Free) |

---

## 2. Security Groups Matrix (Least-Privilege Isolation)

| Security Group | Ingress Rules | Egress Rules | Purpose |
| :--- | :--- | :--- | :--- |
| **`alb-sg`** | Port 80 & 443 from `0.0.0.0/0` | Port 8000 to `ecs-web-sg` | Public HTTP/HTTPS ingress |
| **`ecs-web-sg`** | Port 8000 strictly from `alb-sg` | `0.0.0.0/0` (via NAT Gateway) | Gunicorn web container ingress |
| **`ecs-worker-sg`** | None (Zero inbound open ports) | `0.0.0.0/0` (via NAT Gateway) | Background task daemon egress |
| **`rds-sg`** | Port 5432 from `ecs-web-sg`, `ecs-worker-sg` | `0.0.0.0/0` (local) | PostgreSQL DB access |
| **`redis-sg`** | Port 6379 from `ecs-web-sg`, `ecs-worker-sg` | `0.0.0.0/0` (local) | Redis cache & locks |

---

## 3. Compute Tier (AWS ECS Fargate)

| Component | Resource Type | Capacity / Sizing | Configuration |
| :--- | :--- | :--- | :--- |
| **ECS Cluster** | `aws_ecs_cluster` | `skillsphere-staging-cluster` | Container Insights enabled |
| **Web Service** | `aws_ecs_service` | 2 tasks baseline (scales to 20) | Fargate, Port 8000, Private App subnets |
| **Web Task Def** | `aws_ecs_task_definition` | 1024 CPU (1 vCPU), 2048 MB RAM | Gunicorn (2 workers, 4 threads) |
| **Worker Service** | `aws_ecs_service` | 2 tasks baseline (scales to 10) | Fargate, Private App subnets |
| **Worker Task Def**| `aws_ecs_task_definition` | 1024 CPU (1 vCPU), 2048 MB RAM | `python manage.py run_task_worker` |
| **Auto Scaling** | `aws_appautoscaling_policy` | Min: 2, Max: 20 | Target tracking: 70% CPU utilization |
| **Load Balancer** | `aws_lb` (Application) | Dual-AZ public ALB | Health probe: `/health/live/` |

---

## 4. Managed Services & Persistent Storage Tier

| Service | Resource Type | Engine / Tier | Resilience / Sizing |
| :--- | :--- | :--- | :--- |
| **Relational Database** | `aws_db_instance` | PostgreSQL 17.4 | Multi-AZ DB Instance, 100 GB gp3 storage, 30-day backups |
| **Distributed Cache** | `aws_elasticache_replication_group` | Redis 7.x | 2-node Multi-AZ replication group with automatic failover |
| **Object Storage** | `aws_s3_bucket` | Standard S3 | `skillsphere-staging-media-assets`, Versioning, SSE-S3 |
| **Origin Access** | `aws_cloudfront_origin_access_control`| CloudFront OAC | SigV4 authenticated S3 access |
| **Secrets Store** | `aws_secretsmanager_secret` | AWS KMS encrypted | `skillsphere-staging-app-secrets` (DB, Redis, App keys) |

---

## 5. IAM Roles & Policies

| Role Name | Trusted Entity | Attached Policies | Permissions Scope |
| :--- | :--- | :--- | :--- |
| **`ecs-execution-role`** | `ecs-tasks.amazonaws.com` | `AmazonECSTaskExecutionRolePolicy`<br>`execution-secrets` | CloudWatch logging, ECR image pull, `secretsmanager:GetSecretValue` |
| **`ecs-task-role`** | `ecs-tasks.amazonaws.com` | `task-s3-policy` | `s3:GetObject`, `PutObject`, `DeleteObject`, `ListBucket` on media bucket |
