import base64
import csv
import json
import logging
from datetime import timedelta
from PIL import Image

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponse
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

    # Extract structured beta survey questions if provided
    if request.content_type == 'application/json':
        easy = data.get('easy', '').strip()
        confusing = data.get('confusing', '').strip()
        most_useful = data.get('most_useful', '').strip()
        missing_expected = data.get('missing_expected', '').strip()
        improvements = data.get('improvements', '').strip()
    else:
        easy = request.POST.get('easy', '').strip()
        confusing = request.POST.get('confusing', '').strip()
        most_useful = request.POST.get('most_useful', '').strip()
        missing_expected = request.POST.get('missing_expected', '').strip()
        improvements = request.POST.get('improvements', '').strip()

    if easy or confusing or most_useful or missing_expected or improvements:
        parts = []
        if easy:
            parts.append(f"**What was easy:** {easy}")
        if confusing:
            parts.append(f"**What was confusing:** {confusing}")
        if most_useful:
            parts.append(f"**Most useful feature:** {most_useful}")
        if missing_expected:
            parts.append(f"**Expected but could not find:** {missing_expected}")
        if improvements:
            parts.append(f"**What should be improved:** {improvements}")
        if description:
            parts.append(f"**Additional notes:** {description}")
        description = "\n\n".join(parts)

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

    # Event Funnel Counts (Cohort 1 Milestones)
    first_lesson_count = ProductEvent.objects.filter(event_type__in=['first_lesson_started', 'lesson_completed']).values('user_id').distinct().count()
    returning_student_count = ProductEvent.objects.filter(event_type='returning_login').values('user_id').distinct().count()
    projects_created_count = ProductEvent.objects.filter(event_type='first_project_created').values('user_id').distinct().count()
    resumes_generated_count = ProductEvent.objects.filter(event_type='resume_generated').values('user_id').distinct().count()
    opportunities_saved_count = ProductEvent.objects.filter(event_type__in=['opportunity_saved', 'opportunity_applied']).values('user_id').distinct().count()
    errors_count = ProductEvent.objects.filter(event_type__icontains='error').count()

    funnel = {
        'registrations': total_users,
        'onboarding': onboarding_completed_count,
        'enrolled': Enrollment.objects.values('user_id').distinct().count(),
        'first_lesson': first_lesson_count,
        'returning_student': returning_student_count,
        'projects_created': projects_created_count,
        'resumes_generated': resumes_generated_count,
        'opportunities_saved': opportunities_saved_count,
        'errors_encountered': errors_count,
        'course_completed': CourseCompletion.objects.filter(is_completed=True).values('user_id').distinct().count(),
        'certificates': Certificate.objects.values('user_id').distinct().count(),
    }

    # Beta Invitations Management (Cohort 1)
    from .models import BetaInvitation
    invitations_qs = BetaInvitation.objects.select_related('invited_by', 'registered_user').order_by('-created_at')
    total_invitations = invitations_qs.count()
    pending_invitations = invitations_qs.filter(status='pending').count()
    accepted_invitations = invitations_qs.filter(status='accepted').count()
    invitations_list = invitations_qs[:20]

    # Active Students (Privacy-Shielded: Zero exposure of private notes, calendars, or resumes)
    active_user_ids = list(dau_users | dau_events | wau_users | wau_events)
    if not active_user_ids:
        active_user_ids = list(User.objects.order_by('-last_login', '-date_joined').values_list('id', flat=True)[:15])

    active_students = []
    for u in User.objects.filter(id__in=active_user_ids[:20]).select_related('profile'):
        courses_count = Enrollment.objects.filter(user=u).count()
        lessons_done = LessonProgress.objects.filter(user=u, is_completed=True).count()
        prof = getattr(u, 'profile', None)
        active_students.append({
            'id': u.id,
            'masked_name': (prof.full_name[:2] + '*** ' + prof.full_name.split()[-1][:1] + '***') if prof and prof.full_name else (u.username[:3] + '***'),
            'role': getattr(prof, 'role', 'student'),
            'education_level': getattr(prof, 'get_education_level_display', lambda: 'Undergraduate')() if prof else 'Undergraduate',
            'onboarding_completed': getattr(prof, 'onboarding_completed', False) if prof else False,
            'courses_enrolled': courses_count,
            'lessons_completed': lessons_done,
            'last_active': u.last_login or u.date_joined,
        })

    # Feedback triage & categorization breakdown
    feedbacks_qs = BetaFeedback.objects.select_related('user').order_by('-created_at')
    total_feedback = feedbacks_qs.count()
    unresolved_bugs = feedbacks_qs.filter(category='bug').exclude(status='resolved').count()
    new_feedbacks = feedbacks_qs.filter(status='new').count()
    avg_rating = feedbacks_qs.filter(rating__isnull=False).aggregate(avg=Avg('rating'))['avg']
    avg_rating_display = round(avg_rating, 1) if avg_rating else 'N/A'

    category_counts = {
        'bug': feedbacks_qs.filter(category='bug').count(),
        'usability': feedbacks_qs.filter(category='usability').count(),
        'missing_feature': feedbacks_qs.filter(category='missing_feature').count(),
        'content': feedbacks_qs.filter(category='content').count(),
        'feature': feedbacks_qs.filter(category='feature').count(),
        'feedback': feedbacks_qs.filter(category='feedback').count(),
    }

    # Open Bugs (prioritized by critical & high)
    open_bugs = feedbacks_qs.filter(category='bug').exclude(status='resolved').order_by('-priority', '-created_at')[:10]

    # Filter feedback list
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')

    filtered_feedbacks = feedbacks_qs
    if status_filter in ['new', 'reviewing', 'resolved']:
        filtered_feedbacks = filtered_feedbacks.filter(status=status_filter)
    if category_filter in dict(BetaFeedback.CATEGORY_CHOICES).keys():
        filtered_feedbacks = filtered_feedbacks.filter(category=category_filter)

    display_feedbacks = filtered_feedbacks[:30]

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
        'total_invitations': total_invitations,
        'pending_invitations': pending_invitations,
        'accepted_invitations': accepted_invitations,
        'invitations_list': invitations_list,
        'active_students': active_students,
        'total_feedback': total_feedback,
        'unresolved_bugs': unresolved_bugs,
        'new_feedbacks': new_feedbacks,
        'avg_rating_display': avg_rating_display,
        'category_counts': category_counts,
        'open_bugs': open_bugs,
        'feedbacks': display_feedbacks,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'category_choices': BetaFeedback.CATEGORY_CHOICES,
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


@staff_member_required(login_url='accounts:login')
def export_beta_feedback_csv(request):
    """
    Export all beta feedback submissions as a structured CSV for triage and weekly reporting.
    Staff-only.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    timestamp_str = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="skillsphere_beta_feedback_{timestamp_str}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID',
        'Category',
        'Priority',
        'Status',
        'Rating',
        'Page URL',
        'Reporter',
        'Description',
        'Admin Notes',
        'Created At'
    ])

    feedback_qs = BetaFeedback.objects.select_related('user').order_by('-created_at')
    for fb in feedback_qs:
        reporter = fb.user.username if fb.user else 'Anonymous'
        writer.writerow([
            fb.id,
            fb.get_category_display() if hasattr(fb, 'get_category_display') else fb.category,
            fb.get_priority_display() if hasattr(fb, 'get_priority_display') else fb.priority,
            fb.status,
            fb.rating if fb.rating is not None else '',
            fb.page_url or '',
            reporter,
            fb.description.replace('\r\n', '\n') if fb.description else '',
            fb.admin_notes.replace('\r\n', '\n') if fb.admin_notes else '',
            fb.created_at.strftime('%Y-%m-%d %H:%M:%S') if fb.created_at else ''
        ])

    return response

