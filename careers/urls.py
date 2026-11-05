from django.urls import path
from . import views

app_name = 'careers'

urlpatterns = [
    path('career-hub/', views.career_hub_view, name='hub'),
    path('career-hub/explore/<slug:slug>/', views.career_path_detail_view, name='path_detail'),
    path('career-analytics/', views.career_analytics_view, name='analytics'),
]
