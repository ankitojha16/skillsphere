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
  • Dedicated support contact card: beta-support@skillsphere.test
```

---

## 3. Provisioned Invitation Tokens (Cohort 1)

15 unique, cryptographically random invitation tokens were generated via `python manage.py setup_beta_cohort_1`:

| Token Code | Designated Recipient | Invite URL | Status |
| :--- | :--- | :--- | :---: |
| `BETA-C1-7A918602` | `cohort1_student_01@skillsphere.beta` | `/accounts/invite/BETA-C1-7A918602/` | **Pending** |
| `BETA-C1-12690040` | `cohort1_student_02@skillsphere.beta` | `/accounts/invite/BETA-C1-12690040/` | **Pending** |
| `BETA-C1-5BE4C21A` | `cohort1_student_03@skillsphere.beta` | `/accounts/invite/BETA-C1-5BE4C21A/` | **Pending** |
| `BETA-C1-5E06BB18` | `cohort1_student_04@skillsphere.beta` | `/accounts/invite/BETA-C1-5E06BB18/` | **Pending** |
| `BETA-C1-A5E714BB` | `cohort1_student_05@skillsphere.beta` | `/accounts/invite/BETA-C1-A5E714BB/` | **Pending** |
| `BETA-C1-B66400A1` | `cohort1_student_06@skillsphere.beta` | `/accounts/invite/BETA-C1-B66400A1/` | **Pending** |
| `BETA-C1-33D0A13E` | `cohort1_student_07@skillsphere.beta` | `/accounts/invite/BETA-C1-33D0A13E/` | **Pending** |
| `BETA-C1-1DC80D70` | `cohort1_student_08@skillsphere.beta` | `/accounts/invite/BETA-C1-1DC80D70/` | **Pending** |
| `BETA-C1-BCF6A45F` | `cohort1_student_09@skillsphere.beta` | `/accounts/invite/BETA-C1-BCF6A45F/` | **Pending** |
| `BETA-C1-77DBADF3` | `cohort1_student_10@skillsphere.beta` | `/accounts/invite/BETA-C1-77DBADF3/` | **Pending** |
| `BETA-C1-BB37D8F5` | `cohort1_student_11@skillsphere.beta` | `/accounts/invite/BETA-C1-BB37D8F5/` | **Pending** |
| `BETA-C1-C02C3A4B` | `cohort1_student_12@skillsphere.beta` | `/accounts/invite/BETA-C1-C02C3A4B/` | **Pending** |
| `BETA-C1-C17E208E` | `cohort1_student_13@skillsphere.beta` | `/accounts/invite/BETA-C1-C17E208E/` | **Pending** |
| `BETA-C1-E0D11F7F` | `cohort1_student_14@skillsphere.beta` | `/accounts/invite/BETA-C1-E0D11F7F/` | **Pending** |
| `BETA-C1-7ADA8FD2` | `cohort1_student_15@skillsphere.beta` | `/accounts/invite/BETA-C1-7ADA8FD2/` | **Pending** |

---

## 4. Student Privacy & Minor Safeguards

In compliance with student data rights and COPPA/GDPR guidelines:
1. **Under-18 & High School Isolation**: When students select `high_school` during onboarding, recruiter invitation routes return HTTP 403 Forbidden. Student profiles cannot be contacted or shortlisted by external recruiters.
2. **Private by Default**: Personal student study notes (`workspace.PersonalNote`), daily task calendars (`workspace.WorkspaceTask`), and private draft resumes are completely isolated and never exposed on staff dashboards.
3. **Self-Service Portability**: Students can export their complete account history in JSON format at `/accounts/export-data/` at any time.
4. **Account Deletion**: Self-service account deletion is functional at `/accounts/delete-account/`.

---

## 5. Support & Communications Channel

- **Beta Operations Lead Email**: `beta-support@skillsphere.test`
- **In-App Direct Feedback**: Persistent "Give Feedback" button in navbar and dashboard footer triggering the 5-question structured modal.
- **Staff Operations Hub**: `/analytics/beta/` providing live telemetry, open bug prioritization, and invitation status.
