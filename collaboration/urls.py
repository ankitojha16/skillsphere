from django.urls import path
from . import views

app_name = 'collaboration'

urlpatterns = [
    path('collaboration/', views.project_list_view, name='list'),
    path('collaboration/create/', views.create_project_view, name='create'),
    path('collaboration/<int:pk>/', views.project_detail_view, name='detail'),
    path('collaboration/manage/<int:pk>/', views.manage_team_view, name='manage'),
]
