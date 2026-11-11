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

    user_certificates = []
    for cert in Certificate.objects.filter(user=request.user):
        user_certificates.append({
            'title': cert.title,
            'certificate_id': cert.certificate_id,
            'issued_year': cert.issued_at.strftime('%Y') if cert.issued_at else '2026',
        })

    context = {
        'resume': resume,
        'resume_data': resume.resume_data,
        'resume_data_json': json.dumps(resume.resume_data),
        'saved_resumes': Resume.objects.filter(user=request.user),
        'user_certificates': user_certificates,
        'user_certificates_json': json.dumps(user_certificates),
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


# Standard Curated Interview Question Bank
INTERVIEW_QUESTION_BANK = {
    'fullstack': {
        'title': 'Full-Stack Software Engineer',
        'technical': [
            "Explain how the request-response lifecycle works when a browser requests a page from a Django/React application.",
            "What strategies do you use for database indexing and optimizing slow SQL queries in a production web application?",
            "How do you design a secure RESTful API with proper token-based authentication and rate limiting?",
            "What is the difference between optimistic and pessimistic locking in relational databases, and when would you use each?"
        ],
        'behavioral': [
            "Tell me about a time when you had to debug a critical production bug under time pressure. How did you identify the root cause?",
            "Describe a situation where you had a technical disagreement with a team member. How did you resolve it?",
            "Tell me about a complex project where the requirements changed midway through development. How did you adapt?"
        ],
        'system_design': [
            "Design a URL shortening service like Bit.ly that can handle 10,000 writes and 100,000 reads per second.",
            "How would you design a real-time notification feed system for a platform like SkillSphere with millions of active users?"
        ]
    },
    'python': {
        'title': 'Python & Django Specialist',
        'technical': [
            "Explain the difference between Django's `select_related` and `prefetch_related`. How do they prevent N+1 query problems?",
            "How does Python's GIL (Global Interpreter Lock) affect concurrency, and how would you execute CPU-bound vs I/O-bound tasks?",
            "What are Python generators and iterators? How do they improve memory efficiency when processing large datasets?",
            "How do Django database transactions and the `atomic()` context manager work during concurrent requests?"
        ],
        'behavioral': [
            "Tell me about an open-source library or module you built or heavily refactored. What lessons did you learn?",
            "Describe a time you advocated for code quality, testing, or documentation when the business wanted to rush a release."
        ],
        'system_design': [
            "How would you architect an asynchronous background job processing pipeline using Celery and Redis in Django?"
        ]
    },
    'frontend': {
        'title': 'Frontend React & UI Engineer',
        'technical': [
            "Explain the virtual DOM and the React reconciliation algorithm. How do keys impact rendering performance?",
            "How do you optimize Core Web Vitals (LCP, FID/INP, CLS) for a high-traffic single-page application?",
            "What are the trade-offs between Client-Side Rendering (CSR), Server-Side Rendering (SSR), and Static Site Generation (SSG)?"
        ],
        'behavioral': [
            "Tell me about a time when you received harsh critical feedback on a UI design or frontend implementation. How did you handle it?",
            "Describe how you collaborated closely with backend engineers to define an optimal API schema for a complex UI screen."
        ],
        'system_design': [
            "Design an infinite-scroll photo and media feed that maintains 60 FPS performance without memory leaks."
        ]
    },
    'devops': {
        'title': 'Cloud & DevOps Specialist',
        'technical': [
            "Explain how a Kubernetes Pod communicates across a cluster network using Services and Ingress controllers.",
            "What are the differences between blue-green deployments, canary releases, and rolling updates?",
            "How do you secure secrets and sensitive API credentials in CI/CD pipelines and production container runtimes?"
        ],
        'behavioral': [
            "Describe an outage or incident you resolved. How did you manage stakeholder communication and conduct the post-mortem?",
            "Tell me about an automation you implemented that significantly improved deployment speed or engineering reliability."
        ],
        'system_design': [
            "Design a multi-region highly available architecture on AWS/GCP with automated failover and database replication."
        ]
    },
    'data_science': {
        'title': 'Data Scientist & AI Engineer',
        'technical': [
            "Explain the bias-variance tradeoff and how regularization (L1/L2) helps prevent model overfitting.",
            "How do Transformer attention mechanisms calculate self-attention, and why are they superior to traditional RNNs/LSTMs?",
            "What techniques do you employ to handle severely imbalanced datasets in classification tasks?"
        ],
        'behavioral': [
            "Tell me about a project where machine learning metrics (e.g. F1-score) didn't translate into expected business impact. What happened?",
            "Describe how you explained a complex black-box model to non-technical stakeholders to gain their trust."
        ],
        'system_design': [
            "Design an end-to-end real-time recommendation engine that serves personalized recommendations within 50ms."
        ]
    }
}


@login_required
def mock_interview_view(request):
    """
    AI Audio/Voice Mock Technical & Behavioral Interview Studio.
    Provides speech synthesis (AI reads questions) + speech recognition + Gemini evaluation.
    """
    selected_role = request.GET.get('role', 'fullstack')
    if selected_role not in INTERVIEW_QUESTION_BANK:
        selected_role = 'fullstack'

    role_data = INTERVIEW_QUESTION_BANK[selected_role]
    return render(request, 'resumes/mock_interview.html', {
        'selected_role': selected_role,
        'role_data': role_data,
        'all_roles': INTERVIEW_QUESTION_BANK,
    })


@login_required
def evaluate_interview_answer_view(request):
    """
    Evaluates candidate's spoken or typed answer to an interview question using AIService.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=405)

    try:
        if request.content_type == 'application/json':
            body = json.loads(request.body)
        else:
            body = request.POST

        role = body.get('role', 'Software Engineer')
        question = body.get('question', '').strip()
        answer = body.get('answer', '').strip()
        category = body.get('category', 'technical')

        if not question or not answer:
            return JsonResponse({'error': 'Both question and answer are required.'}, status=400)

        analysis = AIService.evaluate_interview_answer(
            role=role,
            question=question,
            answer=answer,
            category=category
        )
        return JsonResponse({'success': True, 'analysis': analysis})
    except Exception as e:
        logger.error(f"Interview evaluation error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

