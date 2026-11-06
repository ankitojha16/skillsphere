from django.db import models
from django.contrib.auth.models import User

class ProjectIdea(models.Model):
    CATEGORY_CHOICES = [
        ('Web Development', 'Web Development'),
        ('Python Development', 'Python Development'),
        ('Machine Learning', 'Machine Learning & AI'),
        ('Data Science', 'Data Science & Analytics'),
        ('Mobile Applications', 'Mobile Applications'),
        ('Automation', 'Automation & Scripting'),
        ('Database Applications', 'Database & Backend Applications'),
    ]

    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    STATUS_CHOICES = [
        ('planning', 'Planning Phase'),
        ('in_progress', 'In Active Development'),
        ('completed', 'Completed & Deployed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_projects')
    project_ref = models.CharField(max_length=20, unique=True, db_index=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    github_url = models.URLField(max_length=255, blank=True, help_text="Link to public GitHub repository")
    demo_url = models.URLField(max_length=255, blank=True, help_text="Link to live deployment / demo")

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Intermediate')
    technology_stack = models.CharField(max_length=255)
    description = models.TextField()
    problem_statement = models.TextField()
    objectives = models.TextField()
    main_features = models.TextField()
    database_requirements = models.TextField()
    development_phases = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.project_ref:
            import uuid
            new_ref = f"SP-{uuid.uuid4().hex[:8].upper()}"
            while ProjectIdea.objects.filter(project_ref=new_ref).exists():
                new_ref = f"SP-{uuid.uuid4().hex[:8].upper()}"
            self.project_ref = new_ref
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_ref or self.id} - {self.title} ({self.status})"
