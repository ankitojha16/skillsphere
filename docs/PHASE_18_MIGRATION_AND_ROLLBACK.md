# SkillSphere Phase 18 — Production Migration, Cutover & Rollback Runbook

## 1. Executive Summary & Gating Conditions

This runbook outlines the operational steps for executing a zero-downtime, zero-data-loss cutover to the multi-instance cloud architecture when authorized.

> [!CAUTION]
> **Pre-Migration Gate Verification**:
> 1. All 348 automated tests must pass on the target build.
> 2. Database baseline audit must confirm all 3 users, 69 courses, 1,104 lessons, 17 enrollments, and 6 certificates are intact.
> 3. DNS TTL on existing records must be lowered to 60 seconds at least 48 hours prior to maintenance.

---

## 2. Step-by-Step Canary Cutover Procedure

### Phase 1: Pre-Cutover Preparation (T - 48 Hours)
1. **DNS TTL Reduction**: Set TTL on `skillsphere-cyan.vercel.app` and domain records to `60` seconds.
2. **Infrastructure Validation**: Run Terraform plan and apply to provision the VPC, RDS (or connect to Supabase), ElastiCache, S3, and ECS Fargate cluster.
3. **Database Pre-Check**: Run the entity count verification command against the production database:
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
4. **Deploy Application Images**: Push the hardened container image to Amazon ECR and deploy 2 Web tasks and 2 Worker tasks. Verify `/health/ready/` returns HTTP 200.

---

### Phase 2: Canary Traffic Migration (Cutover Day)
1. **Step 1: Synthetic & Staff Traffic (0%)**
   - Route internal QA and staff traffic to the new Application Load Balancer via custom `Host` header.
   - Verify student login, quiz submission, lesson study, and certificate generation.
2. **Step 2: 5% Canary Traffic**
   - In Route 53 or Cloudflare, configure Weighted Routing:
     - Existing Hosting: Weight 95
     - New ECS Fargate ALB: Weight 5
   - Monitor error rates, p95 latency, and PostgreSQL connection pool for 15 minutes.
3. **Step 3: 25% Traffic Expansion**
   - Increase Weight to 25.
   - Verify Redis distributed bulkheads and worker queue throughput.
4. **Step 4: 50% Traffic Expansion**
   - Increase Weight to 50.
   - Monitor database lock metrics (`pg_stat_activity`).
5. **Step 5: 100% Full Cutover**
   - Route 100% of production traffic to the new AWS CloudFront + ALB endpoint.
   - Run the database entity verification command to ensure zero dropped records.

---

## 3. Rollback Runbook & Immediate Triggers

### 3.1 Automated Rollback Triggers:
An immediate, unconditional rollback is triggered if ANY of the following occur during cutover:
- Error rate ($5xx$ HTTP status codes) exceeds **$0.5\%$** for more than 2 consecutive minutes.
- Database connection pool utilization exceeds **$85\%$**.
- Post-cutover entity verification reveals a count discrepancy in Users, Courses, or Certificates.
- Core student workflows (taking a quiz or claiming a certificate) return an unhandled 500 error.

### 3.2 Rollback Execution Steps:
1. **Revert DNS Weighting**: Immediately adjust Route 53 / Cloudflare DNS weights:
   - Existing Hosting: Weight 100
   - New ALB: Weight 0
   - (Thanks to 60-second TTL, global traffic swings back within 1 minute).
2. **Drain ECS Fargate Web Fleet**: Set desired task count to 0 or place ALB target group in maintenance mode.
3. **Quiesce Worker Fleet**: Stop worker tasks to prevent conflicting queue processing.
4. **Post-Rollback Audit**: Re-run the entity verification script to confirm database baseline stability.

---

## 4. Remaining Pre-Deployment Blockers

Before initiating a live production cutover in a future phase:
1. **Cloud Account Authorization**: Explicit user approval required to execute `terraform apply` on AWS.
2. **Production S3 Bucket Provisioning**: Creation of dedicated production S3 bucket and IAM OAC roles.
3. **DNS Registrar Delegation**: Cloudflare or Route 53 zone apex CNAME/ALIAS permissions.
