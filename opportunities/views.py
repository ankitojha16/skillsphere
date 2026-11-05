from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import Opportunity, SavedOpportunity
from notifications.models import Notification

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

    if work_mode:
        opportunities = opportunities.filter(work_mode=work_mode)

    saved_opp_ids = SavedOpportunity.objects.filter(user=request.user).values_list('opportunity_id', flat=True)

    context = {
        'opportunities': opportunities,
        'categories': Opportunity.CATEGORY_CHOICES,
        'work_modes': Opportunity.WORK_MODE_CHOICES,
        'selected_category': category,
        'selected_work_mode': work_mode,
        'query': query,
        'saved_opp_ids': set(saved_opp_ids),
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
