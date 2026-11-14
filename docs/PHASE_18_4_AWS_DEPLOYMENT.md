# SkillSphere Phase 18.4 — AWS ECS Fargate Staging Deployment Guide

**Target Environment**: AWS Cloud Staging (`staging`)  
**Region**: `ap-south-1` (Asia Pacific - Mumbai)  
**Deployment Tooling**: Terraform 1.5+ | Docker 24+ | AWS CLI v2  
**Safety Mandate**: Requires explicit `--apply` flag; zero auto-apply in automated checks.

---

## 1. Cloud Architecture Overview

SkillSphere is deployed as a multi-tier containerized service orchestrated by AWS ECS Fargate, decoupled from physical machine dependencies, and backed by managed AWS cloud services:

```
                               [ Internet Users / API Clients ]
                                              │
                                              ▼ (Port 80 / 443)
                               [ Application Load Balancer ]
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
        [ ECS Web Task: AZ-1 ]                            [ ECS Web Task: AZ-2 ]
        (Gunicorn 2w + 4th)                               (Gunicorn 2w + 4th)
                     │                                                 │
                     ├────────────────────────┬────────────────────────┤
                     ▼                        ▼                        ▼
        [ Amazon S3 Bucket ]       [ ElastiCache Redis ]     [ RDS PostgreSQL ]
        (Direct S3 GW Endpoint)    (Multi-AZ 2-node)         (Multi-AZ DB Instance)
                     ▲                        ▲                        ▲
                     ├────────────────────────┴────────────────────────┤
                     │                                                 │
        [ ECS Worker Task: AZ-1 ]                         [ ECS Worker Task: AZ-2 ]
        (run_task_worker daemon)                          (run_task_worker daemon)
```

### Core Architecture Highlights:
1. **Network Layer**: Custom Multi-AZ VPC (`10.0.0.0/16`) spanning 3 active Availability Zones.
2. **Compute Tier**: AWS ECS Fargate running separate Web services and Background Worker services.
3. **Data Tier**: Amazon RDS for PostgreSQL 17.4 Multi-AZ DB Instance deployment with automated backups.
4. **Cache & Bulkhead Tier**: Amazon ElastiCache Redis 7.x Multi-AZ Replication Group.
5. **Storage Tier**: Amazon S3 bucket (`skillsphere-staging-media-assets`) with S3 Gateway VPC Endpoint, versioning, SSE-S3, and public-access blocking.
6. **Secrets & Identity**: AWS Secrets Manager and IAM least-privilege roles without hardcoded credentials.

---

## 2. Pre-Deployment Readiness Checklist

Before executing provisioning, ensure the following preconditions are met:

- [x] Full Django test suite passing locally (`368 tests passing`).
- [x] Zero references to production Supabase PostgreSQL in staging configuration files.
- [x] PostgreSQL engine version upgraded from deprecated `17.2` to supported `17.4`.
- [x] All VPC route tables and subnet associations verified.
- [x] ECS task definition configured to inject secrets via AWS Secrets Manager.
- [x] Application storage service updated to authenticate via ECS Task IAM role.
- [ ] AWS account credentials supplied in deployment environment (CI/CD OIDC runner or workstation).
- [ ] Explicit project owner authorization granted for cloud expenditures.

---

## 3. Step-by-Step Deployment Runbook

### Step 1: Environment Setup
Ensure your local terminal or CI/CD agent has valid AWS credentials configured with the necessary provisioning permissions:
```bash
export AWS_REGION="ap-south-1"
export AWS_DEFAULT_REGION="ap-south-1"
# Verify AWS caller identity
aws sts get-caller-identity
```

### Step 2: Build & Push Container Image
Build the production SkillSphere Docker image and push to Amazon ECR:
```bash
# Authenticate Docker to AWS ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com

# Build the container image
docker build -t skillsphere:latest -f Dockerfile .

# Tag and push to ECR repository
docker tag skillsphere:latest <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/skillsphere:staging-latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/skillsphere:staging-latest
```

### Step 3: Populate Staging Application Secrets
Inject the application secrets into AWS Secrets Manager before launching tasks:
```bash
aws secretsmanager put-secret-value \
  --secret-id "skillsphere-staging-app-secrets" \
  --secret-string '{"SECRET_KEY":"<GENERATE_SECURE_KEY>","DATABASE_URL":"postgresql://skillsphere_admin:<RDS_PASSWORD>@<RDS_ENDPOINT>:5432/skillsphere","REDIS_URL":"rediss://<REDIS_ENDPOINT>:6379","GEMINI_API_KEY":"<API_KEY>"}'
```

### Step 4: Execute Terraform Provisioning
Run the deployment orchestration script with the `--apply` flag:
```bash
./scripts/deploy_cloud_staging.sh --apply
```
Or execute Terraform manually:
```bash
cd terraform/aws
terraform init
terraform plan -var="environment=staging" -out=staging.tfplan
terraform apply staging.tfplan
```

### Step 5: Execute Database Migrations
Run Django migrations in a one-off ECS Fargate task:
```bash
aws ecs run-task \
  --cluster skillsphere-staging-cluster \
  --task-definition skillsphere-staging-web \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<PRIVATE_APP_SUBNET_1>],securityGroups=[<WEB_SG_ID>],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides": [{"name": "web", "command": ["python", "manage.py", "migrate", "--noinput"]}]}'
```

---

## 4. Post-Deployment Verification & Smoke Tests

Once tasks reach `RUNNING` status in ECS, verify the deployment endpoints:

### 1. Liveness & Readiness Probes
```bash
ALB_DNS=$(terraform -chdir=terraform/aws output -raw alb_dns_name)

# 1. Check Liveness Probe (HTTP 200 expected)
curl -i "http://${ALB_DNS}/health/live/"

# 2. Check Readiness Probe (HTTP 200 expected - verifies DB and Redis reachability)
curl -i "http://${ALB_DNS}/health/ready/"

# 3. Check Prometheus Metrics
curl -i "http://${ALB_DNS}/metrics"
```

### 2. Student Workflow Verification
Execute automated smoke test simulating:
1. Synthetic student registration and login.
2. Course enrollment and lesson completion.
3. Assessment submission and XP award transaction.
4. Background worker PDF certificate generation.
5. Signed S3 download URL generation and retrieval.

---

## 5. Rollback Runbook

If any health check or smoke test fails post-deployment:

1. **ECS Service Rollback**:
   Revert ECS service to the previous stable task definition:
   ```bash
   aws ecs update-service \
     --cluster skillsphere-staging-cluster \
     --service skillsphere-staging-web-svc \
     --task-definition skillsphere-staging-web:<PREVIOUS_VERSION>
   ```
2. **Database Point-in-Time Recovery (PITR)**:
   If a migration error occurs, restore RDS PostgreSQL to the pre-deployment timestamp:
   ```bash
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier skillsphere-staging-db \
     --target-db-instance-identifier skillsphere-staging-db-restored \
     --restore-time "2026-11-15T00:00:00Z"
   ```
