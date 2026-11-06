from django.contrib.auth.models import User
from django.db import transaction
from .models import UserGamification, Badge, UserBadge, XPTransaction
from goals.models import LearningActivity

def get_or_create_gamification(user: User) -> UserGamification:
    gamification, _ = UserGamification.objects.get_or_create(user=user)
    return gamification

def award_user_xp(user: User, amount: int, reason: str = "", activity_key: str = "") -> UserGamification:
    if not user or not user.is_authenticated or amount <= 0:
        return None

    with transaction.atomic():
        # Prevent duplicate awards for the same unique milestone/activity
        if activity_key:
            if XPTransaction.objects.filter(user=user, activity_key=activity_key).exists():
                return get_or_create_gamification(user)

            XPTransaction.objects.create(
                user=user,
                activity_key=activity_key,
                amount=amount,
                reason=reason or f"Activity {activity_key}"
            )

        gamification = get_or_create_gamification(user)
        gamification.add_xp(amount)
        
        if reason:
            LearningActivity.objects.create(
                user=user,
                activity_type='GOAL_COMPLETED',
                description=f"Earned +{amount} XP: {reason}"
            )

        # Check for streak or XP badges
        if gamification.total_xp >= 100:
            award_badge_if_eligible(user, 'explorer-badge')
        if gamification.current_streak >= 7:
            award_badge_if_eligible(user, '7-day-streak')

        return gamification

def award_badge_if_eligible(user: User, badge_slug: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    badge = Badge.objects.filter(slug=badge_slug).first()
    if not badge:
        return False
    user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
    if created:
        LearningActivity.objects.create(
            user=user,
            activity_type='GOAL_COMPLETED',
            description=f"Unlocked Achievement Badge: {badge.name}!"
        )
        return True
    return False
