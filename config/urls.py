from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('courses:list')

urlpatterns = [
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
