from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    # 1. Opportunity Discovery & Exploration
    path('opportunities/', views.opportunity_list_view, name='list'),
    path('opportunities/<int:pk>/', views.opportunity_detail_view, name='detail'),
    path('opportunities/<int:pk>/save/', views.toggle_save_opportunity_view, name='toggle_save_opportunity'),
    path('opportunities/<int:pk>/toggle-save/', views.toggle_save_opportunity_view, name='toggle_save'),
    path('opportunities/<int:pk>/apply/', views.record_application_view, name='apply'),
    path('opportunities/<int:pk>/interview-prep/', views.interview_prep_view, name='interview_prep'),
    path('opportunities/<int:pk>/report/', views.report_opportunity_view, name='report_opportunity'),

    # 2. Student Application Pipeline Tracker
    path('opportunities/my-applications/', views.application_tracker_view, name='my_applications'),
    path('opportunities/tracker/', views.application_tracker_view, name='tracker'),

    # 3. Recruiter Opportunity Management
    path('opportunities/recruiter/post/', views.recruiter_post_opportunity_view, name='recruiter_post'),
    path('opportunities/recruiter/my-listings/', views.recruiter_my_listings_view, name='recruiter_listings'),
    path('opportunities/recruiter/listings/<int:pk>/edit/', views.recruiter_edit_opportunity_view, name='recruiter_edit_listing'),
    path('opportunities/recruiter/listings/<int:pk>/toggle-archive/', views.recruiter_toggle_archive_view, name='recruiter_toggle_archive'),
    path('opportunities/recruiter/listings/<int:pk>/applicants/', views.recruiter_applicants_view, name='recruiter_applicants'),
    path('opportunities/recruiter/applicants/<int:app_id>/status/', views.recruiter_update_applicant_status_api, name='recruiter_update_applicant_status'),

    # 4. Recruiter Talent Portal & Candidate Search (Preserved)
    path('talent/', views.talent_portal_view, name='talent_portal'),
    path('talent/candidate/<str:username>/', views.candidate_dossier_view, name='candidate_dossier'),
    path('talent/candidate/<str:username>/shortlist/', views.toggle_shortlist_candidate_api, name='toggle_shortlist'),
    path('talent/candidate/<str:username>/invite/', views.send_interview_invitation_api, name='send_interview_invitation'),
    path('talent/shortlist/', views.recruiter_shortlist_view, name='my_shortlist'),
]
