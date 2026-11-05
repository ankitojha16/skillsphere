from django.db import models
from django.contrib.auth.models import User

class CollaborationProject(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('recruiting', 'Looking for Members'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner Friendly'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_collaborations')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, default='Web Development')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    technologies = models.CharField(max_length=255, help_text="e.g. Python, Django, PostgreSQL, JavaScript")
    required_roles = models.CharField(max_length=255, help_text="e.g. Backend Developer, Frontend Developer, UI/UX Designer")
    team_size = models.PositiveIntegerField(default=3, help_text="Maximum team capacity")
    expected_duration = models.CharField(max_length=100, default='4-6 weeks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recruiting')
    github_repo = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (by {self.owner.username})"

    @property
    def current_members_count(self):
        # Count owner + active members
        return self.memberships.filter(status='active').count() + 1


class CollaborationMembership(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('left', 'Left'),
        ('removed', 'Removed'),
    ]

    project = models.ForeignKey(CollaborationProject, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaboration_memberships')
    role = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'user'], name='unique_project_member')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.project.title}"


class CollaborationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    project = models.ForeignKey(CollaborationProject, on_delete=models.CASCADE, related_name='requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaboration_requests')
    message = models.TextField(blank=True, help_text="Introduce yourself and your skills/interest")
    role_requested = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['project', 'user'], name='unique_project_user_request')
        ]

    def __str__(self):
        return f"Request by {self.user.username} for {self.project.title} ({self.status})"
