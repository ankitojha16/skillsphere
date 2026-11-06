from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('<slug:course_slug>/<int:lesson_id>/', views.lesson_view, name='lesson_detail'),
    path('<slug:course_slug>/<int:lesson_id>/toggle/', views.complete_lesson_toggle, name='complete_toggle'),
    path('<slug:course_slug>/<int:lesson_id>/video-progress/', views.video_progress_api, name='video_progress'),
    path('<slug:course_slug>/<int:lesson_id>/bookmark/', views.bookmark_toggle_api, name='bookmark_toggle'),
    path('<slug:course_slug>/<int:lesson_id>/note/', views.student_note_api, name='student_note'),
    path('<slug:course_slug>/<int:lesson_id>/download-notes/', views.download_lesson_notes_pdf_view, name='download_notes_pdf'),
    path('<slug:course_slug>/<int:lesson_id>/exercise/<int:exercise_id>/submit/', views.exercise_submit_api, name='exercise_submit'),
    path('<slug:course_slug>/<int:lesson_id>/ai-assist/', views.ai_notes_assist_api, name='ai_notes_assist'),
]
