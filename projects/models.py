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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_projects')
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

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title} ({self.category})"
