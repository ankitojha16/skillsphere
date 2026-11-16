# SkillSphere — Beta Cohort 1 Feedback Management Process

## Objective
Establish a centralized, rigorous feedback intake and triage workflow for Beta Cohort 1 to rapidly identify blockers, prioritize student friction points, and eliminate critical errors.

---

## 1. The 5 Core Feedback Categories

Every report submitted by students through the in-app modal or direct portal (`/feedback/` or `/analytics/api/feedback/submit/`) is classified into one of five structured categories:

| Category Key | Category Label | Primary Focus | Example Student Experience |
| :--- | :--- | :--- | :--- |
| `bug` | **Bug Report** | Crashes, broken UI, broken buttons, 404/500 errors | "Clicking Submit on exercise 3 returns a 500 error." |
| `usability` | **Usability Problem** | Confusing wording, hard-to-find buttons, poor contrast | "I couldn't tell how to initialize my starter project from the recommendation card." |
| `missing_feature` | **Missing Functionality** | Gaps in anticipated workflows or tooling | "I expected to be able to download my resume directly as Markdown as well as PDF." |
| `content` | **Content Problem** | Typos, outdated documentation, broken code snippets | "Lesson 4 in Django course references a deprecated syntax." |
| `feature` | **Feature Suggestion** | Ideas for future enhancements | "Would love a toggle to switch between dark mode and high-contrast OLED mode." |

---

## 2. Priority Classification Matrix

Submissions are assigned an urgency rating to ensure critical bugs are remediated before minor enhancements:

```
[Critical (P0 Blocker)]
  • Crash, 500 Server Error, Data Loss, or Student Blocked from Core Journey
  • SLA: Initial triage < 4 hours; Production hotfix < 24 hours

[High Priority (P1)]
  • Repeated Student Complaints, Broken Form, Visual Layout Distortion on Mobile
  • SLA: Triage < 12 hours; Remediated in current sprint

[Medium Priority (P2)]
  • Minor UI Glitches, Usability Ambiguities, Content Clarifications
  • SLA: Triage < 24 hours; Backlog priority review

[Low Priority (P3)]
  • Cosmetic Suggestions, Long-Term Feature Requests
  • SLA: Reviewed during post-beta product roadmap planning
```

---

## 3. Repeated Complaints & Error Aggregation

When multiple beta students report friction on the same component or route:
1. **Cluster Detection**: The administrator view groups feedback by `page_url` and `category`.
2. **Automatic Escalation**: If two or more students submit feedback tagged with `bug` or `usability` on the same URL within 48 hours, the issue is elevated automatically to **High (P1)**.
3. **Admin Bug Banner**: Open bugs with `priority='critical'` or `priority='high'` are pinned to the top of `/analytics/beta/` with direct status transition actions (`New` → `Reviewing` → `Resolved`).

---

## 4. Triage Access Points & Tools

- **Administrator Operations Hub**: `/analytics/beta/` (Staff only).
  - Filter by category (`bug`, `usability`, `missing_feature`, `content`, `feature`).
  - Filter by status (`new`, `reviewing`, `resolved`).
  - Inline status updates and internal admin notes recording fix commit hashes.
- **Moderation Hub**: `/opportunities/moderation/` (Staff only).
- **Public & In-App Ingest**:
  - Global Header Button: `Give Feedback`
  - Post-Onboarding Banner: `/accounts/onboarding/recommendations/`
  - Standalone Feedback Route: `/feedback/`

---

## 5. Security & Input Verification Controls

1. **Rate Limiting**: Per-user / IP throttling limits submissions to **5 per hour** to prevent spam or accidental double-submissions.
2. **Screenshot Inspection**:
   - File size restricted to **<= 5 MB**.
   - Pillow (`Image.open`) validates that attachments are genuine, uncorrupted images (`JPEG`, `PNG`, `WEBP`, `GIF`).
   - Disguised executable files or scripts are rejected immediately with HTTP 400.
3. **Data Protection**: Screenshots and user reports are accessible only to authenticated staff members.
