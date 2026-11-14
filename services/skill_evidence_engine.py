"""
SkillSphere Career Studio — Skill Evidence Engine.
Aggregates student demonstrated performance across courses, assessments,
coding exercises, portfolio projects, and signed certificates.
Computes transparent, weighted skill gap analysis relative to curated career tracks.
"""

import logging
from typing import Dict, List, Any, Optional
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from careers.models import (
    CareerTrack,
    CareerSkillRequirement,
    StudentSkillEvidence,
    SkillGapReport,
)

logger = logging.getLogger('skillsphere.careers')


class SkillEvidenceEngine:
    """
    Core engine responsible for aggregating verified platform artifacts
    and generating auditable skill gap analyses.
    """

    # Keyword mappings between coarse platform categories and fine-grained career requirements
    CATEGORY_SKILL_MAP = {
        'Python': ['python', 'backend', 'clean code', 'scripting'],
        'Django': ['django', 'rest api', 'backend', 'web framework', 'python'],
        'SQL': ['sql', 'postgresql', 'database', 'relational database', 'query optimization'],
        'DSA': ['data structures', 'algorithms', 'problem solving', 'system design'],
        'HTML_CSS': ['html5', 'css3', 'responsive design', 'web fundamentals'],
        'JavaScript': ['javascript', 'frontend', 'es6', 'dom', 'typescript'],
        'Cloud_Fundamentals': ['cloud', 'aws', 'docker', 'devops', 'ci/cd', 'containers'],
        'Data_Science': ['machine learning', 'data analysis', 'pandas', 'numpy', 'statistics'],
    }

    @classmethod
    def normalize_skill_name(cls, name: str) -> str:
        """Normalizes skill strings for reliable token matching."""
        if not name:
            return ""
        # Remove extra whitespace and lower-case
        cleaned = " ".join(name.strip().lower().split())
        return cleaned

    @classmethod
    def matches_skill(cls, candidate: str, requirement: str) -> bool:
        """
        Determines whether a candidate string matches or partially matches
        a target requirement.
        """
        cand_norm = cls.normalize_skill_name(candidate)
        req_norm = cls.normalize_skill_name(requirement)

        if not cand_norm or not req_norm:
            return False

        if cand_norm == req_norm:
            return True

        if cand_norm in req_norm or req_norm in cand_norm:
            return True

        cand_tokens = set(cand_norm.replace('/', ' ').replace('&', ' ').split())
        req_tokens = set(req_norm.replace('/', ' ').replace('&', ' ').split())
        common = cand_tokens.intersection(req_tokens)
        stop_words = {'and', '&', 'or', 'the', 'in', 'of', 'for', 'with', 'to'}
        substantive = common - stop_words

        return len(substantive) >= 1

    @classmethod
    def aggregate_student_evidence(cls, user: User) -> List[StudentSkillEvidence]:
        """
        Audits all completed student activities across the platform and synchronizes
        verified StudentSkillEvidence records in the database.
        """
        created_or_updated: List[StudentSkillEvidence] = []

        with transaction.atomic():
            # 1. Signed Platform Certificates (Highest Verification: 95%)
            try:
                from certificates.models import Certificate
                certs = Certificate.objects.filter(user=user, verification_status=True).select_related('course')
                for cert in certs:
                    skill_tag = cert.title.replace('Certificate of Completion -', '').strip()
                    if cert.course and cert.course.category:
                        cat_name = cert.course.category.name
                    else:
                        cat_name = 'Technology'

                    evidence, _ = StudentSkillEvidence.objects.update_or_create(
                        user=user,
                        skill_name=skill_tag,
                        evidence_type='certificate_earned',
                        reference_id=cert.certificate_id,
                        defaults={
                            'is_verified': True,
                            'confidence_score': 95,
                            'evidence_title': f"Verified Certificate: {cert.title}",
                            'metadata': {
                                'certificate_id': cert.certificate_id,
                                'issued_at': cert.issued_at.isoformat() if cert.issued_at else '',
                                'course_category': cat_name,
                            }
                        }
                    )
                    created_or_updated.append(evidence)
            except Exception as e:
                logger.warning(f"Error auditing certificates for user {user.id}: {e}")

            # 2. Completed / Published Portfolio Projects (90% verification)
            try:
                from projects.models import ProjectIdea
                projects = ProjectIdea.objects.filter(
                    user=user,
                    workflow_status__in=['completed', 'published']
                )
                for proj in projects:
                    skills_list = []
                    if isinstance(proj.skills_demonstrated, list) and proj.skills_demonstrated:
                        skills_list.extend(proj.skills_demonstrated)
                    if isinstance(proj.technologies_list, list) and proj.technologies_list:
                        skills_list.extend(proj.technologies_list)
                    if not skills_list and proj.technology_stack:
                        skills_list = [s.strip() for s in proj.technology_stack.split(',') if s.strip()]

                    for skill in set(skills_list):
                        evidence, _ = StudentSkillEvidence.objects.update_or_create(
                            user=user,
                            skill_name=skill,
                            evidence_type='project_built',
                            reference_id=proj.project_ref or f"PROJ-{proj.id}",
                            defaults={
                                'is_verified': True,
                                'confidence_score': 90,
                                'evidence_title': f"Project: {proj.title} ({proj.get_workflow_status_display()})",
                                'metadata': {
                                    'project_ref': proj.project_ref,
                                    'github_url': proj.github_url,
                                    'demo_url': proj.demo_url,
                                    'status': proj.workflow_status,
                                }
                            }
                        )
                        created_or_updated.append(evidence)
            except Exception as e:
                logger.warning(f"Error auditing projects for user {user.id}: {e}")

            # 3. Passed Skill Assessments (score >= 70%) (85% verification)
            try:
                from assessments.models import AssessmentAttempt
                attempts = AssessmentAttempt.objects.filter(
                    user=user,
                    percentage__gte=70
                ).select_related('assessment')
                for attempt in attempts:
                    skill_label = attempt.assessment.get_category_display() if hasattr(attempt.assessment, 'get_category_display') else attempt.assessment.category
                    confidence = 90 if attempt.percentage >= 85 else 80

                    evidence, _ = StudentSkillEvidence.objects.update_or_create(
                        user=user,
                        skill_name=skill_label,
                        evidence_type='assessment_score',
                        reference_id=f"ATTEMPT-{attempt.id}",
                        defaults={
                            'is_verified': True,
                            'confidence_score': confidence,
                            'evidence_title': f"Assessment: {attempt.assessment.title} ({attempt.percentage}%)",
                            'metadata': {
                                'score': attempt.score,
                                'total_questions': attempt.total_questions,
                                'percentage': attempt.percentage,
                                'category': attempt.assessment.category,
                                'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else '',
                            }
                        }
                    )
                    created_or_updated.append(evidence)
            except Exception as e:
                logger.warning(f"Error auditing assessments for user {user.id}: {e}")

            # 4. Accepted Coding Challenges (80% verification)
            try:
                from assessments.models import ChallengeSubmission
                subs = ChallengeSubmission.objects.filter(
                    user=user,
                    status='Accepted'
                ).select_related('challenge')
                for sub in subs:
                    ch_cat = sub.challenge.get_category_display() if hasattr(sub.challenge, 'get_category_display') else sub.challenge.category
                    evidence, _ = StudentSkillEvidence.objects.update_or_create(
                        user=user,
                        skill_name=f"DSA ({ch_cat})",
                        evidence_type='coding_submission',
                        reference_id=f"SUB-{sub.id}",
                        defaults={
                            'is_verified': True,
                            'confidence_score': 80,
                            'evidence_title': f"Accepted Challenge: {sub.challenge.title}",
                            'metadata': {
                                'challenge_slug': sub.challenge.slug,
                                'difficulty': sub.challenge.difficulty,
                                'language': sub.language,
                                'runtime_ms': sub.runtime_ms,
                            }
                        }
                    )
                    created_or_updated.append(evidence)
            except Exception as e:
                logger.warning(f"Error auditing coding submissions for user {user.id}: {e}")

            # 5. Completed Courses (75% verification)
            try:
                from courses.models import CourseCompletion
                completions = CourseCompletion.objects.filter(
                    user=user,
                    is_completed=True
                ).select_related('course', 'course__category')
                for comp in completions:
                    course = comp.course
                    evidence, _ = StudentSkillEvidence.objects.update_or_create(
                        user=user,
                        skill_name=course.title,
                        evidence_type='course_completion',
                        reference_id=f"COURSE-{course.id}",
                        defaults={
                            'is_verified': True,
                            'confidence_score': 75,
                            'evidence_title': f"Completed Course: {course.title}",
                            'metadata': {
                                'course_id': course.id,
                                'course_slug': course.slug,
                                'category': course.category.name if course.category else 'General',
                                'progress': comp.learning_progress,
                            }
                        }
                    )
                    created_or_updated.append(evidence)
            except Exception as e:
                logger.warning(f"Error auditing course completions for user {user.id}: {e}")

            # 6. Profile Stated Interests / Skills (Self-reported, unverified: 35% confidence)
            try:
                profile = getattr(user, 'profile', None)
                if profile and hasattr(profile, 'get_interests_list'):
                    for interest in profile.get_interests_list():
                        # Only add if no verified evidence exists for this interest
                        existing_verified = StudentSkillEvidence.objects.filter(
                            user=user,
                            is_verified=True,
                            skill_name__icontains=interest
                        ).exists()
                        if not existing_verified:
                            evidence, _ = StudentSkillEvidence.objects.update_or_create(
                                user=user,
                                skill_name=interest.title(),
                                evidence_type='self_reported',
                                reference_id=f"PROFILE-{interest}",
                                defaults={
                                    'is_verified': False,
                                    'confidence_score': 35,
                                    'evidence_title': f"Self-Reported Interest: {interest.title()}",
                                    'metadata': {'source': 'student_profile'}
                                }
                            )
                            created_or_updated.append(evidence)
            except Exception as e:
                logger.warning(f"Error auditing profile interests for user {user.id}: {e}")

        return created_or_updated

    @classmethod
    def calculate_skill_gap(cls, user: User, track: CareerTrack) -> SkillGapReport:
        """
        Performs a transparent, weighted gap analysis comparing the student's
        verified evidence records against all requirements of the chosen CareerTrack.
        """
        # Ensure latest evidence is aggregated
        cls.aggregate_student_evidence(user)

        user_evidence = list(StudentSkillEvidence.objects.filter(user=user))
        requirements = list(track.skill_requirements.all())

        demonstrated = []
        improving = []
        missing = []

        total_weight = 0
        earned_weight = 0.0

        for req in requirements:
            weight = req.weight
            total_weight += weight

            # Check matches across student evidence
            matching_evidence = []
            for ev in user_evidence:
                if cls.matches_skill(ev.skill_name, req.skill_name) or \
                   cls.matches_skill(ev.evidence_title, req.skill_name):
                    matching_evidence.append(ev)

            if not matching_evidence:
                # Missing
                missing.append({
                    'skill_name': req.skill_name,
                    'category': req.category,
                    'importance': req.importance,
                    'weight': req.weight,
                    'benchmark': req.benchmark_description or req.description or "Complete course & practical project",
                    'status': 'missing',
                    'confidence_score': 0,
                })
            else:
                # Find strongest evidence
                matching_evidence.sort(key=lambda x: (x.is_verified, x.confidence_score), reverse=True)
                top_ev = matching_evidence[0]

                ev_info = {
                    'skill_name': req.skill_name,
                    'category': req.category,
                    'importance': req.importance,
                    'weight': req.weight,
                    'evidence_title': top_ev.evidence_title,
                    'confidence_score': top_ev.confidence_score,
                    'is_verified': top_ev.is_verified,
                    'evidence_type': top_ev.evidence_type,
                }

                if top_ev.is_verified and top_ev.confidence_score >= 70:
                    demonstrated.append(ev_info)
                    earned_weight += (weight * 1.0)
                else:
                    improving.append(ev_info)
                    # Partial / self-reported gives 40% credit
                    earned_weight += (weight * 0.4)

        if total_weight > 0:
            match_percentage = int(round((earned_weight / total_weight) * 100))
        else:
            match_percentage = 0

        # Construct transparent explanation
        explanation = (
            f"Your readiness score of {match_percentage}% is computed across {len(requirements)} benchmark requirements for {track.title}. "
            f"Essential skills carry 3× weight, recommended skills carry 2× weight, and bonus skills carry 1× weight. "
            f"Verified platform evidence (certificates, completed projects, passed assessments) earns 100% of the allocated skill weight, "
            f"while self-reported or in-progress skills contribute 40%. "
            f"Completed courses demonstrate theoretical familiarity, but full professional readiness requires building demonstrable projects."
        )

        # Actionable next steps
        action_plan = []
        # Prioritize essential missing skills first, then recommended missing skills
        sorted_missing = sorted(missing, key=lambda x: x['weight'], reverse=True)
        for m in sorted_missing[:3]:
            action_plan.append({
                'title': f"Master {m['skill_name']}",
                'type': 'course_or_assessment',
                'description': f"Requirement: {m['benchmark']}. Complete the dedicated course and take the platform skill check.",
                'importance': m['importance'],
            })

        # Add project recommendation if student has missing projects
        action_plan.append({
            'title': f"Build a {track.title} Capstone Project",
            'type': 'project',
            'description': f"Select a project from the {track.title} track (e.g., {track.suggested_projects[0].get('title') if track.suggested_projects else 'End-to-End Application'}) to generate verified project evidence.",
            'importance': 'essential',
        })

        # Persist report
        report, _ = SkillGapReport.objects.update_or_create(
            user=user,
            track=track,
            defaults={
                'overall_match_percentage': match_percentage,
                'demonstrated_skills': demonstrated,
                'improving_skills': improving,
                'missing_skills': missing,
                'action_plan': action_plan,
                'score_explanation': explanation,
            }
        )

        return report
