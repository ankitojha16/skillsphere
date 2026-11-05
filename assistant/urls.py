from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('', views.assistant_view, name='index'),
    path('c/<int:conversation_id>/', views.assistant_view, name='chat_detail'),
    path('new/', views.new_conversation_view, name='new_chat'),
    path('delete/<int:conversation_id>/', views.delete_conversation_view, name='delete_chat'),
    path('clear-all/', views.clear_all_conversations_view, name='clear_all'),
]
