from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('', views.assessments_list_view, name='list'),
    path('<int:assessment_id>/take/', views.take_assessment_view, name='take'),
    path('<int:assessment_id>/submit/', views.submit_assessment_view, name='submit'),
    path('result/<int:attempt_id>/', views.assessment_result_view, name='result'),

    # LeetCode-Grade Coding Challenges & Test Judge
    path('challenges/', views.challenges_list_view, name='challenge_list'),
    path('challenges/<slug:slug>/', views.challenge_detail_view, name='challenge_detail'),
    path('challenges/<slug:slug>/submit/', views.submit_challenge_solution, name='challenge_submit'),
    path('challenges/<slug:slug>/test-cases/', views.challenge_test_cases_api, name='challenge_test_cases'),
]
