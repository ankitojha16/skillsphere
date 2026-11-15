# SkillSphere — Controlled Student Beta Launch Checklist

## Status: READY FOR INVITE-ONLY STUDENT ROLLOUT
**Verification Baseline:** Full Regression Suite (406/406 tests passing), 24/24 E2E Student Journeys passing, Playwright Multi-Viewport & Accessibility certified.

---

## 1. Pre-Flight Infrastructure & Database Verification
- [x] **Database Schema & Migrations**: Verified clean on SQLite and PostgreSQL targets. All models synchronized with zero unapplied migrations.
- [x] **Course Content Inventory**: Exactly 69 accredited courses and 1,104 interactive lessons loaded in database.
- [x] **Career Tracks**: All 11 industry career tracks active with associated skill sets and project briefs.
- [x] **Opportunity Hub Data**: 16 verified active internships and entry-level roles populated with freshness checks.
- [x] **Static Assets & WhiteNoise**: Staticfiles collected and compressed with hash fingerprints.

---

## 2. Beta Cohort Governance & Invite Onboarding
- [x] **Cohort Size**: Controlled initial student cohort of 50-100 invited beta users.
- [x] **Registration Flow**: Dedicated invite-code or closed registration link at `/accounts/register/`.
- [x] **Structured Onboarding**:
  - Interests & learning level capture at `/accounts/onboarding/`.
  - Personalized starter course recommendation (`top_course`) with direct "Start First Lesson Now" CTA.
  - Active career goal selection across the 11 tracks.
  - First recommended portfolio project brief with 1-click initialization.
  - In-app Beta Feedback banner linking to the structured modal.

---

## 3. Product Architecture & Navigation ("Less But Better")
- [x] **Navigation Simplification**: Replaced previous 28 scattered sidebar links with the 5 core pillars:
  1. **Home**: Student Launchpad & Daily Workspace (`/dashboard/`)
  2. **Learn**: Courses, My Learning, Roadmaps, and Study AI (`/courses/`, `/courses/my-learning/`, `/roadmaps/`, `/assistant/?mode=study`)
  3. **Practice**: Skill Assessments, Coding Challenges, and Mock Interviews (`/skill-assessment/`, `/skill-assessment/challenges/`, `/mock-interview/`)
  4. **Projects**: Evidence Portfolio and Project Generator (`/portfolio/`, `/projects/generator/`)
  5. **Career**: Career Studio, Gap Analyzer, ATS Resume Builder, and Opportunity Hub (`/career-studio/`, `/career-studio/gap-analyzer/`, `/career-studio/resume/`, `/opportunities/`, `/opportunities/applications/`)
- [x] **Unified Contextual AI Assistant**: `/assistant/` router supporting mode toggles (`study`, `mentor`, `interview`, `resume`) with deterministic fallbacks when AI APIs are unreachable.

---

## 4. Privacy, Safety & Compliance Gates
- [x] **Minor & High School Student Protection**: Students under 18 or high-school level have their profiles automatically hidden from recruiters (`/talent/` and recruiter candidate lookups return 403 Forbidden).
- [x] **Student Data Portability**: Self-service GDPR/CCPA compliant data export available at `/accounts/export-data/` returning all user data in JSON format.
- [x] **Telemetry Privacy**: `ProductEvent` telemetry logs only milestone events (`first_project_created`, `resume_generated`, `opportunity_applied`) without recording PII, browsing histories, or raw keystrokes.
- [x] **Recruiter Access Control**: Role-based access control blocks regular students from recruiter posting routes (`/opportunities/recruiter/post/`).

---

## 5. Beta Feedback Mechanism & Triage SLA
- [x] **5-Question Beta Feedback Modal**: Accessible globally via the top navigation and dashboard banner.
  1. *What was easy to use?*
  2. *What was confusing or unclear?*
  3. *Which feature was most useful?*
  4. *What did you expect but could not find?*
  5. *What should be improved?*
- [x] **Moderation & Engineering Review**: Submissions stored in `BetaFeedback` model, queryable by administrators at `/opportunities/moderation/` and staff dashboard.
- [x] **Triage SLA**:
  - **P0 (Blocker / Bug causing data loss or crash)**: Triage within 4 hours, patch within 24 hours.
  - **P1 (Usability confusion / broken link)**: Triage within 12 hours, fix in next beta sprint.
  - **P2 (Feature request / cosmetic suggestion)**: Logged in beta prioritization backlog.

---

## 6. Daily Monitoring & Health Checks
- [x] Circuit breaker health monitoring for Gemini AI cascade (`AIService`).
- [x] Fast fallbacks active when external AI rate limits or network issues occur.
- [x] Sentry / application logging active with request duration timing and slow-query detection (`skillsphere.performance`).
- [x] Database connection pooling and SQLite/PostgreSQL resilience verified.
