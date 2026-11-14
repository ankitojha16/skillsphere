from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render
from config.views import (
    pwa_manifest_view, service_worker_view, offline_view,
    health_check_view, liveness_probe_view, readiness_probe_view,
    metrics_view, robots_txt_view, sitemap_xml_view,
    privacy_policy_view, terms_of_service_view
)
from analytics.views import feedback_page_view

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('courses:list')

urlpatterns = [
    # Infrastructure, Health & Telemetry Routes
    path('health/live/', liveness_probe_view, name='liveness_probe'),
    path('health/ready/', readiness_probe_view, name='readiness_probe'),
    path('health/startup/', health_check_view, name='startup_probe'),
    path('healthz', health_check_view, name='healthz'),
    path('api/health/', health_check_view, name='api_health'),
    path('api/metrics/', metrics_view, name='api_metrics'),
    path('robots.txt', robots_txt_view, name='robots_txt'),
    path('sitemap.xml', sitemap_xml_view, name='sitemap_xml'),

    # Progressive Web App (PWA) Core Routes
    path('manifest.json', pwa_manifest_view, name='pwa_manifest'),
    path('sw.js', service_worker_view, name='service_worker'),
    path('offline/', offline_view, name='offline'),

    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('courses/', include('courses.urls', namespace='courses')),
    path('learn/', include('learning.urls', namespace='learning')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('goals/', include('goals.urls', namespace='goals')),

    # Phase 2 AI & Career Features
    path('ai-assistant/', include('assistant.urls', namespace='assistant')),
    path('learning-roadmap/', include('roadmaps.urls', namespace='roadmaps')),
    path('skill-assessment/', include('assessments.urls', namespace='assessments')),
    path('mock-interview/', include('interviews.urls', namespace='interviews')),
    path('project-generator/', include('projects.urls', namespace='projects')),
    path('achievements/', include('gamification.urls', namespace='gamification')),

    # Phase 3 Career, Portfolio, Community & Opportunities Features
    path('', include('careers.urls', namespace='careers')),
    path('', include('portfolios.urls', namespace='portfolios')),
    path('', include('resumes.urls', namespace='resumes')),
    path('', include('opportunities.urls', namespace='opportunities')),
    path('', include('community.urls', namespace='community')),
    path('', include('collaboration.urls', namespace='collaboration')),
    path('', include('events.urls', namespace='events')),
    path('', include('certificates.urls', namespace='certificates')),
    path('', include('notifications.urls', namespace='notifications')),

    # Phase 15 Legal, Privacy & Analytics Routes
    path('privacy/', privacy_policy_view, name='privacy_policy'),
    path('terms/', terms_of_service_view, name='terms_of_service'),
    path('feedback/', feedback_page_view, name='feedback_direct'),
    path('analytics/', include('analytics.urls', namespace='analytics')),
]

def custom_bad_request_view(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def custom_permission_denied_view(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def custom_page_not_found_view(request, exception=None):
    return render(request, 'errors/404.html', status=404)

import sys
import traceback
import logging

logger = logging.getLogger('skillsphere.errors')

def custom_server_error_view(request):
    exc_type, exc_value, exc_tb = sys.exc_info()
    if exc_value:
        logger.error(
            f"Unhandled 500 Server Error at {getattr(request, 'path', 'Unknown')}: {exc_type.__name__ if exc_type else 'Unknown'}: {exc_value}\n"
            f"{''.join(traceback.format_exception(exc_type, exc_value, exc_tb))}"
        )
    error_details = None
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and (user.is_staff or getattr(user, 'username', '') == 'ankit.ojha1666'):
        if exc_value:
            error_details = {
                'type': exc_type.__name__ if exc_type else 'ServerError',
                'message': str(exc_value),
                'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_tb)),
                'path': getattr(request, 'path', 'Unknown'),
            }
    return render(request, 'errors/500.html', {'error_details': error_details}, status=500)

handler400 = 'config.urls.custom_bad_request_view'
handler403 = 'config.urls.custom_permission_denied_view'
handler404 = 'config.urls.custom_page_not_found_view'
handler500 = 'config.urls.custom_server_error_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
