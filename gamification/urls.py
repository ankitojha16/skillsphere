from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('', views.achievements_view, name='achievements'),
]
