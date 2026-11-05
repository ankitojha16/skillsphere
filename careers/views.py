from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg

from .models import CareerProfile
from courses.models import Course, Enrollment
from learning.models import LessonProgress
from interviews.models import MockInterview
from assessments.models import AssessmentAttempt
from projects.models import ProjectIdea
from certificates.models import Certificate
from portfolios.models import Portfolio
from resumes.models import Resume

CAREER_PATHS = {
    'python-developer': {
        'name': 'Python Developer',
        'icon': 'terminal',
        'badge': 'High Demand',
        'summary': 'Develop server-side logic, automation pipelines, web frameworks, and robust backends with Python.',
        'required_skills': ['Python 3.12+', 'Django & DRF', 'PostgreSQL', 'Object-Oriented Programming', 'Git & CI/CD', 'Docker'],
        'recommended_courses': ['Python Core & Advanced', 'Mastering Django & REST Framework', 'Relational Database Architecture'],
        'suggested_projects': ['Asynchronous Task Orchestrator', 'Enterprise REST API Service', 'Automated Web Scraping Engine'],
        'important_tools': ['Poetry / Pipenv', 'pytest', 'Redis', 'Celery', 'Postman'],
        'learning_milestones': ['Master OOP & Metaprogramming', 'Build Production RESTful APIs', 'Database Indexing & Query Tuning', 'Microservices Deployment'],
        'interview_topics': ['GIL & Python Concurrency', 'Decorators & Generators', 'Django ORM query optimization', 'ACID transactions & indexing']
    },
    'fullstack-developer': {
        'name': 'Full Stack Developer',
        'icon': 'layers',
        'badge': 'Versatile',
        'summary': 'Engineer complete web applications from responsive frontends to scalable databases and backend APIs.',
        'required_skills': ['HTML5 / CSS3 / JavaScript', 'React or Vue', 'Python / Django', 'RESTful APIs', 'PostgreSQL', 'Cloud Deployment'],
        'recommended_courses': ['Modern Web Development Bootcamp', 'Mastering Django & REST Framework', 'Frontend Architecture'],
        'suggested_projects': ['Full-Stack E-Commerce Platform', 'Real-Time Collaboration Hub', 'Developer Portfolio & CMS'],
        'important_tools': ['VS Code', 'GitHub Actions', 'Docker', 'Webpack / Vite', 'Figma'],
        'learning_milestones': ['Build responsive fluid layouts', 'Design scalable relational schemas', 'State management & API consumption', 'End-to-end testing'],
        'interview_topics': ['CORS and Web Security (CSRF, XSS)', 'DOM rendering lifecycle', 'REST vs GraphQL', 'Caching strategies']
    },
    'frontend-developer': {
        'name': 'Frontend Developer',
        'icon': 'layout',
        'badge': 'UI Focused',
        'summary': 'Create fluid, accessible, high-performance web user interfaces with modern CSS and JavaScript frameworks.',
        'required_skills': ['Modern JavaScript (ES6+)', 'React / Next.js', 'CSS Grid & Flexbox', 'Responsive Design', 'Web Accessibility (a11y)'],
        'recommended_courses': ['Modern Web Development Bootcamp', 'Advanced JavaScript Concepts'],
        'suggested_projects': ['Interactive Analytics Dashboard', 'Accessible Component System', 'Interactive Quiz & Flashcard App'],
        'important_tools': ['Tailwind CSS', 'Bootstrap 5', 'Vite', 'Chrome DevTools', 'Jest'],
        'learning_milestones': ['Master CSS layouts & animations', 'Component-driven state architecture', 'Performance auditing (Lighthouse)', 'Cross-browser compatibility'],
        'interview_topics': ['Event bubbling & delegation', 'Virtual DOM reconciliation', 'CSS specificity & BEM', 'Web performance optimization']
    },
    'backend-developer': {
        'name': 'Backend Developer',
        'icon': 'server',
        'badge': 'Core Architecture',
        'summary': 'Architect high-throughput server backends, microservices, databases, authentication, and security.',
        'required_skills': ['Python / Java / Go', 'Django / FastAPI', 'PostgreSQL & SQL Tuning', 'API Security & OAuth2', 'Message Queues'],
        'recommended_courses': ['Mastering Django & REST Framework', 'Relational Database Architecture', 'CS Fundamentals'],
        'suggested_projects': ['High-Throughput Payment Gateway API', 'Distributed Event Bus', 'Role-Based Authentication Engine'],
        'important_tools': ['Docker', 'Nginx', 'Redis', 'PostgreSQL', 'Swagger / OpenAPI'],
        'learning_milestones': ['REST API design standards', 'Transaction isolation & locking', 'Authentication & JWT flows', 'Scalable caching patterns'],
        'interview_topics': ['Database indexing (B-Tree vs Hash)', 'CAP theorem & consistency models', 'Rate limiting algorithms', 'RESTful status codes & idempotent methods']
    },
    'data-analyst': {
        'name': 'Data Analyst',
        'icon': 'bar-chart-2',
        'badge': 'Analytics',
        'summary': 'Analyze business datasets, create actionable reports, and uncover trends using SQL, Python, and BI dashboards.',
        'required_skills': ['Advanced SQL', 'Python (Pandas, NumPy)', 'Data Visualization (Matplotlib, Seaborn)', 'Excel & Spreadsheets', 'Business Intelligence'],
        'recommended_courses': ['Python Core & Advanced', 'Data Science & Analysis with Python', 'Relational Database Architecture'],
        'suggested_projects': ['Customer Churn Analytics Dashboard', 'Sales Performance Pipeline', 'Exploratory Housing Market Analysis'],
        'important_tools': ['Jupyter Notebooks', 'Tableau / PowerBI', 'PostgreSQL', 'Git'],
        'learning_milestones': ['Complex SQL window functions & aggregates', 'Data cleaning & outlier imputation', 'Cohort & funnel analytics', 'Executive dashboard presentation'],
        'interview_topics': ['Window functions in SQL', 'Handling missing and noisy data', 'Correlation vs causation', 'A/B testing basics']
    },
    'data-scientist': {
        'name': 'Data Scientist',
        'icon': 'pie-chart',
        'badge': 'Predictive Modeling',
        'summary': 'Build predictive models, statistical frameworks, and machine learning pipelines to extract deep insights.',
        'required_skills': ['Applied Statistics & Probability', 'Python (Scikit-Learn, Pandas)', 'Feature Engineering', 'Model Evaluation & Cross-Validation'],
        'recommended_courses': ['Data Science & Analysis with Python', 'Artificial Intelligence & Machine Learning', 'Python Core & Advanced'],
        'suggested_projects': ['Loan Default Prediction Model', 'Recommendation Engine for Courses', 'NLP Sentiment Classification Pipeline'],
        'important_tools': ['Jupyter', 'Scikit-Learn', 'Pandas', 'Weights & Biases', 'Git'],
        'learning_milestones': ['Exploratory data analysis', 'Feature selection & engineering', 'Supervised regression & classification', 'Model validation & bias-variance tradeoff'],
        'interview_topics': ['Precision, Recall, ROC-AUC', 'Overfitting & Regularization (L1/L2)', 'Central Limit Theorem & p-values', 'Random Forest vs Gradient Boosting']
    },
    'ai-ml-engineer': {
        'name': 'AI/ML Engineer',
        'icon': 'cpu',
        'badge': 'Cutting Edge',
        'summary': 'Develop and deploy intelligent machine learning systems, deep learning models, and LLM applications in production.',
        'required_skills': ['Deep Learning (PyTorch / TensorFlow)', 'LLM Integration & Prompt Engineering', 'RAG Systems & Vector Databases', 'Model Deployment (FastAPI, Docker)'],
        'recommended_courses': ['Artificial Intelligence & Machine Learning', 'Python Core & Advanced', 'CS Fundamentals'],
        'suggested_projects': ['Document QA with RAG & Embeddings', 'Autonomous Code Review Assistant', 'Image Classification Service with PyTorch'],
        'important_tools': ['PyTorch', 'Hugging Face', 'ChromaDB / Pinecone', 'Docker', 'FastAPI'],
        'learning_milestones': ['Neural network backpropagation & optimization', 'Transformer architecture & attention', 'RAG pipeline development', 'Serving models via REST API'],
        'interview_topics': ['Self-attention mechanism in Transformers', 'Mitigating LLM hallucinations', 'Quantization & latency optimization', 'Gradient descent variants (Adam, SGD)']
    },
    'database-developer': {
        'name': 'Database Developer',
        'icon': 'database',
        'badge': 'Data Infrastructure',
        'summary': 'Design robust relational schemas, optimize complex query plans, and maintain high availability data stores.',
        'required_skills': ['Relational Schema Design (3NF)', 'Advanced SQL & Stored Procedures', 'PostgreSQL Query Planning (EXPLAIN ANALYZE)', 'ACID Transactions & Lock Management'],
        'recommended_courses': ['Relational Database Architecture', 'CS Fundamentals', 'Mastering Django & REST Framework'],
        'suggested_projects': ['High-Concurrency Banking Transaction Engine', 'Distributed Time-Series Storage Schema', 'Automated Database Backup & Replication Monitor'],
        'important_tools': ['PostgreSQL / pgAdmin', 'Redis', 'DBeaver', 'Docker'],
        'learning_milestones': ['Master ER modeling & normalization', 'Index optimization (B-tree, GIN, GiST)', 'Partitioning & replication', 'Database tuning for concurrency'],
        'interview_topics': ['ACID properties & isolation levels', 'Index types & execution plan analysis', 'Optimistic vs pessimistic locking', 'Database sharding vs replication']
    },
    'software-engineer': {
        'name': 'Software Engineer',
        'icon': 'code',
        'badge': 'Foundational',
        'summary': 'Apply software engineering fundamentals, algorithms, system design, and clean architecture to build reliable products.',
        'required_skills': ['Data Structures & Algorithms', 'Design Patterns (SOLID)', 'Object-Oriented Programming', 'Testing & CI/CD', 'Operating Systems & Networks'],
        'recommended_courses': ['Data Structures & Algorithms', 'CS Fundamentals', 'Python Core & Advanced'],
        'suggested_projects': ['Memory-Efficient In-Memory Key-Value Cache', 'Multi-Threaded HTTP Web Server', 'Algorithm Visualizer & Benchmarking Suite'],
        'important_tools': ['Git', 'Linux / Bash', 'Docker', 'GDB / Debuggers', 'CI/CD Pipelines'],
        'learning_milestones': ['Time & space complexity mastery (Big-O)', 'Clean architecture & refactoring', 'Concurrency & thread safety', 'Basic system design'],
        'interview_topics': ['Array vs LinkedList trade-offs', 'Tree traversal & Graph search (BFS/DFS)', 'SOLID design principles', 'Process vs Thread memory models']
    },
    'ui-ux-designer': {
        'name': 'UI/UX Designer',
        'icon': 'figma',
        'badge': 'User Centric',
        'summary': 'Craft intuitive user journeys, wireframes, interactive design prototypes, and design systems for web products.',
        'required_skills': ['Figma & Wireframing', 'User Research & Personas', 'Design Systems & Component Libraries', 'Interaction Design', 'HTML/CSS Basics'],
        'recommended_courses': ['Modern Web Development Bootcamp', 'Frontend Architecture'],
        'suggested_projects': ['SkillSphere Complete Design System & Prototype', 'Mobile Learning App UX Redesign', 'Accessible SaaS Onboarding Flow'],
        'important_tools': ['Figma', 'FigJam', 'Pen & Paper', 'Contrast Checkers'],
        'learning_milestones': ['Information architecture & user flows', 'Typography, spacing, and color theory', 'Interactive micro-interactions & prototyping', 'Usability testing & heuristic review'],
        'interview_topics': ['Design thinking process', 'Conducting usability testing', 'Accessibility contrast ratios (WCAG AA)', 'Translating design tokens to developer handoff']
    }
}


def compute_career_stats(user):
    """Calculates factual career metrics using user data."""
    # 1. Courses completed
    courses_completed = 0
    enrollments = Enrollment.objects.filter(user=user).select_related('course')
    for enr in enrollments:
        prog = enr.course.get_progress_for_user(user)
        if prog['total'] > 0 and prog['completed'] >= prog['total']:
            courses_completed += 1

    # 2. Total skills acquired
    completed_lessons_count = LessonProgress.objects.filter(user=user, is_completed=True).count()
    skills_count = max(completed_lessons_count // 3, courses_completed * 4)
    if skills_count == 0 and completed_lessons_count > 0:
        skills_count = completed_lessons_count

    # 3. Projects completed
    projects_completed = ProjectIdea.objects.filter(user=user).count()

    # 4. Certificates earned
    certificates_earned = Certificate.objects.filter(user=user).count()

    # 5. Mock interviews completed
    interviews_completed = MockInterview.objects.filter(user=user, is_completed=True).count()
    avg_interview_score = MockInterview.objects.filter(user=user, is_completed=True).aggregate(Avg('overall_score'))['overall_score__avg'] or 0

    # 6. Resume completion percentage
    latest_resume = Resume.objects.filter(user=user).first()
    resume_completion = 0
    if latest_resume:
        data = latest_resume.resume_data or {}
        fields = ['summary', 'skills', 'education', 'projects', 'experience']
        filled = sum(1 for f in fields if data.get(f))
        resume_completion = int((filled / len(fields)) * 100)

    # 7. Portfolio completion percentage
    portfolio = Portfolio.objects.filter(user=user).first()
    portfolio_completion = 0
    if portfolio:
        checks = [
            bool(portfolio.about),
            bool(portfolio.username),
            portfolio.projects.exists(),
            bool(portfolio.template),
            portfolio.is_public
        ]
        portfolio_completion = int((sum(checks) / len(checks)) * 100)

    return {
        'courses_completed': courses_completed,
        'skills_count': skills_count,
        'projects_completed': projects_completed,
        'certificates_earned': certificates_earned,
        'interviews_completed': interviews_completed,
        'avg_interview_score': round(avg_interview_score, 1),
        'resume_completion': resume_completion,
        'portfolio_completion': portfolio_completion,
        'has_resume': latest_resume is not None,
        'has_portfolio': portfolio is not None,
    }


def compute_career_readiness(user, stats):
    """
    Computes transparent weighted career readiness score (0-100):
    - Skills (25%)
    - Projects (25%)
    - Learning Completion (15%)
    - Resume (15%)
    - Portfolio (10%)
    - Interview Practice (10%)
    """
    # Skills score (capped at 100)
    skills_score = min(stats['skills_count'] * 12, 100)

    # Projects score (aiming for 3+ portfolio-grade projects)
    projects_score = min(stats['projects_completed'] * 34, 100)

    # Course completion score (aiming for 2+ completed courses)
    course_score = min(stats['courses_completed'] * 50, 100)

    # Resume readiness
    resume_score = stats['resume_completion']

    # Portfolio readiness
    portfolio_score = stats['portfolio_completion']

    # Interview practice score
    interview_score = min(stats['interviews_completed'] * 40, 100)
    if stats['interviews_completed'] > 0 and stats['avg_interview_score'] > 0:
        interview_score = int((interview_score * 0.5) + (stats['avg_interview_score'] * 0.5))

    weighted_total = (
        (skills_score * 0.25) +
        (projects_score * 0.25) +
        (course_score * 0.15) +
        (resume_score * 0.15) +
        (portfolio_score * 0.10) +
        (interview_score * 0.10)
    )
    overall_score = round(weighted_total, 1)

    strengths = []
    improvements = []

    if skills_score >= 60:
        strengths.append(f"Strong foundation of acquired technical competencies ({stats['skills_count']} technical skills verified).")
    else:
        improvements.append("Complete more course modules and practical lessons to expand your verified technical skill bank.")

    if projects_score >= 60:
        strengths.append(f"Demonstrated practical development capability with {stats['projects_completed']} completed projects.")
    else:
        improvements.append("Build and showcase at least 2 complete, functional projects in the Project Generator or Portfolio.")

    if resume_score >= 70:
        strengths.append("Professional resume is actively configured with structured experience and technical tags.")
    else:
        improvements.append("Complete your profile in the AI Resume Builder to generate an ATS-ready CV.")

    if portfolio_score >= 70:
        strengths.append("Online developer portfolio is configured and showcases your work to recruiters.")
    else:
        improvements.append("Set up your public Portfolio at /portfolio/ and publish it for employer visibility.")

    if interview_score >= 60:
        strengths.append(f"Solid interview practice record with {stats['interviews_completed']} completed mock interview sessions.")
    else:
        improvements.append("Practice technical coding and conceptual questions in the Mock Interview Hub.")

    return {
        'overall_score': overall_score,
        'skills_score': skills_score,
        'projects_score': projects_score,
        'course_score': course_score,
        'resume_score': resume_score,
        'portfolio_score': portfolio_score,
        'interview_score': interview_score,
        'strengths': strengths,
        'improvements': improvements,
    }


@login_required
def career_hub_view(request):
    profile, _ = CareerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.professional_headline = request.POST.get('headline', '').strip()
        profile.professional_summary = request.POST.get('summary', '').strip()
        profile.target_career_path = request.POST.get('target_career_path', 'fullstack-developer')
        profile.save()
        messages.success(request, "Career profile updated successfully!")
        return redirect('careers:hub')

    stats = compute_career_stats(request.user)
    readiness = compute_career_readiness(request.user, stats)
    active_path = CAREER_PATHS.get(profile.target_career_path, CAREER_PATHS['fullstack-developer'])

    context = {
        'profile': profile,
        'stats': stats,
        'readiness': readiness,
        'career_paths': CAREER_PATHS,
        'active_path': active_path,
    }
    return render(request, 'careers/career_hub.html', context)


@login_required
def career_path_detail_view(request, slug):
    path_data = CAREER_PATHS.get(slug)
    if not path_data:
        messages.error(request, "Career path not found.")
        return redirect('careers:hub')

    profile, _ = CareerProfile.objects.get_or_create(user=request.user)
    is_target = (profile.target_career_path == slug)

    if request.method == 'POST' and 'set_target' in request.POST:
        profile.target_career_path = slug
        profile.save()
        messages.success(request, f"Set {path_data['name']} as your target career path!")
        return redirect('careers:path_detail', slug=slug)

    context = {
        'path': path_data,
        'slug': slug,
        'is_target': is_target,
    }
    return render(request, 'careers/career_path_detail.html', context)


@login_required
def career_analytics_view(request):
    profile, _ = CareerProfile.objects.get_or_create(user=request.user)
    stats = compute_career_stats(request.user)
    readiness = compute_career_readiness(request.user, stats)
    active_path = CAREER_PATHS.get(profile.target_career_path, CAREER_PATHS['fullstack-developer'])

    context = {
        'profile': profile,
        'stats': stats,
        'readiness': readiness,
        'active_path': active_path,
    }
    return render(request, 'careers/career_analytics.html', context)
