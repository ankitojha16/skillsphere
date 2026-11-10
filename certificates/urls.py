from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('certificates/', views.certificate_center_view, name='center'),
    path('certificates/course/<int:course_id>/claim/', views.claim_certificate_view, name='claim_by_course'),
    path('certificates/course/<int:course_id>/claim-cert/', views.claim_certificate_view, name='claim_course_certificate'),
    path('certificates/<int:pk>/download/', views.download_certificate_pdf_view, name='download'),
    path('certificates/<int:pk>/download-pdf/', views.download_certificate_pdf_view, name='download_certificate_pdf'),
    path('certificates/course/<int:course_id>/download/', views.download_course_certificate_view, name='download_by_course'),
    path('certificates/course/<int:course_id>/download-cert/', views.download_course_certificate_view, name='download_course_certificate'),
    path('certificates/<int:pk>/pdf/', views.download_certificate_pdf_view, name='download_pdf'),
    path('certificates/<int:pk>/preview/', views.preview_certificate_pdf_view, name='preview_pdf'),
    path('certificates/verify/<str:certificate_id>/', views.verify_certificate_view, name='verify_full'),
    path('certificates/verify/<str:certificate_id>/pdf/', views.public_verify_pdf_view, name='verify_pdf'),
    path('verify/<str:certificate_id>/', views.verify_certificate_view, name='verify'),
    path('verify/<str:certificate_id>/pdf/', views.public_verify_pdf_view, name='verify_pdf_short'),
]

