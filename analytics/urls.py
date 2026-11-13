from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Feedback & Bug Reporting Endpoints
    path('feedback/', views.feedback_page_view, name='feedback_page'),
    path('api/feedback/submit/', views.submit_feedback_api, name='submit_feedback_api'),
    path('api/feedback/<int:feedback_id>/status/', views.update_feedback_status_api, name='update_feedback_status_api'),

    # Admin Beta Operations Dashboard (Staff-Only)
    path('beta/', views.admin_beta_dashboard_view, name='admin_beta_dashboard'),
]
