from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.utils import timezone
import re

from .models import Certificate
from courses.models import Course, Enrollment, CourseAssessmentAttempt, CourseCompletion
from learning.models import LessonProgress
from notifications.models import Notification
from services.pdf_service import PDFService

@login_required
def certificate_center_view(request):
    certificates = Certificate.objects.filter(user=request.user).select_related('course')
    issued_course_ids = set(certificates.values_list('course_id', flat=True))

    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    eligible_courses = []
    locked_courses = []

    for enr in enrollments:
        course = enr.course
        if course.id in issued_course_ids:
            continue

        prog = course.get_user_progress(request.user)

        # Check authoritative eligibility from course.get_user_progress (85% + mandatory assessments)
        if prog.get('is_certificate_eligible', False):
            eligible_courses.append({
                'course': course,
                'progress': prog,
            })
        else:
            locked_courses.append({
                'course': course,
                'progress': prog,
                'remaining_reasons': prog.get('missing_requirements', []),
            })

    # Handle claim request with custom chosen recipient name
    if request.method == 'POST' and 'claim_course_id' in request.POST:
        course_id = request.POST.get('claim_course_id')
        course_to_claim = get_object_or_404(Course, id=course_id)

        # Check for existing certificate (idempotent, return existing certificate)
        existing_cert = Certificate.objects.filter(user=request.user, course=course_to_claim).first()
        if existing_cert:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'already_issued': True,
                    'certificate_id': existing_cert.certificate_id,
                    'download_url': f"/certificates/{existing_cert.id}/download/",
                    'message': f"You already hold a certificate for '{course_to_claim.title}'."
                })
            messages.info(request, f"You already hold a SkillSphere Course Completion Certificate for '{course_to_claim.title}'.")
            return redirect('certificates:center')

        prog = course_to_claim.get_user_progress(request.user)
        if not prog.get('is_certificate_eligible', False):
            missing_text = '; '.join(prog.get('missing_requirements', ['Course requirements not met.']))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f"Cannot claim certificate: {missing_text}",
                    'missing_requirements': prog.get('missing_requirements', [])
                }, status=400)
            messages.error(request, f"Cannot claim certificate: {missing_text}")
            return redirect('certificates:center')

        # Recipient Name validation
        custom_name = request.POST.get('recipient_name', '').strip()
        if not custom_name:
            profile = getattr(request.user, 'profile', None)
            custom_name = profile.full_name if (profile and profile.full_name) else (request.user.get_full_name() or request.user.username)

        # Disallow malicious / symbol-only injection
        custom_name = re.sub(r'[\r\n\t]', ' ', custom_name)[:100]

        cert = Certificate.objects.create(
            user=request.user,
            course=course_to_claim,
            title=f"Course Completion: {course_to_claim.title}",
            recipient_name=custom_name,
            criteria_met=f"Completed ≥85% of curriculum, Final Course Quiz, and Final Mock Examination for {course_to_claim.title}."
        )

        Notification.objects.create(
            user=request.user,
            title="Certificate Issued! 🎓",
            message=f"Congratulations, {custom_name}! Your SkillSphere Course Completion Certificate for '{course_to_claim.title}' has been generated.",
            notification_type='certificate_issued',
            link="/certificates/"
        )
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'certificate_id': cert.certificate_id,
                'download_url': f"/certificates/{cert.id}/download/",
                'message': f"SkillSphere Course Completion Certificate issued to {custom_name}!"
            })
        messages.success(request, f"SkillSphere Course Completion Certificate for '{course_to_claim.title}' issued to {custom_name}!")
        return redirect('certificates:center')

    # Default name suggestion from student profile
    default_name = ""
    profile = getattr(request.user, 'profile', None)
    if profile and profile.full_name:
        default_name = profile.full_name
    elif request.user.get_full_name():
        default_name = request.user.get_full_name()
    else:
        default_name = request.user.username

    context = {
        'certificates': certificates,
        'eligible_courses': eligible_courses,
        'locked_courses': locked_courses,
        'default_name': default_name,
    }
    return render(request, 'certificates/center.html', context)


@login_required
def claim_certificate_view(request, course_id):
    """
    Dedicated POST endpoint for claiming course completion certificates.
    Enforces authentication, CSRF, curriculum progress (>= 85%), and assessment checks.
    Idempotent: returns existing certificate if already issued.
    """
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])

    course = get_object_or_404(Course, id=course_id)

    is_json = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('accept', '') or
        request.content_type == 'application/json'
    )

    # Check for existing certificate (idempotent, return existing certificate)
    existing_cert = Certificate.objects.filter(user=request.user, course=course).first()
    if existing_cert:
        download_url = f"/certificates/{existing_cert.id}/download/"
        if is_json:
            return JsonResponse({
                'success': True,
                'already_issued': True,
                'certificate_id': existing_cert.certificate_id,
                'download_url': download_url,
                'message': f"You already hold a certificate for '{course.title}'."
            })
        messages.info(request, f"You already hold a SkillSphere Course Completion Certificate for '{course.title}'.")
        return redirect(download_url)

    prog = course.get_user_progress(request.user)
    if not prog.get('is_certificate_eligible', False):
        missing_text = '; '.join(prog.get('missing_requirements', ['Course requirements not met.']))
        if is_json:
            return JsonResponse({
                'success': False,
                'error': f"Cannot claim certificate: {missing_text}",
                'missing_requirements': prog.get('missing_requirements', [])
            }, status=400)
        messages.error(request, f"Cannot claim certificate: {missing_text}")
        return redirect('certificates:center')

    # Recipient Name validation
    custom_name = request.POST.get('recipient_name', '').strip()
    if not custom_name:
        profile = getattr(request.user, 'profile', None)
        custom_name = profile.full_name if (profile and profile.full_name) else (request.user.get_full_name() or request.user.username)

    custom_name = re.sub(r'[\r\n\t]', ' ', custom_name)[:100]

    cert = Certificate.objects.create(
        user=request.user,
        course=course,
        title=f"Course Completion: {course.title}",
        recipient_name=custom_name,
        criteria_met=f"Completed ≥85% of curriculum, Final Course Quiz, and Final Mock Examination for {course.title}."
    )

    Notification.objects.create(
        user=request.user,
        title="Certificate Issued! 🎓",
        message=f"Congratulations, {custom_name}! Your SkillSphere Course Completion Certificate for '{course.title}' has been generated.",
        notification_type='certificate_issued',
        link="/certificates/"
    )
    download_url = f"/certificates/{cert.id}/download/"
    if is_json:
        return JsonResponse({
            'success': True,
            'certificate_id': cert.certificate_id,
            'download_url': download_url,
            'message': f"SkillSphere Course Completion Certificate issued to {custom_name}!"
        })
    messages.success(request, f"SkillSphere Course Completion Certificate for '{course.title}' issued to {custom_name}!")
    return redirect(download_url)


@login_required
def download_course_certificate_view(request, course_id):
    """
    Direct course-level certificate download pathway (GET).
    Strictly read-only: retrieves an existing issued certificate.
    GET requests NEVER create database records.
    If eligible but unclaimed, redirects to the claim flow with an explicit message.
    """
    course = get_object_or_404(Course, id=course_id)
    cert = Certificate.objects.filter(user=request.user, course=course).first()
    if not cert:
        prog = course.get_user_progress(request.user)
        if prog.get('is_certificate_eligible', False):
            messages.info(
                request,
                f"You are eligible for the '{course.title}' Certificate! Please claim your certificate to generate your official credential."
            )
            return redirect('certificates:center')
        else:
            missing_text = '; '.join(prog.get('missing_requirements', ['Course requirements not met.']))
            messages.error(request, f"Certificate locked: {missing_text}")
            return redirect('courses:detail', slug=course.slug)

    if not cert.verification_status:
        raise Http404("Certificate has been revoked or is invalid.")

    pdf_bytes = PDFService.generate_certificate_pdf(cert)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"SkillSphere_Certificate_{cert.certificate_id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
    response['Content-Length'] = str(len(pdf_bytes))
    response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def download_certificate_pdf_view(request, pk):
    """
    Protected download endpoint by certificate ID.
    Enforces user ownership (404 on mismatch to prevent enumeration) and validity.
    """
    cert = Certificate.objects.filter(pk=pk).first()
    if not cert:
        raise Http404("Certificate not found.")
    if cert.user != request.user:
        raise Http404("Certificate not found.")
    if not cert.verification_status:
        raise Http404("Certificate has been revoked or is invalid.")

    pdf_bytes = PDFService.generate_certificate_pdf(cert)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"SkillSphere_Certificate_{cert.certificate_id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
    response['Content-Length'] = str(len(pdf_bytes))
    response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def preview_certificate_pdf_view(request, pk):
    """Inline browser preview of the certificate."""
    cert = Certificate.objects.filter(pk=pk).first()
    if not cert:
        raise Http404("Certificate not found.")
    if cert.user != request.user:
        raise Http404("Certificate not found.")
    if not cert.verification_status:
        raise Http404("Certificate has been revoked or is invalid.")

    pdf_bytes = PDFService.generate_certificate_pdf(cert)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"SkillSphere_Certificate_{cert.certificate_id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"; filename*=UTF-8\'\'{filename}'
    response['Content-Length'] = str(len(pdf_bytes))
    return response


def verify_certificate_view(request, certificate_id):
    """
    Public verification endpoint for recruiters, universities, and students.
    Zero private PII exposed.
    """
    cert = Certificate.objects.filter(certificate_id__iexact=certificate_id).select_related('course').first()
    if not cert:
        return render(request, 'certificates/verify_not_found.html', {'certificate_id': certificate_id}, status=404)

    context = {
        'cert': cert,
        'is_valid': cert.verification_status,
        'verify_id': cert.certificate_id,
        'issued_date': cert.issued_at,
        'title': cert.title,
        'course_name': cert.course.title if cert.course else cert.title,
        'recipient_display_name': cert.recipient_name or cert.user.username,
        'criteria': cert.criteria_met,
    }
    return render(request, 'certificates/verify.html', context)
