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
        # Check rate limit
        allowed, retry_after = AIService.check_rate_limit(request.user.id)
        if not allowed:
            messages.error(request, f"Rate limit reached. Please wait {retry_after} seconds before generating another project specification.")
            return redirect('projects:generator')

        language = request.POST.get('language', 'Python').strip()[:50]
        level = request.POST.get('level', 'Intermediate').strip()[:50]
        category = request.POST.get('category', 'Web Development').strip()[:100]
        complexity = request.POST.get('complexity', 'Medium').strip()[:50]
        project_type = request.POST.get('project_type', 'Full-Stack Application').strip()[:100]

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


@login_required
def export_github_bundle_view(request, project_id):
    """
    Generates a full GitHub-ready repository package (README.md, src/, tests/, requirements.txt, .gitignore, LICENSE).
    Supports direct ZIP download or JSON payload with file previews.
    """
    import zipfile
    import io
    from django.http import HttpResponse, JsonResponse

    project = get_object_or_404(ProjectIdea, id=project_id, user=request.user)

    repo_slug = project.title.lower().replace(' ', '-').replace('&', 'and')
    repo_slug = ''.join(c for c in repo_slug if c.isalnum() or c == '-')
    if not repo_slug:
        repo_slug = f"project-{project.id}"

    student_name = request.user.profile.full_name if hasattr(request.user, 'profile') and request.user.profile.full_name else request.user.get_full_name() or request.user.username

    readme_content = f"""# {project.title}

[![SkillSphere Verified Project](https://img.shields.io/badge/SkillSphere-Verified%20Project-6366F1.svg)](https://skillsphere-cyan.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📌 Executive Summary
{project.description}

### Problem Statement
{project.problem_statement}

### Key Objectives
{project.objectives}

---

## 🛠️ Architecture & Technology Stack
- **Primary Category**: {project.category}
- **Engineering Complexity**: {project.difficulty}
- **Core Technologies**: {project.technology_stack}
- **Database Specifications**: {project.database_requirements}

### System Dataflow
```text
[ Client / UI ] ──▶ [ API Gateway / Controller ] ──▶ [ Business Domain Services ]
                                                              │
                                                              ▼
                                                   [ Persistent Store / DB ]
```

---

## ✨ Main Features
{project.main_features}

---

## 🚀 Getting Started & Local Setup

### Prerequisites
- Python 3.10+ / Node.js 18+
- Git & Virtual Environment

### Installation Steps
```bash
# 1. Clone this repository
git clone https://github.com/YOUR_USERNAME/{repo_slug}.git
cd {repo_slug}

# 2. Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

# 3. Install production dependencies
pip install -r requirements.txt

# 4. Execute automated test suite
pytest tests/
```

---

## 📅 Development Phases
{project.development_phases}

---

## 📜 Verification & Authorship
- **Author**: {student_name}
- **Blueprint Reference**: `{project.project_ref}`
- **SkillSphere Verified Credential Registry**: [SkillSphere Platform](https://skillsphere-cyan.vercel.app)

*Licensed under the [MIT License](LICENSE).*
"""

    main_py_content = f'''"""
{project.title} - Core Application Entry Point
Architected via SkillSphere Project Blueprint ({project.project_ref})
Author: {student_name}
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("{repo_slug}")

def initialize_application():
    """Initializes runtime components and validates environment configurations."""
    logger.info("Initializing {project.title} services...")
    logger.info("Tech stack: {project.technology_stack}")
    return True

def run():
    """Executes main application execution loop."""
    if not initialize_application():
        logger.error("Initialization failed.")
        sys.exit(1)
    logger.info("✓ System online and ready.")

if __name__ == "__main__":
    run()
'''

    test_main_py_content = f'''"""
Unit Tests for {project.title}
"""
import unittest
from src.main import initialize_application

class TestProjectInitialization(unittest.TestCase):
    def test_initialize_application(self):
        result = initialize_application()
        self.assertTrue(result, "Application should initialize successfully")

if __name__ == "__main__":
    unittest.main()
'''

    requirements_content = "pytest>=7.4.0\nrequests>=2.31.0\npython-dotenv>=1.0.0\n"
    gitignore_content = "__pycache__/\n*.py[cod]\n*$py.class\n.venv/\nenv/\n.env\n.DS_Store\nbuild/\ndist/\n*.egg-info/\n"
    license_content = f"""MIT License

Copyright (c) {student_name}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
"""

    ci_workflow_content = f"""name: CI Test & Code Quality

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pytest pytest-cov
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      - name: Lint with flake8
        run: |
          flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 src --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
      - name: Run automated test suite with pytest
        run: |
          pytest --cov=src tests/
"""

    dockerfile_content = f"""FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "src/main.py"]
"""

    docker_compose_content = f"""version: '3.8'

services:
  app:
    build: .
    volumes:
      - .:/app
    environment:
      - ENVIRONMENT=development
    ports:
      - "8000:8000"
"""

    powershell_commands = f"""# Windows PowerShell Quick Push
git init
git add .
git commit -m "feat: initial commit from SkillSphere Blueprint"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/{repo_slug}.git
git push -u origin main
"""

    # If format is JSON preview
    if request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'repo_slug': repo_slug,
            'readme': readme_content,
            'file_tree': [
                'README.md',
                'requirements.txt',
                '.gitignore',
                'LICENSE',
                'Dockerfile',
                'docker-compose.yml',
                '.github/workflows/ci.yml',
                'src/main.py',
                'tests/test_main.py'
            ],
            'quick_push_commands': f"git init\ngit add .\ngit commit -m 'feat: initial commit from SkillSphere Blueprint'\ngit branch -M main\ngit remote add origin https://github.com/YOUR_USERNAME/{repo_slug}.git\ngit push -u origin main",
            'powershell_commands': powershell_commands
        })

    # Generate ZIP bundle in-memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"{repo_slug}/README.md", readme_content)
        zip_file.writestr(f"{repo_slug}/requirements.txt", requirements_content)
        zip_file.writestr(f"{repo_slug}/.gitignore", gitignore_content)
        zip_file.writestr(f"{repo_slug}/LICENSE", license_content)
        zip_file.writestr(f"{repo_slug}/Dockerfile", dockerfile_content)
        zip_file.writestr(f"{repo_slug}/docker-compose.yml", docker_compose_content)
        zip_file.writestr(f"{repo_slug}/.github/workflows/ci.yml", ci_workflow_content)
        zip_file.writestr(f"{repo_slug}/src/main.py", main_py_content)
        zip_file.writestr(f"{repo_slug}/src/__init__.py", "")
        zip_file.writestr(f"{repo_slug}/tests/test_main.py", test_main_py_content)
        zip_file.writestr(f"{repo_slug}/tests/__init__.py", "")

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')

    response['Content-Disposition'] = f'attachment; filename="{repo_slug}-github-starter.zip"'
    return response


@login_required
def sync_project_to_portfolio_view(request, project_id):
    """
    Syncs the project into the user's public Developer Portfolio.
    """
    from django.http import JsonResponse
    from portfolios.models import Portfolio, PortfolioProject

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    project = get_object_or_404(ProjectIdea, id=project_id, user=request.user)
    github_url = request.POST.get('github_url', project.github_url).strip()
    demo_url = request.POST.get('demo_url', project.demo_url).strip()

    if github_url:
        project.github_url = github_url
    if demo_url:
        project.demo_url = demo_url
    project.status = 'completed'
    project.save()

    portfolio, _ = Portfolio.objects.get_or_create(
        user=request.user,
        defaults={'username': request.user.username, 'title': f"{request.user.username}'s Portfolio", 'is_public': True}
    )

    port_proj, created = PortfolioProject.objects.update_or_create(
        portfolio=portfolio,
        title=project.title,
        defaults={
            'description': project.description,
            'technologies': project.technology_stack,
            'features': project.main_features,
            'github_url': project.github_url,
            'live_url': project.demo_url,
            'is_featured': True
        }
    )

    award_user_xp(request.user, 30, f"Synced project to portfolio: {project.title}")

    return JsonResponse({
        'success': True,
        'message': f"Project '{project.title}' is now synced to your public Developer Portfolio!",
        'portfolio_url': portfolio.get_public_url()
    })

