from django.db import models
from django.contrib.auth.models import User
import json

class LearningRoadmap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roadmaps')
    title = models.CharField(max_length=200)
    target_skill = models.CharField(max_length=150)
    current_level = models.CharField(max_length=50, default='Beginner')
    career_goal = models.CharField(max_length=200)
    daily_time = models.CharField(max_length=50, default='1 hour/day')
    duration = models.CharField(max_length=50, default='3 months')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    def get_progress(self):
        total = self.milestones.count()
        if total == 0:
            return {'percentage': 0, 'completed': 0, 'total': 0}
        completed = self.milestones.filter(is_completed=True).count()
        pct = int(round((completed / total) * 100))
        return {'percentage': pct, 'completed': completed, 'total': total}


class RoadmapMilestone(models.Model):
    roadmap = models.ForeignKey(LearningRoadmap, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField()
    topics_json = models.TextField(default='[]', help_text='JSON list of subtopics')
    mini_project = models.CharField(max_length=255, blank=True)
    milestone_order = models.PositiveIntegerField(default=1)
    estimated_weeks = models.PositiveIntegerField(default=2)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['milestone_order', 'id']

    def __str__(self):
        status = "Done" if self.is_completed else "Pending"
        return f"[{status}] {self.roadmap.title} - #{self.milestone_order} {self.title}"

    def get_topics_list(self):
        try:
            return json.loads(self.topics_json)
        except Exception:
            return []
