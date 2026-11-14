from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
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
                if project.current_members_count >= project.team_size:
                    messages.error(request, f"Cannot accept member: team capacity ({project.team_size} members) has been reached.")
                    return redirect('collaboration:manage', pk=project.pk)

                with transaction.atomic():
                    join_req.status = 'accepted'
                    join_req.save()
                    # Create active membership
                    CollaborationMembership.objects.get_or_create(
                        project=project,
                        user=join_req.user,
                        defaults={'role': join_req.role_requested or 'Developer', 'status': 'active'}
                    )
                    # If capacity now full, auto-update status to in_progress
                    if project.current_members_count >= project.team_size:
                        project.status = 'in_progress'
                        project.save(update_fields=['status'])

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


# ==============================================================================
# PILLAR 5: COLLABORATIVE PAIR PROGRAMMING & SYSTEM DESIGN WHITEBOARD LOUNGE
# ==============================================================================
import json
import uuid
import secrets
from django.http import JsonResponse, HttpResponseForbidden
from .models import PairProgrammingRoom, RoomChatMessage


@login_required
def lounge_hub_view(request):
    """
    Dashboard of active collaborative pair programming & architecture rooms.
    Allows creating a new lounge room or joining an existing room with code.
    """
    my_hosted_rooms = PairProgrammingRoom.objects.filter(host=request.user, is_active=True).order_by('-updated_at')
    my_joined_rooms = PairProgrammingRoom.objects.filter(collaborator=request.user, is_active=True).order_by('-updated_at')
    public_rooms = PairProgrammingRoom.objects.filter(is_active=True).exclude(host=request.user).order_by('-updated_at')[:12]

    return render(request, 'collaboration/lounge_hub.html', {
        'my_hosted_rooms': my_hosted_rooms,
        'my_joined_rooms': my_joined_rooms,
        'public_rooms': public_rooms,
    })


@login_required
def create_lounge_room_view(request):
    """
    Creates a new pair programming & whiteboard room with a unique room code.
    """
    if request.method == 'POST':
        title = request.POST.get('title', 'System Design & Algorithm Pair Session').strip()
        language = request.POST.get('language', 'python')
        if language not in ['python', 'javascript', 'sql']:
            language = 'python'

        # Generate readable unique room code
        random_suffix = secrets.token_hex(3).upper()
        room_code = f"SPHERE-{random_suffix}"

        room = PairProgrammingRoom.objects.create(
            room_code=room_code,
            title=title or "Collaborative Pair Session",
            host=request.user,
            language=language
        )
        messages.success(request, f"Lounge room created! Share code: {room_code}")
        return redirect('collaboration:pair_room', room_code=room.room_code)

    return redirect('collaboration:lounge_hub')


@login_required
def join_lounge_room_view(request):
    """
    Joins a lounge room via room code.
    """
    if request.method == 'POST':
        code = request.POST.get('room_code', '').strip().upper()
        room = PairProgrammingRoom.objects.filter(room_code=code, is_active=True).first()
        if not room:
            messages.error(request, f"Room '{code}' not found or has been closed.")
            return redirect('collaboration:lounge_hub')

        if room.host != request.user and (room.collaborator is None or room.collaborator == request.user):
            room.collaborator = request.user
            room.save()

        return redirect('collaboration:pair_room', room_code=room.room_code)

    return redirect('collaboration:lounge_hub')


@login_required
def pair_room_view(request, room_code):
    """
    The full-screen collaborative pair programming IDE & System Design whiteboard.
    """
    room = get_object_or_404(PairProgrammingRoom, room_code=room_code)
    
    if not room.is_active:
        return HttpResponseForbidden("This lounge session has ended.")

    # Auto-assign collaborator if slot open, otherwise reject unauthorized intruders if room is full
    if room.host != request.user:
        if room.collaborator is None:
            room.collaborator = request.user
            room.save(update_fields=['collaborator'])
        elif room.collaborator != request.user:
            return HttpResponseForbidden("This lounge room is full (2/2 engineers active).")

    recent_chats = room.chat_messages.select_related('sender').order_by('created_at')[:40]

    return render(request, 'collaboration/pair_room.html', {
        'room': room,
        'recent_chats': recent_chats,
        'is_host': room.host == request.user,
    })


@login_required
def room_sync_api(request, room_code):
    """
    Bidirectional polling/sync API: updates & fetches code, whiteboard state, and chat.
    Restricted strictly to the room's host and active collaborator.
    """
    room = get_object_or_404(PairProgrammingRoom, room_code=room_code)

    if not room.is_active:
        return JsonResponse({'status': 'error', 'message': 'This lounge session has ended.'}, status=403)

    if not (room.host == request.user or room.collaborator == request.user):
        return JsonResponse({
            'status': 'error',
            'message': 'Forbidden: You are not an active member of this pair programming session.'
        }, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}

        updated = False
        if 'code' in data and data['code'] is not None:
            room.code_content = str(data['code'])[:20000]
            updated = True
        if 'language' in data and data['language'] in ['python', 'javascript', 'sql']:
            room.language = data['language']
            updated = True
        if 'whiteboard' in data and data['whiteboard'] is not None:
            if isinstance(data['whiteboard'], dict):
                wb_str = json.dumps(data['whiteboard'])
            else:
                wb_str = str(data['whiteboard'])
            room.whiteboard_data = wb_str[:50000]
            updated = True

        chat_text = data.get('chat_message', '').strip()[:2000]
        if chat_text:
            RoomChatMessage.objects.create(
                room=room,
                sender=request.user,
                message=chat_text
            )

        if updated:
            room.save()

    # Fetch last 30 chat messages
    messages_data = [
        {
            'id': m.id,
            'sender': m.sender.username,
            'is_me': m.sender == request.user,
            'message': m.message,
            'time': m.created_at.strftime('%H:%M')
        }
        for m in room.chat_messages.select_related('sender').order_by('-created_at')[:30][::-1]
    ]

    whiteboard_parsed = {}
    try:
        whiteboard_parsed = json.loads(room.whiteboard_data)
    except Exception:
        whiteboard_parsed = {"nodes": [], "connections": []}

    return JsonResponse({
        'status': 'success',
        'code': room.code_content,
        'language': room.language,
        'whiteboard': whiteboard_parsed,
        'host': room.host.username,
        'collaborator': room.collaborator.username if room.collaborator else None,
        'updated_at': room.updated_at.isoformat(),
        'chat_messages': messages_data,
    })


@login_required
def run_room_code_api(request, room_code):
    """
    Safely validates collaborative code via AST parsing without server-side execution.
    Untrusted code execution in the Django web process is strictly forbidden.
    Execution is delegated to the client browser's WebAssembly Pyodide engine.
    Restricted strictly to the room's host and active collaborator.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)

    room = get_object_or_404(PairProgrammingRoom, room_code=room_code)

    if not room.is_active:
        return JsonResponse({'status': 'error', 'message': 'This lounge session has ended.'}, status=403)

    if not (room.host == request.user or room.collaborator == request.user):
        return JsonResponse({
            'status': 'error',
            'message': 'Forbidden: You are not an active member of this pair programming session.'
        }, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
        code = str(data.get('code', room.code_content))[:20000]
        language = data.get('language', room.language)
    except Exception:
        code = room.code_content
        language = room.language

    # Save code to room
    room.code_content = code
    room.language = language
    room.save(update_fields=['code_content', 'language', 'updated_at'])

    import time
    start_time = time.perf_counter()

    if language == 'python':
        import ast
        error_msg = None
        syntax_valid = True
        try:
            ast.parse(code)
            output_msg = "Python syntax verified successfully. Ready for browser Pyodide execution."
        except SyntaxError as se:
            syntax_valid = False
            error_msg = f"SyntaxError on line {se.lineno}: {se.msg}"
            output_msg = ""
        except Exception as e:
            syntax_valid = False
            error_msg = f"ValidationError: {str(e)}"
            output_msg = ""

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return JsonResponse({
            'status': 'success',
            'syntax_valid': syntax_valid,
            'output': output_msg,
            'error': error_msg,
            'execution_mode': 'client_pyodide',
            'duration_ms': duration_ms,
        })
    else:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return JsonResponse({
            'status': 'success',
            'syntax_valid': True,
            'output': f"Code saved for {language.upper()}! Execute in browser.",
            'error': None,
            'execution_mode': 'client_runtime',
            'duration_ms': duration_ms,
        })
