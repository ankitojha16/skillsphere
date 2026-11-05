from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('community/', views.community_feed_view, name='feed'),
    path('community/new/', views.create_post_view, name='create_post'),
    path('community/post/<int:pk>/', views.post_detail_view, name='post_detail'),
    path('community/post/<int:pk>/like/', views.toggle_like_view, name='toggle_like'),
    path('community/report/', views.report_content_view, name='report'),
]
