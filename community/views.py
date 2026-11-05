from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.contrib import messages
from django.http import JsonResponse

from .models import CommunityPost, CommunityComment, CommunityLike, ContentReport
from notifications.models import Notification

@login_required
def community_feed_view(request):
    category = request.GET.get('category', '').strip()
    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'latest')

    posts = CommunityPost.objects.filter(is_approved=True)

    if category:
        posts = posts.filter(category=category)

    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(user__username__icontains=query)
        )

    if sort == 'most_discussed':
        posts = posts.annotate(c_count=Count('comments')).order_by('-c_count', '-created_at')
    elif sort == 'most_liked':
        posts = posts.annotate(l_count=Count('likes')).order_by('-l_count', '-created_at')
    else:
        posts = posts.order_by('-created_at')

    # Collect liked posts for user
    user_liked_post_ids = set(CommunityLike.objects.filter(user=request.user).values_list('post_id', flat=True))

    context = {
        'posts': posts,
        'categories': CommunityPost.CATEGORY_CHOICES,
        'selected_category': category,
        'query': query,
        'sort': sort,
        'user_liked_post_ids': user_liked_post_ids,
    }
    return render(request, 'community/feed.html', context)


@login_required
def create_post_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', '').strip()
        content = request.POST.get('content', '').strip()

        if title and content and category:
            post = CommunityPost.objects.create(
                user=request.user,
                title=title,
                category=category,
                content=content
            )
            messages.success(request, "Discussion post published successfully!")
            return redirect('community:post_detail', pk=post.pk)
        else:
            messages.error(request, "Please fill in all post fields.")

    context = {
        'categories': CommunityPost.CATEGORY_CHOICES,
    }
    return render(request, 'community/create_post.html', context)


@login_required
def post_detail_view(request, pk):
    post = get_object_or_404(CommunityPost, pk=pk, is_approved=True)

    if request.method == 'POST':
        comment_text = request.POST.get('comment', '').strip()
        parent_id = request.POST.get('parent_id')
        parent_comment = None
        if parent_id:
            parent_comment = CommunityComment.objects.filter(id=parent_id, post=post).first()

        if comment_text:
            comment = CommunityComment.objects.create(
                post=post,
                user=request.user,
                parent_comment=parent_comment,
                content=comment_text
            )

            # Notify author if commented by someone else
            if post.user != request.user:
                Notification.objects.create(
                    user=post.user,
                    title="New Reply in Community",
                    message=f"{request.user.username} replied to your post '{post.title[:30]}...'",
                    notification_type='community_reply',
                    link=f"/community/post/{post.pk}/"
                )

            messages.success(request, "Your reply has been added!")
            return redirect('community:post_detail', pk=post.pk)

    # Get top-level comments
    comments = post.comments.filter(parent_comment__isnull=True).prefetch_related('replies').order_by('created_at')
    is_liked = CommunityLike.objects.filter(user=request.user, post=post).exists()

    context = {
        'post': post,
        'comments': comments,
        'is_liked': is_liked,
    }
    return render(request, 'community/post_detail.html', context)


@login_required
def toggle_like_view(request, pk):
    post = get_object_or_404(CommunityPost, pk=pk)
    like = CommunityLike.objects.filter(user=request.user, post=post).first()

    if like:
        like.delete()
        liked = False
    else:
        CommunityLike.objects.create(user=request.user, post=post)
        liked = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'liked': liked, 'total_likes': post.likes_count})

    next_url = request.META.get('HTTP_REFERER') or f'/community/post/{post.pk}/'
    return redirect(next_url)


@login_required
def report_content_view(request):
    if request.method == 'POST':
        c_type = request.POST.get('content_type')
        obj_id = request.POST.get('object_id')
        reason = request.POST.get('reason')
        desc = request.POST.get('description', '')

        if c_type and obj_id and reason:
            ContentReport.objects.create(
                reporter=request.user,
                content_type=c_type,
                object_id=obj_id,
                reason=reason,
                description=desc
            )
            messages.success(request, "Thank you. Your report has been submitted to moderators for review.")
        else:
            messages.error(request, "Incomplete report parameters.")

    next_url = request.META.get('HTTP_REFERER') or 'community:feed'
    return redirect(next_url)
