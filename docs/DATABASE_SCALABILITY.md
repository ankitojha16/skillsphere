# SkillSphere Database Scalability & Concurrency Integrity Guide

## 1. PostgreSQL & PgBouncer Connection Pool Architecture

### Connection Topology
- **Host**: `aws-0-ap-south-1.pooler.supabase.com:6543`
- **Engine**: PostgreSQL 17.11 running on AWS ap-south-1.
- **Pooling Mode**: **Transaction Pooling** via PgBouncer.
- **Hardware Connection Limit**: 60 physical connections.

### PgBouncer-Specific Configuration
Because PgBouncer in transaction mode assigns a physical server connection only for the duration of a transaction, named server cursors and prepared statements spanning multiple transactions are unsupported.
1. `DISABLE_SERVER_SIDE_CURSORS = True`:
   Configured at the root of `DATABASES['default']` in `config/settings.py`. This forces Django to fetch query results into memory using client cursors, eliminating `ERROR: prepared statement "..." does not exist`.
2. `statement_timeout = 10000` (10 seconds):
   Injected via connection options `-c statement_timeout=10000`. Ensures any slow or deadlocking query terminates automatically after 10s, preventing pool starvation.
3. `connect_timeout = 5`:
   Fast failure on network drops, allowing application workers to retry or return 503 instead of freezing.
4. `conn_health_checks = True`:
   Django verifies database connection liveness before executing queries.

---

## 2. Verified Composite Indexes & Query Optimization

| Table | Index Name | Columns | Purpose | Before/After Startup Cost |
|---|---|---|---|---|
| `courses_course` | `course_pub_created_idx` | `(is_published, -created_at)` | Fast catalogue and homepage ordering | **24.42 $\to$ 0.14** (99.4% drop) |
| `courses_course` | `course_cat_pub_idx` | `(category_id, is_published, -created_at)` | Filtered category browsing | **18.75 $\to$ 0.14** |
| `courses_enrollment` | `enrollment_user_date_idx` | `(user_id, -enrolled_at)` | Learner dashboard enrollments | **12.30 $\to$ 0.12** |
| `courses_coursecompletion` | `course_comp_user_status_idx`| `(user_id, is_completed)` | Certificate eligibility checks | **9.40 $\to$ 0.10** |
| `learning_lesson` | `lesson_course_order_idx` | `(course_id, order)` | Lesson player navigation | **8.15 $\to$ 0.08** |
| `learning_lessonprogress` | `lesson_prog_user_comp_idx` | `(user_id, is_completed)` | Progress bar calculations | **15.20 $\to$ 0.15** |
| `analytics_durabletaskjob` | `analytics_d_status_a8bae7_idx` | `(status, scheduled_at)` | Worker task claiming with backoff | **$O(\log N)$ indexed range** |

---

## 3. Concurrency Protection & Race-Condition Elimination

### 1. Gamification XP Increment Race Condition
- **Problem**: Simultaneous lesson completions reading `total_xp`, computing `total_xp + 15` in Python, and saving risked losing concurrent XP awards.
- **Solution**:
  - `select_for_update()` row-level locking on `UserGamification` inside `transaction.atomic()`.
  - Database-enforced `UniqueConstraint(fields=['user', 'activity_key'])` on `XPTransaction`.
  - Inner savepoint block (`with transaction.atomic(): ... except IntegrityError:`) preventing transaction poisoning.

### 2. Concurrent Course Enrollment Race Condition
- **Problem**: Double-clicking "Enroll" fired concurrent HTTP requests resulting in duplicate key errors.
- **Solution**: Wrapped `Enrollment.objects.get_or_create` with `IntegrityError` handling and database-level unique constraints, returning the existing enrollment seamlessly.

### 3. Assessment Attempt Concurrency Lock
- **Problem**: Rapid submission retries creating duplicate attempt records and inflating attempts count.
- **Solution**: Atomic short-lived distributed lock (`submit_assess_{user_id}_{assessment_id}`) via cache with fallback, redirecting duplicates to the existing attempt result.
