# SkillSphere Personal Notes & Reference Bookmarks

## Overview

The **Personal Notes & Bookmarks Hub** (`/workspace/notes/`) provides students with a private workspace to record technical insights, architectural summaries, and reference material.

---

## Core Capabilities

1. **Folder Organization & Tagging**:
   - Customizable folders (`General`, `Courses`, `Projects`, `Career`, `Interview Prep`, etc.).
   - Multi-tag support (comma-separated tags parsed and displayed as search chips).
   - Pinning capability (`is_pinned=True`) to keep critical reference notes at the top.

2. **Course & Project Attachments**:
   - Notes can be linked directly to a specific `Course`, `Lesson`, or `ProjectIdea`.
   - Enables contextual lookup from both the workspace and course detail pages.

3. **Full-Text Multi-Field Search**:
   - Real-time search across titles, markdown content, tags, and bookmark notes.

4. **Reference Bookmarks (`WorkspaceBookmark`)**:
   - Save external documentation links, GitHub repository references, and official opportunity pages.
   - Categorized by type (`lesson`, `project`, `opportunity`, `resource`).

5. **Strict Ownership & Privacy Guarantee**:
   > [!CAUTION]
   > Personal notes and bookmarks are **strictly private to the author**.
   > All views, mutations, and deletion endpoints enforce `user=request.user` checks. Any cross-user access attempts result in HTTP 404/403 responses.

---

## Models Schema

```python
class PersonalNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_notes')
    title = models.CharField(max_length=255)
    content = models.TextField(help_text='Markdown supported personal note content')
    folder = models.CharField(max_length=100, default='General', db_index=True)
    tags = models.CharField(max_length=255, blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('learning.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('projects.ProjectIdea', on_delete=models.SET_NULL, null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class WorkspaceBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_bookmarks')
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500)
    bookmark_type = models.CharField(max_length=30, choices=BOOKMARK_TYPE_CHOICES, default='lesson')
    category = models.CharField(max_length=100, default='Reference')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('learning.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey('projects.ProjectIdea', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```
