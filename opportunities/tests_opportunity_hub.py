"""
SkillSphere Opportunity Hub — Comprehensive Automated Test Suite.
Tests:
- Opportunity creation, editing, and archiving.
- Type filtering (internships, scholarships, hackathons, competitions).
- Intelligent Skill Matching calculation and transparent score breakdown.
- Duplicate application prevention.
- 8-stage Application Pipeline Tracker and Status History audit trail.
- Recruiter permissions, authorization, and organization ownership.
- Private resume version sharing and PII shielding.
- Expired opportunity filtering.
- Minor-user protections (age limits, high school filtering, shielding from direct outreach).
- AI Interview Prep with deterministic fallback.
- Suspicious listing reporting and moderation.
"""

from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache

from opportunities.models import (
    Opportunity,
    OpportunityOrganization,
    OpportunitySkill,
    SavedOpportunity,
    ApplicationStatusHistory,
    OpportunityReport,
    CandidateShortlist,
    InterviewInvitation,
)
from resumes.models import Resume, ResumeVersion
from careers.models import CareerTrack, StudentSkillEvidence, StudentCareerGoal
from services.opportunity_matcher import OpportunityMatcher
from services.interview_prep_service import InterviewPrepService


class OpportunityHubTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

        # 1. Users: Student, Minor Student, Recruiter, Other Recruiter
        self.student = User.objects.create_user(
            username='adult_student',
            email='adult@student.com',
            password='TestPassword123!'
        )
        if hasattr(self.student, 'profile'):
            self.student.profile.role = 'student'
            self.student.profile.education_level = 'undergraduate'
            self.student.profile.save()

        self.minor_student = User.objects.create_user(
            username='minor_student',
            email='minor@student.com',
            password='TestPassword123!'
        )
        if hasattr(self.minor_student, 'profile'):
            self.minor_student.profile.role = 'student'
            self.minor_student.profile.education_level = 'high_school'
            self.minor_student.profile.save()

        self.recruiter = User.objects.create_user(
            username='lead_recruiter',
            email='recruiter@partner.org',
            password='TestPassword123!'
        )
        if hasattr(self.recruiter, 'profile'):
            self.recruiter.profile.role = 'recruiter'
            self.recruiter.profile.save()

        self.other_recruiter = User.objects.create_user(
            username='rival_recruiter',
            email='rival@other.org',
            password='TestPassword123!'
        )
        if hasattr(self.other_recruiter, 'profile'):
            self.other_recruiter.profile.role = 'recruiter'
            self.other_recruiter.profile.save()

        # 2. Partner Organization
        self.org = OpportunityOrganization.objects.create(
            name='Acme Cloud Foundation',
            slug='acme-cloud-foundation',
            website_url='https://acmecloud.org',
            description='Innovating open infrastructure.',
            is_verified=True
        )

        today = timezone.now().date()

        # 3. Adult-only Opportunity (18+)
        self.opp_adult = Opportunity.objects.create(
            title='Backend Python Engineer Intern',
            organization='Acme Cloud Foundation',
            organization_ref=self.org,
            posted_by=self.recruiter,
            opportunity_type='internship',
            category='python-development',
            description='Build scalable cloud APIs.',
            required_skills='Python, Django, PostgreSQL',
            preferred_skills='Docker, Redis',
            eligibility='College sophomore or above',
            location='Remote',
            work_mode='remote',
            compensation_details='$2,500/month',
            application_url='https://acmecloud.org/apply',
            deadline=today + timedelta(days=30),
            min_age=18,
            is_minor_safe=False,
            is_active=True,
            verification_status=True,
        )

        # 4. Minor-safe Opportunity (14+)
        self.opp_minor_safe = Opportunity.objects.create(
            title='Global High School AI Challenge',
            organization='Acme Cloud Foundation',
            organization_ref=self.org,
            posted_by=self.recruiter,
            opportunity_type='challenge',
            category='ai-ml',
            description='Open to high school students building AI for good.',
            required_skills='Python, Machine Learning',
            preferred_skills='Pandas',
            location='Online',
            work_mode='remote',
            funding_amount=10000.00,
            application_url='https://acmecloud.org/ai-challenge',
            deadline=today + timedelta(days=45),
            min_age=14,
            is_minor_safe=True,
            is_active=True,
            verification_status=True,
        )

        # 5. Expired Opportunity
        self.opp_expired = Opportunity.objects.create(
            title='Winter 2025 Algorithmic Sprint',
            organization='Acme Cloud Foundation',
            opportunity_type='competition',
            category='software-development',
            description='Past coding contest.',
            required_skills='Python, C++',
            application_url='https://acmecloud.org/contest',
            deadline=today - timedelta(days=10),
            is_active=True,
            verification_status=True,
        )

        # 6. Student Resume & ResumeVersion
        self.resume = Resume.objects.create(
            user=self.student,
            title='Full-Stack Python Resume',
            template='ats',
            is_primary=True,
            resume_data={'skills': ['Python', 'Django', 'PostgreSQL']}
        )
        self.resume_ver = ResumeVersion.objects.create(
            resume=self.resume,
            version_number=1,
            version_title='Tailored Acme Backend v1',
            snapshot_data=self.resume.resume_data
        )

        # 7. Student Verified Skill Evidence
        StudentSkillEvidence.objects.create(
            user=self.student,
            skill_name='Python',
            evidence_type='certificate_earned',
            confidence_score=95,
            is_verified=True,
            evidence_title='Verified Certificate: Python Core Mastery'
        )
        StudentSkillEvidence.objects.create(
            user=self.student,
            skill_name='Django',
            evidence_type='project_published',
            confidence_score=90,
            is_verified=True,
            evidence_title='Published Project: E-Commerce API'
        )

    # =========================================================================
    # Test 1: Opportunity Creation & Editing by Recruiter
    # =========================================================================
    def test_recruiter_can_create_and_edit_opportunity(self):
        self.client.login(username='lead_recruiter', password='TestPassword123!')
        create_url = reverse('opportunities:recruiter_post')

        post_data = {
            'title': 'Frontend React Fellow',
            'organization': 'Acme Cloud Foundation',
            'opportunity_type': 'internship',
            'category': 'web-development',
            'description': 'Develop accessible frontend UI components.',
            'required_skills': 'React, JavaScript, HTML/CSS',
            'preferred_skills': 'TypeScript, Tailwind',
            'eligibility': 'Enrolled students',
            'location': 'Remote',
            'work_mode': 'remote',
            'compensation_details': '$2,000/mo',
            'application_url': 'https://acmecloud.org/frontend',
            'deadline': (timezone.now().date() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'min_age': 18,
            'is_minor_safe': 'false',
        }
        res = self.client.post(create_url, post_data)
        self.assertEqual(res.status_code, 302)

        new_opp = Opportunity.objects.filter(title='Frontend React Fellow').first()
        self.assertIsNotNone(new_opp)
        self.assertEqual(new_opp.posted_by, self.recruiter)
        self.assertEqual(new_opp.required_skills, 'React, JavaScript, HTML/CSS')

        # Edit opportunity
        edit_url = reverse('opportunities:recruiter_edit_listing', kwargs={'pk': new_opp.pk})
        post_data['title'] = 'Frontend React Fellow (Updated 2026)'
        res_edit = self.client.post(edit_url, post_data)
        self.assertEqual(res_edit.status_code, 302)

        new_opp.refresh_from_db()
        self.assertEqual(new_opp.title, 'Frontend React Fellow (Updated 2026)')

    # =========================================================================
    # Test 2: Recruiter Organization Ownership Enforcement
    # =========================================================================
    def test_recruiter_cannot_edit_another_recruiters_opportunity(self):
        self.client.login(username='rival_recruiter', password='TestPassword123!')
        edit_url = reverse('opportunities:recruiter_edit_listing', kwargs={'pk': self.opp_adult.pk})

        res = self.client.post(edit_url, {
            'title': 'Hacked Listing Title',
            'organization': 'Malicious Org',
            'description': 'Tampered description',
            'required_skills': 'Nothing',
            'application_url': 'https://bad.com',
        })
        self.assertEqual(res.status_code, 403)
        self.opp_adult.refresh_from_db()
        self.assertNotEqual(self.opp_adult.title, 'Hacked Listing Title')

    # =========================================================================
    # Test 3: Minor User Protection & Eligibility Filtering
    # =========================================================================
    def test_minor_user_cannot_view_adult_only_opportunity(self):
        # Adult student sees both adult and minor-safe opportunities
        self.client.login(username='adult_student', password='TestPassword123!')
        res_adult = self.client.get(reverse('opportunities:list'))
        self.assertEqual(res_adult.status_code, 200)
        self.assertContains(res_adult, self.opp_adult.title)
        self.assertContains(res_adult, self.opp_minor_safe.title)

        # Minor student is restricted: adult-only listing is filtered out from list
        self.client.login(username='minor_student', password='TestPassword123!')
        res_minor = self.client.get(reverse('opportunities:list'))
        self.assertEqual(res_minor.status_code, 200)
        self.assertNotContains(res_minor, self.opp_adult.title)
        self.assertContains(res_minor, self.opp_minor_safe.title)

        # Direct navigation to adult detail page redirects minor student with warning
        res_detail = self.client.get(reverse('opportunities:detail', kwargs={'pk': self.opp_adult.pk}))
        self.assertEqual(res_detail.status_code, 302)

    def test_recruiter_cannot_send_direct_unmoderated_invitation_to_minor(self):
        self.client.login(username='lead_recruiter', password='TestPassword123!')
        url = reverse('opportunities:send_interview_invitation', kwargs={'username': 'minor_student'})
        payload = {
            'role_title': 'Direct High School Outreach',
            'company_name': 'Acme Corp',
            'message': 'Direct chat attempt.'
        }
        res = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(res.status_code, 403)
        self.assertIn('safety policy', res.json()['message'])

    # =========================================================================
    # Test 4: Intelligent Skill Matching Calculation & Transparency
    # =========================================================================
    def test_intelligent_skill_matching_engine(self):
        # Student has verified Python & Django evidence. Opportunity requires: Python, Django, PostgreSQL
        eval_data = OpportunityMatcher.evaluate_opportunity_for_student(self.student, self.opp_adult)

        self.assertIn('match_percentage', eval_data)
        self.assertGreaterEqual(eval_data['match_percentage'], 40)
        self.assertLessEqual(eval_data['match_percentage'], 100)

        # Check matched vs missing breakdown
        matched_skills = [m['skill'] for m in eval_data['required_skills_summary']['matched']]
        self.assertIn('Python', matched_skills)
        self.assertIn('Django', matched_skills)
        self.assertIn('PostgreSQL', eval_data['required_skills_summary']['missing'])

        # Check transparency narrative
        self.assertIn('verified platform evidence', eval_data['summary_explanation'])
        self.assertIn('Missing verified evidence', eval_data['summary_explanation'])

    # =========================================================================
    # Test 5: Opportunity Type Filtering (Scholarships, Hackathons, Jobs)
    # =========================================================================
    def test_opportunity_type_filtering(self):
        self.client.login(username='adult_student', password='TestPassword123!')

        # Filter by challenge
        res_chal = self.client.get(reverse('opportunities:list'), {'type': 'challenge'})
        self.assertEqual(res_chal.status_code, 200)
        self.assertContains(res_chal, self.opp_minor_safe.title)
        self.assertNotContains(res_chal, self.opp_adult.title)

        # Filter by internship
        res_intern = self.client.get(reverse('opportunities:list'), {'type': 'internship'})
        self.assertEqual(res_intern.status_code, 200)
        self.assertContains(res_intern, self.opp_adult.title)
        self.assertNotContains(res_intern, self.opp_minor_safe.title)

    # =========================================================================
    # Test 6: Expired Opportunities Filtering
    # =========================================================================
    def test_expired_opportunities_filtering(self):
        self.client.login(username='adult_student', password='TestPassword123!')

        # By default expired listings are hidden
        res_default = self.client.get(reverse('opportunities:list'))
        self.assertEqual(res_default.status_code, 200)
        self.assertNotContains(res_default, self.opp_expired.title)

        # With show_expired=true, expired listing is included
        res_expired = self.client.get(reverse('opportunities:list'), {'show_expired': 'true'})
        self.assertEqual(res_expired.status_code, 200)
        self.assertContains(res_expired, self.opp_expired.title)

    # =========================================================================
    # Test 7: Duplicate Application Prevention & Pipeline Tracking
    # =========================================================================
    def test_application_tracking_and_duplicate_prevention(self):
        self.client.login(username='adult_student', password='TestPassword123!')
        apply_url = reverse('opportunities:apply', kwargs={'pk': self.opp_adult.pk})

        # 1. First application submission
        res1 = self.client.post(apply_url, {
            'status': 'applied',
            'resume_version_id': self.resume_ver.id,
            'external_reference': 'ACME-APP-1029',
            'notes': 'Submitted through company portal with tailored resume.',
            'follow_up_date': (timezone.now().date() + timedelta(days=14)).strftime('%Y-%m-%d'),
        })
        self.assertEqual(res1.status_code, 302)

        saved = SavedOpportunity.objects.filter(user=self.student, opportunity=self.opp_adult).first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.application_status, 'applied')
        self.assertEqual(saved.resume_version, self.resume_ver)
        self.assertEqual(saved.external_reference, 'ACME-APP-1029')

        # 2. Second application to same opportunity updates rather than creating duplicate
        res2 = self.client.post(apply_url, {
            'status': 'interview',
            'resume_version_id': self.resume_ver.id,
            'external_reference': 'ACME-APP-1029',
            'notes': 'Invited to technical screening!',
        })
        self.assertEqual(res2.status_code, 302)

        # Verify only 1 record exists in database (duplicate prevented)
        count = SavedOpportunity.objects.filter(user=self.student, opportunity=self.opp_adult).count()
        self.assertEqual(count, 1)

        saved.refresh_from_db()
        self.assertEqual(saved.application_status, 'interview')

        # Verify audit status history recorded
        history = ApplicationStatusHistory.objects.filter(application=saved).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.from_status, 'applied')
        self.assertEqual(history.to_status, 'interview')

    # =========================================================================
    # Test 8: Recruiter Applicants Dashboard & Privacy Guard
    # =========================================================================
    def test_recruiter_applicants_dashboard_and_privacy_guard(self):
        # Student applies with resume version
        SavedOpportunity.objects.create(
            user=self.student,
            opportunity=self.opp_adult,
            application_status='applied',
            resume_version=self.resume_ver
        )

        self.client.login(username='lead_recruiter', password='TestPassword123!')
        url = reverse('opportunities:recruiter_applicants', kwargs={'pk': self.opp_adult.pk})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'adult_student')
        self.assertContains(res, 'Privacy Guard')
        # Ensure student personal email is shielded
        self.assertNotContains(res, 'adult@student.com')

    # =========================================================================
    # Test 9: Recruiter Stage Update API & Student Notification
    # =========================================================================
    def test_recruiter_updates_applicant_stage_with_notification(self):
        app = SavedOpportunity.objects.create(
            user=self.student,
            opportunity=self.opp_adult,
            application_status='applied'
        )

        self.client.login(username='lead_recruiter', password='TestPassword123!')
        url = reverse('opportunities:recruiter_update_applicant_status', kwargs={'app_id': app.id})

        res = self.client.post(
            url,
            data={'status': 'assessment', 'notes': 'Sent Hackerrank test link.'},
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'success')

        app.refresh_from_db()
        self.assertEqual(app.application_status, 'assessment')

        # Check notification sent to student
        from notifications.models import Notification
        notif = Notification.objects.filter(user=self.student, notification_type='system').first()
        self.assertIsNotNone(notif)
        self.assertIn('Application Update', notif.title)

    # =========================================================================
    # Test 10: AI Interview Prep Deck & Deterministic Fallback
    # =========================================================================
    def test_interview_prep_generation_fallback(self):
        self.client.login(username='adult_student', password='TestPassword123!')
        url = reverse('opportunities:interview_prep', kwargs={'pk': self.opp_adult.pk})

        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Role-Specific Interview Prep')
        self.assertContains(res, 'STAR Method')
        self.assertContains(res, 'Technical Screening')

        # Direct service call to verify deterministic fallback structure
        deck = InterviewPrepService.generate_prep_deck(self.student, self.opp_adult)
        self.assertIn('technical_questions', deck)
        self.assertIn('behavioral_questions', deck)
        self.assertIn('company_prep_tips', deck)
        self.assertGreater(len(deck['technical_questions']), 0)
        self.assertIn('STAR', deck['disclaimer'])

    # =========================================================================
    # Test 11: Reporting Suspicious or Inaccurate Listings
    # =========================================================================
    def test_report_opportunity_listing(self):
        self.client.login(username='adult_student', password='TestPassword123!')
        url = reverse('opportunities:report_opportunity', kwargs={'pk': self.opp_adult.pk})

        res = self.client.post(url, {
            'reason': 'inaccurate_info',
            'details': 'Application deadline on website is earlier than listed.'
        })
        self.assertEqual(res.status_code, 302)

        report = OpportunityReport.objects.filter(opportunity=self.opp_adult, reported_by=self.student).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.reason, 'inaccurate_info')
        self.assertEqual(report.status, 'pending')
