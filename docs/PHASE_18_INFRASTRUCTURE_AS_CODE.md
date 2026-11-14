# SkillSphere Phase 18 — Infrastructure as Code (Terraform) Reference

## 1. Executive Summary

This document references the modular Infrastructure as Code (IaC) implementation created in `terraform/aws/` for the recommended AWS ECS Fargate deployment, and in `terraform/gcp/` for the alternative Google Cloud Run deployment.

> [!NOTE]
> All Terraform configurations are complete, modular, and reviewable. In accordance with user restrictions, **no paid cloud resources have been created or provisioned**.

---

## 2. Terraform Module Architecture (`terraform/aws/`)

```
terraform/aws/
├── main.tf                    # Root orchestration wiring all submodules
├── variables.tf               # Environment variables and capacity tunables
├── outputs.tf                 # Key endpoints (ALB DNS, RDS endpoint, Redis endpoint)
└── modules/
    ├── vpc/                   # Multi-AZ VPC across 3 Availability Zones
    ├── security/              # Least-privilege security groups and IAM roles
    ├── storage/               # Amazon S3 bucket with CloudFront Origin Access Control
    ├── database/              # Amazon RDS PostgreSQL (Multi-AZ with Automated Backups)
    ├── cache/                 # Amazon ElastiCache Redis (Multi-AZ Replication Group)
    └── ecs/                   # ECS Fargate Cluster, Task Definitions, ALB & Auto Scaling
```

---

## 3. Module Breakdown & Security Specifications

### 3.1 Network Module (`modules/vpc/main.tf`)
- **Multi-AZ Architecture**: Provisions 3 Public Subnets, 3 Private App Subnets, and 3 Private Data Subnets across Availability Zones in `ap-south-1`.
- **Egress Security**: Deploys 3 NAT Gateways ensuring application containers communicate outbound securely without having public IP addresses.

### 3.2 Security Module (`modules/security/main.tf`)
- **Micro-segmentation**:
  - `alb-sg`: Permits HTTP/HTTPS from Internet.
  - `ecs-web-sg`: Ingress restricted exclusively to traffic originating from `alb-sg`.
  - `rds-sg`: Ingress port 5432 restricted strictly to `ecs-web-sg` and `ecs-worker-sg`.
  - `redis-sg`: Ingress port 6379 restricted strictly to `ecs-web-sg` and `ecs-worker-sg`.

### 3.3 Storage Module (`modules/storage/main.tf`)
- **S3 Bucket**: Versioning enabled, AES-256 server-side encryption enforced, and public bucket access completely blocked.
- **CloudFront OAC**: Origin Access Control ensures S3 files are accessible only via authenticated CloudFront distributions, preventing origin bypass.

### 3.4 Database & Cache Modules (`modules/database`, `modules/cache`)
- **RDS Multi-AZ**: High-availability PostgreSQL 17 with automated snapshots (30-day retention), PITR, and Performance Insights.
- **ElastiCache Redis**: Multi-AZ replication group with in-transit and at-rest encryption and automated failover.

### 3.5 Compute & Autoscaling Module (`modules/ecs/main.tf`)
- **Task Definitions**: Hardened Fargate tasks with CloudWatch log shipping.
- **Target Tracking Autoscaling**:
  - Dynamically adjusts web tasks between 2 and 20 based on 70% average CPU utilization.
  - Scale-out cooldown: $60\text{ seconds}$ (rapid response to traffic bursts).
  - Scale-in cooldown: $300\text{ seconds}$ (prevents thrashing).

---

## 4. Environment Separation & State Management

### 4.1 Remote State Configuration
In production environments, Terraform state must be stored in an encrypted remote backend with state locking:
```hcl
terraform {
  backend "s3" {
    bucket         = "skillsphere-terraform-state"
    key            = "environments/production/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "skillsphere-terraform-locks"
    encrypt        = true
  }
}
```

### 4.2 Workspace / Variable Profiles
- `staging.tfvars`: Minimum tasks = 2, db.t4g.medium, cache.t4g.medium.
- `production.tfvars`: Minimum tasks = 4, db.r6g.xlarge Multi-AZ, cache.r6g.large Multi-AZ.
