from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
import json

from .models import LearningRoadmap, RoadmapMilestone
from services.ai_service import AIService
from gamification.services import award_user_xp, award_badge_if_eligible

@login_required
def roadmaps_list_view(request):
    roadmaps = LearningRoadmap.objects.filter(user=request.user)
    roadmaps_data = []
    for r in roadmaps:
        roadmaps_data.append({
            'roadmap': r,
            'progress': r.get_progress(),
        })

    return render(request, 'roadmaps/list.html', {
        'roadmaps_data': roadmaps_data,
    })


@login_required
def roadmap_generate_view(request):
    if request.method == 'POST':
        skill = request.POST.get('target_skill', '').strip()
        current_level = request.POST.get('current_level', 'Beginner')
        career_goal = request.POST.get('career_goal', '').strip()
        daily_time = request.POST.get('daily_time', '1 hour/day')
        duration = request.POST.get('duration', '3 months')

        if not skill:
            messages.error(request, "Please enter a target skill to generate your roadmap.")
            return render(request, 'roadmaps/generate.html')

        title = f"{skill} Mastery ({career_goal or 'Developer Path'})"

        roadmap = LearningRoadmap.objects.create(
            user=request.user,
            title=title,
            target_skill=skill,
            current_level=current_level,
            career_goal=career_goal or f"{skill} Specialist",
            daily_time=daily_time,
            duration=duration,
        )

        # Call AI Roadmap Generator
        phases = AIService.generate_roadmap(
            skill=skill,
            level=current_level,
            goal=career_goal or f"{skill} Developer",
            daily_time=daily_time,
            duration=duration
        )

        for idx, phase in enumerate(phases, start=1):
            topics = phase.get('topics', [])
            RoadmapMilestone.objects.create(
                roadmap=roadmap,
                title=phase.get('title', f"Phase {idx}"),
                description=phase.get('description', ''),
                topics_json=json.dumps(topics),
                mini_project=phase.get('mini_project', ''),
                milestone_order=idx,
                estimated_weeks=phase.get('estimated_weeks', 2),
            )

        # Award XP for roadmap creation
        award_user_xp(request.user, 30, f"Generated roadmap for {skill}")

        messages.success(request, f"Your personalized {skill} roadmap has been generated!")
        return redirect('roadmaps:detail', roadmap_id=roadmap.id)

    # Prefill from student profile if available
    profile = getattr(request.user, 'profile', None)
    initial_goal = profile.career_goal if profile else ''
    initial_level = profile.get_learning_level_display() if profile else 'Beginner'

    return render(request, 'roadmaps/generate.html', {
        'initial_goal': initial_goal,
        'initial_level': initial_level,
    })


@login_required
def roadmap_detail_view(request, roadmap_id):
    roadmap = get_object_or_404(LearningRoadmap, id=roadmap_id, user=request.user)
    milestones = roadmap.milestones.all().order_by('milestone_order', 'id')
    progress = roadmap.get_progress()

    return render(request, 'roadmaps/detail.html', {
        'roadmap': roadmap,
        'milestones': milestones,
        'progress': progress,
    })


@login_required
def roadmap_toggle_milestone(request, milestone_id):
    if request.method != 'POST':
        return redirect('roadmaps:list')

    milestone = get_object_or_404(RoadmapMilestone, id=milestone_id, roadmap__user=request.user)
    milestone.is_completed = not milestone.is_completed
    milestone.completed_at = timezone.now() if milestone.is_completed else None
    milestone.save()

    if milestone.is_completed:
        award_user_xp(request.user, 40, f"Completed roadmap milestone: {milestone.title}")
        prog = milestone.roadmap.get_progress()
        if prog['percentage'] == 100:
            award_user_xp(request.user, 200, f"Completed entire roadmap: {milestone.roadmap.title}!")
            award_badge_if_eligible(request.user, 'first-roadmap-complete')

    progress = milestone.roadmap.get_progress()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_completed': milestone.is_completed,
            'percentage': progress['percentage'],
            'completed': progress['completed'],
            'total': progress['total'],
        })

    return redirect('roadmaps:detail', roadmap_id=milestone.roadmap.id)


@login_required
def roadmap_delete_view(request, roadmap_id):
    roadmap = get_object_or_404(LearningRoadmap, id=roadmap_id, user=request.user)
    if request.method == 'POST':
        title = roadmap.title
        roadmap.delete()
        messages.info(request, f"Roadmap '{title}' removed.")
    return redirect('roadmaps:list')
