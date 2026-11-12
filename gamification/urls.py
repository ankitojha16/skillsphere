from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('', views.achievements_view, name='achievements'),
    path('leagues/', views.leagues_view, name='leagues'),
    path('duels/start/', views.start_duel_api, name='start_duel'),
    path('duels/submit/', views.submit_duel_api, name='submit_duel'),
    path('badge/<str:username>/', views.public_user_badge_svg, name='user_badge'),
]

