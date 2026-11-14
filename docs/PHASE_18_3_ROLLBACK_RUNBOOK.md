# SkillSphere Phase 18.3 — Emergency Rollback & Disaster Recovery Runbook

## 1. Rollback Mandate & Trigger Thresholds

This runbook defines deterministic, step-by-step procedures to revert SkillSphere application code, container revisions, or database schemas if a critical regression occurs in staging or production.

### Operational Trigger Criteria
Initiate immediate rollback if any of the following conditions persist for $\ge 3$ minutes post-deployment:
- HTTP 5xx error rate exceeds **1.0%** of total traffic.
- Health probes (`/health/live/` or `/health/ready/`) fail on more than 50% of tasks.
- Median request latency increases by $> 300\%$ over pre-deployment baseline.
- Database connection pool reaches 100% saturation without shedding.

---

## 2. Fast Application Container Rollback (< 60 Seconds)

If the defect is isolated to application code (no schema migrations applied):

### Step 1: Identify Previous Stable Task Definition Revision
```bash
# Query previous stable ECS task definition revision:
aws ecs describe-services \
  --cluster skillsphere-staging-cluster \
  --services skillsphere-staging-web-svc \
  --region ap-south-1 \
  --query "services[0].taskDefinition"
```

### Step 2: Revert ECS Web & Worker Services
```bash
# Revert web service to prior stable revision (e.g. revision 42):
aws ecs update-service \
  --cluster skillsphere-staging-cluster \
  --service skillsphere-staging-web-svc \
  --task-definition skillsphere-staging-web:42 \
  --force-new-deployment \
  --region ap-south-1

# Revert worker service:
aws ecs update-service \
  --cluster skillsphere-staging-cluster \
  --service skillsphere-staging-worker-svc \
  --task-definition skillsphere-staging-worker:42 \
  --force-new-deployment \
  --region ap-south-1
```

### Step 3: Verify Traffic Drain & Stable Target Health
```bash
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups --names skillsphere-staging-tg --query "TargetGroups[0].TargetGroupArn" --output text) \
  --region ap-south-1
```
All targets must report `State: healthy`.

---

## 3. Database Schema Rollback

If the faulty release included backward-incompatible database migrations:

### Step 1: Isolate Web Traffic (Maintenance Mode)
Temporarily divert traffic at ALB or return HTTP 503 maintenance page to prevent database writes during rollback.

### Step 2: Execute Reverse Migration Container
```bash
# Run one-off Fargate task to reverse specific migration:
aws ecs run-task \
  --cluster skillsphere-staging-cluster \
  --task-definition skillsphere-staging-web:42 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-abc12345],securityGroups=[sg-web123],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides": [{"name": "web", "command": ["python", "manage.py", "migrate", "<app_name>", "<prior_migration_num>"]}]}' \
  --region ap-south-1
```

---

## 4. Disaster Recovery: Point-in-Time Database Recovery (PITR)

If catastrophic data corruption occurred:

1. **Initiate Point-in-Time Restore**:
   ```bash
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier skillsphere-staging-pg \
     --target-db-instance-identifier skillsphere-staging-pg-restored \
     --restore-time "2026-11-14T18:00:00.000Z" \
     --db-subnet-group-name skillsphere-staging-db-subnets \
     --vpc-security-group-ids sg-rds12345 \
     --region ap-south-1
   ```
2. **Update Secrets Manager**:
   Update `DATABASE_URL` secret with the restored instance endpoint.
3. **Restart ECS Fleet**:
   Force new deployment of web and worker tasks to bind to the restored database.

---

## 5. Post-Rollback Verification Checklist

- [ ] Confirm `/health/live/` returns `HTTP 200 OK`.
- [ ] Confirm `/health/ready/` reports `"database": "ok"`, `"cache": "ok"`.
- [ ] Query database entity count baseline; verify zero corrupted rows.
- [ ] Confirm Prometheus error rate drops back to `< 0.05%`.
