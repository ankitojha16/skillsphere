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
        ('Cybersecurity', 'Cybersecurity & Auditing'),
        ('Cloud Engineering', 'Cloud Engineering & DevOps'),
        ('FinTech', 'FinTech & Blockchain'),
        ('UI/UX Design', 'UI/UX Design & Frontend'),
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

    WORKFLOW_STATUS_CHOICES = [
        ('idea', '1. Idea / Concept'),
        ('planning', '2. Architecture & Planning'),
        ('in_progress', '3. Active Development'),
        ('completed', '4. Completed & Tested'),
        ('published', '5. Published in Portfolio 🚀'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_projects')
    project_ref = models.CharField(max_length=20, unique=True, db_index=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    workflow_status = models.CharField(max_length=20, choices=WORKFLOW_STATUS_CHOICES, default='planning')
    github_url = models.URLField(max_length=255, blank=True, help_text="Link to public GitHub repository")
    demo_url = models.URLField(max_length=255, blank=True, help_text="Link to live deployment / demo")

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Intermediate')
    technology_stack = models.CharField(max_length=255)
    technologies_list = models.JSONField(default=list, blank=True, help_text="Structured array of technology strings")
    skills_demonstrated = models.JSONField(default=list, blank=True, help_text="Skills evidenced by this project")

    description = models.TextField()
    problem_statement = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    main_features = models.TextField(blank=True)
    database_requirements = models.TextField(blank=True)
    development_phases = models.TextField(blank=True)

    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    is_team_project = models.BooleanField(default=False)
    team_role = models.CharField(max_length=100, blank=True)
    is_public = models.BooleanField(default=False, help_text="Private by default for student data protection")

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

        # Bi-directional sync between legacy status and modern workflow_status
        if self.status == 'completed' and self.workflow_status in ('idea', 'planning', 'in_progress'):
            self.workflow_status = 'completed'
        elif self.status == 'in_progress' and self.workflow_status in ('idea', 'planning'):
            self.workflow_status = 'in_progress'
        elif self.workflow_status in ('completed', 'published'):
            self.status = 'completed'
        elif self.workflow_status == 'in_progress':
            self.status = 'in_progress'
        elif self.workflow_status in ('idea', 'planning') and self.status not in ('in_progress', 'completed'):
            self.status = 'planning'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_ref or self.id} - {self.title} ({self.workflow_status})"

    def get_progress_percentage(self):
        total = self.milestones.count()
        if total == 0:
            if self.workflow_status in ('completed', 'published'):
                return 100
            elif self.workflow_status == 'in_progress':
                return 50
            return 15
        completed = self.milestones.filter(is_completed=True).count()
        return int(round((completed / total) * 100))


class ProjectMilestone(models.Model):
    """
    Checklist milestone for managing project delivery in Career Studio.
    """
    project = models.ForeignKey(ProjectIdea, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Project Milestone'
        verbose_name_plural = 'Project Milestones'

    def __str__(self):
        status = "Done" if self.is_completed else "Pending"
        return f"[{status}] {self.project.title} - #{self.order} {self.title}"
