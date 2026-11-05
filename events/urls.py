from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('events/', views.event_list_view, name='list'),
    path('events/<int:pk>/', views.event_detail_view, name='detail'),
    path('events/<int:pk>/save/', views.toggle_save_event_view, name='toggle_save_event'),
    path('events/<int:pk>/toggle-save/', views.toggle_save_event_view, name='toggle_save'),
]
