from django.urls import path
from . import views

app_name = 'interviews'

urlpatterns = [
    path('', views.interview_setup_view, name='setup'),
    path('<int:interview_id>/session/', views.interview_session_view, name='session'),
    path('<int:interview_id>/submit/', views.interview_submit_answer, name='submit_answer'),
    path('<int:interview_id>/report/', views.interview_report_view, name='report'),
]
