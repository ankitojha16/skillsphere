from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ProjectIdea
from services.ai_service import AIService
from gamification.services import award_user_xp

@login_required
def generator_view(request):
    generated_project = None

    if request.method == 'POST':
        language = request.POST.get('language', 'Python')
        level = request.POST.get('level', 'Intermediate')
        category = request.POST.get('category', 'Web Development')
        complexity = request.POST.get('complexity', 'Medium')
        project_type = request.POST.get('project_type', 'Full-Stack Application')

        generated_project = AIService.generate_project_idea(
            language=language,
            level=level,
            category=category,
            complexity=complexity,
            project_type=project_type
        )
        generated_project['language'] = language
        generated_project['level'] = level
        generated_project['category'] = category

    saved_count = ProjectIdea.objects.filter(user=request.user).count()

    return render(request, 'projects/generator.html', {
        'generated_project': generated_project,
        'saved_count': saved_count,
        'categories': ProjectIdea.CATEGORY_CHOICES,
        'difficulties': ProjectIdea.DIFFICULTY_CHOICES,
    })


@login_required
def save_project_view(request):
    if request.method != 'POST':
        return redirect('projects:generator')

    title = request.POST.get('title', 'New Project Idea')
    category = request.POST.get('category', 'Web Development')
    difficulty = request.POST.get('difficulty', 'Intermediate')
    tech_stack = request.POST.get('technology_stack', 'Python, Django')
    description = request.POST.get('description', '')
    problem_statement = request.POST.get('problem_statement', '')
    objectives = request.POST.get('objectives', '')
    main_features = request.POST.get('main_features', '')
    db_requirements = request.POST.get('database_requirements', '')
    development_phases = request.POST.get('development_phases', '')

    github_url = request.POST.get('github_url', '').strip()
    demo_url = request.POST.get('demo_url', '').strip()

    project = ProjectIdea.objects.create(
        user=request.user,
        title=title,
        category=category,
        difficulty=difficulty,
        technology_stack=tech_stack,
        description=description,
        problem_statement=problem_statement,
        objectives=objectives,
        main_features=main_features,
        database_requirements=db_requirements,
        development_phases=development_phases,
        github_url=github_url,
        demo_url=demo_url,
    )

    award_user_xp(request.user, 20, f"Saved portfolio project idea: {title}")
    messages.success(request, f"Project '{title}' (ID: {project.project_ref}) saved to your collection!")
    return redirect('projects:saved')


@login_required
def saved_projects_view(request):
    projects = ProjectIdea.objects.filter(user=request.user)

    category_filter = request.GET.get('category', 'all')
    if category_filter and category_filter != 'all':
        projects = projects.filter(category=category_filter)

    return render(request, 'projects/saved.html', {
        'projects': projects,
        'category_choices': ProjectIdea.CATEGORY_CHOICES,
        'selected_category': category_filter,
    })


@login_required
def project_detail_view(request, project_id=None, project_ref=None):
    if project_ref:
        project = get_object_or_404(ProjectIdea, project_ref=project_ref, user=request.user)
    else:
        project = get_object_or_404(ProjectIdea, id=project_id, user=request.user)

    # Handle status or link updates
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_github = request.POST.get('github_url', '').strip()
        new_demo = request.POST.get('demo_url', '').strip()

        if new_status in dict(ProjectIdea.STATUS_CHOICES):
            project.status = new_status
        project.github_url = new_github
        project.demo_url = new_demo
        project.save()
        messages.success(request, f"Project '{project.title}' updated successfully!")
        return redirect('projects:detail', project_id=project.id)

    return render(request, 'projects/detail.html', {'project': project})


@login_required
def project_delete_view(request, project_id):
    project = get_object_or_404(ProjectIdea, id=project_id, user=request.user)
    if request.method == 'POST':
        title = project.title
        project.delete()
        messages.info(request, f"Project '{title}' removed from your saved collection.")
    return redirect('projects:saved')
