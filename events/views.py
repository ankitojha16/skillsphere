from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone

from .models import Event, SavedEvent
from notifications.models import Notification

@login_required
def event_list_view(request):
    category = request.GET.get('category', '').strip()
    query = request.GET.get('q', '').strip()

    events = Event.objects.filter(is_active=True)

    if category:
        events = events.filter(category=category)

    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(organizer__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )

    saved_event_ids = set(SavedEvent.objects.filter(user=request.user).values_list('event_id', flat=True))

    context = {
        'events': events,
        'categories': Event.CATEGORY_CHOICES,
        'selected_category': category,
        'query': query,
        'saved_event_ids': saved_event_ids,
        'my_saved_events': SavedEvent.objects.filter(user=request.user).select_related('event'),
    }
    return render(request, 'events/list.html', context)


@login_required
def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    saved_entry = SavedEvent.objects.filter(user=request.user, event=event).first()

    context = {
        'event': event,
        'saved_entry': saved_entry,
    }
    return render(request, 'events/detail.html', context)


@login_required
def toggle_save_event_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    saved = SavedEvent.objects.filter(user=request.user, event=event).first()

    if saved:
        saved.delete()
        messages.info(request, f"Removed '{event.title}' from your saved events.")
    else:
        SavedEvent.objects.create(
            user=request.user,
            event=event,
            reminder_set=True
        )
        Notification.objects.create(
            user=request.user,
            title="Event Reminder Set",
            message=f"You saved '{event.title}'. Mark your calendar for {event.start_date.strftime('%B %d, %Y')}!",
            notification_type='saved_event',
            link=f"/events/{event.pk}/"
        )
        messages.success(request, f"Saved '{event.title}'! A participation reminder has been logged.")

    next_url = request.META.get('HTTP_REFERER') or 'events:list'
    return redirect(next_url)
