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


class League(models.Model):
    TIER_CHOICES = [
        ('BRONZE', 'Bronze League'),
        ('SILVER', 'Silver League'),
        ('GOLD', 'Gold League'),
        ('DIAMOND', 'Diamond League'),
    ]

    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='BRONZE')
    tier_level = models.PositiveSmallIntegerField(default=1)  # 1: Bronze, 2: Silver, 3: Gold, 4: Diamond
    cohort_id = models.CharField(max_length=60)
    week_start = models.DateField()
    week_end = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_start', 'tier_level']
        unique_together = ('cohort_id', 'week_start')

    def __str__(self):
        return f"{self.get_tier_display()} (Cohort {self.cohort_id})"


class LeagueMembership(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='league_memberships')
    weekly_xp = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(default=1)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-weekly_xp', 'joined_at']
        unique_together = ('league', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.league} - {self.weekly_xp} XP (Rank #{self.rank})"


class SkillDuel(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
    ]

    challenger = models.ForeignKey(User, related_name='duels_initiated', on_delete=models.CASCADE)
    opponent = models.ForeignKey(User, related_name='duels_received', on_delete=models.SET_NULL, null=True, blank=True)
    opponent_name = models.CharField(max_length=100, default='AI Rival')
    topic = models.CharField(max_length=100, default='Python & Algorithms')
    challenger_score = models.PositiveIntegerField(default=0)
    opponent_score = models.PositiveIntegerField(default=0)
    winner = models.ForeignKey(User, related_name='duels_won', on_delete=models.SET_NULL, null=True, blank=True)
    xp_wager = models.PositiveIntegerField(default=25)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.challenger.username} vs {self.opponent_name} ({self.topic}) - Winner: {self.winner.username if self.winner else 'Draw'}"


class UserArenaRating(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='arena_rating')
    elo = models.PositiveIntegerField(default=1200)
    matches_played = models.PositiveIntegerField(default=0)
    matches_won = models.PositiveIntegerField(default=0)
    matches_lost = models.PositiveIntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    peak_elo = models.PositiveIntegerField(default=1200)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-elo']

    def __str__(self):
        return f"{self.user.username} - {self.elo} ELO ({self.tier_name})"

    @property
    def tier_name(self):
        if self.elo >= 1800:
            return 'Grandmaster'
        elif self.elo >= 1500:
            return 'Diamond'
        elif self.elo >= 1300:
            return 'Gold'
        elif self.elo >= 1050:
            return 'Silver'
        return 'Bronze'

    @property
    def win_rate(self):
        if self.matches_played == 0:
            return 0.0
        return round((self.matches_won / self.matches_played) * 100, 1)


class CodeArenaMatch(models.Model):
    STATUS_CHOICES = [
        ('WAITING', 'Waiting for Opponent'),
        ('IN_PROGRESS', 'Battle in Progress'),
        ('COMPLETED', 'Completed'),
        ('EXPIRED', 'Expired'),
    ]

    player_one = models.ForeignKey(User, related_name='arena_matches_as_p1', on_delete=models.CASCADE)
    player_two = models.ForeignKey(User, related_name='arena_matches_as_p2', on_delete=models.SET_NULL, null=True, blank=True)
    player_two_name = models.CharField(max_length=100, default='Grandmaster Bot')
    is_bot_match = models.BooleanField(default=False)
    
    challenge = models.ForeignKey('assessments.CodingChallenge', on_delete=models.CASCADE, related_name='arena_matches')

    player_one_elo_before = models.PositiveIntegerField(default=1200)
    player_two_elo_before = models.PositiveIntegerField(default=1200)
    player_one_elo_change = models.IntegerField(default=0)
    player_two_elo_change = models.IntegerField(default=0)

    player_one_cases_passed = models.PositiveIntegerField(default=0)
    player_two_cases_passed = models.PositiveIntegerField(default=0)
    total_cases = models.PositiveIntegerField(default=5)

    winner = models.ForeignKey(User, related_name='arena_victories', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    duration_seconds = models.PositiveIntegerField(default=180)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Match #{self.id}: {self.player_one.username} vs {self.player_two_name} ({self.challenge.title})"



