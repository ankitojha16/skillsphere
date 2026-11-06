from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class UserGamification(models.Model):
    LEVEL_THRESHOLDS = [
        (1500, 'Skill Master'),
        (1000, 'Advanced Learner'),
        (600, 'Developer'),
        (300, 'Learner'),
        (100, 'Explorer'),
        (0, 'Beginner'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gamification')
    total_xp = models.PositiveIntegerField(default=0)
    current_level = models.CharField(max_length=50, default='Beginner')
    current_streak = models.PositiveIntegerField(default=1)
    longest_streak = models.PositiveIntegerField(default=1)
    last_activity_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.current_level} ({self.total_xp} XP)"

    def update_level(self):
        for threshold, level_name in self.LEVEL_THRESHOLDS:
            if self.total_xp >= threshold:
                self.current_level = level_name
                break

    def add_xp(self, amount: int):
        self.total_xp += amount
        self.update_level()
        self.record_activity()
        self.save()

    def record_activity(self):
        today = timezone.now().date()
        if self.last_activity_date == today:
            return  # Activity already logged today
        elif self.last_activity_date == today - timedelta(days=1):
            self.current_streak += 1
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
        else:
            self.current_streak = 1
        self.last_activity_date = today


class Badge(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='award', help_text='Lucide icon name')
    xp_requirement = models.PositiveIntegerField(default=50)

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-awarded_at']

    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"


class XPTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='xp_transactions')
    activity_key = models.CharField(max_length=150, help_text="Unique key per learning milestone e.g. lesson_12, quiz_3")
    amount = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'activity_key'], name='unique_user_activity_xp')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: +{self.amount} XP for {self.activity_key}"

