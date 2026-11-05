from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('notifications/', views.notification_list_view, name='list'),
    path('notifications/<int:pk>/read/', views.mark_as_read_view, name='mark_read'),
    path('notifications/mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('notifications/<int:pk>/delete/', views.delete_notification_view, name='delete'),
]
