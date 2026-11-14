"""
SkillSphere Career Studio — AI Career Assistant.
Provides context-aware student career mentoring grounded strictly in verified
student records, chosen career tracks, skill gap reports, and active projects.
Features circuit-breaker resilience, rate limiting, and an offline Knowledge Engine fallback.
"""

import json
import logging
from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone

from careers.models import StudentCareerGoal, SkillGapReport, StudentSkillEvidence, CareerTrack
from projects.models import ProjectIdea
from services.ai_service import AIService

logger = logging.getLogger('skillsphere.careers')


class CareerAIAssistant:
    """
    Intelligent Career Mentor grounded in student data.
    """

    RATE_LIMIT_SECONDS = 5
    MAX_REQUESTS_PER_MINUTE = 12

    @classmethod
    def check_rate_limit(cls, user_id: int) -> tuple[bool, int]:
        """
        Rate limiting check per user.
        """
        now = int(timezone.now().timestamp())
        key = f"career_ai_limit_{user_id}"
        timestamps = cache.get(key, [])
        # filter last 60 seconds
        valid_ts = [ts for ts in timestamps if now - ts < 60]

        if len(valid_ts) >= cls.MAX_REQUESTS_PER_MINUTE:
            oldest = valid_ts[0]
            retry_after = 60 - (now - oldest)
            return False, max(1, retry_after)

        valid_ts.append(now)
        cache.set(key, valid_ts, 65)
        return True, 0

    @classmethod
    def assemble_student_context(cls, user: User) -> Dict[str, Any]:
        """
        Aggregates live verified platform data to ground AI responses.
        """
        context = {
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'target_track': 'Software Developer',
            'match_score': 0,
            'demonstrated_skills': [],
            'missing_skills': [],
            'active_projects': [],
            'verified_evidence_count': 0,
        }

        # 1. Career Goal
        goal = StudentCareerGoal.objects.filter(user=user).select_related('primary_track').first()
        if goal and goal.primary_track:
            context['target_track'] = goal.primary_track.title
            context['track_slug'] = goal.primary_track.slug
            context['target_timeline'] = f"{goal.target_timeline_months} months"

            # 2. Skill Gap Report
            report = SkillGapReport.objects.filter(user=user, track=goal.primary_track).first()
            if report:
                context['match_score'] = report.overall_match_percentage
                context['demonstrated_skills'] = [s.get('skill_name') for s in report.demonstrated_skills[:6]]
                context['missing_skills'] = [s.get('skill_name') for s in report.missing_skills[:5]]

        # 3. Evidence count
        context['verified_evidence_count'] = StudentSkillEvidence.objects.filter(user=user, is_verified=True).count()

        # 4. Active projects
        projects = ProjectIdea.objects.filter(user=user)[:3]
        for p in projects:
            context['active_projects'].append({
                'title': p.title,
                'status': p.get_workflow_status_display(),
                'technologies': p.technology_stack,
            })

        return context

    @classmethod
    def query_assistant(
        cls,
        user: User,
        prompt: str,
        topic: str = 'general_chat',
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processes a career mentoring query from the student.
        Grounded in student context with fallback to deterministic knowledge engine.
        """
        allowed, retry_after = cls.check_rate_limit(user.id)
        if not allowed:
            return {
                'success': False,
                'error': f"Rate limit reached. Please wait {retry_after}s before asking another question.",
                'content': None,
                'grounded_context': None,
            }

        student_ctx = cls.assemble_student_context(user)

        # Include specific project details if requested
        if project_id:
            try:
                target_project = ProjectIdea.objects.get(id=project_id, user=user)
                student_ctx['target_project'] = {
                    'title': target_project.title,
                    'category': target_project.category,
                    'status': target_project.get_workflow_status_display(),
                    'tech': target_project.technology_stack,
                    'problem': target_project.problem_statement,
                }
            except ProjectIdea.DoesNotExist:
                pass

        # Build grounded prompt
        system_prompt = (
            f"You are the SkillSphere Career Studio AI Mentor. "
            f"You are advising student '{student_ctx['full_name']}' who is targeting the career track: '{student_ctx['target_track']}'. "
            f"Student context:\n"
            f"- Readiness match: {student_ctx['match_score']}%\n"
            f"- Demonstrated skills: {', '.join(student_ctx['demonstrated_skills']) or 'None yet verified'}\n"
            f"- Missing required skills: {', '.join(student_ctx['missing_skills']) or 'None'}\n"
            f"- Verified credentials on platform: {student_ctx['verified_evidence_count']}\n"
            f"- Active projects: {json.dumps(student_ctx['active_projects'])}\n\n"
            f"STRICT RULES:\n"
            f"1. Never hallucinate skills the student has not verified.\n"
            f"2. Emphasize that taking courses alone does not prove proficiency; real projects with clean Git histories and test suites do.\n"
            f"3. Provide concrete, actionable, realistic advice formatted in clean GitHub markdown.\n"
            f"4. If advising on interview preparation, provide structured answers with STAR method principles."
        )

        full_query = f"{system_prompt}\n\nStudent Question:\n{prompt}"

        # Attempt AI Service call
        try:
            ai_resp = AIService.generate_text(
                prompt=prompt,
                system_instruction=system_prompt,
            )
            if ai_resp and len(ai_resp.strip()) > 30:
                return {
                    'success': True,
                    'content': ai_resp.strip(),
                    'source': 'gemini_ai',
                    'grounded_context': student_ctx,
                }
        except Exception as e:
            logger.info(f"Gemini call unavailable or failed ({e}), using Offline Knowledge Engine.")

        # Graceful Fallback: High Quality Offline Knowledge Engine
        fallback_content = cls._generate_knowledge_engine_response(student_ctx, prompt, topic)
        return {
            'success': True,
            'content': fallback_content,
            'source': 'offline_knowledge_engine',
            'grounded_context': student_ctx,
        }

    @classmethod
    def _generate_knowledge_engine_response(
        cls,
        ctx: Dict[str, Any],
        prompt: str,
        topic: str
    ) -> str:
        """
        Offline deterministic career knowledge engine.
        Provides comprehensive, relevant advice tailored to the student's exact track and gap.
        """
        track = ctx.get('target_track', 'Software Developer')
        score = ctx.get('match_score', 0)
        missing = ctx.get('missing_skills', [])
        demonstrated = ctx.get('demonstrated_skills', [])
        prompt_lower = prompt.lower()

        if 'project' in prompt_lower or topic == 'project_architecture':
            proj = ctx.get('target_project')
            proj_title = proj.get('title') if proj else "Production Portfolio Project"
            return (
                f"### 🛠️ Architecture Recommendation for **{track}**\n\n"
                f"**Project**: {proj_title}\n\n"
                f"To establish verified proof of competence for hiring managers, build with this 3-tier architecture:\n\n"
                f"1. **Core Data & Persistence Layer**:\n"
                f"   - Relational database schema with clean foreign keys, indices on foreign keys and timestamps.\n"
                f"   - Avoid N+1 query traps using `select_related()` and `prefetch_related()`.\n\n"
                f"2. **Service & Domain Layer**:\n"
                f"   - Separate business logic from view controllers. Implement clean domain services.\n"
                f"   - Add unit tests for edge cases (zero inputs, boundary states, authorization checks).\n\n"
                f"3. **Observability & Deployment**:\n"
                f"   - Containerize with Docker and run automated linting (flake8/black/eslint) in GitHub Actions CI.\n"
                f"   - Deploy live with HTTPS and link the GitHub repository in your SkillSphere Studio."
            )

        elif 'interview' in prompt_lower or topic == 'interview_prep':
            return (
                f"### 🎯 Technical & Behavioral Interview Preparation for **{track}**\n\n"
                f"Based on your current readiness match of **{score}%**, here is a targeted prep strategy:\n\n"
                f"#### Core Technical Questions to Expect:\n"
                f"1. **Architecture & Tradeoffs**: Explain the trade-offs between relational normalization vs indexing for high-read APIs.\n"
                f"2. **Debugging**: Walk through how you diagnosed and resolved the most complex bug or performance bottleneck in your projects.\n"
                f"3. **Concurrency & State**: How do you prevent race conditions or stale reads in multi-user environments?\n\n"
                f"#### STAR Method Framework for Behavioral Rounds:\n"
                f"- **Situation**: State the team or project context in 2 sentences.\n"
                f"- **Task**: What exact problem were you tasked with solving?\n"
                f"- **Action**: Highlight *your* specific technical contributions (not just 'we did').\n"
                f"- **Result**: Quantify outcomes (e.g. 'reduced latency by 35%', 'passed 100% of test suites')."
            )

        elif 'gap' in prompt_lower or missing or topic == 'gap_guidance':
            missing_str = ", ".join(missing[:3]) if missing else "Advanced system design & performance tuning"
            return (
                f"### 📊 Skill Gap Remediation Plan for **{track}**\n\n"
                f"**Current Match**: {score}%\n\n"
                f"Your highest priority areas to address next:\n"
                f"**Missing Requirements**: `{missing_str}`\n\n"
                f"**Action Plan**:\n"
                f"1. **Focus on Verified Proof**: Review platform courses for `{missing_str}` and complete the corresponding hands-on labs.\n"
                f"2. **Take the Skill Assessment**: Score >= 70% on the topic assessment to turn missing skills into verified badges.\n"
                f"3. **Commit Project Code**: Build a feature in your portfolio project actively demonstrating `{missing_str}` and document the pull request."
            )

        else:
            return (
                f"### 🚀 Career Studio Mentorship: **{track}**\n\n"
                f"Hello {ctx['full_name']}! You are currently tracking at **{score}% readiness** for **{track}**.\n\n"
                f"- **Verified Strengths**: {', '.join(demonstrated) if demonstrated else 'Ready to establish through assessments and projects'}\n"
                f"- **Top Priority Focus**: {', '.join(missing[:3]) if missing else 'Deepen capstone project portfolio'}\n\n"
                f"**How can I help you today?**\n"
                f"- Ask me for **project architecture advice** for your next portfolio piece.\n"
                f"- Ask me for **mock interview questions** specific to {track}.\n"
                f"- Ask me to **review and polish your resume bullet points** using measurable action verbs.\n"
                f"- Ask for guidance on tackling any missing technical benchmark."
            )
