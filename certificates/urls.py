from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('certificates/', views.certificate_center_view, name='center'),
    path('certificates/<int:pk>/pdf/', views.download_certificate_pdf_view, name='download_pdf'),
    path('verify/<str:certificate_id>/', views.verify_certificate_view, name='verify'),
]
