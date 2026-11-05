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
            # Prefill from existing user data
            student_profile = getattr(request.user, 'student_profile', None)
            full_name = student_profile.full_name if student_profile and student_profile.full_name else request.user.get_full_name() or request.user.username
            
            # Prefill completed courses and projects
            user_projects = []
            for gp in ProjectIdea.objects.filter(user=request.user)[:3]:
                user_projects.append({
                    'title': gp.title,
                    'technologies': gp.technology_stack,
                    'description': gp.description,
                    'github_url': '',
                })

            user_certifications = []
            for cert in Certificate.objects.filter(user=request.user)[:3]:
                user_certifications.append(f"{cert.title} - SkillSphere Verified")

            prefilled_data = {
                'contact': {
                    'full_name': full_name,
                    'headline': student_profile.bio if student_profile else 'Software Developer',
                    'email': request.user.email,
                    'phone': '',
                    'location': student_profile.country if student_profile else 'Remote',
                    'links': f"github.com/{request.user.username}"
                },
                'summary': f"Motivated software developer passionate about building high-quality, scalable applications. Proficient in modern programming practices, problem solving, and collaborative engineering.",
                'education': [
                    {
                        'school': 'University / College of Engineering',
                        'degree': 'Bachelor of Science in Computer Science',
                        'year': '2023 - 2026',
                        'gpa': '3.8 / 4.0'
                    }
                ],
                'skills': ['Python', 'Django', 'PostgreSQL', 'JavaScript', 'HTML5/CSS3', 'Git', 'REST APIs'],
                'projects': user_projects if user_projects else [
                    {
                        'title': 'SkillSphere Full-Stack Learning Platform',
                        'technologies': 'Python, Django, PostgreSQL, Bootstrap 5',
                        'description': 'Engineered a modular learning and career development web platform featuring automated progress tracking, AI roadmaps, and career readiness analytics.',
                        'github_url': 'https://github.com/example/skillsphere'
                    }
                ],
                'experience': [
                    {
                        'role': 'Software Engineering Intern',
                        'company': 'Tech Solutions Lab',
                        'dates': 'Summer 2025',
                        'description': 'Collaborated with engineering teammates to develop RESTful API endpoints and optimize database query latency by 25%.'
                    }
                ],
                'certifications': user_certifications if user_certifications else ['Python Core & Advanced - SkillSphere Verified'],
            }

            resume = Resume.objects.create(
                user=request.user,
                title='Master Tech Resume',
                template='ats',
                is_primary=True,
                resume_data=prefilled_data,
                ats_score=78
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
                    # Re-calculate ATS score
                    analysis = AIService.check_ats_readability(parsed)
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

    try:
        body = json.loads(request.body.decode('utf-8'))
        action_type = body.get('type')
        
        if action_type == 'summary':
            headline = body.get('headline', '')
            skills = body.get('skills', [])
            education = body.get('education', '')
            result = AIService.generate_resume_summary(headline, skills, education)
            return JsonResponse({'success': True, 'content': result})

        elif action_type == 'project':
            title = body.get('title', '')
            description = body.get('description', '')
            technologies = body.get('technologies', '')
            result = AIService.improve_project_description(title, description, technologies)
            return JsonResponse({'success': True, 'content': result})

        elif action_type == 'bullet':
            text = body.get('text', '')
            result = AIService.rewrite_resume_bullet(text)
            return JsonResponse({'success': True, 'content': result})

        elif action_type == 'ats_check':
            resume_data = body.get('resume_data', {})
            job_desc = body.get('job_description', '')
            analysis = AIService.check_ats_readability(resume_data, job_desc)
            return JsonResponse({'success': True, 'analysis': analysis})

        return JsonResponse({'error': 'Unknown action type'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
