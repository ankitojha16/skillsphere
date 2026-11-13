import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Opportunity, SavedOpportunity, CandidateShortlist, InterviewInvitation
from notifications.models import Notification
from accounts.models import StudentProfile
from accounts.decorators import recruiter_required
from resumes.models import Resume
from assessments.models import ChallengeSubmission
from gamification.models import UserArenaRating
from certificates.models import Certificate
from django.core.cache import cache

@login_required
def opportunity_list_view(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    work_mode = request.GET.get('work_mode', '').strip()

    opportunities = Opportunity.objects.filter(is_active=True)

    if query:
        opportunities = opportunities.filter(
            Q(title__icontains=query) |
            Q(organization__icontains=query) |
            Q(required_skills__icontains=query) |
            Q(description__icontains=query)
        )

    if category:
        opportunities = opportunities.filter(category=category)

    show_expired = request.GET.get('show_expired') == 'true'
    today = timezone.now().date()
    if not show_expired:
        opportunities = opportunities.filter(Q(deadline__isnull=True) | Q(deadline__gte=today))

    opportunities = opportunities.order_by('deadline')

    saved_opp_ids = SavedOpportunity.objects.filter(user=request.user).values_list('opportunity_id', flat=True)

    context = {
        'opportunities': opportunities,
        'categories': Opportunity.CATEGORY_CHOICES,
        'work_modes': Opportunity.WORK_MODE_CHOICES,
        'selected_category': category,
        'selected_work_mode': work_mode,
        'query': query,
        'saved_opp_ids': set(saved_opp_ids),
        'today': today,
        'show_expired': show_expired,
    }
    return render(request, 'opportunities/list.html', context)


@login_required
def opportunity_detail_view(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk)
    saved_entry = SavedOpportunity.objects.filter(user=request.user, opportunity=opportunity).first()

    context = {
        'opportunity': opportunity,
        'saved_entry': saved_entry,
    }
    return render(request, 'opportunities/detail.html', context)


@login_required
def toggle_save_opportunity_view(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk)
    saved = SavedOpportunity.objects.filter(user=request.user, opportunity=opportunity).first()

    if saved:
        saved.delete()
        messages.info(request, f"Removed '{opportunity.title}' from your saved tracker.")
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
def application_tracker_view(request):
    saved_opportunities = SavedOpportunity.objects.filter(user=request.user).select_related('opportunity')

    if request.method == 'POST':
        saved_id = request.POST.get('saved_id')
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')

        entry = get_object_or_404(SavedOpportunity, id=saved_id, user=request.user)
        if new_status in dict(SavedOpportunity.STATUS_CHOICES):
            entry.application_status = new_status
            if new_status == 'applied' and not entry.applied_at:
                entry.applied_at = timezone.now()
        entry.application_notes = notes
        entry.save()
        messages.success(request, f"Updated application status for {entry.opportunity.title}!")
        return redirect('opportunities:tracker')

    # Group by status
    pipeline = {
        'interested': [],
        'preparing': [],
        'applied': [],
        'interview': [],
        'selected': [],
        'rejected': [],
    }

    for item in saved_opportunities:
        status_key = item.application_status
        if status_key in pipeline:
            pipeline[status_key].append(item)

    context = {
        'pipeline': pipeline,
        'total_tracked': saved_opportunities.count(),
        'statuses': SavedOpportunity.STATUS_CHOICES,
    }
    return render(request, 'opportunities/tracker.html', context)


# ==========================================
# RECRUITER TALENT PORTAL & CANDIDATE SEARCH
# ==========================================

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

    # Pre-fetch shortlists for this recruiter in 1 query
    shortlisted_ids = set(
        CandidateShortlist.objects.filter(recruiter=request.user, candidate_id__in=user_ids)
        .values_list('candidate_id', flat=True)
    )

    # Batch pre-fetch primary resumes in 1 query
    resumes_by_user = {}
    if user_ids:
        for r in Resume.objects.filter(user_id__in=user_ids).order_by('-is_primary', '-updated_at'):
            if r.user_id not in resumes_by_user:
                resumes_by_user[r.user_id] = r

    # Batch calculate distinct solved challenges in 1 aggregate query
    solved_counts = {}
    if user_ids:
        solved_counts = dict(
            ChallengeSubmission.objects.filter(user_id__in=user_ids, status='Accepted')
            .values('user_id')
            .annotate(cnt=Count('challenge_id', distinct=True))
            .values_list('user_id', 'cnt')
        )

    # Batch calculate certificates in 1 aggregate query
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
            res_skills = resume.get_skills_list() if hasattr(resume, 'get_skills_list') else (resume.skills if isinstance(resume.skills, list) else [])
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

    # Rate limiting: max 15 invitations per hour per recruiter
    rate_limit_key = f"recruiter_invitations_{request.user.id}"
    current_count = cache.get(rate_limit_key, 0)
    if current_count >= 15:
        return JsonResponse({
            'status': 'error',
            'error': 'Hourly interview invitation limit reached (15/hr). Please try again later.',
            'message': 'Hourly interview invitation limit reached (15/hr). Please try again later.'
        }, status=429)

    candidate = get_object_or_404(User, username=username)
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

    # Increment rate limit counter
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

    # Batch fetch resumes
    resumes_by_user = {}
    if user_ids:
        for r in Resume.objects.filter(user_id__in=user_ids).order_by('-is_primary', '-updated_at'):
            if r.user_id not in resumes_by_user:
                resumes_by_user[r.user_id] = r

    # Batch calculate solved challenges
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

