from django.db import models
from django.contrib.auth.models import User
import json

class StudentProfile(models.Model):
    EDUCATION_CHOICES = [
        ('high_school', 'High School / Secondary'),
        ('undergraduate', 'Undergraduate (Bachelors)'),
        ('postgraduate', 'Postgraduate (Masters / PhD)'),
        ('self_taught', 'Self-Taught / Career Transition'),
        ('other', 'Other'),
    ]

    LEARNING_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    AVAILABLE_INTERESTS = [
        ('python', 'Python'),
        ('cpp', 'C/C++'),
        ('java', 'Java'),
        ('web_dev', 'Web Development'),
        ('dsa', 'Data Structures & Algorithms'),
        ('ai', 'Artificial Intelligence'),
        ('data_science', 'Data Science'),
        ('dbms', 'Database Management'),
    ]

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('recruiter', 'Recruiter'),
        ('instructor', 'Instructor'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', db_index=True)
    full_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    avatar_url_external = models.URLField(max_length=500, blank=True, help_text='Direct URL to profile photo (e.g. GitHub, Gravatar, Unsplash)')
    avatar_data_uri = models.TextField(blank=True, default='', help_text='Base64 data URI of uploaded avatar for serverless cloud persistence')
    education_level = models.CharField(max_length=50, choices=EDUCATION_CHOICES, default='undergraduate')
    institution = models.CharField(max_length=200, blank=True)
    learning_level = models.CharField(max_length=20, choices=LEARNING_LEVEL_CHOICES, default='beginner')
    learning_interests = models.TextField(default='[]', help_text='JSON list of interest slugs')
    career_goal = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name or self.user.username}'s Profile"

    def get_interests_list(self):
        try:
            return json.loads(self.learning_interests)
        except Exception:
            if isinstance(self.learning_interests, str) and self.learning_interests:
                return [i.strip() for i in self.learning_interests.split(',') if i.strip()]
            return []

    def set_interests_list(self, interests):
        if isinstance(interests, list):
            self.learning_interests = json.dumps(interests)
        else:
            self.learning_interests = '[]'

    @property
    def avatar_url(self):
        if self.avatar_data_uri:
            return self.avatar_data_uri
        if self.avatar_url_external:
            return self.avatar_url_external
        if self.avatar and hasattr(self.avatar, 'url'):
            try:
                return self.avatar.url
            except Exception:
                pass
        # Premium fallback avatar with user initials
        display_name = self.full_name or self.user.username or "Student"
        return f"https://ui-avatars.com/api/?name={display_name.replace(' ', '+')}&background=8B5CF6&color=F8FAFC&bold=true"
