from django.urls import path
from . import views

app_name = 'collaboration'

urlpatterns = [
    path('collaboration/', views.project_list_view, name='list'),
    path('collaboration/create/', views.create_project_view, name='create'),
    path('collaboration/<int:pk>/', views.project_detail_view, name='detail'),
    path('collaboration/manage/<int:pk>/', views.manage_team_view, name='manage'),

    # Pair Programming & System Design Whiteboard Lounge
    path('lounge/', views.lounge_hub_view, name='lounge_hub'),
    path('lounge/create/', views.create_lounge_room_view, name='create_room'),
    path('lounge/join/', views.join_lounge_room_view, name='join_room'),
    path('lounge/room/<str:room_code>/', views.pair_room_view, name='pair_room'),
    path('lounge/room/<str:room_code>/sync/', views.room_sync_api, name='room_sync'),
    path('lounge/room/<str:room_code>/run/', views.run_room_code_api, name='run_room_code'),
]
