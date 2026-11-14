# SkillSphere Phase 17.3 — Production Readiness & Migration Checklist

## 1. Executive Summary

This checklist establishes the gating criteria and operational procedure for executing zero-downtime, zero-data-loss deployment of SkillSphere across multi-instance production environments.

> [!IMPORTANT]
> Do NOT perform DNS cutovers or decommissioning of existing hosting until all gates in this checklist pass with verified operational sign-off.

---

## 2. Production Migration Gating Matrix

| Verification Area | Gate Status | Verification Mechanism | Sign-off Criteria |
| :--- | :---: | :--- | :--- |
| **1. Storage Portability** | ✅ **READY** | `test_storage_production_configuration_validation`<br>`test_storage_chunked_file_streaming`<br>`test_storage_idor_authorization_enforcement` | Fail-fast S3 config validation, memory-efficient chunk streaming, strict IDOR ownership checks. |
| **2. Distributed Bulkheads**| ✅ **READY** | `test_distributed_bulkhead_atomic_lua_and_renewal`<br>`DistributedBulkhead` (Redis Lua scripts) | Atomic slot acquisition, active lease renewal, automatic stale permit GC, degraded fallback. |
| **3. Worker Lease Safety** | ✅ **READY** | `test_worker_fencing_token_and_atomic_claim`<br>`test_zombie_worker_defense_stale_completion_rejected` | Unique fencing tokens, atomic claims via `SKIP LOCKED`, zombie worker writes rejected. |
| **4. Multi-Instance Metrics**| ✅ **READY** | `test_metrics_security_and_instance_stability`<br>`services/observability.py` | Token-protected `/api/metrics/`, stabilized bounded instance ID labels, cardinality defense. |
| **5. Health Check Probes** | ✅ **READY** | `/health/live/`, `/health/ready/`, `/health/startup/` | Decoupled liveness probe (never cascades DB drops), diagnostic readiness probe. |
| **6. Automated Test Suite** | ✅ **READY** | `manage.py test` (100% pass) | 0 regressions across all core, concurrency, failure-injection, and hardening test suites. |
| **7. Database Baseline Integrity**| ✅ **READY** | Production Supabase Entity Count Audit | Exact preservation of all 3 users, 69 courses, 1,104 lessons, 17 enrollments, 6 certificates. |

---

## 3. Production Database Baseline Verification

Before any deployment or migration step, the production database baseline must be cryptographically recorded and verified.

### Confirmed Supabase Production Baseline:
```
- Users: 3 (Admin: ankitojha, Students: demo_user, test_student)
- Student Profiles: 3
- Courses: 69
- Modules: 276
- Lessons: 1,104
- Enrollments: 17
- Assessments: 131
- Questions: 775
- Progress Records: 84
- Certificates: 6
- XP Transactions: 84
```

### Verification Command:
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
print('Student Profiles:', StudentProfile.objects.count())
print('Courses:', Course.objects.count())
print('Modules:', CourseModule.objects.count())
print('Lessons:', Lesson.objects.count())
print('Enrollments:', Enrollment.objects.count())
print('Assessments:', CourseAssessment.objects.count())
print('Questions:', CourseAssessmentQuestion.objects.count())
print('Progress Records:', LessonProgress.objects.count())
print('Certificates:', Certificate.objects.count())
print('XP Transactions:', XPTransaction.objects.count())
"
```
Any mismatch before or after deployment indicates a critical migration failure and immediately triggers the rollback plan.

---

## 4. Multi-Instance Cutover Runbook

### Phase A: Pre-Cutover Deployment (Dry Run)
1. Provision new multi-container cluster (e.g., Kubernetes Deployment or ECS Task Definition with 3+ replicas).
2. Configure environment variables in secret store (Vault / AWS Secrets Manager) using `docs/PHASE_17_3_CONFIGURATION_REFERENCE.md`.
3. Verify that `DATABASE_URL` connects to the Supabase pooler (`port: 6543`, `sslmode=require`).
4. Set `STORAGE_BACKEND=s3` with verified S3 or Cloudflare R2 bucket credentials.
5. Deploy application pods with `replicas: 3`.
6. Query `/health/ready/` on each pod: verify HTTP 200 and healthy DB/cache indicators.
7. Verify `/health/live/` returns HTTP 200 without touching the database.
8. Query `/api/metrics/` with `X-Metrics-Token`: verify Prometheus payload output with stable instance labels.

### Phase B: Dual-Routing / Canary Cutover
1. Direct 5% of production traffic to the new multi-instance fleet via load balancer weighting.
2. Monitor error rates, p95 latencies, and circuit breaker trip counts for 15 minutes:
   ```promql
   sum(rate(django_http_requests_total{status_code=~"5.."}[1m])) / sum(rate(django_http_requests_total[1m]))
   ```
3. Verify zero database lock contention on `DurableTaskJob`.
4. Scale traffic weighting: 5% $\rightarrow$ 25% $\rightarrow$ 50% $\rightarrow$ 100%.

### Phase C: Post-Cutover Audit & Monitoring
1. Run the database entity verification script to confirm zero data alteration.
2. Verify background task queue workers are actively processing jobs without zombie collisions.
3. Keep the previous deployment standby in a paused state for 24 hours.

---

## 5. Rollback Contingency Plan

If any critical anomaly occurs during cutover (error rate $> 0.5\%$, database connection starvation, or failed entity check):

1. **Immediate Traffic Rollback**: Revert load balancer routing 100% back to the legacy instance.
2. **Task Queue Quiesce**: Drain or pause background workers on the multi-instance fleet:
   ```bash
   python manage.py shell -c "from services.task_queue import DurableTaskJob; print('Active running jobs:', DurableTaskJob.objects.filter(status='running').count())"
   ```
3. **Database Audit**: Run the entity baseline count script to ensure no corrupted rows were committed.
4. **Log Collection**: Dump container logs from all instances filtered by `[TaskQueue:Fencing]`, `[DistributedBulkhead]`, and `[StorageService]` for post-mortem analysis.
