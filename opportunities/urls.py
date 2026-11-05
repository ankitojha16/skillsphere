from django.urls import path
from . import views

app_name = 'opportunities'

urlpatterns = [
    path('opportunities/', views.opportunity_list_view, name='list'),
    path('opportunities/<int:pk>/', views.opportunity_detail_view, name='detail'),
    path('opportunities/<int:pk>/save/', views.toggle_save_opportunity_view, name='toggle_save_opportunity'),
    path('opportunities/<int:pk>/toggle-save/', views.toggle_save_opportunity_view, name='toggle_save'),
    path('opportunities/tracker/', views.application_tracker_view, name='tracker'),
]
