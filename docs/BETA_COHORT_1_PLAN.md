# SkillSphere — Beta Cohort 1 Execution Plan

## Objective
Execute a controlled, invite-only beta for an initial cohort of **10–20 students** to validate the core user journey (**Learn → Practice → Build → Showcase → Grow**), measure real-world student progression, and establish an active feedback loop.

> [!IMPORTANT]
> **Product Pause Doctrine**: The feature expansion phase is officially paused. No major new features or UI redesigns may be introduced during Beta Cohort 1. The focus is strictly on reliability, usability, content accuracy, and student outcomes.

---

## 1. Cohort Specification & Scope

- **Cohort Size**: 10 to 20 invited students (15 initial invitation tokens provisioned).
- **Target Profile**: Computer science, software engineering, and self-taught learners seeking entry-level developer roles or internships.
- **Duration**: 2-week active validation window.
- **Baseline Git Commit**: `21a5812` (with Beta Cohort 1 operations enhancements).
- **Core Pillars Available**:
  1. **Home**: Daily Student Workspace (`/dashboard/`)
  2. **Learn**: 69 accredited courses, 1,104 lessons, study roadmaps, AI Study Assistant (`/courses/`, `/roadmaps/`, `/ai-assistant/?mode=study`)
  3. **Practice**: Skill assessments, coding challenges, mock interviews (`/skill-assessment/`, `/skill-assessment/challenges/`, `/mock-interview/`)
  4. **Projects**: Project portfolio studio, project idea generator (`/portfolio/`, `/project-generator/`)
  5. **Career**: 11 career tracks, skill gap analyzer, ATS resume builder, 16 verified opportunities (`/career-studio/`, `/career-studio/gap-analyzer/`, `/resume-builder/`, `/opportunities/`)

---

## 2. Controlled Onboarding Architecture

```
[Invitation Token Sent to Student]
                │
                ▼
[Dedicated Welcome Landing: /accounts/invite/<code>/]
  • Token verification & seat reservation
  • Clear 4-step journey instructions
  • Minor student privacy safeguard notice
  • Support contact information
                │
                ▼
[Registration: /accounts/signup/?invite=<code>]
  • Email + Password account creation
  • Auto-links BetaInvitation record (status: accepted)
  • Fires idempotent registration_completed telemetry
                │
                ▼
[Onboarding Preferences: /accounts/profile-setup/]
  • Education level & learning level
  • Technical interests selection
  • Automatic Minor Safeguard: If high_school, hides profile from recruiters
                │
                ▼
[Step 2 Launchpad: /accounts/onboarding/recommendations/]
  • High-affinity starter course recommendation with estimated minutes
  • Direct 1-click CTA: "Start First Lesson Now" (auto-enrolls & starts lesson 1)
  • 1-click Career Track selection across 11 industry paths
  • Starter portfolio project brief with 1-click initialization
  • Global 5-question Beta Feedback modal link
  • Dedicated support contact card: support@skillsphere.app
```

---

## 3. Provisioned Secure Invitation Architecture (Cohort 1)

All previously exposed tokens have been **revoked**. Beta Cohort 1 invitations now employ a hardened cryptographic architecture:

- **Entropy**: $\ge 160$ bits of randomness per token (`secrets.token_urlsafe(24)`).
- **Storage**: Raw secret tokens are **never** stored in the database or persisted in server logs. Only cryptographic SHA-256 hashes (`token_hash`) are persisted.
- **Single-Use**: Row-level atomic transactions enforce strict single-use upon account creation.
- **Expiry**: 7-day TTL expiration (`expires_at`), after which unredeemed tokens automatically expire.
- **Email Binding**: Each invitation is cryptographically bound to its authorized recipient email. Registration requests with non-matching emails are rejected with validation errors.
- **Operator Distribution**: Private URLs (`https://skillsphere.app/accounts/invite/<raw_token>/`) are output once to the operator terminal via `python manage.py setup_beta_cohort_1` and never checked into documentation.

| Invitation Reference | Designated Recipient | Status | Expiration Policy |
| :--- | :--- | :---: | :--- |
| `BETA-C1-01` | `student_01@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-02` | `student_02@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-03` | `student_03@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-04` | `student_04@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-05` | `student_05@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-06` | `student_06@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-07` | `student_07@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-08` | `student_08@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-09` | `student_09@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-10` | `student_10@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-11` | `student_11@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-12` | `student_12@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-13` | `student_13@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-14` | `student_14@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |
| `BETA-C1-15` | `student_15@skillsphere.app` | **Created / Active** | 7-day TTL • SHA-256 Hashed |

---

## 4. Student Privacy & Minor Safeguards

In compliance with student data rights and COPPA/GDPR guidelines:
1. **Under-18 & High School Isolation**: When students select `high_school` during onboarding, recruiter invitation routes return HTTP 403 Forbidden. Student profiles cannot be contacted or shortlisted by external recruiters.
2. **Private by Default**: Personal student study notes (`workspace.PersonalNote`), daily task calendars (`workspace.WorkspaceTask`), and private draft resumes are completely isolated and never exposed on staff dashboards.
3. **Self-Service Portability**: Students can export their complete account history in JSON format at `/accounts/export-data/` at any time.
4. **Account Deletion**: Self-service account deletion is functional at `/accounts/delete-account/`.

---

## 5. Support & Communications Channel

- **Beta Operations Lead Email**: `support@skillsphere.app`
- **In-App Direct Feedback**: Persistent "Give Feedback" button in navbar and dashboard footer triggering the 5-question structured modal.
- **Staff Operations Hub**: `/analytics/beta/` providing live telemetry, open bug prioritization, and invitation status.
- **In-App Direct Feedback**: Persistent "Give Feedback" button in navbar and dashboard footer triggering the 5-question structured modal.
- **Staff Operations Hub**: `/analytics/beta/` providing live telemetry, open bug prioritization, and invitation status.
