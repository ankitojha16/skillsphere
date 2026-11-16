# SkillSphere — Beta Cohort 1 Product Analytics & Telemetry

## Framework Overview
SkillSphere’s telemetry framework is designed around **privacy-first milestone measurement**. It replaces surveillance-style behavioral analytics (keystrokes, mouse heatmaps, third-party pixels) with transparent, first-party event tracking.

---

## 1. The 8 Core Beta Cohort 1 Metrics

The administrator operations view at `/analytics/beta/` measures eight primary progression milestones across the student journey:

| Metric # | Milestone Name | Database Source / Event Type | Definition |
| :---: | :--- | :--- | :--- |
| **1** | **Registration Completion** | `auth.User.objects.count()` | Total invited students who completed registration and verified their account. |
| **2** | **Onboarding Completion** | `StudentProfile.objects.filter(onboarding_completed=True)` | Students who selected learning level, interests, and target career track. |
| **3** | **First Lesson Completion** | `ProductEvent(event_type__in=['first_lesson_started', 'lesson_completed'])` | Students who launched their recommended starter course and engaged with lesson 1. |
| **4** | **Returning Student Activity** | `ProductEvent(event_type='returning_login')` | Retained students logging in 24+ hours after registration. |
| **5** | **Project Creation & Completion** | `ProductEvent(event_type='first_project_created')` | Students initializing an evidence-backed project in Portfolio Studio. |
| **6** | **Resume Generation** | `ProductEvent(event_type='resume_generated')` | Students compiling their tailored ATS resume in Career Studio. |
| **7** | **Opportunity Saves & Applies** | `ProductEvent(event_type__in=['opportunity_saved', 'opportunity_applied'])` | Students bookmarking or applying to verified entry-level roles. |
| **8** | **Errors & Abandoned Workflows** | `ProductEvent(event_type__icontains='error')` + `DurableTaskJob(status='failed')` | Runtime exceptions, fallback triggers, or abandoned user flows flagged for investigation. |

---

## 2. Privacy & Data Minimization Principles

1. **Zero Keystroke / Heatmap Tracking**: No client-side keyloggers or click-recording scripts are permitted.
2. **Zero Third-Party Trackers**: No Meta Pixel, Google Analytics, or third-party marketing tags are injected.
3. **No Disclosure of Private Personal Content**:
   - Private markdown notes in Student Workspace (`workspace.PersonalNote`) are strictly inaccessible to staff.
   - Private daily calendars (`workspace.WorkspaceTask`) are excluded from telemetry.
   - Draft unshared resumes are never indexed or viewable by recruiters or administrators.
4. **Masked Student Identifiers**: The administrator view displays masked student usernames (`ale***`, `joh***`) to protect personal privacy while enabling cohort size verification.
5. **GDPR / CCPA Right to Portability**: Students can export all stored telemetry and personal records in JSON format via `/accounts/export-data/`.

---

## 3. Operational Administrator View (`/analytics/beta/`)

The Staff Beta Operations Hub provides live aggregated visibility into:

```
[Beta Operations & Product Analytics]
├── 1. Top KPI Summary (Invitations, DAU/WAU, Onboarding Rate, Open Bugs)
├── 2. 8-Stage Student Milestones Funnel
├── 3. Cohort 1 Invitations Table (15 Tokens: Code, Email, Status, Claimed User)
├── 4. Active Students Overview (Masked Name, Role, Level, Enrolled, Lessons Done)
├── 5. Prioritized Open Bugs & Blockers (Critical P0 / High Alert Card)
└── 6. Centralized Feedback Inbox (Filterable by Bugs, Usability, Missing, Content, Suggestions)
```

---

## 4. Telemetry Verification Log

- **Automated Validation**: Verified in preflight test `Telemetry Logging Idempotent & Functional`.
- **Idempotency Enforcement**: `ProductEvent.track()` utilizes SHA-256 idempotency keys preventing duplicate counts on page refreshes.
- **Circuit Breaker Fallbacks**: When external AI services encounter rate limits or network latency, graceful fallbacks to the deterministic Knowledge Engine are logged under telemetry without crashing user requests.
