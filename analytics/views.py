import base64
import json
import logging
from datetime import timedelta
from PIL import Image

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.contrib.auth.models import User

from .models import ProductEvent, BetaFeedback
from accounts.models import StudentProfile
from courses.models import Course, Enrollment, CourseCompletion
from learning.models import LessonProgress, Lesson
from certificates.models import Certificate
from assessments.models import SkillAssessment, AssessmentAttempt, CodingChallenge

logger = logging.getLogger(__name__)

MAX_FEEDBACK_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
Image.MAX_IMAGE_PIXELS = 10_000_000        # 10 Million pixels decomp defense
ALLOWED_FEEDBACK_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP', 'GIF'}


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def submit_feedback_api(request):
    """
    Submits user feedback or bug reports with:
    - Category & Rating
    - Written feedback
    - Contextual page URL
    - Secure screenshot upload validation (format, dimensions, max 5MB)
    - Rate-limiting (5 per hour per user/IP)
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    # Rate Limiting: 5 submissions per hour
    ip = _get_client_ip(request)
    user_key = f"user_{request.user.id}" if request.user.is_authenticated else f"ip_{ip}"
    cache_key = f"beta_feedback_rate_{user_key}"
    submission_count = cache.get(cache_key, 0)

    if submission_count >= 5:
        return JsonResponse({
            'success': False,
            'error': 'Rate limit reached. You can submit up to 5 feedback reports per hour.'
        }, status=429)

    # Extract fields from POST (multipart or json)
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'success': False, 'error': 'Invalid JSON body'}, status=400)
        category = data.get('category', 'feedback')
        rating = data.get('rating')
        description = data.get('description', '').strip()
        page_url = data.get('page_url', '')
        screenshot_file = None
    else:
        category = request.POST.get('category', 'feedback')
        rating = request.POST.get('rating')
        description = request.POST.get('description', '').strip()
        page_url = request.POST.get('page_url', '')
        screenshot_file = request.FILES.get('screenshot')

    if not description:
        return JsonResponse({'success': False, 'error': 'Description is required'}, status=400)

    # Validate rating
    parsed_rating = None
    if rating:
        try:
            r_val = int(rating)
            if 1 <= r_val <= 5:
                parsed_rating = r_val
        except (ValueError, TypeError):
            pass

    # Validate category
    valid_categories = dict(BetaFeedback.CATEGORY_CHOICES).keys()
    if category not in valid_categories:
        category = 'feedback'

    # Secure Image Validation
    screenshot_data_uri = ''
    if screenshot_file:
        if screenshot_file.size > MAX_FEEDBACK_IMAGE_SIZE:
            return JsonResponse({
                'success': False,
                'error': 'Screenshot exceeds the 5 MB maximum file size limit.'
            }, status=400)
        try:
            img = Image.open(screenshot_file)
            img.verify()
            if img.format not in ALLOWED_FEEDBACK_IMAGE_FORMATS:
                return JsonResponse({
                    'success': False,
                    'error': f'Unsupported image format: {img.format}. Allowed: JPEG, PNG, WEBP, GIF.'
                }, status=400)
            
            # Reset seek position for base64 encoding
            screenshot_file.seek(0)
            file_bytes = screenshot_file.read()
            mime_type = f"image/{img.format.lower()}"
            screenshot_data_uri = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode('utf-8')}"
            screenshot_file.seek(0)
        except Exception as e:
            logger.warning(f"Screenshot validation failed: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Uploaded file is not a valid or safe image.'
            }, status=400)

    # Create BetaFeedback record
    feedback = BetaFeedback.objects.create(
        user=request.user if request.user.is_authenticated else None,
        category=category,
        rating=parsed_rating,
        description=description,
        page_url=page_url[:500],
        screenshot=screenshot_file,
        screenshot_data_uri=screenshot_data_uri,
        status='new'
    )

    # Increment rate limiter (1 hour TTL)
    cache.set(cache_key, submission_count + 1, timeout=3600)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your feedback has been sent directly to the engineering team.',
            'feedback_id': feedback.id
        })
    else:
        messages.success(request, 'Thank you! Your feedback has been sent directly to the engineering team.')
        return redirect(page_url if page_url.startswith('/') else 'dashboard:index')


def feedback_page_view(request):
    """
    Standalone Feedback & Bug Report page.
    """
    return render(request, 'analytics/feedback_page.html', {
        'page_url': request.GET.get('page_url', request.META.get('HTTP_REFERER', '/dashboard/')),
        'category_choices': BetaFeedback.CATEGORY_CHOICES,
    })


@staff_member_required(login_url='accounts:login')
def admin_beta_dashboard_view(request):
    """
    Restricted Admin Beta Operations & Product Telemetry Dashboard.
    Provides verified metrics:
    - Daily & Weekly Active Users (real event & login queries)
    - Registration & Onboarding conversion
    - Course enrollment & lesson completion funnel
    - Live Feedback triage inbox
    Zero fabricated numbers.
    """
    now = timezone.now()
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)

    # Real User Metrics
    total_users = User.objects.count()
    new_users_7d = User.objects.filter(date_joined__gte=cutoff_7d).count()
    new_users_30d = User.objects.filter(date_joined__gte=cutoff_30d).count()

    # Active Users (DAU, WAU, MAU) based on logins or product events
    dau_users = set(User.objects.filter(last_login__gte=cutoff_24h).values_list('id', flat=True))
    dau_events = set(ProductEvent.objects.filter(timestamp__gte=cutoff_24h, user__isnull=False).values_list('user_id', flat=True))
    dau_count = len(dau_users | dau_events)

    wau_users = set(User.objects.filter(last_login__gte=cutoff_7d).values_list('id', flat=True))
    wau_events = set(ProductEvent.objects.filter(timestamp__gte=cutoff_7d, user__isnull=False).values_list('user_id', flat=True))
    wau_count = len(wau_users | wau_events)

    mau_users = set(User.objects.filter(last_login__gte=cutoff_30d).values_list('id', flat=True))
    mau_events = set(ProductEvent.objects.filter(timestamp__gte=cutoff_30d, user__isnull=False).values_list('user_id', flat=True))
    mau_count = len(mau_users | mau_events)

    # Onboarding Metrics
    onboarding_completed_count = StudentProfile.objects.filter(onboarding_completed=True).count()
    onboarding_rate = int(round((onboarding_completed_count / total_users) * 100)) if total_users > 0 else 0

    # Course & Learning Metrics
    total_enrollments = Enrollment.objects.count()
    total_lessons_completed = LessonProgress.objects.filter(is_completed=True).count()
    total_course_completions = CourseCompletion.objects.filter(is_completed=True).count()
    total_certificates = Certificate.objects.count()
    total_assessments_taken = AssessmentAttempt.objects.count()

    # Event Funnel Counts
    funnel = {
        'registrations': total_users,
        'onboarding': onboarding_completed_count,
        'enrolled': Enrollment.objects.values('user_id').distinct().count(),
        'first_lesson': ProductEvent.objects.filter(event_type='first_lesson_started').values('user_id').distinct().count(),
        'course_completed': CourseCompletion.objects.filter(is_completed=True).values('user_id').distinct().count(),
        'certificates': Certificate.objects.values('user_id').distinct().count(),
    }

    # Feedback triage counts
    feedbacks_qs = BetaFeedback.objects.select_related('user').order_by('-created_at')
    total_feedback = feedbacks_qs.count()
    unresolved_bugs = feedbacks_qs.filter(category='bug').exclude(status='resolved').count()
    new_feedbacks = feedbacks_qs.filter(status='new').count()
    avg_rating = feedbacks_qs.filter(rating__isnull=False).aggregate(avg=Avg('rating'))['avg']
    avg_rating_display = round(avg_rating, 1) if avg_rating else 'N/A'

    # Filter feedback list
    status_filter = request.GET.get('status', 'all')
    if status_filter in ['new', 'reviewing', 'resolved']:
        display_feedbacks = feedbacks_qs.filter(status=status_filter)[:30]
    else:
        display_feedbacks = feedbacks_qs[:30]

    # Recent Telemetry Log
    recent_events = ProductEvent.objects.select_related('user').order_by('-timestamp')[:25]

    return render(request, 'analytics/beta_dashboard.html', {
        'total_users': total_users,
        'new_users_7d': new_users_7d,
        'new_users_30d': new_users_30d,
        'dau_count': dau_count,
        'wau_count': wau_count,
        'mau_count': mau_count,
        'onboarding_completed_count': onboarding_completed_count,
        'onboarding_rate': onboarding_rate,
        'total_enrollments': total_enrollments,
        'total_lessons_completed': total_lessons_completed,
        'total_course_completions': total_course_completions,
        'total_certificates': total_certificates,
        'total_assessments_taken': total_assessments_taken,
        'funnel': funnel,
        'total_feedback': total_feedback,
        'unresolved_bugs': unresolved_bugs,
        'new_feedbacks': new_feedbacks,
        'avg_rating_display': avg_rating_display,
        'feedbacks': display_feedbacks,
        'status_filter': status_filter,
        'recent_events': recent_events,
    })


@staff_member_required(login_url='accounts:login')
def update_feedback_status_api(request, feedback_id):
    """
    Staff-only endpoint to triage feedback: update status and admin internal notes.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    feedback = get_object_or_404(BetaFeedback, id=feedback_id)
    new_status = request.POST.get('status')
    admin_notes = request.POST.get('admin_notes')

    if new_status in ['new', 'reviewing', 'resolved']:
        feedback.status = new_status
    if admin_notes is not None:
        feedback.admin_notes = admin_notes.strip()

    feedback.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'feedback_id': feedback.id,
            'status': feedback.status,
            'admin_notes': feedback.admin_notes
        })

    messages.success(request, f"Feedback #{feedback.id} updated.")
    return redirect('analytics:admin_beta_dashboard')
