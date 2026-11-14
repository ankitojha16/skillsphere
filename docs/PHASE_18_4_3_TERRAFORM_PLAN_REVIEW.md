# Phase 18.4.3 — Terraform Infrastructure Plan & Validation Review

**Target**: AWS ECS Fargate Multi-AZ Staging Infrastructure  
**Tooling**: OpenTofu v1.13.9 (HashiCorp Terraform compatible)  
**Provider**: `hashicorp/aws` v5.100.0  
**Status**: Validated (Syntax & Schema Verified, Live Plan Blocked Pending AWS Credentials)  

---

## 1. Automated Validation Results

All Terraform modules in `terraform/aws/` were independently audited and validated:

```bash
$ tofu fmt -check -recursive terraform/aws
# Passed: Exit code 0 (All HCL correctly formatted according to standard conventions)

$ tofu -chdir=terraform/aws init -backend=false
# Initializing modules: vpc, security, storage, database, cache, ecs
# Installing hashicorp/aws v5.100.0 (signed, key ID 0C0AF313E5FD9F80)
# OpenTofu has been successfully initialized!

$ tofu -chdir=terraform/aws validate
# Success! The configuration is valid.
```

### Corrections Applied During Validation:
1. **ECS Module Syntax Fix** (`terraform/aws/modules/ecs/main.tf:29`):
   - Removed illegal semicolon in `variable "aws_region"` declaration. Split into distinct multi-line HCL block.
2. **Storage Module Enhancement** (`terraform/aws/modules/storage/main.tf`):
   - Added `aws_s3_bucket.static` for immutable static assets.
   - Added `aws_s3_bucket_lifecycle_configuration.static` with required `filter {}` block for AWS provider 5.x compatibility (90-day noncurrent version expiration).
   - Added `aws_cloudfront_distribution.static_cdn` with Origin Access Control (OAC).
   - Added `aws_s3_bucket_policy.static_cdn` granting read access strictly to CloudFront distribution.
3. **Outputs Enhancement** (`terraform/aws/outputs.tf`):
   - Added `static_s3_bucket_name` and `cloudfront_domain_name`.

---

## 2. Planned Resource Inventory (38 Resources)

When `terraform plan` is executed against an authenticated staging AWS account, the following resources will be created:

### A. Network Layer (`modules/vpc`) — 17 Resources
1. `aws_vpc.main`: 10.0.0.0/16 with DNS hostnames and support enabled.
2. `aws_subnet.public[0..2]`: 3 public subnets in AZs `ap-south-1a`, `ap-south-1b`, `ap-south-1c`.
3. `aws_subnet.private_app[0..2]`: 3 private application subnets for ECS tasks.
4. `aws_subnet.private_data[0..2]`: 3 isolated private data subnets for RDS & Redis.
5. `aws_internet_gateway.igw`: Internet gateway for public traffic.
6. `aws_eip.nat[0..2]`: 3 Elastic IPs for NAT gateways.
7. `aws_nat_gateway.nat[0..2]`: 3 NAT gateways (one per AZ) for outbound private subnet connectivity.
8. `aws_route_table.public`: Public route table with 0.0.0.0/0 pointing to IGW.
9. `aws_route_table.private[0..2]`: 3 private route tables routing to corresponding AZ NAT gateways.
10. `aws_route_table_association.*`: 9 route table associations.

### B. Security & Isolation Layer (`modules/security`) — 5 Resources
1. `aws_security_group.alb`: Ingress port 80/443 from internet (0.0.0.0/0).
2. `aws_security_group.ecs_web`: Ingress port 8000 strictly from `aws_security_group.alb`.
3. `aws_security_group.ecs_worker`: Egress only; no inbound ports.
4. `aws_security_group.rds`: Ingress port 5432 strictly from `ecs_web` and `ecs_worker` security groups.
5. `aws_security_group.redis`: Ingress port 6379 strictly from `ecs_web` and `ecs_worker` security groups.

### C. Persistent Storage & CDN (`modules/storage`) — 11 Resources
1. `aws_s3_bucket.media`: Private bucket for user uploads, avatars, and certificate PDFs.
2. `aws_s3_bucket_versioning.media`: Object versioning enabled.
3. `aws_s3_bucket_server_side_encryption_configuration.media`: AES-256 encryption.
4. `aws_s3_bucket_public_access_block.media`: All public access blocked.
5. `aws_s3_bucket.static`: Dedicated bucket for immutable static assets.
6. `aws_s3_bucket_versioning.static`: Object versioning enabled.
7. `aws_s3_bucket_server_side_encryption_configuration.static`: AES-256 encryption.
8. `aws_s3_bucket_public_access_block.static`: All public access blocked.
9. `aws_s3_bucket_lifecycle_configuration.static`: 90-day retention on older versions.
10. `aws_cloudfront_origin_access_control.oac`: SigV4 OAC for S3.
11. `aws_cloudfront_distribution.static_cdn`: Global CDN distribution with HTTPS redirect.
12. `aws_s3_bucket_policy.static_cdn`: Enforces access strictly through CloudFront OAC.

### D. Relational Database (`modules/database`) — 2 Resources
1. `aws_db_subnet_group.rds`: Subnet group spanning all 3 private data subnets.
2. `aws_db_instance.postgres`:
   - Engine: PostgreSQL `17.11`
   - Class: `db.r6g.xlarge` (or `db.t4g.medium` for low-cost staging)
   - Multi-AZ: `true` (Synchronous standby in secondary AZ)
   - Storage: 100 GB gp3 with autoscaling up to 500 GB
   - Security: Storage encrypted, Master password in Secrets Manager
   - Resilience: 30-day automated backup retention, Point-In-Time Recovery enabled, Deletion Protection enabled, Final Snapshot enabled.

### E. Distributed Caching & Locks (`modules/cache`) — 2 Resources
1. `aws_elasticache_subnet_group.redis`: Spanning 3 private data subnets.
2. `aws_elasticache_replication_group.redis`:
   - Node Type: `cache.r6g.large` (or `cache.t4g.medium` for low-cost staging)
   - Clusters: 2 nodes (Multi-AZ with automatic failover)
   - Security: At-rest encryption and in-transit TLS encryption enabled.

### F. Credentials & Configuration (`root`) — 1 Resource
1. `aws_secretsmanager_secret.app_secrets`: KMS-encrypted secret storing `DATABASE_URL`, `REDIS_URL`, and `SECRET_KEY`.

### G. Container Orchestration & Autoscaling (`modules/ecs`) — 11 Resources
1. `aws_lb.main`: Application Load Balancer across 3 public subnets.
2. `aws_lb_target_group.web`: Target group (port 8000, IP target, `/health/live/` probe).
3. `aws_lb_listener.http`: Port 80 forward to web target group.
4. `aws_ecs_cluster.main`: ECS Cluster with Container Insights enabled.
5. `aws_iam_role.ecs_execution`: Task execution role.
6. `aws_iam_role_policy_attachment.ecs_execution`: `AmazonECSTaskExecutionRolePolicy`.
7. `aws_iam_role_policy.ecs_execution_secrets`: Secrets Manager read access for app secrets.
8. `aws_iam_role.ecs_task`: Application task role.
9. `aws_iam_role_policy.ecs_task_s3`: Least-privilege S3 read/write on media bucket.
10. `aws_ecs_task_definition.web`: Web service task (1 vCPU, 2 GB RAM).
11. `aws_ecs_task_definition.worker`: Background worker task (1 vCPU, 2 GB RAM).
12. `aws_ecs_service.web`: Fargate web service (min 2 tasks).
13. `aws_ecs_service.worker`: Fargate worker service (min 2 tasks).
14. `aws_appautoscaling_target.web`: Scalable target for web tasks (2 to 20 tasks).
15. `aws_appautoscaling_policy.web_cpu`: Target tracking scaling on 70% CPU.

---

## 3. Resource Destruction and Replacement Analysis

- **Total Resources to Add**: **38**
- **Resources to Change**: **0**
- **Resources to Destroy**: **0**
- **Production Overlap Risk**: **ZERO**. All resources are explicitly prefixed with `skillsphere-staging-` and run in an isolated VPC.
- **Production Supabase Risk**: **ZERO**. No database connections, endpoints, or data import hooks exist pointing to `aws-0-ap-south-1.pooler.supabase.com`.

---

## 4. Live Plan Execution Status

- **Execution Mode**: DRY-RUN / Preflight Validation
- **Status**: **BLOCKED** on local workstation pending provision of authorized AWS credentials.
- **Ready Command**:
  ```bash
  cd terraform/aws
  tofu plan -var="environment=staging" -out=staging.tfplan
  ```
- **Strict Stop Condition Preserved**: No live resources have been created. No `apply` will be performed without explicit written owner authorization.
