from django.contrib import admin
from .models import WorkspaceTask, CalendarEvent, FocusSession, PersonalNote, WorkspaceBookmark, NotificationPreference


@admin.register(WorkspaceTask)
class WorkspaceTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'task_type', 'priority', 'due_date', 'is_completed')
    list_filter = ('task_type', 'priority', 'is_completed')
    search_fields = ('title', 'description', 'user__username')


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'event_type', 'start_time', 'end_time', 'is_all_day')
    list_filter = ('event_type', 'is_all_day')
    search_fields = ('title', 'description', 'user__username')


@admin.register(FocusSession)
class FocusSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_type', 'duration_minutes', 'completed', 'created_at')
    list_filter = ('session_type', 'completed')
    search_fields = ('user__username', 'notes')


@admin.register(PersonalNote)
class PersonalNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'folder', 'is_pinned', 'updated_at')
    list_filter = ('folder', 'is_pinned')
    search_fields = ('title', 'content', 'tags', 'user__username')


@admin.register(WorkspaceBookmark)
class WorkspaceBookmarkAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'bookmark_type', 'category', 'created_at')
    list_filter = ('bookmark_type', 'category')
    search_fields = ('title', 'url', 'user__username')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'digest_frequency', 'advance_reminder_hours', 'notify_deadlines')
