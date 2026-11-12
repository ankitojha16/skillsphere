from django.urls import path
from . import views

app_name = 'careers'

urlpatterns = [
    path('career-hub/', views.career_hub_view, name='hub'),
    path('career-hub/explore/<slug:slug>/', views.career_path_detail_view, name='path_detail'),
    path('career-analytics/', views.career_analytics_view, name='analytics'),

    # AI Job Search Co-Pilot & Kanban Application Tracker
    path('tracker/', views.job_tracker_view, name='job_tracker'),
    path('tracker/create/', views.create_job_application_view, name='create_job_application'),
    path('tracker/<int:job_id>/status/', views.update_job_status_view, name='update_job_status'),
    path('tracker/<int:job_id>/delete/', views.delete_job_application_view, name='delete_job_application'),
    path('tracker/<int:job_id>/outreach/', views.generate_outreach_view, name='generate_outreach'),
    path('tracker/export/csv/', views.export_job_applications_csv, name='export_csv'),
]


