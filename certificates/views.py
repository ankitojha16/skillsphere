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

        # Check for existing certificate
        if Certificate.objects.filter(user=request.user, course=course_to_claim).exists():
            messages.info(request, f"You already hold a SkillSphere Course Completion Certificate for '{course_to_claim.title}'.")
            return redirect('certificates:center')

        prog = course_to_claim.get_user_progress(request.user)
        if not prog.get('is_certificate_eligible', False):
            messages.error(request, f"Cannot claim certificate: {'; '.join(prog.get('missing_requirements', ['Requirements not met.']))}")
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
            criteria_met=f"Completed 100% of curriculum, Final Course Quiz, and Final Mock Examination for {course_to_claim.title}."
        )

        Notification.objects.create(
            user=request.user,
            title="Certificate Issued! 🎓",
            message=f"Congratulations, {custom_name}! Your SkillSphere Course Completion Certificate for '{course_to_claim.title}' has been generated.",
            notification_type='certificate_issued',
            link="/certificates/"
        )
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
def download_certificate_pdf_view(request, pk):
    cert = get_object_or_404(Certificate, pk=pk, user=request.user)
    if not cert.verification_status:
        raise Http404("Certificate has been revoked or is invalid.")
    pdf_bytes = PDFService.generate_certificate_pdf(cert)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"SkillSphere_Certificate_{cert.certificate_id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def preview_certificate_pdf_view(request, pk):
    """Inline browser preview of the certificate."""
    cert = get_object_or_404(Certificate, pk=pk, user=request.user)
    if not cert.verification_status:
        raise Http404("Certificate has been revoked or is invalid.")
    pdf_bytes = PDFService.generate_certificate_pdf(cert)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"SkillSphere_Certificate_{cert.certificate_id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
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
