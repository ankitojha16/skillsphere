import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages

from .models import Resume
from accounts.models import StudentProfile
from courses.models import Course, Enrollment
from projects.models import ProjectIdea
from certificates.models import Certificate
from services.ai_service import AIService
from services.pdf_service import PDFService

@login_required
def resume_list_view(request):
    resumes = Resume.objects.filter(user=request.user)
    return render(request, 'resumes/resume_list.html', {'resumes': resumes})


@login_required
def resume_builder_view(request, pk=None):
    if pk:
        resume = get_object_or_404(Resume, pk=pk, user=request.user)
    else:
        # Check if user has an existing resume or create initial default prefilled one
        resume = Resume.objects.filter(user=request.user, is_primary=True).first()
        if not resume:
            resume = Resume.objects.filter(user=request.user).first()
        
        if not resume:
            # Prefill from existing user data (Strict Zero-Fabrication Policy)
            profile = getattr(request.user, 'profile', None)
            full_name = profile.full_name if profile and profile.full_name else request.user.get_full_name() or request.user.username
            headline = profile.career_goal if profile and profile.career_goal else 'Software Developer'

            # Real education from profile if provided by the student
            user_education = []
            if profile and profile.institution:
                degree_display = profile.get_education_level_display() if hasattr(profile, 'get_education_level_display') else 'Degree Program'
                user_education.append({
                    'school': profile.institution,
                    'degree': degree_display,
                    'year': '',
                    'gpa': ''  # NEVER invent a fake GPA
                })

            # Real skills mapped from student profile interests
            interest_map = {
                'python': 'Python', 'cpp': 'C/C++', 'java': 'Java', 'web_dev': 'Web Development',
                'dsa': 'Data Structures & Algorithms', 'ai': 'Artificial Intelligence',
                'data_science': 'Data Science', 'dbms': 'PostgreSQL / SQL'
            }
            user_skills = []
            if profile:
                for slug in profile.get_interests_list():
                    user_skills.append(interest_map.get(slug, slug.title()))
            if not user_skills:
                user_skills = ['Python', 'Git', 'Problem Solving']

            # Real user-saved projects ONLY (no fabricated accomplishments)
            user_projects = []
            for gp in ProjectIdea.objects.filter(user=request.user)[:3]:
                user_projects.append({
                    'title': gp.title,
                    'technologies': gp.technology_stack,
                    'description': gp.description,
                    'github_url': getattr(gp, 'github_url', ''),
                })

            # Real user certifications ONLY (no fabricated certificates)
            user_certifications = []
            for cert in Certificate.objects.filter(user=request.user)[:3]:
                user_certifications.append(f"{cert.title} - SkillSphere Verified")

            career_goal_initial = (profile.career_goal if (profile and profile.career_goal) else headline) or "Software Developer"
            target_industry_initial = "Technology & Software Engineering"

            prefilled_data = {
                'contact': {
                    'full_name': full_name,
                    'headline': headline,
                    'email': request.user.email,
                    'phone': '',
                    'location': '',
                    'links': f"github.com/{request.user.username}"
                },
                'career_goal': career_goal_initial,
                'target_industry': target_industry_initial,
                'career_objective': f"Dedicated {headline.lower()} with hands-on practice in modern software engineering principles, eager to contribute and build impactful applications.",
                'short_term_goals': [
                    "Master core algorithms, data structures, and system design patterns",
                    "Build and deploy scalable full-stack applications with test automation",
                    "Contribute to open-source systems and collaborate in agile development workflows"
                ],
                'summary': f"Dedicated {headline.lower()} with hands-on practice in modern software engineering principles, eager to contribute and build impactful applications.",
                'education': user_education,
                'skills': user_skills,
                'projects': user_projects,
                'experience': [],  # ZERO fabricated experience
                'certifications': user_certifications,  # ZERO fabricated certificates
            }

            resume = Resume.objects.create(
                user=request.user,
                title='Master Tech Resume',
                template='ats',
                is_primary=True,
                resume_data=prefilled_data,
                ats_score=75
            )

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'save_resume':
            resume.title = request.POST.get('title', 'My Resume').strip()
            resume.template = request.POST.get('template', 'ats')

            # Parse JSON payload from client editor
            data_raw = request.POST.get('resume_data_json')
            if data_raw:
                try:
                    parsed = json.loads(data_raw)
                    resume.resume_data = parsed
                    # Re-calculate ATS score with user isolation
                    analysis = AIService.check_ats_readability(parsed, user_id=request.user.id)
                    resume.ats_score = analysis['score']
                except Exception as e:
                    messages.error(request, f"Error parsing resume JSON: {e}")

            resume.save()
            messages.success(request, "Resume saved successfully!")
            return redirect('resumes:builder_edit', pk=resume.pk)

    context = {
        'resume': resume,
        'resume_data': resume.resume_data,
        'resume_data_json': json.dumps(resume.resume_data),
        'saved_resumes': Resume.objects.filter(user=request.user),
    }
    return render(request, 'resumes/builder.html', context)


@login_required
def export_resume_pdf_view(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    pdf_bytes = PDFService.generate_resume_pdf(resume)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"{resume.user.username}_resume.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def ai_improve_view(request):
    """AJAX endpoint for AI-assisted resume copy improvements."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    # Check rate limit
    allowed, retry_after = AIService.check_rate_limit(request.user.id)
    if not allowed:
        return JsonResponse({'error': f'Rate limit reached. Please wait {retry_after} seconds before requesting AI improvements.'}, status=429)

    try:
        body = json.loads(request.body.decode('utf-8'))
        action_type = body.get('type')
        
        if action_type in ('career_goal', 'objective'):
            target_role = body.get('target_role', '') or body.get('career_goal', '') or body.get('headline', '')
            target_industry = body.get('target_industry', '')
            skills = body.get('skills', [])
            education = body.get('education', '')
            result = AIService.generate_career_goal_and_objective(
                target_role=target_role,
                target_industry=target_industry,
                skills=skills,
                education=education,
                user_id=request.user.id
            )
            return JsonResponse({'success': True, 'content': result['career_objective'], 'data': result})

        elif action_type == 'summary':
            headline = body.get('headline', '')
            skills = body.get('skills', [])
            education = body.get('education', '')
            result = AIService.generate_resume_summary(headline, skills, education, user_id=request.user.id)
            return JsonResponse({'success': True, 'content': result})

        elif action_type == 'project':
            title = body.get('title', '')
            description = body.get('description', '')
            technologies = body.get('technologies', '')
            result = AIService.improve_project_description(title, description, technologies, user_id=request.user.id)
            return JsonResponse({'success': True, 'content': result})

        elif action_type == 'bullet':
            text = body.get('text', '')
            result = AIService.rewrite_resume_bullet(text, user_id=request.user.id)
            return JsonResponse({'success': True, 'content': result})

        elif action_type == 'ats_check':
            resume_data = body.get('resume_data', {})
            job_desc = body.get('job_description', '')
            analysis = AIService.check_ats_readability(resume_data, job_desc, user_id=request.user.id)
            return JsonResponse({'success': True, 'analysis': analysis})

        return JsonResponse({'error': 'Unknown action type'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
