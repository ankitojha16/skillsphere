# SkillSphere Phase 18.2 — Cloud Deployment Pre-Flight & Go-Live Checklist

This checklist must be executed sequentially by the Platform & SRE team before promoting SkillSphere from staging to multi-instance cloud production.

---

## 1. Network & Infrastructure (Terraform)

- [ ] **Multi-AZ VPC Provisioning**: Confirm VPC is deployed across $\ge 3$ Availability Zones (`terraform/aws/modules/vpc`).
- [ ] **Subnet Isolation**:
  - [ ] Public subnets contain only ALBs and NAT Gateways.
  - [ ] Private App subnets contain only ECS Fargate tasks.
  - [ ] Private Data subnets contain only RDS PostgreSQL and ElastiCache Redis (no internet routing).
- [ ] **Security Group Rules**:
  - [ ] RDS security group allows ingress on port `5432` strictly from ECS Web and Worker security groups.
  - [ ] Redis security group allows ingress on port `6379` strictly from ECS tasks.
  - [ ] ECS Web security group allows ingress on port `8000` strictly from the Application Load Balancer.
- [ ] **Remote State Protection**: Terraform backend is configured with encrypted S3 and DynamoDB state locking.

---

## 2. Storage & Secrets Management

- [ ] **Object Storage Provisioning**:
  - [ ] Production S3 bucket (`aws_s3_bucket.media`) has Versioning **Enabled**.
  - [ ] Default server-side encryption is set to `AES256` or AWS KMS.
  - [ ] `aws_s3_bucket_public_access_block` has all 4 public access blocks set to `true`.
  - [ ] CloudFront Origin Access Control (OAC) policy is attached to allow secure CDN distribution.
- [ ] **Secret Management**:
  - [ ] `SECRET_KEY`, `DATABASE_URL`, and `REDIS_URL` are stored in AWS Secrets Manager / Parameter Store.
  - [ ] No hardcoded passwords exist in `.env`, Dockerfiles, or Git history.
  - [ ] `STORAGE_BACKEND` is set to `s3` (or `r2`/`supabase`) and `ALLOW_LOCAL_STORAGE_IN_PRODUCTION` is `False`.

---

## 3. Database & Cache Readiness

- [ ] **PgBouncer Configuration**:
  - [ ] Pooling mode set to `transaction`.
  - [ ] `max_client_conn` sized to `500`.
  - [ ] `max_db_connections` capped at `80` (guaranteeing $\ge 20\%$ safety headroom under PostgreSQL `max_connections = 100`).
- [ ] **Automated Backups & PITR**:
  - [ ] RDS Point-in-Time Recovery (PITR) retention set to $\ge 7$ days.
  - [ ] Multi-AZ failover enabled for zero-downtime database maintenance.
- [ ] **Redis Cluster**:
  - [ ] ElastiCache Multi-AZ replication group with automatic failover active.

---

## 4. Application Runtime & Worker Fleet

- [ ] **Container Hardening**:
  - [ ] Container image executes as unprivileged user `skillsphere:skillsphere` (UID 1001).
  - [ ] `tini` is configured as PID 1 entrypoint for signal forwarding and process reaping.
  - [ ] `DEBUG` is set to `False`.
- [ ] **Worker Daemons**:
  - [ ] Background worker containers execute `python manage.py run_task_worker`.
  - [ ] Worker fencing tokens active; lease grace period set to `30s`.
  - [ ] At least 2 worker tasks active across separate Availability Zones.
- [ ] **Autoscaling Policies**:
  - [ ] ECS Web tasks configured with Min: 2, Max: 20 tasks.
  - [ ] Target tracking policy set to 70% average CPU utilization.

---

## 5. Ingress, Edge Security & Observability

- [ ] **TLS Termination & Certificates**:
  - [ ] Valid ACM certificate bound to ALB on port 443 with TLS 1.3 preferred.
  - [ ] HTTP-to-HTTPS redirection rule active on ALB port 80.
- [ ] **Edge Proxy Defenses**:
  - [ ] `nginx.staging.conf` rate limits configured (`limit_req_zone 100r/s`, `burst=120`).
  - [ ] Trusted proxy CIDRs configured in `set_real_ip_from` with `real_ip_recursive on`.
  - [ ] Static asset path `/static/` excluded from restrictive rate limiting.
- [ ] **Health & Telemetry Monitoring**:
  - [ ] ALB target group health check polling `/health/live/` (interval 15s, healthy threshold 2).
  - [ ] Prometheus scraping `/metrics` every 15 seconds.
  - [ ] Grafana alert rules configured for 5xx errors ($> 1\%$), CPU saturation ($> 80\%$), and PgBouncer pool saturation ($> 90\%$).

---

## 6. Pre-Cutover Verification & Rollback Preparation

- [ ] **Database Pre-Check**: Run entity count query to establish pre-cutover baseline.
- [ ] **Staging Smoke Test**:
  - [ ] Upload test document via Node A; verify download via Node B.
  - [ ] Trigger async report job; verify worker completion and zombie fencing.
- [ ] **Rollback Plan Verified**: Previous stable container image digest documented and ready for instant ECS task definition redeployment.
