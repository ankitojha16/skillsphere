from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('', views.achievements_view, name='achievements'),
    path('leagues/', views.leagues_view, name='leagues'),
    path('duels/start/', views.start_duel_api, name='start_duel'),
    path('duels/submit/', views.submit_duel_api, name='submit_duel'),
    path('badge/<str:username>/', views.public_user_badge_svg, name='user_badge'),

    # Real-Time 1v1 Code Arena
    path('arena/', views.code_arena_hub_view, name='arena_hub'),
    path('arena/start/', views.start_arena_match_api, name='arena_start'),
    path('arena/match/<int:match_id>/', views.code_arena_match_view, name='arena_match'),
    path('arena/match/<int:match_id>/progress/', views.arena_match_progress_api, name='arena_progress'),
    path('arena/match/<int:match_id>/submit/', views.submit_arena_match_api, name='arena_submit'),
]

