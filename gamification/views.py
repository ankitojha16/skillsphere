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

    # Compute user metrics for badge progress tracking
    completed_courses = 0
    try:
        from courses.models import CourseCompletion
        completed_courses = CourseCompletion.objects.filter(user=request.user, is_completed=True).count()
    except Exception:
        pass

    passed_assessments = 0
    try:
        from assessments.models import AssessmentAttempt
        passed_assessments = AssessmentAttempt.objects.filter(user=request.user, is_passed=True).count()
    except Exception:
        pass

    completed_interviews = 0
    try:
        from interviews.models import MockInterview
        completed_interviews = MockInterview.objects.filter(user=request.user, is_completed=True).count()
    except Exception:
        pass

    completed_milestones = 0
    try:
        from roadmaps.models import RoadmapMilestone
        completed_milestones = RoadmapMilestone.objects.filter(roadmap__user=request.user, is_completed=True).count()
    except Exception:
        pass

    badges_data = []
    for badge in all_badges:
        is_unlocked = badge.id in unlocked_badge_ids
        slug = badge.slug

        if slug == 'first-course-complete':
            current_val = 1 if is_unlocked or completed_courses > 0 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Course"
            progress_pct = 100 if (is_unlocked or completed_courses > 0) else 0
        elif slug == 'explorer-badge':
            target_val = max(1, badge.xp_requirement or 100)
            current_val = min(target_val, gamification.total_xp) if not is_unlocked else target_val
            progress_label = f"{current_val} / {target_val} XP"
            progress_pct = 100 if is_unlocked else min(100, int((current_val / target_val) * 100))
        elif slug == '7-day-streak':
            target_val = 7
            best_streak = max(gamification.current_streak, gamification.longest_streak)
            current_val = 7 if is_unlocked else min(7, best_streak)
            progress_label = f"{current_val} / 7 Days"
            progress_pct = 100 if is_unlocked else min(100, int((current_val / 7) * 100))
        elif slug == 'dsa-explorer':
            current_val = 1 if is_unlocked or completed_milestones > 0 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Milestone"
            progress_pct = 100 if (is_unlocked or completed_milestones > 0) else 0
        elif slug == 'first-assessment-complete':
            current_val = 1 if is_unlocked or passed_assessments > 0 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Assessment"
            progress_pct = 100 if (is_unlocked or passed_assessments > 0) else 0
        elif slug == 'first-roadmap-complete':
            current_val = 1 if is_unlocked or completed_milestones >= 3 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Roadmap"
            progress_pct = 100 if (is_unlocked or completed_milestones >= 3) else 0
        elif slug == 'interview-ready':
            current_val = 1 if is_unlocked or completed_interviews > 0 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Session"
            progress_pct = 100 if (is_unlocked or completed_interviews > 0) else 0
        else:
            current_val = 1 if is_unlocked else 0
            target_val = 1
            progress_label = "Completed" if is_unlocked else "In Progress"
            progress_pct = 100 if is_unlocked else 0

        badges_data.append({
            'badge': badge,
            'is_unlocked': is_unlocked,
            'current_value': current_val,
            'target_value': target_val,
            'progress_label': progress_label,
            'progress_pct': progress_pct,
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
