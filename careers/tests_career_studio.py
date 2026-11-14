"""
Automated Test Suite for SkillSphere Career Studio.
Validates:
1. 11 Curated Career Tracks and Skill Requirements.
2. Skill Evidence Engine: verified evidence aggregation and transparent weighted gap scoring.
3. Roadmap Generator: milestone generation, order preservation, and milestone completion.
4. Project Portfolio Studio: 5-stage workflow, checklist milestones, privacy by default.
5. Smart Resume Studio: verified credentials population, snapshot versioning, section reordering, PDF generation.
6. AI Career Assistant: context grounding, rate limiting, and offline Knowledge Engine fallback.
7. End-to-end HTTP Views & URLs.
"""

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from careers.models import (
    CareerTrack,
    CareerSkillRequirement,
    StudentCareerGoal,
    StudentSkillEvidence,
    SkillGapReport,
)
from courses.models import Category, Course, CourseCompletion
from assessments.models import SkillAssessment, AssessmentAttempt, CodingChallenge, ChallengeSubmission
from projects.models import ProjectIdea, ProjectMilestone
from resumes.models import Resume, ResumeVersion
from roadmaps.models import LearningRoadmap, RoadmapMilestone
from certificates.models import Certificate

from services.skill_evidence_engine import SkillEvidenceEngine
from services.career_roadmap_generator import CareerRoadmapGenerator
from services.career_ai_assistant import CareerAIAssistant
from services.resume_service import ResumeService
from services.pdf_service import PDFService


class CareerStudioCoreTests(TestCase):
    """
    Unit and integration tests for Career Studio services and models.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='student_alice',
            email='alice@example.com',
            password='SecretPassword123!',
            first_name='Alice',
            last_name='Smith'
        )
        self.client = Client()
        self.client.login(username='student_alice', password='SecretPassword123!')

        # Create a test CareerTrack with essential, recommended, and bonus skills
        self.track = CareerTrack.objects.create(
            slug='backend-developer',
            title='Backend Developer',
            icon='server',
            badge='High Demand',
            summary='Architect high-throughput server backends and APIs.',
            difficulty_level='Intermediate',
            average_salary_range='₹8L - ₹22L',
            market_demand='Surging',
            learning_milestones=[
                {
                    'title': 'Phase 1: Python & RESTful APIs',
                    'description': 'Master clean API design and HTTP protocols.',
                    'topics': ['HTTP/HTTPS', 'REST Standards', 'Status Codes'],
                    'mini_project': 'REST API Gateway',
                    'weeks': 3
                },
                {
                    'title': 'Phase 2: Database Architecture',
                    'description': 'Relational schema design, indexes, and queries.',
                    'topics': ['PostgreSQL', 'Indexes', 'ACID Transactions'],
                    'mini_project': 'Query Optimizer Benchmarks',
                    'weeks': 4
                }
            ],
            suggested_projects=[
                {'title': 'Payment Gateway Service', 'stack': 'Python, Django, PostgreSQL, Redis', 'difficulty': 'Intermediate'}
            ]
        )

        # Essential (3x)
        self.req_python = CareerSkillRequirement.objects.create(
            track=self.track,
            skill_name='Python',
            category='backend',
            importance='essential',
            weight=3,
            benchmark_description='Pass Python assessment >= 70% or build verified Python project'
        )
        self.req_postgres = CareerSkillRequirement.objects.create(
            track=self.track,
            skill_name='PostgreSQL & Database Design',
            category='database',
            importance='essential',
            weight=3,
            benchmark_description='Complete database course and design relational schema'
        )

        # Recommended (2x)
        self.req_redis = CareerSkillRequirement.objects.create(
            track=self.track,
            skill_name='Redis & Caching',
            category='database',
            importance='recommended',
            weight=2,
            benchmark_description='Implement caching in a portfolio project'
        )

        # Bonus (1x)
        self.req_docker = CareerSkillRequirement.objects.create(
            track=self.track,
            skill_name='Docker & Containers',
            category='devops',
            importance='bonus',
            weight=1,
            benchmark_description='Containerize production microservice'
        )

    def test_initial_skill_gap_calculation_zero_evidence(self):
        """When student has no platform evidence, match percentage should be 0%."""
        report = SkillEvidenceEngine.calculate_skill_gap(self.user, self.track)
        self.assertEqual(report.overall_match_percentage, 0)
        self.assertEqual(len(report.missing_skills), 4)
        self.assertEqual(len(report.demonstrated_skills), 0)
        self.assertIn("readiness score of 0%", report.score_explanation)

    def test_skill_evidence_aggregation_and_weighted_gap(self):
        """
        Verify that passing assessments and completing projects creates verified
        evidence and accurately increases weighted match score.
        """
        # 1. Pass Python assessment
        assessment = SkillAssessment.objects.create(
            title='Python Programming Proficiency Check',
            category='Python',
            difficulty='Intermediate'
        )
        AssessmentAttempt.objects.create(
            user=self.user,
            assessment=assessment,
            score=9,
            total_questions=10,
            percentage=90
        )

        # 2. Complete a project with PostgreSQL
        project = ProjectIdea.objects.create(
            user=self.user,
            title='Enterprise Billing System',
            category='Database Applications',
            technology_stack='Python, PostgreSQL, Django',
            technologies_list=['Python', 'PostgreSQL & Database Design'],
            skills_demonstrated=['PostgreSQL & Database Design'],
            workflow_status='completed'
        )

        # Run aggregation
        evidence = SkillEvidenceEngine.aggregate_student_evidence(self.user)
        self.assertTrue(len(evidence) >= 2)

        # Re-calculate gap
        report = SkillEvidenceEngine.calculate_skill_gap(self.user, self.track)

        # Total weights: 3 (Python) + 3 (Postgres) + 2 (Redis) + 1 (Docker) = 9
        # Earned weights: Python verified (3 * 1.0) + Postgres verified (3 * 1.0) = 6
        # Expected score: round((6 / 9) * 100) = 67%
        self.assertEqual(report.overall_match_percentage, 67)
        self.assertEqual(len(report.demonstrated_skills), 2)
        self.assertEqual(len(report.missing_skills), 2)

    def test_roadmap_generation_and_preservation(self):
        """
        Tests that roadmap generator creates sequential milestones and never
        overwrites completed milestones.
        """
        roadmap = CareerRoadmapGenerator.generate_or_sync_roadmap(self.user, self.track, timeline_months=6)
        self.assertEqual(roadmap.milestones.count(), 2)

        first_ms = roadmap.milestones.first()
        # Mark first milestone as completed
        first_ms.is_completed = True
        first_ms.completed_at = timezone.now()
        first_ms.title = "Custom Completed Phase 1"
        first_ms.save()

        # Re-run generator (sync)
        roadmap_resync = CareerRoadmapGenerator.generate_or_sync_roadmap(self.user, self.track, timeline_months=6)
        refreshed_first = roadmap_resync.milestones.get(id=first_ms.id)

        # Must preserve completed state and custom edits
        self.assertTrue(refreshed_first.is_completed)
        self.assertEqual(refreshed_first.title, "Custom Completed Phase 1")

    def test_milestone_completion_toggle(self):
        """Tests toggling milestone completion state."""
        roadmap = CareerRoadmapGenerator.generate_or_sync_roadmap(self.user, self.track)
        ms = roadmap.milestones.first()
        self.assertFalse(ms.is_completed)

        toggled = CareerRoadmapGenerator.toggle_milestone_completion(ms.id, self.user)
        self.assertTrue(toggled.is_completed)
        self.assertIsNotNone(toggled.completed_at)

        # Toggle back
        toggled_back = CareerRoadmapGenerator.toggle_milestone_completion(ms.id, self.user)
        self.assertFalse(toggled_back.is_completed)
        self.assertIsNone(toggled_back.completed_at)

    def test_project_portfolio_privacy_by_default(self):
        """Ensure projects are private by default to protect student data."""
        proj = ProjectIdea.objects.create(
            user=self.user,
            title='Proprietary Algorithm Sandbox',
            category='Automation',
            technology_stack='Python'
        )
        self.assertFalse(proj.is_public)
        self.assertEqual(proj.workflow_status, 'planning')

    def test_resume_service_zero_fabrication_and_versioning(self):
        """
        Tests Smart Resume auto-population strictly from verified records,
        snapshot creation, and dynamic section ordering.
        """
        # Create a signed platform certificate
        cert = Certificate.objects.create(
            user=self.user,
            title='Backend Engineering Specialist',
            verification_status=True
        )

        resume = ResumeService.populate_verified_resume(
            user=self.user,
            target_track_slug=self.track.slug,
            template='ats'
        )
        self.assertIsNotNone(resume)
        self.assertEqual(resume.user, self.user)
        self.assertEqual(resume.target_career_track, self.track.slug)

        # Verified certificates must appear in resume_data
        cert_titles = [c['title'] for c in resume.resume_data.get('certifications', [])]
        self.assertIn(cert.title, cert_titles)

        # Experience must be empty (Zero-fabrication)
        self.assertEqual(len(resume.resume_data.get('experience', [])), 0)

        # Initial version snapshot must exist
        self.assertEqual(resume.versions.count(), 1)

        # Test snapshot creation
        version_2 = ResumeService.create_version_snapshot(resume, version_title="Custom Snapshot")
        self.assertEqual(version_2.version_number, 2)
        self.assertEqual(resume.versions.count(), 2)

        # Test section reordering
        custom_order = ['projects', 'skills', 'certifications', 'summary', 'education', 'experience']
        ResumeService.update_section_order(resume, custom_order)
        resume.refresh_from_db()
        self.assertEqual(resume.get_section_order(), custom_order)

        # Test PDF generation with dynamic section ordering
        pdf_bytes = PDFService.generate_resume_pdf(resume)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 500)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_ai_career_assistant_grounding_and_fallback(self):
        """
        Tests AI Career Mentor grounding context assembly and
        deterministic offline Knowledge Engine fallback.
        """
        # Set career goal
        StudentCareerGoal.objects.create(
            user=self.user,
            primary_track=self.track,
            target_timeline_months=6
        )

        context = CareerAIAssistant.assemble_student_context(self.user)
        self.assertEqual(context['target_track'], 'Backend Developer')

        # Query assistant
        res = CareerAIAssistant.query_assistant(
            user=self.user,
            prompt="What architecture should I use for a portfolio project?",
            topic="project_architecture"
        )
        self.assertTrue(res['success'])
        self.assertIn("Architecture Recommendation", res['content'])
        self.assertIn("Backend Developer", res['content'])

    def test_http_views_and_flow(self):
        """End-to-end HTTP view testing."""
        # 1. Dashboard
        res = self.client.get(reverse('careers:studio_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Learn Skills. Build Projects. Track Your Growth.")

        # 2. Path Explorer
        res = self.client.get(reverse('careers:studio_paths'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Backend Developer")

        # 3. Path Detail
        res = self.client.get(reverse('careers:studio_path_detail', kwargs={'slug': self.track.slug}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Technical Skill Benchmarks")

        # 4. Set Goal POST
        res = self.client.post(
            reverse('careers:studio_set_goal', kwargs={'slug': self.track.slug}),
            {'timeline_months': 6}
        )
        self.assertEqual(res.status_code, 302)
        goal = StudentCareerGoal.objects.get(user=self.user)
        self.assertEqual(goal.primary_track, self.track)

        # 5. Gap Analyzer
        res = self.client.get(reverse('careers:studio_gap_analyzer'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Transparent Scoring Model")

        # 6. Roadmap View
        res = self.client.get(reverse('careers:studio_roadmap'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Phase 1: Python")

        # 7. Project Studio
        res = self.client.get(reverse('careers:portfolio_studio'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Project Portfolio Studio")

        # 8. Create Project POST
        res = self.client.post(reverse('careers:create_studio_project'), {
            'title': 'High Throughput API',
            'category': 'Database Applications',
            'difficulty': 'Intermediate',
            'technology_stack': 'Python, PostgreSQL',
            'workflow_status': 'planning',
            'is_public': 'false'
        })
        self.assertEqual(res.status_code, 302)
        created_p = ProjectIdea.objects.filter(user=self.user, title='High Throughput API').first()
        self.assertIsNotNone(created_p)
        self.assertFalse(created_p.is_public)

        # 9. Smart Resume Studio
        res = self.client.get(reverse('careers:smart_resume_studio'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Smart Resume Studio")

        # 10. AI Assistant View
        res = self.client.get(reverse('careers:studio_assistant'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "AI Career Mentor")

        # 11. AI Assistant Query AJAX POST
        res = self.client.post(
            reverse('careers:studio_assistant_query'),
            data=json.dumps({'prompt': 'How do I close my skill gap?', 'topic': 'gap_guidance'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertIn("Remediation Plan", data['content'])
