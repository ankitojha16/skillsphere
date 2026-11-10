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

