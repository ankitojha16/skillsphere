from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('study-lounge/', views.study_lounge_view, name='study_lounge'),
    path('study-lounge/log-session/', views.log_focus_session_view, name='log_focus_session'),
    path('api/daily-drill/', views.get_daily_micro_drill_api, name='daily_drill_get'),
    path('api/daily-drill/submit/', views.submit_daily_micro_drill_api, name='daily_drill_submit'),
]
