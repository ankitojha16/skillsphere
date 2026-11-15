from django.urls import path
from . import views

app_name = 'workspace'

urlpatterns = [
    # 1. Main Workspace Dashboard
    path('', views.workspace_dashboard_view, name='dashboard'),

    # 2. Daily Planner & Tasks
    path('planner/', views.planner_view, name='planner'),
    path('tasks/create/', views.task_create_view, name='task_create'),
    path('tasks/<int:task_id>/toggle/', views.task_toggle_view, name='task_toggle'),
    path('tasks/<int:task_id>/reschedule/', views.task_reschedule_view, name='task_reschedule'),
    path('tasks/<int:task_id>/delete/', views.task_delete_view, name='task_delete'),
    path('tasks/adopt-suggestion/', views.task_adopt_suggestion_view, name='task_adopt_suggestion'),

    # 3. Smart Calendar
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/events/json/', views.calendar_events_json_api, name='calendar_events_json'),
    path('calendar/events/create/', views.calendar_event_create_view, name='calendar_event_create'),
    path('calendar/events/<int:event_id>/delete/', views.calendar_event_delete_view, name='calendar_event_delete'),

    # 4. Focus Sessions
    path('focus/', views.focus_session_view, name='focus'),
    path('focus/log/', views.focus_session_log_api, name='focus_log_api'),

    # 5. Personal Notes & Bookmarks
    path('notes/', views.notes_view, name='notes'),
    path('notes/save/', views.note_save_view, name='note_save'),
    path('notes/<int:note_id>/delete/', views.note_delete_view, name='note_delete'),
    path('bookmarks/save/', views.bookmark_save_view, name='bookmark_save'),
    path('bookmarks/<int:bookmark_id>/delete/', views.bookmark_delete_view, name='bookmark_delete'),

    # 6. Weekly Progress Intelligence
    path('weekly-report/', views.weekly_report_view, name='weekly_report'),

    # 7. AI Study Planner
    path('ai-planner/', views.ai_study_planner_view, name='ai_planner'),

    # 8. Notification Preferences
    path('notifications/settings/', views.notification_settings_view, name='notification_settings'),
]
