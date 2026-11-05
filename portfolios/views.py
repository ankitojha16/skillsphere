from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404, JsonResponse
from django.contrib import messages

from .models import Portfolio, PortfolioProject
from projects.models import ProjectIdea
from certificates.models import Certificate
from learning.models import LessonProgress

@login_required
def portfolio_builder_view(request):
    portfolio, created = Portfolio.objects.get_or_create(
        user=request.user,
        defaults={
            'username': request.user.username,
            'title': f"{request.user.get_full_name() or request.user.username}'s Portfolio",
            'about': "Passionate software engineer focused on building robust, accessible, and high-performance applications.",
            'template': 'modern',
            'theme': 'dark',
            'accent_color': '#8B5CF6',
            'is_public': False,
        }
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_settings':
            portfolio.title = request.POST.get('title', '').strip() or portfolio.title
            portfolio.about = request.POST.get('about', '').strip()
            portfolio.template = request.POST.get('template', 'modern')
            portfolio.theme = request.POST.get('theme', 'dark')
            portfolio.accent_color = request.POST.get('accent_color', '#8B5CF6')
            portfolio.github_url = request.POST.get('github_url', '').strip()
            portfolio.linkedin_url = request.POST.get('linkedin_url', '').strip()
            portfolio.website_url = request.POST.get('website_url', '').strip()
            portfolio.twitter_url = request.POST.get('twitter_url', '').strip()
            portfolio.show_skills = 'show_skills' in request.POST
            portfolio.show_certifications = 'show_certifications' in request.POST
            portfolio.is_public = 'is_public' in request.POST
            portfolio.save()
            messages.success(request, "Portfolio preferences saved successfully!")
            return redirect('portfolios:builder')

        elif action == 'add_project':
            title = request.POST.get('project_title', '').strip()
            desc = request.POST.get('project_desc', '').strip()
            tech = request.POST.get('project_tech', '').strip()
            github = request.POST.get('project_github', '').strip()
            live = request.POST.get('project_live', '').strip()
            features = request.POST.get('project_features', '').strip()
            is_featured = 'is_featured' in request.POST
            thumbnail = request.FILES.get('thumbnail')

            if title and desc:
                order = portfolio.projects.count()
                PortfolioProject.objects.create(
                    portfolio=portfolio,
                    title=title,
                    description=desc,
                    technologies=tech,
                    github_url=github,
                    live_url=live,
                    features=features,
                    is_featured=is_featured,
                    thumbnail=thumbnail,
                    display_order=order
                )
                messages.success(request, f"Project '{title}' added to your portfolio!")
            else:
                messages.error(request, "Project title and description are required.")
            return redirect('portfolios:builder')

        elif action == 'import_skillsphere_project':
            project_id = request.POST.get('skillsphere_project_id')
            if project_id:
                gen_proj = ProjectIdea.objects.filter(id=project_id, user=request.user).first()
                if gen_proj:
                    order = portfolio.projects.count()
                    PortfolioProject.objects.create(
                        portfolio=portfolio,
                        title=gen_proj.title,
                        description=gen_proj.description,
                        technologies=gen_proj.technology_stack,
                        features=gen_proj.main_features,
                        display_order=order,
                        is_featured=True
                    )
                    messages.success(request, f"Imported '{gen_proj.title}' into your portfolio!")
            return redirect('portfolios:builder')

    # Get available projects for import
    existing_imported_titles = portfolio.projects.values_list('title', flat=True)
    available_generated = ProjectIdea.objects.filter(user=request.user).exclude(title__in=existing_imported_titles)
    
    # User's certificates
    user_certificates = Certificate.objects.filter(user=request.user)

    context = {
        'portfolio': portfolio,
        'projects': portfolio.projects.all(),
        'available_generated': available_generated,
        'user_certificates': user_certificates,
    }
    return render(request, 'portfolios/builder.html', context)


@login_required
def delete_project_view(request, project_id):
    project = get_object_or_404(PortfolioProject, id=project_id, portfolio__user=request.user)
    if request.method == 'POST':
        title = project.title
        project.delete()
        messages.success(request, f"Project '{title}' removed from portfolio.")
    return redirect('portfolios:builder')


def public_portfolio_view(request, username):
    portfolio = get_object_or_404(Portfolio, username=username)

    # Privacy enforcement: if not public and not the owner
    if not portfolio.is_public:
        if not (request.user.is_authenticated and request.user == portfolio.user):
            raise Http404("This portfolio is private or does not exist.")

    projects = portfolio.projects.all()
    certificates = Certificate.objects.filter(user=portfolio.user, verification_status=True) if portfolio.show_certifications else []

    # Student verified skills
    student_profile = getattr(portfolio.user, 'student_profile', None)
    avatar_url = student_profile.avatar_url if student_profile else "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80"
    full_name = student_profile.full_name if (student_profile and student_profile.full_name) else portfolio.user.get_full_name() or portfolio.user.username

    # Determine template to render
    template_map = {
        'minimal': 'portfolios/templates/minimal.html',
        'modern': 'portfolios/templates/modern.html',
        'creative': 'portfolios/templates/creative.html',
    }
    target_template = template_map.get(portfolio.template, 'portfolios/templates/modern.html')

    context = {
        'portfolio': portfolio,
        'projects': projects,
        'certificates': certificates,
        'full_name': full_name,
        'avatar_url': avatar_url,
        'is_owner': request.user.is_authenticated and (request.user == portfolio.user),
    }
    return render(request, target_template, context)


@login_required
def preview_portfolio_view(request):
    portfolio, _ = Portfolio.objects.get_or_create(user=request.user, defaults={'username': request.user.username})
    return public_portfolio_view(request, portfolio.username)
