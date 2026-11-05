from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.http import Http404

from .models import CollaborationProject, CollaborationMembership, CollaborationRequest
from notifications.models import Notification

@login_required
def project_list_view(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'recruiting')

    projects = CollaborationProject.objects.all()

    if status_filter and status_filter != 'all':
        projects = projects.filter(status=status_filter)

    if query:
        projects = projects.filter(
            Q(title__icontains=query) |
            Q(technologies__icontains=query) |
            Q(required_roles__icontains=query) |
            Q(description__icontains=query)
        )

    context = {
        'projects': projects,
        'query': query,
        'status_filter': status_filter,
        'my_projects': CollaborationProject.objects.filter(owner=request.user),
    }
    return render(request, 'collaboration/list.html', context)


@login_required
def create_project_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'Web Development').strip()
        difficulty = request.POST.get('difficulty', 'intermediate')
        technologies = request.POST.get('technologies', '').strip()
        required_roles = request.POST.get('required_roles', '').strip()
        team_size = int(request.POST.get('team_size', 3))
        duration = request.POST.get('expected_duration', '4-6 weeks').strip()
        github_repo = request.POST.get('github_repo', '').strip()

        if title and description and technologies and required_roles:
            proj = CollaborationProject.objects.create(
                owner=request.user,
                title=title,
                description=description,
                category=category,
                difficulty=difficulty,
                technologies=technologies,
                required_roles=required_roles,
                team_size=team_size,
                expected_duration=duration,
                github_repo=github_repo,
                status='recruiting'
            )
            messages.success(request, f"Collaboration project '{title}' published! You can now accept teammates.")
            return redirect('collaboration:detail', pk=proj.pk)
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'collaboration/create.html')


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(CollaborationProject, pk=pk)

    if request.method == 'POST':
        # Submit join request
        message_text = request.POST.get('message', '').strip()
        role_req = request.POST.get('role_requested', '').strip()

        if project.owner == request.user:
            messages.warning(request, "You are the project owner.")
            return redirect('collaboration:detail', pk=project.pk)

        existing_req = CollaborationRequest.objects.filter(project=project, user=request.user).first()
        if existing_req:
            messages.info(request, "You have already submitted a join request for this project.")
        else:
            CollaborationRequest.objects.create(
                project=project,
                user=request.user,
                message=message_text,
                role_requested=role_req,
                status='pending'
            )

            # Trigger notification to project owner
            Notification.objects.create(
                user=project.owner,
                title="New Teammate Request",
                message=f"{request.user.username} requested to join '{project.title}' as {role_req or 'Contributor'}.",
                notification_type='collaboration_request',
                link=f"/collaboration/manage/{project.pk}/"
            )

            messages.success(request, "Your application to join the team has been submitted to the project owner!")
        return redirect('collaboration:detail', pk=project.pk)

    user_request = CollaborationRequest.objects.filter(project=project, user=request.user).first() if request.user.is_authenticated else None
    active_members = project.memberships.filter(status='active').select_related('user')
    is_member = active_members.filter(user=request.user).exists() or (project.owner == request.user)

    context = {
        'project': project,
        'active_members': active_members,
        'user_request': user_request,
        'is_member': is_member,
        'is_owner': (project.owner == request.user),
    }
    return render(request, 'collaboration/detail.html', context)


@login_required
def manage_team_view(request, pk):
    project = get_object_or_404(CollaborationProject, pk=pk, owner=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'handle_request':
            req_id = request.POST.get('request_id')
            decision = request.POST.get('decision')  # 'accept' or 'reject'
            join_req = get_object_or_404(CollaborationRequest, id=req_id, project=project)

            if decision == 'accept':
                join_req.status = 'accepted'
                join_req.save()
                # Create active membership
                CollaborationMembership.objects.get_or_create(
                    project=project,
                    user=join_req.user,
                    defaults={'role': join_req.role_requested or 'Developer', 'status': 'active'}
                )
                # Send notification to accepted student
                Notification.objects.create(
                    user=join_req.user,
                    title="Collaboration Request Accepted! 🎉",
                    message=f"You have been accepted into the team for '{project.title}'!",
                    notification_type='collaboration_accepted',
                    link=f"/collaboration/{project.pk}/"
                )
                messages.success(request, f"Accepted {join_req.user.username} onto the team!")

            elif decision == 'reject':
                join_req.status = 'rejected'
                join_req.save()
                messages.info(request, f"Declined join request from {join_req.user.username}.")

        elif action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(CollaborationProject.STATUS_CHOICES):
                project.status = new_status
                project.save()
                messages.success(request, f"Project status updated to {project.get_status_display()}.")

        elif action == 'remove_member':
            member_id = request.POST.get('member_id')
            mem = get_object_or_404(CollaborationMembership, id=member_id, project=project)
            mem.delete()
            messages.info(request, f"Removed {mem.user.username} from the team.")

        return redirect('collaboration:manage', pk=project.pk)

    requests = project.requests.filter(status='pending').select_related('user')
    members = project.memberships.filter(status='active').select_related('user')

    context = {
        'project': project,
        'requests': requests,
        'members': members,
        'statuses': CollaborationProject.STATUS_CHOICES,
    }
    return render(request, 'collaboration/manage.html', context)
