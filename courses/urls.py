from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list_view, name='list'),
    path('my-learning/', views.my_learning_view, name='my_learning'),
    path('<slug:slug>/', views.course_detail_view, name='detail'),
    path('<slug:slug>/enroll/', views.enroll_course_view, name='enroll'),
    path('<slug:slug>/unenroll/', views.unenroll_course_view, name='unenroll'),
]
