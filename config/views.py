import os
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

def pwa_manifest_view(request):
    """
    Serves the Progressive Web App manifest.json with official MIME type.
    """
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/manifest+json')
    except Exception as e:
        return JsonResponse({
            'name': 'SkillSphere',
            'short_name': 'SkillSphere',
            'start_url': '/dashboard/',
            'display': 'standalone',
            'background_color': '#0b0f19',
            'theme_color': '#0b0f19'
        })


def service_worker_view(request):
    """
    Serves the PWA Service Worker with root scope permissions (Service-Worker-Allowed: /).
    """
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        content = "// Fallback Service Worker\nself.addEventListener('fetch', () => {});"

    response = HttpResponse(content, content_type='application/javascript')
    # Required for the service worker to control all routes from root /
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


def offline_view(request):
    """
    Renders the offline fallback screen when network connectivity is lost.
    """
    return render(request, 'offline.html')
