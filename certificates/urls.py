from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('certificates/', views.certificate_center_view, name='center'),
    path('certificates/<int:pk>/pdf/', views.download_certificate_pdf_view, name='download_pdf'),
    path('certificates/<int:pk>/preview/', views.preview_certificate_pdf_view, name='preview_pdf'),
    path('certificates/verify/<str:certificate_id>/', views.verify_certificate_view, name='verify_full'),
    path('verify/<str:certificate_id>/', views.verify_certificate_view, name='verify'),
]
