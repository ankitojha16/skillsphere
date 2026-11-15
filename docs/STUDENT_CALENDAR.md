# SkillSphere Smart Calendar

## Overview

The **Smart Calendar** (`/workspace/calendar/`) provides a unified, timezone-aware timeline that brings together student-authored study events and official platform deadlines.

---

## Architectural Features

1. **Unified Event Aggregation**:
   - `Personal Events`: Student-created study sessions, reviews, and reminders (`CalendarEvent`).
   - `Task Deadlines`: Automatic projection of `WorkspaceTask.due_date` onto the timeline. Completed tasks render in green, overdue tasks in red, pending in blue.
   - `Official Opportunity Deadlines`: Strict system deadlines from `Opportunity.deadline` rendered in distinct pink/red with `[Official Program Deadline]` badges.
   - `Project Delivery Targets`: `ProjectIdea.completion_date` projections in purple.
   - `Hackathons & Competitions`: Event start and end dates from `SavedEvent`.

2. **Timezone Awareness**:
   - Dynamically detects the user's browser timezone via `Intl.DateTimeFormat().resolvedOptions().timeZone`.
   - All server timestamps are UTC aware (`django.utils.timezone`).

3. **Views Supported**:
   - `Month Grid`: Monthly overview of all commitments and deadlines.
   - `Week View`: Weekly schedule layout with time intervals.
   - `Day View`: Granular hourly breakdown of daily tasks and sessions.
   - `Agenda List`: Compact tabular list of upcoming milestones.

4. **Security & Ownership**:
   - Students can create, edit, and delete their own `CalendarEvent` records.
   - Official deadlines cannot be deleted by students, preventing accidental loss of critical program deadlines.

---

## JSON Feed API: `/workspace/calendar/events/json/`

The calendar fetches events asynchronously using the standard FullCalendar format:

```json
[
  {
    "id": "event-12",
    "raw_id": 12,
    "title": "Django ORM Deep Dive",
    "description": "Study QuerySet prefetch_related and select_related",
    "start": "2026-11-16T10:00:00+00:00",
    "end": "2026-11-16T12:00:00+00:00",
    "allDay": false,
    "color": "#6366f1",
    "type": "study",
    "is_official": false,
    "category_label": "Study Session",
    "can_edit": true
  },
  {
    "id": "opp-5",
    "raw_id": 5,
    "title": "🎯 Deadline: Google Summer of Code 2026 (Google Open Source)",
    "description": "Official Opportunity Deadline: Internship / Program",
    "start": "2026-04-08T00:00:00",
    "end": "2026-04-08T00:00:00",
    "allDay": true,
    "color": "#ec4899",
    "type": "opportunity_deadline",
    "is_official": true,
    "category_label": "Official Program Deadline",
    "can_edit": false,
    "url": "/opportunities/5/"
  }
]
```
