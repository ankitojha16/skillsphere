# SkillSphere Phase 18 — Disaster Recovery & High-Availability Playbook

## 1. Executive Summary & Realistic Target Metrics

This disaster recovery playbook documents the failure modes, automated recovery behaviors, and operational runbooks for SkillSphere under multi-instance cloud deployment.

### Realistic Recovery Objectives:
- **Recovery Point Objective (RPO)**: **$\le 5\text{ minutes}$** (via PostgreSQL continuous WAL archiving and automated daily snapshots).
- **Recovery Time Objective (RTO)**:
  - Single task crash: **$< 45\text{ seconds}$** (automated container replacement).
  - Availability Zone outage: **$< 60\text{ seconds}$** (Multi-AZ RDS failover and ALB task re-routing).
  - Catastrophic regional disaster: **$\le 30\text{ minutes}$** (infrastructure reprovisioning via Terraform in alternate region and snapshot restoration).

> [!WARNING]
> Do not claim zero-second RPO or instantaneous multi-region active-active recovery. True multi-region active-active databases introduce complex write conflicts and cross-region consensus latency that are neither implemented nor required for SkillSphere's current operational scale.

---

## 2. Failure Mode Analysis & Automated Mitigations

| Failure Scenario | Impact | Automated System Mitigation | Verified In Tests |
| :--- | :--- | :--- | :--- |
| **1. Web Task Crash / OOM** | Loss of 1 container process | ALB detects failed `/health/live/` within 15s; redirects traffic to healthy tasks; ECS launches replacement task immediately. | `test_decoupled_health_probes` |
| **2. Worker Node Crash** | Abandoned in-flight background job | Job lease expires ($60\text{s}$). Sibling worker's `recover_expired_leases()` claims job, increments retry, and reschedules with full jitter. If zombie worker awakens later, write is rejected. | `test_zombie_worker_defense_stale_completion_rejected`<br>`test_worker_fencing_token_and_atomic_claim` |
| **3. Redis Cluster Interruption** | Shared cache and bulkheads unreachable | `RedisService` catches connection error and falls back to `LocMemCache`. `DistributedBulkhead` falls back to process-local semaphore. Core learning and exams continue uninterrupted. | `test_multiprocess_bulkhead_capacity_and_failover`<br>`RedisDegradationAndRecoveryTests` |
| **4. Database Transient Stall** | DB connection pool latency spikes | `/health/live/` continues returning HTTP 200 (does not trigger container restart). `/health/ready/` reports degraded status to load balancer. Django retries connection on next request. | `services.test_phase_17_1.ReadinessProbeTests` |
| **5. Storage Service Degradation** | S3 API temporary timeout | Chunked streaming generator yields partial bytes or raises controlled `StorageError`. User receives friendly error; retried via exponential backoff. | `test_storage_streaming_and_path_security` |

---

## 3. Operational Recovery Runbooks

### Runbook 1: PostgreSQL Standby Promotion (Multi-AZ Failover)
1. **Trigger**: Primary database instance suffers hardware or network failure in Availability Zone 1.
2. **Automated Action**: AWS RDS detects health check failure and triggers automated failover to the Multi-AZ standby replica in Availability Zone 2.
3. **DNS Cutover**: RDS automatically updates the database CNAME endpoint to point to the new primary.
4. **Application Behavior**: Django database connection drops, logs `OperationalError`, and reconnects cleanly on the subsequent request within 60 seconds.

---

### Runbook 2: Database Snapshot Point-in-Time Restoration
1. Identify target timestamp prior to data corruption incident:
   ```bash
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier skillsphere-production-db \
     --target-db-instance-identifier skillsphere-restored-db \
     --restore-time "2026-11-14T20:00:00Z" \
     --db-subnet-group-name skillsphere-production-db-subnet
   ```
2. Wait for instance status to report `available`.
3. Run the SkillSphere entity verification audit script to verify baseline data integrity:
   ```bash
   python manage.py shell -c "
   from django.contrib.auth import get_user_model
   from accounts.models import StudentProfile
   from courses.models import Course, CourseModule, CourseAssessment, CourseAssessmentQuestion, Enrollment
   from learning.models import Lesson, LessonProgress
   from certificates.models import Certificate
   from gamification.models import XPTransaction

   User = get_user_model()
   print('Users:', User.objects.count())
   print('Courses:', Course.objects.count())
   print('Certificates:', Certificate.objects.count())
   "
   ```
4. Update `DATABASE_URL` in AWS Secrets Manager and trigger rolling update on ECS Fargate.
