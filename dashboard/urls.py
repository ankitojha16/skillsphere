from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('study-lounge/', views.study_lounge_view, name='study_lounge'),
    path('study-lounge/log-session/', views.log_focus_session_view, name='log_focus_session'),
]
