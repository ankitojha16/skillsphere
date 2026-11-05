from django.urls import path
from . import views

app_name = 'roadmaps'

urlpatterns = [
    path('', views.roadmaps_list_view, name='list'),
    path('generate/', views.roadmap_generate_view, name='generate'),
    path('<int:roadmap_id>/', views.roadmap_detail_view, name='detail'),
    path('milestone/<int:milestone_id>/toggle/', views.roadmap_toggle_milestone, name='toggle_milestone'),
    path('<int:roadmap_id>/delete/', views.roadmap_delete_view, name='delete'),
]
