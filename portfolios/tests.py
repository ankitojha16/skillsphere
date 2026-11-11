from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from portfolios.models import Portfolio, PortfolioProject

class PortfolioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='portfoliotester', email='port@test.com', password='Password123!')
        self.other_user = User.objects.create_user(username='otheruser', email='other@test.com', password='Password123!')
        self.client = Client()
        self.client.login(username='portfoliotester', password='Password123!')

    def test_builder_view_creates_portfolio(self):
        response = self.client.get(reverse('portfolios:builder'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Portfolio.objects.filter(user=self.user).exists())

    def test_portfolio_privacy_enforcement(self):
        portfolio, _ = Portfolio.objects.get_or_create(user=self.user, username='portfoliotester', is_public=False)
        
        # Owner can view private portfolio
        response = self.client.get(reverse('portfolios:public', kwargs={'username': 'portfoliotester'}))
        self.assertEqual(response.status_code, 200)

        # Unauthenticated user gets 404
        anon_client = Client()
        anon_resp = anon_client.get(reverse('portfolios:public', kwargs={'username': 'portfoliotester'}))
        self.assertEqual(anon_resp.status_code, 404)

        # Once made public, anonymous user can view
        portfolio.is_public = True
        portfolio.save()
        anon_resp_public = anon_client.get(reverse('portfolios:public', kwargs={'username': 'portfoliotester'}))
        self.assertEqual(anon_resp_public.status_code, 200)

    def test_add_and_delete_project(self):
        portfolio, _ = Portfolio.objects.get_or_create(user=self.user, username='portfoliotester')
        response = self.client.post(reverse('portfolios:builder'), {
            'action': 'add_project',
            'project_title': 'Cloud Orchestrator',
            'project_desc': 'Scalable Kubernetes deployment engine',
            'project_tech': 'Python, Docker',
            'is_featured': 'on',
        })
        self.assertEqual(response.status_code, 302)
        project = PortfolioProject.objects.filter(portfolio=portfolio, title='Cloud Orchestrator').first()
        self.assertIsNotNone(project)

        # Delete project
        del_resp = self.client.post(reverse('portfolios:delete_project', kwargs={'project_id': project.id}))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(PortfolioProject.objects.filter(id=project.id).exists())

    def test_public_portfolio_shows_career_goal_and_skills(self):
        from accounts.models import StudentProfile
        profile, _ = StudentProfile.objects.get_or_create(user=self.user)
        profile.career_goal = "Senior AI Architect"
        profile.learning_interests = '["python", "ai"]'
        profile.save()

        portfolio, _ = Portfolio.objects.get_or_create(
            user=self.user,
            username='portfoliotester',
            is_public=True,
            show_skills=True
        )

        response = self.client.get(reverse('portfolios:public', kwargs={'username': 'portfoliotester'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Senior AI Architect')
        self.assertContains(response, 'Python')
        self.assertContains(response, 'sharePortfolioBtn')

    def test_public_portfolio_displays_resume_pdf_download_link(self):
        from resumes.models import Resume
        resume = Resume.objects.create(
            user=self.user,
            title='Staff Software Engineer CV',
            is_primary=True,
            resume_data={'contact': {'full_name': 'Portfolio Tester'}}
        )
        for tmpl in ['modern', 'minimal', 'creative']:
            portfolio, _ = Portfolio.objects.get_or_create(user=self.user, username='portfoliotester')
            portfolio.template = tmpl
            portfolio.is_public = True
            portfolio.save()
            response = self.client.get(reverse('portfolios:public', kwargs={'username': 'portfoliotester'}))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Resume PDF')
            self.assertContains(response, reverse('resumes:export_pdf', kwargs={'pk': resume.pk}))

    def test_public_portfolio_displays_52_week_heatmap(self):
        portfolio, _ = Portfolio.objects.get_or_create(
            user=self.user,
            username='portfoliotester',
            is_public=True
        )
        for tmpl in ['modern', 'minimal', 'creative']:
            portfolio.template = tmpl
            portfolio.save()
            response = self.client.get(reverse('portfolios:public', kwargs={'username': 'portfoliotester'}))
            self.assertEqual(response.status_code, 200)
            self.assertIn('portfolio_heatmap_days_json', response.context)
            self.assertIn('portfolio_total_active_days', response.context)
            self.assertContains(response, 'portfolioHeatmapGrid')
            self.assertContains(response, '52-Week Learning')



