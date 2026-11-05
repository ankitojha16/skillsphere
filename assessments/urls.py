from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('', views.assessments_list_view, name='list'),
    path('<int:assessment_id>/take/', views.take_assessment_view, name='take'),
    path('<int:assessment_id>/submit/', views.submit_assessment_view, name='submit'),
    path('result/<int:attempt_id>/', views.assessment_result_view, name='result'),
]
