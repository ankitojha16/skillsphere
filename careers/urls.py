from django.urls import path
from . import views
from . import views_studio

app_name = 'careers'

urlpatterns = [
    # Legacy Career Hub & Job Application Tracker Routes
    path('career-hub/', views.career_hub_view, name='hub'),
    path('career-hub/explore/<slug:slug>/', views.career_path_detail_view, name='path_detail'),
    path('career-analytics/', views.career_analytics_view, name='analytics'),
    path('tracker/', views.job_tracker_view, name='job_tracker'),
    path('tracker/create/', views.create_job_application_view, name='create_job_application'),
    path('tracker/<int:job_id>/status/', views.update_job_status_view, name='update_job_status'),
    path('tracker/<int:job_id>/delete/', views.delete_job_application_view, name='delete_job_application'),
    path('tracker/<int:job_id>/outreach/', views.generate_outreach_view, name='generate_outreach'),
    path('tracker/export/csv/', views.export_job_applications_csv, name='export_csv'),

    # =========================================================================
    # SkillSphere Career Studio Routes (/career-studio/...)
    # =========================================================================
    path('career-studio/', views_studio.career_studio_dashboard, name='studio_dashboard'),
    path('career-studio/paths/', views_studio.career_path_explorer, name='studio_paths'),
    path('career-studio/paths/<slug:slug>/', views_studio.career_path_detail, name='studio_path_detail'),
    path('career-studio/paths/<slug:slug>/set-goal/', views_studio.set_career_goal, name='studio_set_goal'),
    path('career-studio/gap-analyzer/', views_studio.skill_gap_analyzer, name='studio_gap_analyzer'),
    path('career-studio/gap-analyzer/<slug:slug>/', views_studio.skill_gap_analyzer, name='studio_gap_analyzer_track'),
    path('career-studio/roadmap/', views_studio.career_roadmap_view, name='studio_roadmap'),
    path('career-studio/roadmap/toggle/<int:milestone_id>/', views_studio.toggle_roadmap_milestone, name='studio_toggle_roadmap_milestone'),
    path('career-studio/roadmap/reorder/', views_studio.reorder_roadmap_milestones, name='studio_reorder_roadmap_milestones'),

    # Project Portfolio Studio (5-Stage Workflow)
    path('career-studio/projects/', views_studio.portfolio_studio_view, name='portfolio_studio'),
    path('career-studio/projects/new/', views_studio.create_studio_project, name='create_studio_project'),
    path('career-studio/projects/<int:project_id>/', views_studio.studio_project_detail, name='studio_project_detail'),
    path('career-studio/projects/<int:project_id>/milestones/add/', views_studio.add_project_milestone, name='add_project_milestone'),
    path('career-studio/projects/<int:project_id>/milestones/<int:milestone_id>/toggle/', views_studio.toggle_project_milestone, name='toggle_project_milestone'),
    path('career-studio/projects/<int:project_id>/visibility/', views_studio.toggle_project_visibility, name='toggle_project_visibility'),

    # Smart Resume Studio
    path('career-studio/resume/', views_studio.smart_resume_studio, name='smart_resume_studio'),
    path('career-studio/resume/generate/', views_studio.generate_smart_resume, name='generate_smart_resume'),
    path('career-studio/resume/<int:resume_id>/preview/', views_studio.preview_smart_resume, name='preview_smart_resume'),
    path('career-studio/resume/<int:resume_id>/version/', views_studio.create_resume_version, name='create_resume_version'),
    path('career-studio/resume/<int:resume_id>/reorder/', views_studio.reorder_resume_sections, name='reorder_resume_sections'),
    path('career-studio/resume/<int:resume_id>/export/', views_studio.export_smart_resume_pdf, name='export_smart_resume_pdf'),

    # AI Career Assistant
    path('career-studio/assistant/', views_studio.career_assistant_view, name='studio_assistant'),
    path('career-studio/assistant/query/', views_studio.career_assistant_query, name='studio_assistant_query'),
]
