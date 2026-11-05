from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import LearningGoal, LearningActivity
from .forms import LearningGoalForm

@login_required
def goals_list_view(request):
    goals = LearningGoal.objects.filter(user=request.user)
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'active':
        goals = goals.filter(is_completed=False)
    elif status_filter == 'completed':
        goals = goals.filter(is_completed=True)

    form = LearningGoalForm()

    total_goals = request.user.goals.count()
    completed_goals = request.user.goals.filter(is_completed=True).count()
    active_goals = total_goals - completed_goals
    completion_rate = int(round((completed_goals / total_goals) * 100)) if total_goals > 0 else 0

    return render(request, 'goals/index.html', {
        'goals': goals,
        'form': form,
        'total_goals': total_goals,
        'active_goals': active_goals,
        'completed_goals': completed_goals,
        'completion_rate': completion_rate,
        'status_filter': status_filter,
    })


@login_required
def goal_create_view(request):
    if request.method == 'POST':
        form = LearningGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()

            LearningActivity.objects.create(
                user=request.user,
                activity_type='GOAL_CREATED',
                reference_id=goal.id,
                description=f"Created learning goal: '{goal.title}'"
            )
            messages.success(request, f"New goal '{goal.title}' created successfully!")
            return redirect('goals:index')
        else:
            messages.error(request, "Failed to create goal. Please check the inputs.")
    return redirect('goals:index')


@login_required
def goal_update_view(request, goal_id):
    # Enforce user data isolation
    goal = get_object_or_404(LearningGoal, id=goal_id, user=request.user)
    if request.method == 'POST':
        form = LearningGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, f"Goal '{goal.title}' updated successfully.")
            return redirect('goals:index')
    else:
        form = LearningGoalForm(instance=goal)

    return render(request, 'goals/edit.html', {'form': form, 'goal': goal})


@login_required
def goal_delete_view(request, goal_id):
    # Enforce user data isolation
    goal = get_object_or_404(LearningGoal, id=goal_id, user=request.user)
    if request.method == 'POST':
        title = goal.title
        goal.delete()
        messages.info(request, f"Goal '{title}' deleted.")
    return redirect('goals:index')


@login_required
def goal_toggle_view(request, goal_id):
    if request.method != 'POST':
        return redirect('goals:index')

    goal = get_object_or_404(LearningGoal, id=goal_id, user=request.user)
    goal.is_completed = not goal.is_completed
    goal.save()

    if goal.is_completed:
        LearningActivity.objects.create(
            user=request.user,
            activity_type='GOAL_COMPLETED',
            reference_id=goal.id,
            description=f"Achieved learning goal: '{goal.title}'"
        )
        messages.success(request, f"Congratulations! Goal '{goal.title}' marked as achieved.")
    else:
        messages.info(request, f"Goal '{goal.title}' marked as active.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'is_completed': goal.is_completed})

    return redirect('goals:index')
