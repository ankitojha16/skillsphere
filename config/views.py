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


import time
from django.db import connection
from django.core.cache import cache
from django.utils import timezone

def health_check_view(request):
    """
    Production Health Check & Telemetry endpoint for cloud load balancers,
    Kubernetes probes, and uptime monitors.
    Returns 200 OK with system metrics or 503 if critical dependencies are down.
    """
    start_time = time.time()
    checks = {}
    is_healthy = True

    # 1. Database Check
    try:
        db_start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_latency_ms = round((time.time() - db_start) * 1000, 2)
        checks['database'] = {
            'status': 'ok',
            'latency_ms': db_latency_ms
        }
    except Exception as e:
        is_healthy = False
        checks['database'] = {
            'status': 'error',
            'message': str(e)
        }

    # 2. Cache Check
    try:
        cache_start = time.time()
        cache.set('_health_ping', 'ok', 10)
        cached_val = cache.get('_health_ping')
        cache_latency_ms = round((time.time() - cache_start) * 1000, 2)
        checks['cache'] = {
            'status': 'ok' if cached_val == 'ok' else 'degraded',
            'latency_ms': cache_latency_ms
        }
    except Exception as e:
        checks['cache'] = {
            'status': 'degraded',
            'message': str(e)
        }

    total_latency_ms = round((time.time() - start_time) * 1000, 2)
    payload = {
        'status': 'healthy' if is_healthy else 'unhealthy',
        'timestamp': timezone.now().isoformat(),
        'platform': 'SkillSphere Autonomous Education & Career Platform',
        'version': '2.5.0',
        'environment': 'production' if not settings.DEBUG else 'development',
        'latency_ms': total_latency_ms,
        'checks': checks
    }
    status_code = 200 if is_healthy else 503
    response = JsonResponse(payload, status=status_code)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


def robots_txt_view(request):
    """
    Serves robots.txt with search indexing guidelines and sitemap declaration.
    """
    base_url = request.build_absolute_uri('/').rstrip('/')
    lines = [
        "User-agent: *",
        "Allow: /",
        "Allow: /courses/",
        "Allow: /careers/",
        "Allow: /opportunities/",
        "Allow: /u/",
        "Allow: /certificates/verify/",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /api/",
        "Disallow: /dashboard/",
        "Disallow: /goals/",
        "Disallow: /mock-interview/session/",
        "",
        f"Sitemap: {base_url}/sitemap.xml"
    ]
    response = HttpResponse("\n".join(lines), content_type="text/plain")
    response['Cache-Control'] = 'public, max-age=86400'
    return response


def sitemap_xml_view(request):
    """
    Dynamically generates sitemap.xml indexing public courses, career paths, and features.
    """
    base_url = request.build_absolute_uri('/').rstrip('/')
    now_str = timezone.now().strftime('%Y-%m-%d')

    urls = [
        {'loc': f"{base_url}/", 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': f"{base_url}/courses/", 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': f"{base_url}/careers/", 'priority': '0.8', 'changefreq': 'weekly'},
        {'loc': f"{base_url}/opportunities/", 'priority': '0.8', 'changefreq': 'daily'},
        {'loc': f"{base_url}/achievements/", 'priority': '0.7', 'changefreq': 'weekly'},
    ]

    try:
        from courses.models import Course
        for course in Course.objects.only('slug', 'updated_at')[:50]:
            lastmod = course.updated_at.strftime('%Y-%m-%d') if hasattr(course, 'updated_at') and course.updated_at else now_str
            urls.append({
                'loc': f"{base_url}/courses/{course.slug}/",
                'lastmod': lastmod,
                'priority': '0.8',
                'changefreq': 'weekly'
            })
    except Exception:
        pass

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for u in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f"    <loc>{u['loc']}</loc>")
        if 'lastmod' in u:
            xml_lines.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{u['priority']}</priority>")
        xml_lines.append('  </url>')
    xml_lines.append('</urlset>')

    response = HttpResponse("\n".join(xml_lines), content_type="application/xml")
    response['Cache-Control'] = 'public, max-age=43200'
    return response

