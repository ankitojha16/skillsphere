from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Badge, UserBadge
from .services import get_or_create_gamification

@login_required
def achievements_view(request):
    gamification = get_or_create_gamification(request.user)
    all_badges = Badge.objects.all()
    unlocked_badge_ids = set(
        UserBadge.objects.filter(user=request.user).values_list('badge_id', flat=True)
    )

    badges_data = []
    for badge in all_badges:
        is_unlocked = badge.id in unlocked_badge_ids
        badges_data.append({
            'badge': badge,
            'is_unlocked': is_unlocked,
        })

    # Next level progress
    level_order = [
        ('Beginner', 0, 100),
        ('Explorer', 100, 300),
        ('Learner', 300, 600),
        ('Developer', 600, 1000),
        ('Advanced Learner', 1000, 1500),
        ('Skill Master', 1500, 2500)
    ]
    next_level = 'Skill Master'
    xp_to_next = 0
    level_progress_pct = 100
    for idx, (lvl_name, low, high) in enumerate(level_order):
        if gamification.current_level == lvl_name:
            if idx < len(level_order) - 1:
                next_level = level_order[idx + 1][0]
                target_xp = high
                xp_in_level = gamification.total_xp - low
                span = high - low
                level_progress_pct = min(100, max(0, int((xp_in_level / span) * 100)))
                xp_to_next = max(0, target_xp - gamification.total_xp)
            else:
                level_progress_pct = 100
                xp_to_next = 0
            break

    return render(request, 'gamification/achievements.html', {
        'gamification': gamification,
        'badges_data': badges_data,
        'unlocked_count': len(unlocked_badge_ids),
        'total_badges': len(all_badges),
        'next_level': next_level,
        'xp_to_next': xp_to_next,
        'level_progress_pct': level_progress_pct,
    })
