# SkillSphere Workspace Privacy, Safety & Security

## Overview

The Student Workspace is designed around strict privacy, data isolation, and minor protection standards.

---

## 1. Private by Default

All resources created within the workspace are strictly private to the student account:
- `WorkspaceTask`: Tasks, priorities, and checklists are inaccessible to anyone else.
- `CalendarEvent`: Student schedules and personal reminders are completely hidden from public APIs and recruiters.
- `FocusSession`: Session durations, study intervals, and personal notes are never shared.
- `PersonalNote`: Notes and code drafts are private by default.
- `WorkspaceBookmark`: Bookmarks and links are visible only to the owning user.

---

## 2. Minor Student Protections

1. **No Recruiter Exposure**:
   - Recruiters using the Talent Scout portal cannot view private student workspace schedules, daily task lists, focus session habits, or personal notes.
   - Minor students (`education_level='high_school'`) remain protected from unmoderated direct outreach or unsolicited recruiter contact.
2. **Account Deletion & Data Rights**:
   - In accordance with GDPR / COPPA / CCPA principles, cascading deletions (`on_delete=models.CASCADE`) ensure that if a student account is removed, all associated tasks, events, focus sessions, notes, bookmarks, and notification preferences are permanently purged.

---

## 3. Anti-Spam & Notification Controls

Students hold complete control over alerts via `/workspace/notifications/settings/`:
- Granular toggles for deadlines, task reminders, project milestones, and opportunities.
- Digest frequency controls (`Immediate`, `Daily Digest`, `Weekly Digest`, or `Mute All`).
- Cooldown and deduplication mechanisms prevent reminder spam.
