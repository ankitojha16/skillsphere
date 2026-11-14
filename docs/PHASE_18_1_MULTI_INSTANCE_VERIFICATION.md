# SkillSphere Phase 18.1 — Multi-Instance Verification & Shared State Integrity

## 1. Executive Summary

This report verifies that multiple independent SkillSphere web instances operate correctly behind a round-robin load balancer without requiring sticky sessions, without data desynchronization, and without in-memory state fragmentation.

---

## 2. Session Consistency & Authentication Across Instances

### 2.1 Shared Session Backend
In SkillSphere, session management is configured through Django's cached database or Redis session backend:
- When a student authenticates on **Instance 1**, the session key and serialized user session data are stored in shared Redis / PostgreSQL (`django_session`).
- When a subsequent HTTP request arrives at **Instance 2** via round-robin load balancing, Instance 2 fetches and deserializes the session from the shared store.
- **Zero Sticky Sessions**: The platform requires no session affinity at the load balancer. Requests can freely alternate between instances on every click without logging the user out.

### 2.2 Cross-Instance Workflow Verification Matrix

| Workflow | Mechanism | Verification Status | Shared State Protection |
| :--- | :--- | :---: | :--- |
| **User Authentication** | Django Session / PBKDF2 Password | ✅ **VERIFIED** | Centralized session in Redis/PostgreSQL; token verified across instances. |
| **Course Discovery** | Catalog & Autocomplete Views | ✅ **VERIFIED** | Read from shared database; cache fragments stored in shared Redis. |
| **Course Enrollment** | `Enrollment.objects.create()` | ✅ **VERIFIED** | Unique constraint `(student, course)` in PostgreSQL prevents race-condition double enrollment. |
| **Lesson Progress** | `LessonProgress.objects.update_or_create()` | ✅ **VERIFIED** | Idempotent updates with atomic database transactions. |
| **Assessment Submission**| `CourseAssessmentAttempt` | ✅ **VERIFIED** | Atomic score calculation and streak increments. |
| **XP Gamification** | `XPTransaction.objects.create()` | ✅ **VERIFIED** | Atomic balance increments protected by database transactions. |
| **Certificate Retrieval**| `Certificate.objects.filter()` | ✅ **VERIFIED** | Deterministic certificate codes (`SS-CERT-...`) queried from shared database. |

---

## 3. Concurrency Protection & Rate Limiting

1. **Sliding-Window Rate Limiting**: Implemented via `RedisService.check_sliding_window_rate_limit()`:
   - When Instance 1 records a request, it pushes the timestamp to the student's Redis sorted set.
   - When Instance 2 receives a request 100ms later, it queries the same Redis key.
   - Prevents students from bypassing AI prompt limits or quiz attempt limits by switching instances.
2. **Distributed Bulkheads**: Implemented via `DistributedBulkhead`:
   - Concurrency ceilings (e.g. max 10 concurrent PDF renders fleet-wide) are enforced globally in Redis, not multiplied per container.
