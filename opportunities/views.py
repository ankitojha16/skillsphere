import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.core.cache import cache

from .models import (
    Opportunity,
    SavedOpportunity,
    CandidateShortlist,
    InterviewInvitation,
    OpportunityOrganization,
    OpportunitySkill,
    ApplicationStatusHistory,
    OpportunityReport,
)
from notifications.models import Notification
from accounts.models import StudentProfile
from accounts.decorators import recruiter_required
from resumes.models import Resume, ResumeVersion
from assessments.models import ChallengeSubmission
from gamification.models import UserArenaRating
from certificates.models import Certificate
from services.opportunity_matcher import OpportunityMatcher
from services.interview_prep_service import InterviewPrepService


# =============================================================================
# 1. OPPORTUNITY DISCOVERY & DETAIL
# =============================================================================

@login_required
def opportunity_list_view(request):
    """
    Unified Opportunity Hub discovery portal.
    Supports filtering by type (internship, job, scholarship, hackathon, etc.),
    domain/category, work mode, eligibility, and search.
    Provides transparent match scores and filters out adult-only listings for minors.
    """
    query = request.GET.get('q', '').strip()
    opp_type = request.GET.get('type', '').strip()
    category = request.GET.get('category', '').strip()
    work_mode = request.GET.get('work_mode', '').strip()
    sort_by = request.GET.get('sort', 'deadline')
    show_expired = request.GET.get('show_expired') == 'true'

    today = timezone.now().date()

    opportunities = Opportunity.objects.filter(is_active=True, is_archived=False)

    # Minor student safety filter: high school students cannot view adult-only roles
    profile = getattr(request.user, 'profile', None)
    is_minor = False
    if profile and getattr(profile, 'education_level', '') == 'high_school':
        is_minor = True
        opportunities = opportunities.filter(is_minor_safe=True, min_age__lte=17)

    # Search query
    if query:
        opportunities = opportunities.filter(
            Q(title__icontains=query) |
            Q(organization__icontains=query) |
            Q(required_skills__icontains=query) |
            Q(description__icontains=query) |
            Q(eligibility__icontains=query)
        )

    # Opportunity Type Filter (Internship, Job, Scholarship, Hackathon, etc.)
    if opp_type and opp_type != 'all':
        opportunities = opportunities.filter(opportunity_type=opp_type)

    # Category / Domain
    if category and category != 'all':
        opportunities = opportunities.filter(category=category)

    # Work Mode
    if work_mode and work_mode != 'all':
        opportunities = opportunities.filter(work_mode=work_mode)

    # Expiry Filter
    if not show_expired:
        opportunities = opportunities.filter(Q(deadline__isnull=True) | Q(deadline__gte=today))

    # Sorting
    if sort_by == 'newest':
        opportunities = opportunities.order_by('-created_at')
    elif sort_by == 'award':
        opportunities = opportunities.order_by('-funding_amount', 'deadline')
    else:  # default 'deadline'
        opportunities = opportunities.order_by('deadline', '-created_at')

    # Pagination: 12 opportunities per page
    paginator = Paginator(opportunities, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Track saved/applied opportunities for this student
    saved_records = SavedOpportunity.objects.filter(user=request.user)
    saved_map = {s.opportunity_id: s for s in saved_records}

    # Evaluate intelligent match scores for displayed items
    evaluated_opportunities = []
    for opp in page_obj:
        eval_data = OpportunityMatcher.evaluate_opportunity_for_student(request.user, opp)
        evaluated_opportunities.append({
            'opp': opp,
            'match': eval_data,
            'saved_entry': saved_map.get(opp.id),
        })

    # Summary counts for quick filters
    base_qs = Opportunity.objects.filter(is_active=True, is_archived=False)
    if is_minor:
        base_qs = base_qs.filter(is_minor_safe=True, min_age__lte=17)

    type_counts = {
        'all': base_qs.count(),
        'internship': base_qs.filter(opportunity_type='internship').count(),
        'job': base_qs.filter(opportunity_type='job').count(),
        'scholarship': base_qs.filter(opportunity_type='scholarship').count(),
        'hackathon': base_qs.filter(opportunity_type='hackathon').count(),
        'competition': base_qs.filter(opportunity_type='competition').count(),
        'challenge': base_qs.filter(opportunity_type='challenge').count(),
        'mentorship': base_qs.filter(opportunity_type='mentorship').count(),
    }

    context = {
        'page_obj': page_obj,
        'evaluated_opportunities': evaluated_opportunities,
        'query': query,
        'selected_type': opp_type or 'all',
        'selected_category': category,
        'selected_work_mode': work_mode,
        'selected_sort': sort_by,
        'show_expired': show_expired,
        'type_counts': type_counts,
        'opportunity_types': Opportunity.OPPORTUNITY_TYPE_CHOICES,
        'categories': Opportunity.CATEGORY_CHOICES,
        'work_modes': Opportunity.WORK_MODE_CHOICES,
        'is_minor': is_minor,
        'today': today,
    }
    return render(request, 'opportunities/list.html', context)


@login_required
def opportunity_detail_view(request, pk):
    """
    Detailed opportunity profile with transparent match breakdown,
    candidate application form, interview preparation trigger, and reporting.
    """
    opportunity = get_object_or_404(Opportunity, pk=pk)

    # Minor safety check
    profile = getattr(request.user, 'profile', None)
    is_minor = profile and getattr(profile, 'education_level', '') == 'high_school'
    if is_minor and (not opportunity.is_minor_safe or opportunity.min_age > 17):
        messages.warning(request, "This opportunity is age-restricted (18+) and not open to minor students.")
        return redirect('opportunities:list')

    # Match evaluation
    match_eval = OpportunityMatcher.evaluate_opportunity_for_student(request.user, opportunity)

    # Student's tracking state
    saved_entry = SavedOpportunity.objects.filter(user=request.user, opportunity=opportunity).first()

    # Student's available resume versions for application submission
    user_resumes = Resume.objects.filter(user=request.user).prefetch_related('versions')
    resume_versions = ResumeVersion.objects.filter(resume__user=request.user).order_by('-created_at')

    # Application status history if already tracked
    history = []
    if saved_entry:
        history = saved_entry.status_history.all()[:10]

    context = {
        'opportunity': opportunity,
        'match': match_eval,
        'saved_entry': saved_entry,
        'user_resumes': user_resumes,
        'resume_versions': resume_versions,
        'history': history,
        'today': timezone.now().date(),
        'is_minor': is_minor,
    }
    return render(request, 'opportunities/detail.html', context)


# =============================================================================
# 2. STUDENT APPLICATION TRACKER & PIPELINE
# =============================================================================

@login_required
def toggle_save_opportunity_view(request, pk):
    """
    One-click bookmark / save toggle.
    """
    opportunity = get_object_or_404(Opportunity, pk=pk)
    saved = SavedOpportunity.objects.filter(user=request.user, opportunity=opportunity).first()

    if saved:
        saved.delete()
        messages.info(request, f"Removed '{opportunity.title}' from your saved opportunities.")
    else:
        SavedOpportunity.objects.create(
            user=request.user,
            opportunity=opportunity,
            application_status='interested'
        )
        messages.success(request, f"Saved '{opportunity.title}' to your application tracker!")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'opportunities:list'
    return redirect(next_url)


@login_required
def record_application_view(request, pk):
    """
    Records or updates a formal application to an opportunity.
    Allows linking a specific ResumeVersion, notes, follow-up date, and external ref.
    """
    opportunity = get_object_or_404(Opportunity, pk=pk)

    if request.method != 'POST':
        return redirect('opportunities:detail', pk=pk)

    new_status = request.POST.get('status', 'applied').strip()
    notes = request.POST.get('notes', '').strip()
    version_id = request.POST.get('resume_version_id')
    follow_up_str = request.POST.get('follow_up_date')
    ext_ref = request.POST.get('external_reference', '').strip()

    resume_version = None
    if version_id:
        resume_version = ResumeVersion.objects.filter(id=version_id, resume__user=request.user).first()

    follow_up_date = None
    if follow_up_str:
        try:
            follow_up_date = timezone.datetime.strptime(follow_up_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    saved, created = SavedOpportunity.objects.get_or_create(
        user=request.user,
        opportunity=opportunity,
        defaults={
            'application_status': new_status,
            'application_notes': notes,
            'resume_version': resume_version,
            'follow_up_date': follow_up_date,
            'external_reference': ext_ref,
            'applied_at': timezone.now() if new_status == 'applied' else None,
        }
    )

    if not created:
        old_status = saved.application_status
        saved.application_status = new_status
        if notes:
            saved.application_notes = notes
        if resume_version:
            saved.resume_version = resume_version
        if follow_up_date:
            saved.follow_up_date = follow_up_date
        if ext_ref:
            saved.external_reference = ext_ref
        if new_status == 'applied' and not saved.applied_at:
            saved.applied_at = timezone.now()
        saved.save()

        # Record stage history
        if old_status != new_status:
            ApplicationStatusHistory.objects.create(
                application=saved,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user,
                notes=f"Updated by student via application portal"
            )

    messages.success(request, f"Application for '{opportunity.title}' updated to '{new_status.title()}'!")
    return redirect('opportunities:tracker')


@login_required
def application_tracker_view(request):
    """
    Personal student application tracker dashboard (/opportunities/my-applications/).
    Provides 8-stage pipeline visualization, follow-up reminders, notes,
    and stage history.
    """
    saved_records = (
        SavedOpportunity.objects.filter(user=request.user)
        .select_related('opportunity', 'resume_version', 'resume_version__resume')
        .prefetch_related('status_history')
    )

    if request.method == 'POST':
        saved_id = request.POST.get('saved_id')
        action = request.POST.get('action', 'update_status')
        entry = get_object_or_404(SavedOpportunity, id=saved_id, user=request.user)

        if action == 'delete':
            entry.delete()
            messages.info(request, f"Removed '{entry.opportunity.title}' from tracker.")
            return redirect('opportunities:tracker')

        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '').strip()
        follow_up_str = request.POST.get('follow_up_date')
        ext_ref = request.POST.get('external_reference', '').strip()

        old_status = entry.application_status
        if new_status and new_status in dict(SavedOpportunity.STATUS_CHOICES):
            entry.application_status = new_status
            if new_status == 'applied' and not entry.applied_at:
                entry.applied_at = timezone.now()

        if notes:
            entry.application_notes = notes
        if ext_ref:
            entry.external_reference = ext_ref

        if follow_up_str:
            try:
                entry.follow_up_date = timezone.datetime.strptime(follow_up_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        entry.save()

        if old_status != entry.application_status:
            ApplicationStatusHistory.objects.create(
                application=entry,
                from_status=old_status,
                to_status=entry.application_status,
                changed_by=request.user,
                notes=notes or "Status updated in tracker"
            )

        messages.success(request, f"Updated application status for {entry.opportunity.title}!")
        return redirect('opportunities:tracker')

    # Group into 8 pipeline stages
    pipeline = {
        'saved': [],
        'preparing': [],
        'applied': [],
        'assessment': [],
        'interview': [],
        'selected': [],
        'rejected': [],
        'withdrawn': [],
    }

    for item in saved_records:
        st = item.normalized_status
        if st in pipeline:
            pipeline[st].append(item)
        else:
            pipeline['saved'].append(item)

    # Upcoming follow-ups (next 7 days)
    today = timezone.now().date()
    upcoming_followups = [
        item for item in saved_records
        if item.follow_up_date and today <= item.follow_up_date <= (today + timezone.timedelta(days=7))
    ]

    context = {
        'pipeline': pipeline,
        'total_tracked': saved_records.count(),
        'statuses': SavedOpportunity.STATUS_CHOICES,
        'upcoming_followups': upcoming_followups,
        'today': today,
    }
    return render(request, 'opportunities/tracker.html', context)


# =============================================================================
# 3. AI INTERVIEW PREPARATION
# =============================================================================

@login_required
def interview_prep_view(request, pk):
    """
    Generates role-specific technical and behavioral interview preparation
    for an opportunity, grounded in student projects and listing requirements.
    """
    opportunity = get_object_or_404(Opportunity, pk=pk)

    # Handle practice response evaluation via AJAX/POST
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = {}
        question = body.get('question', '').strip()
        answer = body.get('answer', '').strip()
        evaluation = InterviewPrepService.evaluate_practice_answer(question, answer, opportunity)
        return JsonResponse({'status': 'success', 'evaluation': evaluation})

    prep_deck = InterviewPrepService.generate_prep_deck(request.user, opportunity)

    context = {
        'opportunity': opportunity,
        'prep_deck': prep_deck,
    }
    return render(request, 'opportunities/interview_prep.html', context)


# =============================================================================
# 4. REPORTING & MODERATION
# =============================================================================

@login_required
def report_opportunity_view(request, pk):
    """
    Submits a moderation report for suspicious, inaccurate, or expired listings.
    """
    opportunity = get_object_or_404(Opportunity, pk=pk)

    if request.method != 'POST':
        return redirect('opportunities:detail', pk=pk)

    reason = request.POST.get('reason', 'other')
    details = request.POST.get('details', '').strip()

    if not details:
        messages.error(request, "Please provide brief details explaining why you are reporting this listing.")
        return redirect('opportunities:detail', pk=pk)

    OpportunityReport.objects.create(
        opportunity=opportunity,
        reported_by=request.user,
        reason=reason,
        details=details
    )

    messages.success(
        request,
        "Thank you. Your report has been submitted to the moderation team for review."
    )
    return redirect('opportunities:detail', pk=pk)


# =============================================================================
# 5. RECRUITER OPPORTUNITY MANAGEMENT
# =============================================================================

@recruiter_required
def recruiter_post_opportunity_view(request):
    """
    Allows authorized recruiters to create new opportunity listings
    for their organization with required skills and eligibility criteria.
    """
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        organization = request.POST.get('organization', '').strip()
        opp_type = request.POST.get('opportunity_type', 'internship')
        category = request.POST.get('category', 'software-development')
        description = request.POST.get('description', '').strip()
        required_skills = request.POST.get('required_skills', '').strip()
        preferred_skills = request.POST.get('preferred_skills', '').strip()
        eligibility = request.POST.get('eligibility', '').strip()
        location = request.POST.get('location', 'Remote').strip()
        work_mode = request.POST.get('work_mode', 'remote')
        compensation = request.POST.get('compensation_details', '').strip()
        stipend_info = request.POST.get('stipend_information', '').strip()
        funding_str = request.POST.get('funding_amount', '').strip()
        app_url = request.POST.get('application_url', '').strip()
        deadline_str = request.POST.get('deadline', '').strip()
        min_age = int(request.POST.get('min_age', 18))
        is_minor_safe = request.POST.get('is_minor_safe') == 'true'

        if not title or not organization or not description or not required_skills or not app_url:
            messages.error(request, "Please fill in all mandatory listing fields.")
            return render(request, 'opportunities/recruiter_post.html', {
                'categories': Opportunity.CATEGORY_CHOICES,
                'opportunity_types': Opportunity.OPPORTUNITY_TYPE_CHOICES,
                'work_modes': Opportunity.WORK_MODE_CHOICES,
            })

        funding_amount = None
        if funding_str:
            try:
                funding_amount = float(funding_str)
            except ValueError:
                pass

        deadline = None
        if deadline_str:
            try:
                deadline = timezone.datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        opp = Opportunity.objects.create(
            title=title,
            organization=organization,
            posted_by=request.user,
            opportunity_type=opp_type,
            category=category,
            description=description,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            eligibility=eligibility,
            location=location,
            work_mode=work_mode,
            compensation_details=compensation,
            stipend_information=stipend_info or compensation,
            funding_amount=funding_amount,
            application_url=app_url,
            deadline=deadline,
            min_age=min_age,
            is_minor_safe=is_minor_safe,
            source_type='authorized_recruiter',
            source_name=f"Recruiter: {request.user.username}",
            verification_status=True,
            is_active=True,
        )

        messages.success(request, f"Opportunity '{opp.title}' published successfully!")
        return redirect('opportunities:recruiter_listings')

    context = {
        'opportunity': None,
        'categories': Opportunity.CATEGORY_CHOICES,
        'opportunity_types': Opportunity.OPPORTUNITY_TYPE_CHOICES,
        'work_modes': Opportunity.WORK_MODE_CHOICES,
    }
    return render(request, 'opportunities/recruiter_post.html', context)


@recruiter_required
def recruiter_my_listings_view(request):
    """
    Recruiter dashboard listing all opportunities published by the current recruiter
    or organization, with applicant counts and stage breakdowns.
    """
    listings = (
        Opportunity.objects.filter(posted_by=request.user)
        .annotate(applicant_count=Count('saves'))
        .order_by('-created_at')
    )

    context = {
        'listings': listings,
        'total_listings': listings.count(),
    }
    return render(request, 'opportunities/recruiter_listings.html', context)


@recruiter_required
def recruiter_edit_opportunity_view(request, pk):
    """
    Edit an existing opportunity with ownership validation.
    """
    opp = get_object_or_404(Opportunity, pk=pk)

    # Ownership check: recruiter can only edit their own listings unless superuser/staff
    if not (request.user.is_staff or request.user.is_superuser or opp.posted_by == request.user):
        return HttpResponseForbidden("You do not have permission to modify this opportunity.")

    if request.method == 'POST':
        opp.title = request.POST.get('title', opp.title).strip()
        opp.organization = request.POST.get('organization', opp.organization).strip()
        opp.opportunity_type = request.POST.get('opportunity_type', opp.opportunity_type)
        opp.category = request.POST.get('category', opp.category)
        opp.description = request.POST.get('description', opp.description).strip()
        opp.required_skills = request.POST.get('required_skills', opp.required_skills).strip()
        opp.preferred_skills = request.POST.get('preferred_skills', opp.preferred_skills).strip()
        opp.eligibility = request.POST.get('eligibility', opp.eligibility).strip()
        opp.location = request.POST.get('location', opp.location).strip()
        opp.work_mode = request.POST.get('work_mode', opp.work_mode)
        opp.compensation_details = request.POST.get('compensation_details', opp.compensation_details).strip()
        opp.application_url = request.POST.get('application_url', opp.application_url).strip()
        opp.is_minor_safe = request.POST.get('is_minor_safe') == 'true'

        deadline_str = request.POST.get('deadline', '').strip()
        if deadline_str:
            try:
                opp.deadline = timezone.datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        opp.save()
        messages.success(request, f"Listing '{opp.title}' updated successfully.")
        return redirect('opportunities:recruiter_listings')

    context = {
        'opportunity': opp,
        'categories': Opportunity.CATEGORY_CHOICES,
        'opportunity_types': Opportunity.OPPORTUNITY_TYPE_CHOICES,
        'work_modes': Opportunity.WORK_MODE_CHOICES,
    }
    return render(request, 'opportunities/recruiter_post.html', context)


@recruiter_required
def recruiter_toggle_archive_view(request, pk):
    """
    Toggles is_archived status for an opportunity listing.
    """
    opp = get_object_or_404(Opportunity, pk=pk)
    if not (request.user.is_staff or request.user.is_superuser or opp.posted_by == request.user):
        return HttpResponseForbidden("Permission denied.")

    opp.is_archived = not opp.is_archived
    opp.save(update_fields=['is_archived'])
    status_label = "archived" if opp.is_archived else "re-activated"
    messages.info(request, f"Opportunity '{opp.title}' has been {status_label}.")
    return redirect('opportunities:recruiter_listings')


@recruiter_required
def recruiter_applicants_view(request, pk):
    """
    Recruiter applicant review dashboard for a specific opportunity.
    Enforces student privacy: shields raw email and contact info by default.
    Minors cannot receive unmoderated recruiter contact.
    """
    opp = get_object_or_404(Opportunity, pk=pk)
    if not (request.user.is_staff or request.user.is_superuser or opp.posted_by == request.user):
        return HttpResponseForbidden("Permission denied to view applicants for this listing.")

    applications = (
        SavedOpportunity.objects.filter(opportunity=opp)
        .select_related('user', 'user__profile', 'resume_version', 'resume_version__resume')
        .order_by('-applied_at', '-created_at')
    )

    applicant_data = []
    for app in applications:
        u = app.user
        prof = getattr(u, 'profile', None)
        is_minor = prof and getattr(prof, 'education_level', '') == 'high_school'

        # Calculate student match score for recruiter insight
        eval_data = OpportunityMatcher.evaluate_opportunity_for_student(u, opp)

        applicant_data.append({
            'application': app,
            'user': u,
            'profile': prof,
            'is_minor': is_minor,
            'match_score': eval_data['match_percentage'],
            'match_level': eval_data['match_level'],
            'badge_color': eval_data['badge_color'],
            'resume_version': app.resume_version,
        })

    context = {
        'opportunity': opp,
        'applicant_data': applicant_data,
        'total_applicants': len(applicant_data),
        'statuses': SavedOpportunity.STATUS_CHOICES,
    }
    return render(request, 'opportunities/recruiter_applicants.html', context)


@recruiter_required
def recruiter_update_applicant_status_api(request, app_id):
    """
    Recruiter API to advance applicant stage (assessment, interview, selected, rejected).
    Sends an in-app notification to the student and records audit history.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)

    app = get_object_or_404(SavedOpportunity.objects.select_related('opportunity'), id=app_id)
    opp = app.opportunity

    if not (request.user.is_staff or request.user.is_superuser or opp.posted_by == request.user):
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = {}

    new_status = body.get('status')
    recruiter_notes = body.get('notes', '').strip()

    if new_status not in dict(SavedOpportunity.STATUS_CHOICES):
        return JsonResponse({'status': 'error', 'message': 'Invalid status choice.'}, status=400)

    old_status = app.application_status
    app.application_status = new_status
    app.save(update_fields=['application_status', 'updated_at'])

    ApplicationStatusHistory.objects.create(
        application=app,
        from_status=old_status,
        to_status=new_status,
        changed_by=request.user,
        notes=recruiter_notes or f"Updated by recruiter @{request.user.username}"
    )

    # Notify candidate of the stage change
    Notification.objects.create(
        user=app.user,
        title=f"Application Update: {opp.title}",
        message=f"{opp.organization} updated your application status to '{new_status.title()}'.",
        notification_type="system"
    )

    return JsonResponse({
        'status': 'success',
        'application_id': app.id,
        'new_status': new_status,
        'new_status_display': dict(SavedOpportunity.STATUS_CHOICES).get(new_status, new_status)
    })


# =============================================================================
# 6. TALENT PORTAL & CANDIDATE SEARCH (EXISTING PRESERVED)
# =============================================================================

@recruiter_required
def talent_portal_view(request):
    query = request.GET.get('q', '').strip()
    min_challenges = int(request.GET.get('min_challenges', 0))
    tier_filter = request.GET.get('tier', 'all')

    candidates_qs = (
        User.objects.filter(is_active=True)
        .exclude(id=request.user.id)
        .select_related('profile', 'arena_rating')
    )

    if query:
        candidates_qs = candidates_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(profile__career_goal__icontains=query) |
            Q(profile__learning_interests__icontains=query) |
            Q(profile__institution__icontains=query)
        ).distinct()

    candidates_list = list(candidates_qs[:40])
    user_ids = [u.id for u in candidates_list]

    shortlisted_ids = set(
        CandidateShortlist.objects.filter(recruiter=request.user, candidate_id__in=user_ids)
        .values_list('candidate_id', flat=True)
    )

    resumes_by_user = {}
    if user_ids:
        for r in Resume.objects.filter(user_id__in=user_ids).order_by('-is_primary', '-updated_at'):
            if r.user_id not in resumes_by_user:
                resumes_by_user[r.user_id] = r

    solved_counts = {}
    if user_ids:
        solved_counts = dict(
            ChallengeSubmission.objects.filter(user_id__in=user_ids, status='Accepted')
            .values('user_id')
            .annotate(cnt=Count('challenge_id', distinct=True))
            .values_list('user_id', 'cnt')
        )

    cert_counts = {}
    if user_ids:
        cert_counts = dict(
            Certificate.objects.filter(user_id__in=user_ids)
            .values('user_id')
            .annotate(cnt=Count('id'))
            .values_list('user_id', 'cnt')
        )

    candidate_cards = []
    for user in candidates_list:
        profile = getattr(user, 'profile', None)
        resume = resumes_by_user.get(user.id)
        arena_rating = getattr(user, 'arena_rating', None)
        challenges_solved = solved_counts.get(user.id, 0)
        certs_count = cert_counts.get(user.id, 0)

        tier_name = arena_rating.tier_name if arena_rating else 'Bronze'
        if tier_filter != 'all' and tier_name.lower() != tier_filter.lower():
            continue

        if challenges_solved < min_challenges:
            continue

        skills = []
        if profile and hasattr(profile, 'get_interests_list'):
            skills.extend(profile.get_interests_list())
        if resume and resume.skills:
            res_skills = resume.skills if isinstance(resume.skills, list) else []
            for s in res_skills[:4]:
                if s not in skills:
                    skills.append(s)

        candidate_cards.append({
            'user': user,
            'profile': profile,
            'resume': resume,
            'arena_rating': arena_rating,
            'headline': profile.career_goal if profile and profile.career_goal else (resume.title if resume and hasattr(resume, 'title') else 'Software Developer'),
            'institution': profile.institution if profile else '',
            'skills': skills[:6],
            'challenges_solved': challenges_solved,
            'elo': arena_rating.elo if arena_rating else 1200,
            'tier_name': tier_name,
            'certificates_count': certs_count,
            'ats_score': resume.ats_score if resume else 0,
            'is_shortlisted': user.id in shortlisted_ids,
        })

    return render(request, 'opportunities/talent_portal.html', {
        'candidate_cards': candidate_cards,
        'candidates': candidate_cards,
        'query': query,
        'min_challenges': min_challenges,
        'tier_filter': tier_filter,
        'total_candidates': len(candidate_cards),
        'shortlisted_count': len(shortlisted_ids),
    })


@recruiter_required
def candidate_dossier_view(request, username):
    candidate = get_object_or_404(User.objects.select_related('profile', 'arena_rating'), username=username)
    profile = getattr(candidate, 'profile', None)
    resume = Resume.objects.filter(user=candidate, is_primary=True).first() or Resume.objects.filter(user=candidate).first()
    arena_rating = getattr(candidate, 'arena_rating', None)

    solved_challenges = ChallengeSubmission.objects.filter(
        user=candidate, status='Accepted'
    ).select_related('challenge').order_by('-created_at')[:10]

    certificates = Certificate.objects.filter(user=candidate).order_by('-issued_at')
    is_shortlisted = CandidateShortlist.objects.filter(recruiter=request.user, candidate=candidate).exists()
    invitations = InterviewInvitation.objects.filter(recruiter=request.user, candidate=candidate)

    return render(request, 'opportunities/candidate_dossier.html', {
        'candidate': candidate,
        'profile': profile,
        'resume': resume,
        'arena_rating': arena_rating,
        'solved_challenges': solved_challenges,
        'certificates': certificates,
        'is_shortlisted': is_shortlisted,
        'invitations': invitations,
    })


@recruiter_required
def toggle_shortlist_candidate_api(request, username):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)

    candidate = get_object_or_404(User, username=username)
    existing = CandidateShortlist.objects.filter(recruiter=request.user, candidate=candidate).first()

    if existing:
        existing.delete()
        is_shortlisted = False
    else:
        CandidateShortlist.objects.create(recruiter=request.user, candidate=candidate, status='shortlisted')
        is_shortlisted = True

    return JsonResponse({
        'status': 'success',
        'is_shortlisted': is_shortlisted,
        'username': candidate.username
    })


@recruiter_required
def send_interview_invitation_api(request, username):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)

    # Minor safety check: recruiters cannot send direct unmoderated invitations to minors
    candidate = get_object_or_404(User, username=username)
    candidate_profile = getattr(candidate, 'profile', None)
    if candidate_profile and getattr(candidate_profile, 'education_level', '') == 'high_school':
        return JsonResponse({
            'status': 'error',
            'message': 'Direct recruiter invitations to minor students are prohibited by safety policy. Minors must apply through official verified opportunities.'
        }, status=403)

    # Rate limiting: max 15 invitations per hour per recruiter
    rate_limit_key = f"recruiter_invitations_{request.user.id}"
    current_count = cache.get(rate_limit_key, 0)
    if current_count >= 15:
        return JsonResponse({
            'status': 'error',
            'error': 'Hourly interview invitation limit reached (15/hr). Please try again later.',
            'message': 'Hourly interview invitation limit reached (15/hr). Please try again later.'
        }, status=429)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = {}

    role_title = body.get('role_title', 'Software Engineering Role').strip()
    company_name = body.get('company_name', 'Hiring Partner').strip()
    message = body.get('message', '').strip()
    meeting_link = body.get('meeting_link', '').strip()

    invitation = InterviewInvitation.objects.create(
        recruiter=request.user,
        candidate=candidate,
        role_title=role_title,
        company_name=company_name,
        message=message,
        meeting_link=meeting_link,
        status='pending'
    )

    Notification.objects.create(
        user=candidate,
        title="Direct Interview Invitation!",
        message=f"{request.user.username} ({company_name}) invited you to interview for {role_title}.",
        notification_type="system"
    )

    cache.set(rate_limit_key, current_count + 1, timeout=3600)

    return JsonResponse({
        'status': 'success',
        'invitation_id': invitation.id,
        'message': f"Invitation dispatched to @{candidate.username} successfully!"
    })


@recruiter_required
def recruiter_shortlist_view(request):
    shortlists = (
        CandidateShortlist.objects.filter(recruiter=request.user)
        .select_related('candidate', 'candidate__profile', 'candidate__arena_rating')
    )

    candidates_list = [item.candidate for item in shortlists]
    user_ids = [c.id for c in candidates_list]

    resumes_by_user = {}
    if user_ids:
        for r in Resume.objects.filter(user_id__in=user_ids).order_by('-is_primary', '-updated_at'):
            if r.user_id not in resumes_by_user:
                resumes_by_user[r.user_id] = r

    solved_counts = {}
    if user_ids:
        solved_counts = dict(
            ChallengeSubmission.objects.filter(user_id__in=user_ids, status='Accepted')
            .values('user_id')
            .annotate(cnt=Count('challenge_id', distinct=True))
            .values_list('user_id', 'cnt')
        )

    candidates_data = []
    for item in shortlists:
        c = item.candidate
        resume = resumes_by_user.get(c.id)
        rating = getattr(c, 'arena_rating', None)
        challenges_solved = solved_counts.get(c.id, 0)

        candidates_data.append({
            'shortlist_entry': item,
            'candidate': c,
            'headline': c.profile.career_goal if hasattr(c, 'profile') and c.profile and c.profile.career_goal else 'Developer',
            'elo': rating.elo if rating else 1200,
            'challenges_solved': challenges_solved,
            'ats_score': resume.ats_score if resume else 0,
        })

    return render(request, 'opportunities/recruiter_shortlist.html', {
        'candidates': candidates_data,
        'total_shortlisted': len(candidates_data),
    })


# =============================================================================
# 5. ADMINISTRATOR MODERATION & USER SUSPENSION
# =============================================================================

@login_required
def moderation_dashboard_view(request):
    """
    Administrator and staff moderation dashboard for managing reported listings,
    verifying partner opportunities, archiving stale items, and managing users.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Administrator access required.")

    pending_reports = OpportunityReport.objects.filter(status='pending').select_related('opportunity', 'reported_by')
    resolved_reports = OpportunityReport.objects.exclude(status='pending').select_related('opportunity', 'reported_by').order_by('-created_at')[:20]
    stale_opportunities = Opportunity.objects.filter(is_active=True).order_by('last_verified_at')[:20]

    return render(request, 'opportunities/moderation.html', {
        'pending_reports': pending_reports,
        'resolved_reports': resolved_reports,
        'stale_opportunities': stale_opportunities,
        'total_active': Opportunity.objects.filter(is_active=True).count(),
        'total_pending': pending_reports.count(),
    })


@login_required
def moderate_report_action_view(request, report_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Administrator access required.")

    report = get_object_or_404(OpportunityReport, id=report_id)
    action = request.POST.get('action')

    if action == 'deactivate':
        report.status = 'resolved'
        report.admin_notes = f"Deactivated listing by staff action {request.user.username}"
        report.save(update_fields=['status', 'admin_notes'])
        report.opportunity.is_active = False
        report.opportunity.save(update_fields=['is_active'])
        messages.success(request, f"Opportunity '{report.opportunity.title}' has been deactivated and report resolved.")
    elif action == 'verify':
        report.status = 'resolved'
        report.admin_notes = f"Verified listing authenticity by staff {request.user.username}"
        report.save(update_fields=['status', 'admin_notes'])
        report.opportunity.verification_status = True
        report.opportunity.last_verified_at = timezone.now()
        report.opportunity.save(update_fields=['verification_status', 'last_verified_at'])
        messages.success(request, f"Opportunity '{report.opportunity.title}' marked as verified active.")
    elif action == 'dismiss':
        report.status = 'dismissed'
        report.admin_notes = f"Dismissed as invalid by staff {request.user.username}"
        report.save(update_fields=['status', 'admin_notes'])
        messages.info(request, f"Report on '{report.opportunity.title}' dismissed.")

    return redirect('opportunities:moderation_dashboard')


@login_required
def toggle_user_suspension_view(request, user_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Administrator access required.")

    target_user = get_object_or_404(User, id=user_id)
    if target_user.is_superuser:
        messages.error(request, "Cannot suspend superuser accounts.")
        return redirect('opportunities:moderation_dashboard')

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])
    status_label = "restored" if target_user.is_active else "suspended"
    messages.success(request, f"User account '{target_user.username}' has been {status_label}.")
    return redirect('opportunities:moderation_dashboard')

