"""
SkillSphere Career Studio — Studio Views.
Implements the Career Studio dashboard, 11-track explorer, transparent skill gap analyzer,
personalized learning roadmaps, 5-stage project portfolio studio, smart resume builder,
and grounded AI career assistant.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    CareerTrack,
    CareerSkillRequirement,
    StudentCareerGoal,
    StudentSkillEvidence,
    SkillGapReport,
)
from projects.models import ProjectIdea, ProjectMilestone
from resumes.models import Resume, ResumeVersion
from roadmaps.models import LearningRoadmap, RoadmapMilestone
from certificates.models import Certificate
from gamification.services import award_user_xp

from services.skill_evidence_engine import SkillEvidenceEngine
from services.career_roadmap_generator import CareerRoadmapGenerator
from services.career_ai_assistant import CareerAIAssistant
from services.resume_service import ResumeService
from services.pdf_service import PDFService


@login_required
def career_studio_dashboard(request):
    """
    Unified Career Studio Dashboard (/career-studio/).
    Displays career goal, overall readiness index, evidence summary,
    active roadmap milestones, project portfolio stages, and resume health.
    """
    user = request.user

    # Ensure evidence is audited
    SkillEvidenceEngine.aggregate_student_evidence(user)

    # 1. Career Goal
    goal = StudentCareerGoal.objects.filter(user=user).select_related('primary_track').first()
    primary_track = goal.primary_track if goal else None

    # If no goal is set, suggest the first track
    if not primary_track:
        primary_track = CareerTrack.objects.filter(slug='fullstack-developer').first() or CareerTrack.objects.first()

    # 2. Skill Gap Report
    gap_report = None
    if primary_track:
        gap_report = SkillGapReport.objects.filter(user=user, track=primary_track).first()
        if not gap_report:
            gap_report = SkillEvidenceEngine.calculate_skill_gap(user, primary_track)

    readiness_score = gap_report.overall_match_percentage if gap_report else 0

    # 3. Learning Roadmap
    roadmap = None
    milestones = []
    if primary_track:
        roadmap = LearningRoadmap.objects.filter(user=user, target_skill=primary_track.title).first()
        if roadmap:
            milestones = roadmap.milestones.all()[:4]

    # 4. Project Portfolio Stats
    user_projects = ProjectIdea.objects.filter(user=user)
    completed_projects_count = user_projects.filter(workflow_status__in=['completed', 'published']).count()
    active_projects_count = user_projects.filter(workflow_status='in_progress').count()
    recent_projects = user_projects[:3]

    # 5. Verified Credentials Count
    verified_evidence_count = StudentSkillEvidence.objects.filter(user=user, is_verified=True).count()
    certificates_count = Certificate.objects.filter(user=user, verification_status=True).count()

    # 6. Primary Resume
    primary_resume = Resume.objects.filter(user=user, is_primary=True).first() or Resume.objects.filter(user=user).first()

    # 7. Quick tracks list for switcher
    available_tracks = CareerTrack.objects.filter(is_active=True).order_by('display_order')[:6]

    context = {
        'goal': goal,
        'primary_track': primary_track,
        'gap_report': gap_report,
        'readiness_score': readiness_score,
        'roadmap': roadmap,
        'milestones': milestones,
        'completed_projects_count': completed_projects_count,
        'active_projects_count': active_projects_count,
        'recent_projects': recent_projects,
        'verified_evidence_count': verified_evidence_count,
        'certificates_count': certificates_count,
        'primary_resume': primary_resume,
        'available_tracks': available_tracks,
    }
    return render(request, 'careers/studio/dashboard.html', context)


@login_required
def career_path_explorer(request):
    """
    Career Path Explorer (/career-studio/paths/).
    Displays all 11 curated engineering career tracks.
    """
    tracks = CareerTrack.objects.filter(is_active=True).order_by('display_order')
    goal = StudentCareerGoal.objects.filter(user=request.user).select_related('primary_track').first()
    primary_track = goal.primary_track if goal else None

    # Retrieve match scores for user across tracks
    existing_reports = {r.track_id: r.overall_match_percentage for r in SkillGapReport.objects.filter(user=request.user)}

    track_cards = []
    for t in tracks:
        match_pct = existing_reports.get(t.id, None)
        track_cards.append({
            'track': t,
            'is_primary': primary_track and primary_track.id == t.id,
            'match_pct': match_pct,
            'skills_count': t.skill_requirements.count(),
        })

    context = {
        'tracks': track_cards,
        'primary_track': primary_track,
    }
    return render(request, 'careers/studio/path_explorer.html', context)


@login_required
def career_path_detail(request, slug):
    """
    Detailed Track View (/career-studio/paths/<slug>/).
    Shows curriculum milestones, benchmark requirements, suggested projects,
    and technical interview topics.
    """
    track = get_object_or_404(CareerTrack, slug=slug, is_active=True)
    goal = StudentCareerGoal.objects.filter(user=request.user).first()
    is_primary = goal and goal.primary_track_id == track.id

    # Compute or retrieve user's gap report for this track
    gap_report = SkillEvidenceEngine.calculate_skill_gap(request.user, track)

    essential_skills = track.skill_requirements.filter(importance='essential')
    recommended_skills = track.skill_requirements.filter(importance='recommended')
    bonus_skills = track.skill_requirements.filter(importance='bonus')

    context = {
        'track': track,
        'is_primary': is_primary,
        'gap_report': gap_report,
        'essential_skills': essential_skills,
        'recommended_skills': recommended_skills,
        'bonus_skills': bonus_skills,
        'milestones': track.learning_milestones or [],
        'suggested_projects': track.suggested_projects or [],
        'interview_topics': track.interview_topics or [],
    }
    return render(request, 'careers/studio/path_detail.html', context)


@login_required
@require_POST
def set_career_goal(request, slug):
    """
    Sets a chosen CareerTrack as the student's primary career goal.
    Synchronizes the personal roadmap and awards initial progress XP.
    """
    track = get_object_or_404(CareerTrack, slug=slug, is_active=True)
    timeline_months = int(request.POST.get('timeline_months', 6))

    goal, created = StudentCareerGoal.objects.get_or_create(
        user=request.user,
        defaults={
            'primary_track': track,
            'target_timeline_months': timeline_months,
            'status': 'exploring',
        }
    )

    if not created:
        goal.primary_track = track
        goal.target_timeline_months = timeline_months
        goal.save(update_fields=['primary_track', 'target_timeline_months', 'updated_at'])

    # Synchronize or generate roadmap
    CareerRoadmapGenerator.generate_or_sync_roadmap(
        user=request.user,
        track=track,
        timeline_months=timeline_months
    )

    # Recompute skill gap
    SkillEvidenceEngine.calculate_skill_gap(request.user, track)

    # Award XP for active career planning
    award_user_xp(request.user, 50, f"Set primary career goal: {track.title}")

    messages.success(request, f"🎉 '{track.title}' is now your primary career track! Roadmap synchronized.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'track': track.title, 'slug': track.slug})

    return redirect('careers:studio_dashboard')


@login_required
def skill_gap_analyzer(request, slug=None):
    """
    Skill Gap Analyzer (/career-studio/gap-analyzer/ or /career-studio/gap-analyzer/<slug>/).
    Displays transparent, auditable skill score breakdown with verified evidence badges,
    missing benchmark requirements, and prioritized action plan.
    """
    tracks = CareerTrack.objects.filter(is_active=True).order_by('display_order')

    target_track = None
    if slug:
        target_track = get_object_or_404(CareerTrack, slug=slug, is_active=True)
    else:
        goal = StudentCareerGoal.objects.filter(user=request.user).select_related('primary_track').first()
        if goal and goal.primary_track:
            target_track = goal.primary_track
        else:
            target_track = tracks.first()

    report = SkillEvidenceEngine.calculate_skill_gap(request.user, target_track)

    context = {
        'tracks': tracks,
        'current_track': target_track,
        'report': report,
        'match_score': report.overall_match_percentage,
        'demonstrated': report.demonstrated_skills,
        'improving': report.improving_skills,
        'missing': report.missing_skills,
        'action_plan': report.action_plan,
        'score_explanation': report.score_explanation,
    }
    return render(request, 'careers/studio/gap_analyzer.html', context)


@login_required
def career_roadmap_view(request):
    """
    Personalized Learning Roadmap (/career-studio/roadmap/).
    Displays milestone checklist linked to courses and portfolio deliverables.
    """
    goal = StudentCareerGoal.objects.filter(user=request.user).select_related('primary_track').first()
    track = goal.primary_track if goal else CareerTrack.objects.first()

    roadmap = None
    if track:
        roadmap = LearningRoadmap.objects.filter(user=request.user, target_skill=track.title).first()
        if not roadmap:
            roadmap = CareerRoadmapGenerator.generate_or_sync_roadmap(
                user=request.user,
                track=track,
                timeline_months=goal.target_timeline_months if goal else 6
            )

    progress = roadmap.get_progress() if roadmap else {'percentage': 0, 'completed': 0, 'total': 0}
    milestones = roadmap.milestones.all().order_by('milestone_order') if roadmap else []

    context = {
        'track': track,
        'goal': goal,
        'roadmap': roadmap,
        'milestones': milestones,
        'progress': progress,
    }
    return render(request, 'careers/studio/roadmap.html', context)


@login_required
@require_POST
def toggle_roadmap_milestone(request, milestone_id):
    """
    Toggles completion state of a roadmap milestone.
    """
    ms = CareerRoadmapGenerator.toggle_milestone_completion(milestone_id, request.user)
    if not ms:
        return JsonResponse({'error': 'Milestone not found or unauthorized.'}, status=404)

    if ms.is_completed:
        award_user_xp(request.user, 30, f"Completed milestone: {ms.title}")

    # Re-audit evidence so completed milestones reflect in dashboard
    SkillEvidenceEngine.aggregate_student_evidence(request.user)

    progress = ms.roadmap.get_progress()
    return JsonResponse({
        'success': True,
        'milestone_id': ms.id,
        'is_completed': ms.is_completed,
        'progress': progress,
    })


@login_required
@require_POST
def reorder_roadmap_milestones(request):
    """
    Reorders roadmap milestones.
    """
    try:
        body = json.loads(request.body.decode('utf-8'))
        ordered_ids = body.get('ordered_ids', [])
        roadmap_id = body.get('roadmap_id')

        roadmap = get_object_or_404(LearningRoadmap, id=roadmap_id, user=request.user)
        CareerRoadmapGenerator.reorder_milestones(roadmap, ordered_ids)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# =============================================================================
# Project Portfolio Studio (5-Stage Workflow)
# =============================================================================

@login_required
def portfolio_studio_view(request):
    """
    Project Portfolio Studio (/career-studio/projects/).
    Organized into 5 workflow stages:
    Idea -> Planning -> In Progress -> Completed -> Published in Portfolio
    """
    projects = ProjectIdea.objects.filter(user=request.user).order_by('-created_at')

    stages = {
        'idea': [],
        'planning': [],
        'in_progress': [],
        'completed': [],
        'published': [],
    }

    for p in projects:
        st = p.workflow_status if p.workflow_status in stages else 'planning'
        stages[st].append(p)

    context = {
        'projects': projects,
        'stages': stages,
        'total_count': projects.count(),
        'published_count': len(stages['published']),
        'completed_count': len(stages['completed']),
    }
    return render(request, 'careers/studio/project_studio.html', context)


@login_required
def create_studio_project(request):
    """
    Create a new portfolio project (/career-studio/projects/new/).
    Private by default (is_public=False) to safeguard student work.
    """
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', 'Web Development')
        difficulty = request.POST.get('difficulty', 'Intermediate')
        technology_stack = request.POST.get('technology_stack', '').strip()
        description = request.POST.get('description', '').strip()
        github_url = request.POST.get('github_url', '').strip()
        demo_url = request.POST.get('demo_url', '').strip()
        workflow_status = request.POST.get('workflow_status', 'planning')
        is_public = request.POST.get('is_public') == 'true'

        if not title:
            messages.error(request, "Project title is required.")
            return redirect('careers:portfolio_studio')

        tech_list = [t.strip() for t in technology_stack.split(',') if t.strip()]

        project = ProjectIdea.objects.create(
            user=request.user,
            title=title,
            category=category,
            difficulty=difficulty,
            technology_stack=technology_stack,
            technologies_list=tech_list,
            skills_demonstrated=tech_list,
            description=description,
            github_url=github_url,
            demo_url=demo_url,
            workflow_status=workflow_status,
            is_public=is_public, # Private by default
        )

        # Create standard initial delivery milestones
        default_milestones = [
            ("1. System Architecture & Schema", "Design database schema, ER diagrams, and API specifications."),
            ("2. Core Implementation & Testing", "Build domain features, business logic, and automated unit test suite."),
            ("3. CI/CD Deployment & Documentation", "Containerize with Docker, configure GitHub Actions, and deploy live."),
        ]
        for idx, (m_title, m_desc) in enumerate(default_milestones, start=1):
            ProjectMilestone.objects.create(
                project=project,
                title=m_title,
                description=m_desc,
                order=idx,
                is_completed=False,
            )

        award_user_xp(request.user, 40, f"Initiated project: {title}")
        messages.success(request, f"Project '{title}' created successfully!")
        return redirect('careers:studio_project_detail', project_id=project.id)

    return render(request, 'careers/studio/project_form.html', {
        'categories': ProjectIdea.CATEGORY_CHOICES,
        'difficulties': ProjectIdea.DIFFICULTY_CHOICES,
        'workflow_statuses': ProjectIdea.WORKFLOW_STATUS_CHOICES,
    })


@login_required
def studio_project_detail(request, project_id):
    """
    Project Workspace Detail View (/career-studio/projects/<project_id>/).
    Checklist milestones, live links, workflow progression, privacy controls.
    """
    project = get_object_or_404(ProjectIdea, id=project_id, user=request.user)
    milestones = project.milestones.all().order_by('order')

    if request.method == 'POST':
        # Update project fields
        project.title = request.POST.get('title', project.title).strip()
        project.description = request.POST.get('description', project.description).strip()
        project.technology_stack = request.POST.get('technology_stack', project.technology_stack).strip()
        project.github_url = request.POST.get('github_url', project.github_url).strip()
        project.demo_url = request.POST.get('demo_url', project.demo_url).strip()
        new_status = request.POST.get('workflow_status', project.workflow_status)
        project.workflow_status = new_status
        project.is_public = request.POST.get('is_public') == 'true'

        tech_list = [t.strip() for t in project.technology_stack.split(',') if t.strip()]
        project.technologies_list = tech_list
        project.skills_demonstrated = tech_list
        project.save()

        # Update evidence engine if project is completed or published
        if project.workflow_status in ['completed', 'published']:
            SkillEvidenceEngine.aggregate_student_evidence(request.user)

        messages.success(request, "Project details updated!")
        return redirect('careers:studio_project_detail', project_id=project.id)

    context = {
        'project': project,
        'milestones': milestones,
        'progress_pct': project.get_progress_percentage(),
        'workflow_statuses': ProjectIdea.WORKFLOW_STATUS_CHOICES,
    }
    return render(request, 'careers/studio/project_detail.html', context)


@login_required
@require_POST
def add_project_milestone(request, project_id):
    """
    Adds a checklist milestone to a project.
    """
    project = get_object_or_404(ProjectIdea, id=project_id, user=request.user)
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()

    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)

    next_order = project.milestones.count() + 1
    ms = ProjectMilestone.objects.create(
        project=project,
        title=title,
        description=description,
        order=next_order,
        is_completed=False,
    )
    return JsonResponse({
        'success': True,
        'milestone_id': ms.id,
        'title': ms.title,
        'order': ms.order,
        'progress_pct': project.get_progress_percentage(),
    })


@login_required
@require_POST
def toggle_project_milestone(request, project_id, milestone_id):
    """
    Toggles completion state of a project milestone.
    """
    project = get_object_or_404(ProjectIdea, id=project_id, user=request.user)
    ms = get_object_or_404(ProjectMilestone, id=milestone_id, project=project)

    ms.is_completed = not ms.is_completed
    ms.completed_at = timezone.now() if ms.is_completed else None
    ms.save(update_fields=['is_completed', 'completed_at'])

    return JsonResponse({
        'success': True,
        'milestone_id': ms.id,
        'is_completed': ms.is_completed,
        'progress_pct': project.get_progress_percentage(),
    })


@login_required
@require_POST
def toggle_project_visibility(request, project_id):
    """
    Toggles public visibility of a project (opt-in public sharing).
    """
    project = get_object_or_404(ProjectIdea, id=project_id, user=request.user)
    project.is_public = not project.is_public
    project.save(update_fields=['is_public', 'updated_at'])

    return JsonResponse({
        'success': True,
        'is_public': project.is_public,
        'label': 'Public' if project.is_public else 'Private',
    })


# =============================================================================
# Smart Resume Studio
# =============================================================================

@login_required
def smart_resume_studio(request):
    """
    Smart Resume Studio (/career-studio/resume/).
    Allows students to generate, customize, reorder sections, and maintain versions
    of verified tech resumes.
    """
    user = request.user
    resumes = Resume.objects.filter(user=user)
    primary_resume = resumes.filter(is_primary=True).first() or resumes.first()

    # If no resume exists, pre-populate a verified one
    if not primary_resume:
        primary_resume = ResumeService.populate_verified_resume(user)
        resumes = Resume.objects.filter(user=user)

    versions = primary_resume.versions.all() if primary_resume else []

    context = {
        'resumes': resumes,
        'primary_resume': primary_resume,
        'resume_data': primary_resume.resume_data if primary_resume else {},
        'section_order': primary_resume.get_section_order() if primary_resume else [],
        'versions': versions,
        'templates': Resume.TEMPLATE_CHOICES,
    }
    return render(request, 'careers/studio/smart_resume.html', context)


@login_required
@require_POST
def generate_smart_resume(request):
    """
    Auto-populates a fresh resume from verified platform credentials.
    """
    template = request.POST.get('template', 'ats')
    track_slug = request.POST.get('target_career_track', '')
    title = request.POST.get('title', '').strip() or None

    resume = ResumeService.populate_verified_resume(
        user=request.user,
        target_track_slug=track_slug,
        template=template,
        resume_title=title,
    )

    award_user_xp(request.user, 50, "Generated verified Smart Resume")
    messages.success(request, f"Smart Resume '{resume.title}' successfully generated from your verified credentials!")
    return redirect('careers:smart_resume_studio')


@login_required
def preview_smart_resume(request, resume_id):
    """
    Preview interactive resume layout.
    """
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    context = {
        'resume': resume,
        'resume_data': resume.resume_data,
        'section_order': resume.get_section_order(),
        'template': resume.template,
    }
    return render(request, 'careers/studio/resume_preview.html', context)


@login_required
@require_POST
def create_resume_version(request, resume_id):
    """
    Creates an immutable version snapshot of the current resume state.
    """
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    version_title = request.POST.get('version_title', '').strip() or None
    version = ResumeService.create_version_snapshot(resume, version_title=version_title)

    messages.success(request, f"Snapshot '{version.version_title}' (v{version.version_number}) created.")
    return redirect('careers:smart_resume_studio')


@login_required
@require_POST
def reorder_resume_sections(request, resume_id):
    """
    Reorders resume sections dynamically.
    """
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    try:
        body = json.loads(request.body.decode('utf-8'))
        order = body.get('section_order', [])
        ResumeService.update_section_order(resume, order)
        return JsonResponse({'success': True, 'section_order': resume.get_section_order()})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def export_smart_resume_pdf(request, resume_id):
    """
    Exports clean, ATS-compliant PDF using ReportLab Platypus.
    """
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    pdf_bytes = PDFService.generate_resume_pdf(resume)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"{request.user.username}_{resume.template}_resume.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# =============================================================================
# AI Career Assistant
# =============================================================================

@login_required
def career_assistant_view(request):
    """
    AI Career Mentor chat interface (/career-studio/assistant/).
    Grounded in student's verified data, target track, and projects.
    """
    context = CareerAIAssistant.assemble_student_context(request.user)
    user_projects = ProjectIdea.objects.filter(user=request.user)

    return render(request, 'careers/studio/assistant.html', {
        'student_context': context,
        'projects': user_projects,
    })


@login_required
@require_POST
def career_assistant_query(request):
    """
    AJAX endpoint for AI Career Assistant queries.
    """
    try:
        body = json.loads(request.body.decode('utf-8'))
        prompt = body.get('prompt', '').strip()
        topic = body.get('topic', 'general_chat')
        project_id = body.get('project_id')

        if not prompt:
            return JsonResponse({'error': 'Prompt cannot be empty.'}, status=400)

        result = CareerAIAssistant.query_assistant(
            user=request.user,
            prompt=prompt,
            topic=topic,
            project_id=project_id,
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
