from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.generator_view, name='generator'),
    path('save/', views.save_project_view, name='save'),
    path('saved/', views.saved_projects_view, name='saved'),
    path('saved/<int:project_id>/', views.project_detail_view, name='detail'),
    path('view/<str:project_ref>/', views.project_detail_view, name='detail_ref'),
    path('saved/<int:project_id>/delete/', views.project_delete_view, name='delete'),
]
