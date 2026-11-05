from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.utils import timezone

from .models import Certificate
from courses.models import Course, Enrollment
from learning.models import LessonProgress
from notifications.models import Notification
from services.pdf_service import PDFService

@login_required
def certificate_center_view(request):
    certificates = Certificate.objects.filter(user=request.user)

    # Check for eligible courses completed without a certificate yet
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    eligible_courses = []

    for enr in enrollments:
        course = enr.course
        total_lessons = course.lessons.count()
        if total_lessons > 0:
            completed_lessons = LessonProgress.objects.filter(
                user=request.user,
                lesson__course=course,
                is_completed=True
            ).count()

            if completed_lessons >= total_lessons:
                # Check if already issued
                already_issued = Certificate.objects.filter(user=request.user, course=course).exists()
                if not already_issued:
                    eligible_courses.append(course)

    if request.method == 'POST' and 'claim_course_id' in request.POST:
        course_id = request.POST.get('claim_course_id')
        course_to_claim = get_object_or_404(Course, id=course_id)

        # Re-verify completion
        total = course_to_claim.lessons.count()
        done = LessonProgress.objects.filter(user=request.user, lesson__course=course_to_claim, is_completed=True).count()
        if done >= total and total > 0:
            cert = Certificate.objects.create(
                user=request.user,
                course=course_to_claim,
                title=f"Course Completion: {course_to_claim.title}",
                criteria_met=f"Successfully completed all {total} lessons and practical coding exercises in {course_to_claim.title}."
            )
            # Send notification
            Notification.objects.create(
                user=request.user,
                title="Certificate Issued! 🎓",
                message=f"Congratulations! Your official SkillSphere certificate for '{course_to_claim.title}' has been issued.",
                notification_type='certificate_issued',
                link="/certificates/"
            )
            messages.success(request, f"Official certificate for '{course_to_claim.title}' generated successfully!")
            return redirect('certificates:center')
        else:
            messages.error(request, "Course requirements not yet 100% completed.")

    context = {
        'certificates': certificates,
        'eligible_courses': eligible_courses,
    }
    return render(request, 'certificates/center.html', context)


@login_required
def download_certificate_pdf_view(request, pk):
    cert = get_object_or_404(Certificate, pk=pk, user=request.user)
    pdf_bytes = PDFService.generate_certificate_pdf(cert)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"SkillSphere_Certificate_{cert.certificate_id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def verify_certificate_view(request, certificate_id):
    """
    Public verification endpoint for recruiters and academic reviewers.
    Zero private PII exposed.
    """
    cert = Certificate.objects.filter(certificate_id__iexact=certificate_id).first()
    if not cert:
        return render(request, 'certificates/verify_not_found.html', {'certificate_id': certificate_id}, status=404)

    context = {
        'cert': cert,
        'is_valid': cert.verification_status,
        'verify_id': cert.certificate_id,
        'issued_date': cert.issued_at,
        'title': cert.title,
        'recipient_display_name': cert.recipient_name or cert.user.username,
        'criteria': cert.criteria_met,
    }
    return render(request, 'certificates/verify.html', context)
