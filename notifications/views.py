from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Notification

@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    type_filter = request.GET.get('type')
    if type_filter:
        notifications = notifications.filter(notification_type=type_filter)

    context = {
        'notifications': notifications,
        'types': Notification.TYPE_CHOICES,
        'selected_type': type_filter,
    }
    return render(request, 'notifications/index.html', context)


@login_required
def mark_as_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'id': pk})

    if notification.link:
        return redirect(notification.link)

    next_url = request.META.get('HTTP_REFERER') or 'notifications:list'
    return redirect(next_url)


@login_required
def mark_all_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'message': 'All notifications marked as read'})

    messages.success(request, "All notifications marked as read.")
    next_url = request.META.get('HTTP_REFERER') or 'notifications:list'
    return redirect(next_url)


@login_required
def delete_notification_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'id': pk})

    messages.info(request, "Notification deleted.")
    next_url = request.META.get('HTTP_REFERER') or 'notifications:list'
    return redirect(next_url)

