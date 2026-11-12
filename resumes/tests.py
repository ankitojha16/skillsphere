import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from resumes.models import Resume

class ResumeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='resumetester', email='resume@test.com', password='Password123!')
        self.client = Client()
        self.client.login(username='resumetester', password='Password123!')

    def test_resume_builder_auto_prefill(self):
        response = self.client.get(reverse('resumes:builder'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Resume.objects.filter(user=self.user).exists())

    def test_save_resume_json(self):
        resume = Resume.objects.create(
            user=self.user,
            title='Software Engineer Resume',
            template='ats',
            resume_data={'contact': {'full_name': 'Tester'}, 'skills': ['Python', 'Django']}
        )
        updated_data = {
            'contact': {'full_name': 'Tester Updated', 'email': 'resume@test.com'},
            'summary': 'Experienced developer with solid Python foundations and database expertise.',
            'skills': ['Python', 'Django', 'PostgreSQL', 'Docker', 'Git'],
            'education': [{'school': 'State Univ', 'degree': 'B.S. CS', 'year': '2025'}],
            'projects': [{'title': 'SkillSphere', 'technologies': 'Django', 'description': 'Full stack platform'}],
            'experience': []
        }
        response = self.client.post(reverse('resumes:builder_edit', kwargs={'pk': resume.pk}), {
            'action': 'save_resume',
            'title': 'Senior Software Engineer CV',
            'template': 'ats',
            'resume_data_json': json.dumps(updated_data)
        })
        self.assertEqual(response.status_code, 302)
        resume.refresh_from_db()
        self.assertEqual(resume.title, 'Senior Software Engineer CV')
        self.assertEqual(resume.resume_data['contact']['full_name'], 'Tester Updated')
        self.assertGreater(resume.ats_score, 0)

    def test_pdf_export_returns_pdf(self):
        resume = Resume.objects.create(
            user=self.user,
            title='PDF Test Resume',
            template='ats',
            resume_data={
                'contact': {'full_name': 'Jane Doe', 'email': 'jane@example.com'},
                'summary': 'Motivated developer',
                'skills': ['Python', 'SQL'],
                'education': [],
                'projects': [],
                'experience': []
            }
        )
        response = self.client.get(reverse('resumes:export_pdf', kwargs={'pk': resume.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(len(response.content) > 500)

    def test_ai_improve_ajax_endpoint(self):
        response = self.client.post(
            reverse('resumes:ai_improve'),
            data=json.dumps({
                'type': 'summary',
                'headline': 'Backend Developer',
                'skills': ['Python', 'Django'],
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('content', data)

    def test_zero_fabrication_in_prefill(self):
        response = self.client.get(reverse('resumes:builder'))
        self.assertEqual(response.status_code, 200)
        resume = Resume.objects.filter(user=self.user).first()
        self.assertIsNotNone(resume)
        data = resume.resume_data

        # Zero fabrication enforcement: no fake jobs/companies
        self.assertEqual(data.get('experience', []), [])

        # No fabricated GPA or unearned certificates
        education = data.get('education', [])
        for edu in education:
            self.assertNotIn('3.8', str(edu.get('gpa', '')))
            self.assertNotIn('State University', str(edu.get('school', '')))

        # Certifications should only be real earned certificates
        self.assertEqual(data.get('certifications', []), [])

    def test_all_pdf_templates(self):
        for template_name in ['ats', 'modern', 'fresher', 'minimal']:
            resume = Resume.objects.create(
                user=self.user,
                title=f'{template_name} Resume',
                template=template_name,
                resume_data={
                    'contact': {'full_name': 'Jane Doe', 'email': 'jane@example.com'},
                    'summary': 'Dedicated software engineering student.',
                    'skills': ['Python', 'Django', 'PostgreSQL'],
                    'education': [{'school': 'NIT Trichy', 'degree': 'B.Tech CSE', 'year': '2026'}],
                    'projects': [{'title': 'SkillSphere', 'technologies': 'Django', 'description': 'Production platform'}],
                    'experience': []
                }
            )
            resp = self.client.get(reverse('resumes:export_pdf', kwargs={'pk': resume.pk}))
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp['Content-Type'], 'application/pdf')
            self.assertGreater(len(resp.content), 500)

    def test_resume_career_goal_prefill_and_save(self):
        # Test prefill contains career_goal & short_term_goals
        response = self.client.get(reverse('resumes:builder'))
        self.assertEqual(response.status_code, 200)
        resume = Resume.objects.filter(user=self.user).first()
        self.assertIsNotNone(resume)
        self.assertIn('career_goal', resume.resume_data)
        self.assertIn('short_term_goals', resume.resume_data)
        self.assertTrue(len(resume.resume_data['short_term_goals']) >= 2)

        # Test saving customized career_goal and short_term_goals
        updated_data = resume.resume_data.copy()
        updated_data['career_goal'] = 'Principal Cloud Architect'
        updated_data['target_industry'] = 'FinTech & Distributed Systems'
        updated_data['short_term_goals'] = ['Master Kubernetes', 'Lead cloud migration']
        post_resp = self.client.post(reverse('resumes:builder_edit', kwargs={'pk': resume.pk}), {
            'action': 'save_resume',
            'title': 'Cloud Architect CV',
            'template': 'modern',
            'resume_data_json': json.dumps(updated_data)
        })
        self.assertEqual(post_resp.status_code, 302)
        resume.refresh_from_db()
        self.assertEqual(resume.resume_data['career_goal'], 'Principal Cloud Architect')
        self.assertEqual(resume.resume_data['target_industry'], 'FinTech & Distributed Systems')
        self.assertEqual(resume.resume_data['short_term_goals'], ['Master Kubernetes', 'Lead cloud migration'])

    def test_ai_improve_career_goal_endpoint(self):
        response = self.client.post(
            reverse('resumes:ai_improve'),
            data=json.dumps({
                'type': 'career_goal',
                'target_role': 'Full-Stack Developer',
                'target_industry': 'Web Platforms',
                'skills': ['Python', 'Django', 'React'],
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('content', data)
        self.assertIn('data', data)
        self.assertIn('career_objective', data['data'])
        self.assertIn('short_term_goals', data['data'])
        self.assertTrue(len(data['data']['short_term_goals']) > 0)

    def test_pdf_with_career_goal_and_milestones(self):
        resume = Resume.objects.create(
            user=self.user,
            title='Goal Enhanced Resume',
            template='fresher',
            resume_data={
                'contact': {'full_name': 'Ankit Kumar', 'email': 'ankit@example.com'},
                'career_goal': 'Full-Stack Software Engineer',
                'target_industry': 'Cloud & Enterprise SaaS',
                'career_objective': 'High-performing developer aiming to scale web architectures.',
                'short_term_goals': ['Architect resilient microservices', 'Automate CI/CD pipelines'],
                'skills': ['Python', 'Django', 'Docker'],
                'education': [],
                'projects': [],
                'experience': []
            }
        )
        resp = self.client.get(reverse('resumes:export_pdf', kwargs={'pk': resume.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertGreater(len(resp.content), 800)

    def test_resume_builder_education_and_certifications(self):
        # 1. Verify template contains interactive education and certification containers
        response = self.client.get(reverse('resumes:builder'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="educationContainer"')
        self.assertContains(response, 'id="addEducationBtn"')
        self.assertContains(response, 'id="certificationsContainer"')
        self.assertContains(response, 'id="addCertificationBtn"')
        self.assertContains(response, 'id="preview_education_wrap"')
        self.assertContains(response, 'id="preview_certifications_wrap"')

        # 2. Save resume with full education & certifications
        resume = Resume.objects.filter(user=self.user).first()
        updated_data = resume.resume_data.copy()
        updated_data['education'] = [
            {'degree': 'B.Tech in Computer Science', 'school': 'IIT Delhi', 'year': '2026', 'gpa': '9.1 / 10.0'}
        ]
        updated_data['certifications'] = [
            {'title': 'Python & Django Core Specialist', 'issuer': 'SkillSphere Verified (ID: SS-CERT-2026-A1B2C3D4)'},
            {'title': 'AWS Certified Cloud Practitioner', 'issuer': 'Amazon Web Services'}
        ]
        post_resp = self.client.post(reverse('resumes:builder_edit', kwargs={'pk': resume.pk}), {
            'action': 'save_resume',
            'title': 'Certified Software Engineer Resume',
            'template': 'modern',
            'resume_data_json': json.dumps(updated_data)
        })
        self.assertEqual(post_resp.status_code, 302)

        resume.refresh_from_db()
        self.assertEqual(len(resume.resume_data['education']), 1)
        self.assertEqual(resume.resume_data['education'][0]['school'], 'IIT Delhi')
        self.assertEqual(len(resume.resume_data['certifications']), 2)
        self.assertGreater(resume.ats_score, 0)

        # 3. Verify PDF generation succeeds with education and certifications
        pdf_resp = self.client.get(reverse('resumes:export_pdf', kwargs={'pk': resume.pk}))
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp['Content-Type'], 'application/pdf')
        self.assertGreater(len(pdf_resp.content), 1000)

    def test_user_certificates_passed_to_builder(self):
        from certificates.models import Certificate
        Certificate.objects.create(
            user=self.user,
            title='Full Stack Django Architecture Specialist',
            certificate_id='SS-CERT-2026-TEST99'
        )
        response = self.client.get(reverse('resumes:builder'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="importSkillSphereCertsBtn"')
        self.assertContains(response, 'Import SkillSphere (1)')

    def test_ats_check_with_target_job_description(self):
        response = self.client.post(
            reverse('resumes:ai_improve'),
            data=json.dumps({
                'type': 'ats_check',
                'resume_data': {
                    'contact': {'full_name': 'Test Dev', 'email': 'test@example.com'},
                    'summary': 'Passionate Python and Django developer with database skills.',
                    'skills': ['Python', 'Django'],
                    'education': [{'school': 'NIT', 'degree': 'B.Tech', 'year': '2025'}],
                    'projects': [{'title': 'Project 1', 'technologies': 'Python', 'description': 'Web app'}],
                },
                'job_description': 'Looking for an engineer skilled in Python, Django, React, PostgreSQL, and Docker.'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        analysis = data.get('analysis', {})
        self.assertIn('score', analysis)
        self.assertIn('keywords_matched', analysis)
        self.assertIn('keywords_missing', analysis)
        matched_lower = [k.lower() for k in analysis['keywords_matched']]
        self.assertIn('python', matched_lower)
        missing_lower = [k.lower() for k in analysis['keywords_missing']]
        self.assertTrue(any(k in missing_lower for k in ['react', 'postgresql', 'docker']))

    def test_mock_interview_page_loads(self):
        """Verify the mock interview studio loads with audio/voice controls."""
        resp = self.client.get(reverse('resumes:mock_interview'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'AI Technical & Behavioral Mock Interviewer')
        self.assertContains(resp, 'voiceRecordBtn')
        self.assertContains(resp, 'Listen to AI')
        self.assertContains(resp, 'Evaluate with AI')

        # Test with specific role
        resp_python = self.client.get(reverse('resumes:mock_interview') + '?role=python')
        self.assertEqual(resp_python.status_code, 200)
        self.assertContains(resp_python, 'select_related')

    def test_evaluate_interview_answer_success(self):
        """Verify the AI interview evaluation API endpoint returns structured scoring."""
        resp = self.client.post(
            reverse('resumes:mock_interview_evaluate'),
            data=json.dumps({
                'role': 'Full-Stack Software Engineer',
                'question': 'Tell me about a time you optimized a slow database query.',
                'answer': 'In my project at SkillSphere, when user traffic doubled, our dashboard API was taking 1.5 seconds. I analyzed the slow query log, added compound indexes on user_id and created_at, and refactored N+1 queries using select_related. As a result, API latency was reduced by 85% to under 200ms.',
                'category': 'technical'
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        analysis = data.get('analysis', {})
        self.assertIn('overall_score', analysis)
        self.assertIn('accuracy_score', analysis)
        self.assertIn('clarity_score', analysis)
        self.assertIn('star_adherence', analysis)
        self.assertIn('strengths', analysis)
        self.assertIn('improvements', analysis)
        self.assertIn('model_answer', analysis)
        self.assertGreaterEqual(analysis['overall_score'], 50)

    def test_evaluate_interview_answer_validation_error(self):
        """Verify empty answers are rejected with 400 Bad Request."""
        resp = self.client.post(
            reverse('resumes:mock_interview_evaluate'),
            data=json.dumps({
                'role': 'Full-Stack Software Engineer',
                'question': 'How does indexing work?',
                'answer': ''
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_tailor_resume_for_job_api(self):
        """Verify the AI Resume Tailor generates keyword alignments and STAR bullets."""
        resp = self.client.post(
            reverse('resumes:tailor_for_job'),
            data=json.dumps({
                'job_title': 'Senior Backend Engineer',
                'company_name': 'Stripe',
                'job_description': 'Seeking an engineer skilled in Python, SQL, REST APIs, and Docker.'
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        tailored = data.get('tailored', {})
        self.assertIn('match_score', tailored)
        self.assertIn('tailored_headline', tailored)
        self.assertIn('tailored_summary', tailored)
        self.assertIn('tailored_bullets', tailored)
        self.assertGreaterEqual(len(tailored['tailored_bullets']), 2)
        self.assertIn('matched_keywords', tailored)




