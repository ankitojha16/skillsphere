from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('', views.goals_list_view, name='index'),
    path('create/', views.goal_create_view, name='create'),
    path('<int:goal_id>/update/', views.goal_update_view, name='update'),
    path('<int:goal_id>/delete/', views.goal_delete_view, name='delete'),
    path('<int:goal_id>/toggle/', views.goal_toggle_view, name='toggle'),
]
