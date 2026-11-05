from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    path('resume-builder/', views.resume_builder_view, name='builder'),
    path('resume-builder/<int:pk>/', views.resume_builder_view, name='builder_edit'),
    path('resume-builder/my-resumes/', views.resume_list_view, name='list'),
    path('resume-builder/<int:pk>/pdf/', views.export_resume_pdf_view, name='export_pdf'),
    path('resume-builder/ai/improve/', views.ai_improve_view, name='ai_improve'),
]
