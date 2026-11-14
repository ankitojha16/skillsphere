from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from .models import UserGamification, Badge, UserBadge, XPTransaction
from goals.models import LearningActivity

def get_or_create_gamification(user: User, for_update: bool = False) -> UserGamification:
    try:
        with transaction.atomic():
            UserGamification.objects.get_or_create(user=user)
    except IntegrityError:
        pass
    if for_update:
        return UserGamification.objects.select_for_update().get(user=user)
    return UserGamification.objects.get(user=user)

def award_user_xp(user: User, amount: int, reason: str = "", activity_key: str = "") -> UserGamification:
    if not user or not user.is_authenticated or amount <= 0:
        return None

    with transaction.atomic():
        # Prevent duplicate awards for the same unique milestone/activity using DB constraint
        if activity_key:
            try:
                with transaction.atomic():
                    XPTransaction.objects.create(
                        user=user,
                        activity_key=activity_key,
                        amount=amount,
                        reason=reason or f"Activity {activity_key}"
                    )
            except IntegrityError:
                # Milestone already recorded concurrently
                return get_or_create_gamification(user)

        gamification = get_or_create_gamification(user, for_update=True)
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
