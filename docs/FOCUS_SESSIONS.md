# SkillSphere Focus Sessions & Study Timer

## Overview

The **Focus Sessions Lounge** (`/workspace/focus/`) gives students a dedicated, distraction-free environment to cultivate deep-work habits.

---

## Design Principles

1. **Configurable Timer Modes**:
   - `Pomodoro (25m)`: Standard 25-minute study sprint.
   - `Deep Work (50m)`: Extended block for complex coding or architecture design.
   - `Short Break (5m)`: Rapid mental recharge.
   - `Long Break (15m)`: Rest period after multiple completed Pomodoro cycles.
   - `Custom Duration`: Flexible timeboxing for specialized assignments.

2. **Session Context Association**:
   - Students can optionally link a focus session to:
     - An enrolled `Course`.
     - An active `ProjectIdea`.
     - A specific `WorkspaceTask`.
   - Notes field captures what was accomplished during the sprint.

3. **Strict Zero-Fabrication XP Policy**:
   > [!IMPORTANT]
   > Focus sessions log study dedication and track time spent. In strict adherence to SkillSphere's authentic skill evidence standard, **timers do not artificially grant gamification XP or level-ups**.
   > XP and verified skill badges remain exclusively tied to verified quiz completions, code challenge judge passes, and published projects.

4. **Telemetry & Aggregation**:
   - Records duration, timestamp, notes, and session type in `FocusSession`.
   - Aggregates daily focus minutes and 7-day rolling totals for the workspace summary and weekly intelligence reports.

---

## Database Model: `FocusSession`

```python
class FocusSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='focus_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='pomodoro')
    duration_minutes = models.PositiveIntegerField(default=25)
    notes = models.TextField(blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('projects.ProjectIdea', on_delete=models.SET_NULL, null=True, blank=True)
    task = models.ForeignKey(WorkspaceTask, on_delete=models.SET_NULL, null=True, blank=True)
    completed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
```
