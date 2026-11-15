# SkillSphere Smart Daily Planner

## Overview

The **Smart Daily Planner** (`/workspace/planner/`) enables students to organize, prioritize, and execute their day-to-day learning without cognitive overload.

---

## Core Capabilities

1. **Task Taxonomy**:
   - `personal`: Student-authored tasks (e.g. "Review system design chapter").
   - `course`: Linked directly to an enrolled course and specific lesson.
   - `exercise`: Practical coding exercise goals.
   - `project`: Project delivery milestones linked to `ProjectIdea`.
   - `career`: Application preparation, resume updates, and interview prep.
   - `assessment`: Skill assessment preparation.

2. **Priority Hierarchy**:
   - `urgent`: Highlighted with red badge. Immediate attention required.
   - `high`: Yellow badge. Significant impact on learning goals.
   - `medium`: Primary blue badge. Default standard priority.
   - `low`: Muted badge. Nice-to-have activities.

3. **Status Filters & Tabs**:
   - `All`: Total count of tasks created.
   - `Today`: Tasks due today (`due_date == today`).
   - `Overdue`: Incomplete tasks where `due_date < today`.
   - `Pending`: All open incomplete tasks.
   - `Completed`: Archived tasks completed by student.

4. **Task Rescheduling Engine**:
   - Students can quickly reschedule unfinished tasks with single-click options:
     - `Due Today`: Moves task deadline to current date.
     - `Due Tomorrow`: Adjusts deadline to `today + 1 day`.
     - `Due Next Week`: Shifts deadline out by 7 days.
     - `Custom Date`: Allows manual calendar date selection.

5. **Grounded Daily Task Recommendations**:
   - The planner analyzes student records in real time:
     - Detects the next incomplete lesson in enrolled courses.
     - Identifies the next incomplete milestone in active learning roadmaps.
     - Detects pending milestones in active development projects.
     - Checks approaching opportunity application deadlines within 5 days.
   - Suggestions are displayed at the top of the planner. Students adopt them with one click (`/workspace/tasks/adopt-suggestion/`).

---

## Database Model: `WorkspaceTask`

```python
class WorkspaceTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=30, choices=TASK_TYPE_CHOICES, default='personal', db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    estimated_minutes = models.PositiveIntegerField(default=30)
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Optional contextual links
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('learning.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('projects.ProjectIdea', on_delete=models.SET_NULL, null=True, blank=True)
    roadmap_milestone = models.ForeignKey('roadmaps.RoadmapMilestone', on_delete=models.SET_NULL, null=True, blank=True)
    saved_opportunity = models.ForeignKey('opportunities.SavedOpportunity', on_delete=models.SET_NULL, null=True, blank=True)
```
