# SkillSphere — Beta Feedback System & Operations Report

## Objective
Establish an unobtrusive, structured, and rapid feedback loop for controlled beta students to report usability friction, highlight valuable features, and identify curriculum gaps.

---

## 1. The 5 Core Beta Feedback Questions

Rather than asking for unstructured generic comments, the feedback dialog gathers targeted responses to five key questions:

1. **What was easy to use?**
   - *Purpose*: Identifies UI flows where student cognitive load was low and navigation was intuitive.
2. **What was confusing or unclear?**
   - *Purpose*: Uncovers ambiguous terminology, confusing navigation links, or complex forms.
3. **Which feature was most useful?**
   - *Purpose*: Highlights the core value drivers (e.g. ATS Resume Builder, Code Runner, Skill Gap Radar).
4. **What did you expect but could not find?**
   - *Purpose*: Discovers missing features, missing course topics, or broken expectations.
5. **What should be improved?**
   - *Purpose*: Solicits concrete recommendations for polish, performance, or styling adjustments.

---

## 2. In-App Presentation & Access Points

The feedback mechanism is integrated in two prominent locations:
1. **Global Header Action**: A persistent, accessible button in the top navigation bar labeled `Give Feedback`, allowing one-click dialog opening from any page.
2. **Post-Onboarding Banner**: An inline prompt on the Onboarding Recommendations page:
   > *"Help Us Improve SkillSphere — Notice anything confusing or missing? Share your quick feedback in 30 seconds."*

The modal is implemented using semantic HTML5 `<dialog>` and Bootstrap styling, guaranteeing full keyboard navigation and escape-key dismissal.

---

## 3. Data Storage & Schema Compatibility

To ensure zero database schema breakages and avoid complex migrations during the beta rollout:
- The backend endpoint (`/analytics/api/feedback/submit/`) accepts both JSON payloads and multipart form submissions.
- Structured answers are parsed and formatted into markdown within the existing `BetaFeedback.description` field:
  ```markdown
  **What was easy:** Navigating core sections
  **What was confusing:** None
  **Most useful feature:** ATS Resume Builder
  **Expected but could not find:** More Docker / Cloud labs
  **What should be improved:** Dark mode contrast toggle
  **Additional notes:** Beta experience test review.
  ```
- Captures optional star rating (1–5), current URL context (`page_url`), user authentication ID (or anonymous session), and uploaded screenshot proof.

---

## 4. Security & Abuse Protections

1. **Rate Limiting**: IP- and user-based throttling restricts submissions to a maximum of **10 submissions per hour** using cache keys (`beta_feedback_ratelimit_<ip_or_user>`).
2. **Image Validation**:
   - File size capped at **5 MB**.
   - Pillow (`Image.open`) inspection validates that uploaded files are authentic, non-malicious image formats (`JPEG`, `PNG`, `WEBP`, `GIF`).
   - Invalid or disguised binaries are rejected immediately with HTTP 400.

---

## 5. Staff Triage Workflow & Moderation Portal

Feedback items are reviewed by engineering and product staff:
- **Moderation Dashboard**: Located at `/opportunities/moderation/` (restricted to superusers and staff).
- **Status Lifecycle**: Items progress through `new` → `in_review` → `resolved` → `archived`.
- **Triage SLA**:
  - **Critical Bug (P0)**: Under 4-hour initial triage, 24-hour hotfix deployment.
  - **Friction / UX Ambiguity (P1)**: Reviewed daily at standup; prioritized in weekly sprint.
  - **Feature Enhancement (P2)**: Reviewed bi-weekly; tagged for future roadmap.

---

## 6. Feedback Log Verification
The feedback mechanism was verified in test `Journey Q: 5-Question Structured Beta Feedback Submission` of `e2e/test_student_journeys.py`. It confirmed automated parsing, model persistence, and correct JSON responses (`success: true, feedback_id: <id>`). Zero synthetic user quotes or manufactured reviews were fabricated in accordance with project policy.
