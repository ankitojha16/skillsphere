from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('<slug:course_slug>/<int:lesson_id>/', views.lesson_view, name='lesson_detail'),
    path('<slug:course_slug>/<int:lesson_id>/toggle/', views.complete_lesson_toggle, name='complete_toggle'),
]
