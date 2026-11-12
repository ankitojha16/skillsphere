from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from projects.models import ProjectIdea

class ProjectsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='projbuilder', email='proj@test.com', password='Password123!')
        self.client.force_login(self.user)

    def test_generator_view_loads(self):
        resp = self.client.get(reverse('projects:generator'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'AI Practical Project Generator')

    def test_save_project_idea(self):
        save_url = reverse('projects:save')
        resp = self.client.post(save_url, {
            'title': 'Automated Code Reviewer',
            'category': 'Python Development',
            'difficulty': 'Intermediate',
            'technology_stack': 'Python, AST, Django',
            'description': 'Static code analysis tool',
            'problem_statement': 'Detect anti-patterns',
            'objectives': 'Clean code metrics',
            'main_features': 'Syntax checks',
            'database_requirements': 'Reports table',
            'development_phases': 'Phase 1 and 2',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(ProjectIdea.objects.filter(user=self.user, title='Automated Code Reviewer').exists())

    def test_delete_project_idea(self):
        idea = ProjectIdea.objects.create(
            user=self.user,
            title='Delete Me',
            category='Web Development',
            difficulty='Beginner'
        )
        del_url = reverse('projects:delete', kwargs={'project_id': idea.id})
        resp = self.client.post(del_url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(ProjectIdea.objects.filter(id=idea.id).exists())

    def test_project_ref_generation_and_status_update(self):
        idea = ProjectIdea.objects.create(
            user=self.user,
            title='AI Research Assistant',
            category='Machine Learning',
            difficulty='Advanced',
            technology_stack='Python, PyTorch',
            description='Automated literature reviewer',
            problem_statement='Dense paper reading',
            objectives='Summarize papers',
            main_features='PDF parsing',
            database_requirements='Paper index',
            development_phases='Weeks 1-4'
        )
        # Verify automatic SP-XXXXXXXX reference format
        self.assertTrue(idea.project_ref.startswith('SP-'))
        self.assertEqual(len(idea.project_ref), 11)

        # Update status and links via detail_ref view
        url = reverse('projects:detail_ref', kwargs={'project_ref': idea.project_ref})
        resp = self.client.post(url, {
            'status': 'in_progress',
            'github_url': 'https://github.com/ankitojha16/ai-research-assistant',
            'demo_url': 'https://ai-research-assistant.vercel.app'
        })
        self.assertEqual(resp.status_code, 302)
        idea.refresh_from_db()
        self.assertEqual(idea.status, 'in_progress')
        self.assertEqual(idea.github_url, 'https://github.com/ankitojha16/ai-research-assistant')

    def test_project_detail_has_readme_generator_and_goal_link(self):
        idea = ProjectIdea.objects.create(
            user=self.user,
            title='Autonomous Trading Bot',
            category='FinTech',
            difficulty='Advanced',
            technology_stack='Python, Celery, Redis',
            description='Algorithmic trading engine with risk control',
            problem_statement='High frequency latency',
            objectives='Sub-millisecond execution',
            main_features='Order matching\nRisk limits',
            database_requirements='Trades, Ledgers',
            development_phases='Phase 1\nPhase 2'
        )
        url = reverse('projects:detail_ref', kwargs={'project_ref': idea.project_ref})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'openReadmeBtn')
        self.assertContains(resp, 'readmeModal')
        self.assertContains(resp, 'Track as Goal')
        self.assertContains(resp, 'goals/?preset_title=Autonomous%20Trading%20Bot')

    def test_export_github_bundle_zip(self):
        """Test generating and downloading a GitHub ZIP starter bundle."""
        idea = ProjectIdea.objects.create(
            user=self.user,
            title='ML Model Registry',
            category='Machine Learning',
            difficulty='Intermediate',
            technology_stack='Python, FastAPI, PyTorch',
            description='Model versioning registry',
            problem_statement='Model drift and provenance',
            objectives='Version models and track metrics',
            main_features='Metadata tracking\nModel deployment',
            database_requirements='Postgres registry',
            development_phases='Phase 1\nPhase 2'
        )
        # 1. JSON preview test
        url_preview = reverse('projects:export_github', kwargs={'project_id': idea.id}) + '?format=json'
        resp_preview = self.client.get(url_preview)
        self.assertEqual(resp_preview.status_code, 200)
        data = resp_preview.json()
        self.assertTrue(data.get('success'))
        self.assertIn('README.md', data.get('file_tree'))
        self.assertIn('requirements.txt', data.get('file_tree'))
        self.assertIn('SkillSphere Verified Project', data.get('readme'))

        # 2. ZIP download test
        url_zip = reverse('projects:export_github', kwargs={'project_id': idea.id})
        resp_zip = self.client.get(url_zip)
        self.assertEqual(resp_zip.status_code, 200)
        self.assertEqual(resp_zip['Content-Type'], 'application/zip')
        self.assertIn('attachment; filename=', resp_zip['Content-Disposition'])

    def test_sync_project_to_portfolio(self):
        """Test 1-click syncing a project to the user's public Developer Portfolio."""
        from portfolios.models import Portfolio, PortfolioProject
        idea = ProjectIdea.objects.create(
            user=self.user,
            title='Realtime Chat Engine',
            category='Web Development',
            difficulty='Intermediate',
            technology_stack='Python, Django Channels, Redis',
            description='WebSockets chat platform'
        )
        url = reverse('projects:sync_portfolio', kwargs={'project_id': idea.id})
        resp = self.client.post(url, {
            'github_url': 'https://github.com/projbuilder/realtime-chat',
            'demo_url': 'https://chat-demo.vercel.app'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))

        # Verify database updates
        idea.refresh_from_db()
        self.assertEqual(idea.status, 'completed')
        self.assertEqual(idea.github_url, 'https://github.com/projbuilder/realtime-chat')

        portfolio = Portfolio.objects.filter(user=self.user).first()
        self.assertIsNotNone(portfolio)
        port_proj = PortfolioProject.objects.filter(portfolio=portfolio, title=idea.title).first()
        self.assertIsNotNone(port_proj)
        self.assertEqual(port_proj.github_url, 'https://github.com/projbuilder/realtime-chat')
        self.assertEqual(port_proj.live_url, 'https://chat-demo.vercel.app')


