from django.db import models
from django.contrib.auth.models import User

class Portfolio(models.Model):
    TEMPLATE_CHOICES = [
        ('minimal', 'Minimal Professional'),
        ('modern', 'Modern Developer'),
        ('creative', 'Creative Portfolio'),
    ]

    THEME_CHOICES = [
        ('dark', 'Dark Glow'),
        ('midnight', 'Midnight Slate'),
        ('emerald', 'Emerald Cyber'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    username = models.CharField(max_length=150, unique=True, db_index=True)
    title = models.CharField(max_length=200, blank=True, default='Portfolio')
    about = models.TextField(blank=True)
    template = models.CharField(max_length=50, choices=TEMPLATE_CHOICES, default='minimal')
    theme = models.CharField(max_length=50, choices=THEME_CHOICES, default='dark')
    accent_color = models.CharField(max_length=20, default='#8B5CF6')
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    show_certifications = models.BooleanField(default=True)
    show_skills = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}'s Portfolio"

    def get_public_url(self):
        return f"/u/{self.username}/"


class PortfolioProject(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    description = models.TextField()
    technologies = models.CharField(max_length=255, blank=True, help_text="Comma-separated technologies, e.g. Python, Django, React")
    features = models.TextField(blank=True, help_text="Key features list or bullet points")
    github_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    thumbnail = models.ImageField(upload_to='portfolios/thumbnails/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.portfolio.username})"
