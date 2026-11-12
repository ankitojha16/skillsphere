from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('opportunities/', views.opportunity_list_view, name='list'),
    path('opportunities/<int:pk>/', views.opportunity_detail_view, name='detail'),
    path('opportunities/<int:pk>/save/', views.toggle_save_opportunity_view, name='toggle_save_opportunity'),
    path('opportunities/<int:pk>/toggle-save/', views.toggle_save_opportunity_view, name='toggle_save'),
    path('opportunities/tracker/', views.application_tracker_view, name='tracker'),
    
    # Recruiter Talent Portal & Candidate Search
    path('talent/', views.talent_portal_view, name='talent_portal'),
    path('talent/candidate/<str:username>/', views.candidate_dossier_view, name='candidate_dossier'),
    path('talent/candidate/<str:username>/shortlist/', views.toggle_shortlist_candidate_api, name='toggle_shortlist'),
    path('talent/candidate/<str:username>/invite/', views.send_interview_invitation_api, name='send_interview_invitation'),
    path('talent/shortlist/', views.recruiter_shortlist_view, name='my_shortlist'),
]
