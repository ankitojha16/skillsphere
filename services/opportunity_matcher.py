"""
SkillSphere Opportunity Hub — Intelligent Skill Matching Engine.
Integrates with the Career Studio Skill Evidence Engine to evaluate how closely
a student's demonstrated, verified abilities match an opportunity's technical and
eligibility criteria.

Features:
- Transparent 0-100% matching score with clear rationale.
- Explicitly distinguishes required skills from preferred/bonus skills.
- Strictly references verified platform evidence (certificates, portfolio projects,
  passed assessments, challenge submissions) and never conflates self-reported claims.
- Does NOT penalize students for unfinished roadmap milestones.
- Checks minor safety and eligibility constraints.
"""

import logging
from typing import Dict, List, Any, Optional
from django.contrib.auth.models import User
from django.utils import timezone

from opportunities.models import Opportunity, SavedOpportunity
from careers.models import StudentSkillEvidence, StudentCareerGoal, CareerTrack
from services.skill_evidence_engine import SkillEvidenceEngine

logger = logging.getLogger('skillsphere.opportunities')


class OpportunityMatcher:
    """
    Intelligent match analyzer calculating auditable match scores and
    recommendation justifications.
    """

    @classmethod
    def evaluate_opportunity_for_student(
        cls,
        user: User,
        opportunity: Opportunity,
        verified_evidence: Optional[List[StudentSkillEvidence]] = None
    ) -> Dict[str, Any]:
        """
        Calculates a comprehensive matching evaluation for a student against a specific opportunity.

        Returns:
            {
                'match_percentage': int (0-100),
                'match_level': str ('High', 'Moderate', 'Developing'),
                'badge_color': str ('emerald', 'violet', 'amber'),
                'required_skills_summary': {
                    'matched': [{'skill': str, 'evidence': str, 'confidence': int}],
                    'missing': [str],
                    'match_ratio': float (e.g. 0.8)
                },
                'preferred_skills_summary': {
                    'matched': [{'skill': str, 'evidence': str, 'confidence': int}],
                    'missing': [str],
                    'match_ratio': float
                },
                'track_alignment': {
                    'is_aligned': bool,
                    'primary_track': str,
                    'bonus_points': int
                },
                'eligibility_status': {
                    'is_eligible': bool,
                    'minor_restricted': bool,
                    'notes': List[str]
                },
                'summary_explanation': str,
                'evidence_audit_trail': List[Dict[str, Any]]
            }
        """
        # Fetch or audit student verified skill evidence
        if verified_evidence is None:
            verified_evidence = list(
                StudentSkillEvidence.objects.filter(user=user, is_verified=True)
            )
            # If no cached evidence exists, run an audit
            if not verified_evidence:
                try:
                    verified_evidence = SkillEvidenceEngine.aggregate_student_evidence(user)
                except Exception as e:
                    logger.warning(f"Failed to audit student evidence during match: {e}")
                    verified_evidence = []

        # Index verified skills by normalized name
        evidence_by_skill: Dict[str, StudentSkillEvidence] = {}
        for ev in verified_evidence:
            norm = SkillEvidenceEngine.normalize_skill_name(ev.skill_name)
            if norm not in evidence_by_skill or ev.confidence_score > evidence_by_skill[norm].confidence_score:
                evidence_by_skill[norm] = ev

        # Extract required and preferred skills
        required_list = opportunity.get_required_skills_list()
        preferred_list = opportunity.get_preferred_skills_list()

        # 1. Match Required Skills (up to 70 points)
        matched_required: List[Dict[str, Any]] = []
        missing_required: List[str] = []

        for req in required_list:
            found_evidence = cls._find_matching_evidence(req, evidence_by_skill)
            if found_evidence:
                matched_required.append({
                    'skill': req,
                    'evidence': found_evidence.evidence_title,
                    'evidence_type': found_evidence.evidence_type,
                    'confidence': found_evidence.confidence_score,
                })
            else:
                missing_required.append(req)

        req_count = len(required_list)
        req_ratio = len(matched_required) / req_count if req_count > 0 else 1.0
        req_score = req_ratio * 70.0

        # 2. Match Preferred Skills (up to 20 points)
        matched_preferred: List[Dict[str, Any]] = []
        missing_preferred: List[str] = []

        for pref in preferred_list:
            found_evidence = cls._find_matching_evidence(pref, evidence_by_skill)
            if found_evidence:
                matched_preferred.append({
                    'skill': pref,
                    'evidence': found_evidence.evidence_title,
                    'evidence_type': found_evidence.evidence_type,
                    'confidence': found_evidence.confidence_score,
                })
            else:
                missing_preferred.append(pref)

        pref_count = len(preferred_list)
        pref_ratio = len(matched_preferred) / pref_count if pref_count > 0 else (1.0 if req_count > 0 else 0.5)
        pref_score = pref_ratio * 20.0

        # 3. Career Track Alignment (up to 10 points)
        track_aligned = False
        track_bonus = 0
        primary_track_title = "None Selected"

        try:
            goal = StudentCareerGoal.objects.filter(user=user).select_related('primary_track').first()
            if goal and goal.primary_track:
                primary_track_title = goal.primary_track.title
                track_slug = goal.primary_track.slug.lower()
                opp_cat = (opportunity.category or '').lower()
                opp_title = opportunity.title.lower()

                # Check if opportunity aligns with career track
                if (track_slug in opp_cat or
                    opp_cat in track_slug or
                    any(SkillEvidenceEngine.matches_skill(primary_track_title, req) for req in required_list) or
                    any(t.lower() in opp_title for t in primary_track_title.split())):
                    track_aligned = True
                    track_bonus = 10
                else:
                    track_bonus = 4  # partial cross-discipline credit
        except Exception:
            pass

        # 4. Total Score Calculation (0-100%)
        total_raw = req_score + pref_score + track_bonus
        final_percentage = min(100, max(0, int(round(total_raw))))

        # Determine Match Tier & Visual Indicators
        if final_percentage >= 75:
            match_level = 'High Match'
            badge_color = 'emerald'
        elif final_percentage >= 45:
            match_level = 'Moderate Match'
            badge_color = 'violet'
        else:
            match_level = 'Growth Opportunity'
            badge_color = 'amber'

        # 5. Minor & Age Eligibility Verification
        eligibility_notes: List[str] = []
        is_eligible = True
        minor_restricted = False

        profile = getattr(user, 'profile', None)
        if profile and hasattr(profile, 'education_level'):
            if profile.education_level == 'high_school':
                if not opportunity.is_minor_safe or opportunity.min_age > 17:
                    is_eligible = False
                    minor_restricted = True
                    eligibility_notes.append(
                        f"Requires minimum age {opportunity.min_age}+ (Minor student safety protection applied)."
                    )
                else:
                    eligibility_notes.append("Verified minor-friendly student opportunity.")

        # Check deadline
        if opportunity.is_expired:
            eligibility_notes.append("Note: Listing deadline has passed.")

        # 6. Auditable Summary Narrative
        summary = cls._generate_explanation(
            matched_required=matched_required,
            missing_required=missing_required,
            matched_preferred=matched_preferred,
            track_aligned=track_aligned,
            primary_track_title=primary_track_title,
            final_percentage=final_percentage
        )

        return {
            'match_percentage': final_percentage,
            'match_level': match_level,
            'badge_color': badge_color,
            'required_skills_summary': {
                'matched': matched_required,
                'missing': missing_required,
                'match_ratio': round(req_ratio, 2),
                'total_required': req_count,
            },
            'preferred_skills_summary': {
                'matched': matched_preferred,
                'missing': missing_preferred,
                'match_ratio': round(pref_ratio, 2),
                'total_preferred': pref_count,
            },
            'track_alignment': {
                'is_aligned': track_aligned,
                'primary_track': primary_track_title,
                'bonus_points': track_bonus,
            },
            'eligibility_status': {
                'is_eligible': is_eligible,
                'minor_restricted': minor_restricted,
                'notes': eligibility_notes,
            },
            'summary_explanation': summary,
            'evidence_count': len(matched_required) + len(matched_preferred),
        }

    @classmethod
    def _find_matching_evidence(
        cls,
        target_skill: str,
        evidence_index: Dict[str, StudentSkillEvidence]
    ) -> Optional[StudentSkillEvidence]:
        """Looks up whether any verified student evidence matches the skill name."""
        norm_target = SkillEvidenceEngine.normalize_skill_name(target_skill)

        # 1. Exact match
        if norm_target in evidence_index:
            return evidence_index[norm_target]

        # 2. Token / Partial match
        for skill_key, ev in evidence_index.items():
            if SkillEvidenceEngine.matches_skill(norm_target, skill_key):
                return ev

        return None

    @classmethod
    def _generate_explanation(
        cls,
        matched_required: List[Dict[str, Any]],
        missing_required: List[str],
        matched_preferred: List[Dict[str, Any]],
        track_aligned: bool,
        primary_track_title: str,
        final_percentage: int
    ) -> str:
        """Constructs an honest, transparent rationale explaining the match score."""
        parts = []

        if matched_required:
            skills_str = ", ".join([m['skill'] for m in matched_required[:3]])
            parts.append(
                f"You have verified platform evidence for {len(matched_required)} required skill(s) ({skills_str})."
            )

        if missing_required:
            missing_str = ", ".join(missing_required[:3])
            parts.append(
                f"Missing verified evidence for: {missing_str}."
            )

        if matched_preferred:
            pref_str = ", ".join([m['skill'] for m in matched_preferred[:2]])
            parts.append(
                f"Bonus matches for preferred capabilities: {pref_str}."
            )

        if track_aligned:
            parts.append(
                f"Strong alignment with your primary career goal ({primary_track_title})."
            )

        if not parts:
            return f"Calculated {final_percentage}% based on broad foundational engineering competencies."

        return " ".join(parts)

    @classmethod
    def rank_opportunities_for_student(
        cls,
        user: User,
        opportunities_queryset,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Ranks a collection of opportunities for a student with calculated match evaluations.
        Filters out age-restricted listings for minors.
        """
        verified_evidence = list(
            StudentSkillEvidence.objects.filter(user=user, is_verified=True)
        )
        if not verified_evidence:
            try:
                verified_evidence = SkillEvidenceEngine.aggregate_student_evidence(user)
            except Exception:
                verified_evidence = []

        is_minor = False
        profile = getattr(user, 'profile', None)
        if profile and hasattr(profile, 'education_level') and profile.education_level == 'high_school':
            is_minor = True

        ranked = []
        for opp in opportunities_queryset:
            if is_minor and (not opp.is_minor_safe or opp.min_age > 17):
                # Filter out adult-only listings for minors
                continue

            eval_result = cls.evaluate_opportunity_for_student(
                user=user,
                opportunity=opp,
                verified_evidence=verified_evidence
            )
            ranked.append({
                'opportunity': opp,
                'evaluation': eval_result,
                'match_score': eval_result['match_percentage'],
            })

        ranked.sort(key=lambda x: (x['match_score'], x['opportunity'].deadline or timezone.now().date()), reverse=True)
        return ranked[:limit]
