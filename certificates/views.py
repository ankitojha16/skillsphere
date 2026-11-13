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
    certificates = list(Certificate.objects.filter(user=request.user).select_related('course', 'course__category'))
    issued_course_ids = set(c.course_id for c in certificates)

    enrollments = list(Enrollment.objects.filter(user=request.user).select_related('course', 'course__category'))
    eligible_courses = []
    locked_courses = []

    unissued_enrollments = [enr for enr in enrollments if enr.course_id not in issued_course_ids]
    if unissued_enrollments:
        course_ids = [enr.course_id for enr in unissued_enrollments]
        completions = {
            c.course_id: c
            for c in CourseCompletion.objects.filter(user=request.user, course_id__in=course_ids)
        }
        from django.db.models import Count
        from learning.models import Lesson
        completed_counts = dict(
            LessonProgress.objects.filter(
                user=request.user,
                is_completed=True,
                lesson__course_id__in=course_ids
            ).values('lesson__course_id').annotate(cnt=Count('id')).values_list('lesson__course_id', 'cnt')
        )
        lessons_counts = dict(
            Lesson.objects.filter(course_id__in=course_ids)
            .values('course_id').annotate(cnt=Count('id')).values_list('course_id', 'cnt')
        )

        for enr in unissued_enrollments:
            course = enr.course
            comp = completions.get(course.id)
            comp_cnt = completed_counts.get(course.id, 0)
            tot_cnt = lessons_counts.get(course.id, 0)

            # If student has completed all lessons, fetch full progress for optional assessment bonuses
            if comp_cnt >= tot_cnt and tot_cnt > 0:
                prog = course.get_user_progress(request.user)
            else:
                video_ratio = (comp_cnt / tot_cnt) if tot_cnt > 0 else 0.0
                video_pct = int(round(video_ratio * 100))
                is_eligible = (comp and comp.is_completed)
                base_weighted = int(round(video_ratio * 80.0))
                weighted = max(base_weighted, comp.learning_progress) if comp else base_weighted
                missing = [f"Complete all mandatory video lessons ({comp_cnt}/{tot_cnt} completed)."] if not is_eligible else []
                prog = {
                    'percentage': weighted,
                    'weighted_course_progress': weighted,
                    'video_completion_percentage': video_pct,
                    'assessment_bonus_percentage': max(0, weighted - base_weighted),
                    'completed': comp_cnt,
                    'total': tot_cnt,
                    'is_completed': is_eligible,
                    'is_certificate_eligible': is_eligible,
                    'missing_requirements': missing,
                }

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

    # Handle claim request or name update with custom chosen recipient name
    if request.method == 'POST' and 'claim_course_id' in request.POST:
        course_id = request.POST.get('claim_course_id')
        course_to_claim = get_object_or_404(Course, id=course_id)
        custom_name = request.POST.get('recipient_name', '').strip()
        custom_name = re.sub(r'[\r\n\t]', ' ', custom_name)[:100] if custom_name else ""

        # Check for existing certificate (idempotent, allows updating recipient name)
        existing_cert = Certificate.objects.filter(user=request.user, course=course_to_claim).first()
        if existing_cert:
            if custom_name and existing_cert.recipient_name != custom_name:
                existing_cert.recipient_name = custom_name
                existing_cert.save(update_fields=['recipient_name'])
                Course.invalidate_user_progress_cache(request.user.id, course_to_claim.id)
                msg = f"Certificate recipient name successfully updated to '{custom_name}'."
            else:
                msg = f"SkillSphere Course Completion Certificate already issued and ready for '{course_to_claim.title}'."

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'already_issued': True,
                    'certificate_id': existing_cert.certificate_id,
                    'download_url': f"/certificates/{existing_cert.id}/download/",
                    'message': msg
                })
            messages.success(request, msg)
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
            criteria_met=f"Successfully completed all mandatory video lessons and curriculum for {course_to_claim.title}."
        )
        Course.invalidate_user_progress_cache(request.user.id, course_to_claim.id)

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
    Enforces authentication, CSRF, and mandatory video curriculum completion checks.
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

    custom_name = request.POST.get('recipient_name', '').strip()
    custom_name = re.sub(r'[\r\n\t]', ' ', custom_name)[:100] if custom_name else ""

    # Check for existing certificate (idempotent, allow name update)
    existing_cert = Certificate.objects.filter(user=request.user, course=course).first()
    if existing_cert:
        download_url = f"/certificates/{existing_cert.id}/download/"
        if custom_name and existing_cert.recipient_name != custom_name:
            existing_cert.recipient_name = custom_name
            existing_cert.save(update_fields=['recipient_name'])
            Course.invalidate_user_progress_cache(request.user.id, course.id)
            msg = f"SkillSphere Course Completion Certificate updated for {custom_name}!"
        else:
            msg = f"SkillSphere Course Completion Certificate ready for '{course.title}'."

        if is_json:
            return JsonResponse({
                'success': True,
                'already_issued': True,
                'certificate_id': existing_cert.certificate_id,
                'download_url': download_url,
                'message': msg
            })
        messages.success(request, msg)
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
        criteria_met=f"Successfully completed all mandatory video lessons and curriculum for {course.title}."
    )
    Course.invalidate_user_progress_cache(request.user.id, course.id)

    # Telemetry: Certificate earned
    from analytics.services import track_event
    track_event(
        user=request.user,
        event_type='certificate_earned',
        metadata={'course_id': course.id, 'certificate_id': cert.certificate_id, 'course_title': course.title},
        event_key=f"cert_{request.user.id}_{course.id}"
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
            messages.error(request, f"Certificate in progress: {missing_text}")
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


def public_verify_pdf_view(request, certificate_id):
    """
    Public download endpoint for a verified certificate PDF.
    Enforces that certificate is valid and not revoked.
    """
    cert = Certificate.objects.filter(certificate_id__iexact=certificate_id, verification_status=True).select_related('course').first()
    if not cert:
        raise Http404("Certificate not found or revoked.")
    pdf_bytes = PDFService.generate_certificate_pdf(cert)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"SkillSphere_Certificate_{cert.certificate_id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
    response['Content-Length'] = str(len(pdf_bytes))
    return response


def verify_portal_view(request):
    """
    Public Certificate Verification Portal.
    Allows recruiters, employers, and students to:
    1. Search certificates by Certificate ID.
    2. Scan physical or screen QR codes using device camera or file upload.
    """
    cert_id = request.GET.get('id', '').strip()
    if cert_id:
        return redirect('certificates:verify', certificate_id=cert_id)
    return render(request, 'certificates/verify_portal.html')


def certificate_social_card_view(request, certificate_id):
    """
    Generates a high-resolution 1200x630 OpenGraph / Twitter Card social preview image
    for the verified certificate, rendered dynamically with PIL.
    """
    cert = Certificate.objects.filter(certificate_id__iexact=certificate_id).select_related('course').first()
    if not cert:
        raise Http404("Certificate not found.")

    from PIL import Image, ImageDraw
    import io

    img = Image.new("RGBA", (1200, 630), color=(11, 17, 32, 255))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(630):
        ratio = y / 630.0
        r = int(11 * (1 - ratio) + 20 * ratio)
        g = int(17 * (1 - ratio) + 30 * ratio)
        b = int(32 * (1 - ratio) + 55 * ratio)
        draw.line([(0, y), (1200, y)], fill=(r, g, b, 255))

    # Gold and navy borders
    draw.rounded_rectangle([(30, 30), (1170, 600)], radius=20, outline=(199, 164, 90, 255), width=3)
    draw.rounded_rectangle([(38, 38), (1162, 592)], radius=16, outline=(36, 87, 167, 180), width=1)

    # Header badge
    draw.rounded_rectangle([(80, 70), (460, 116)], radius=23, fill=(36, 87, 167, 70), outline=(109, 159, 232, 200))
    draw.text((105, 83), "★ SKILLSPHERE VERIFIED CREDENTIAL ★", fill=(219, 234, 254, 255))

    # Certificate details
    recipient = cert.recipient_name or cert.user.username
    course_name = cert.course.title if cert.course else cert.title
    issue_date = cert.issued_at.strftime('%B %d, %Y')

    draw.text((80, 150), "CERTIFICATE OF PROFICIENCY & MASTERY", fill=(199, 164, 90, 255))
    draw.text((80, 195), "Proudly Presented To:", fill=(148, 163, 184, 255))
    draw.text((80, 235), f"{recipient}", fill=(255, 255, 255, 255))

    draw.text((80, 310), "For successfully demonstrating technical mastery in:", fill=(148, 163, 184, 255))
    draw.text((80, 345), f"{course_name[:65]}", fill=(165, 243, 252, 255))

    # Details Box
    draw.rounded_rectangle([(80, 430), (1120, 515)], radius=12, fill=(30, 41, 59, 180), outline=(71, 85, 105, 120))
    draw.text((105, 450), f"Certificate ID: {cert.certificate_id}", fill=(255, 255, 255, 255))
    draw.text((105, 480), f"Issued Date: {issue_date}   |   Status: Verified & Tamper-Proof", fill=(148, 163, 184, 255))
    draw.text((820, 465), "✔ Verified by SkillSphere", fill=(34, 197, 94, 255))

    # Footer
    draw.text((80, 545), f"Verify online: {request.scheme}://{request.get_host()}/verify/{cert.certificate_id}/", fill=(100, 116, 139, 255))

    buf = io.BytesIO()
    img.save(buf, "PNG")
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Cache-Control'] = 'public, max-age=86400'
    return response


