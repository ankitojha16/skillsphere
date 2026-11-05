from django.db import models
from django.contrib.auth.models import User

class CommunityPost(models.Model):
    CATEGORY_CHOICES = [
        ('programming-help', 'Programming Help'),
        ('python', 'Python'),
        ('web-development', 'Web Development'),
        ('dsa', 'DSA'),
        ('ai-ml', 'AI & Machine Learning'),
        ('career-guidance', 'Career Guidance'),
        ('project-showcase', 'Project Showcase'),
        ('internship-prep', 'Internship Preparation'),
        ('general', 'General Discussion'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()


class CommunityComment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title[:30]}"


class CommunityLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_likes')
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_user_community_post_like')
        ]

    def __str__(self):
        return f"{self.user.username} liked {self.post.title[:30]}"


class ContentReport(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('post', 'Community Post'),
        ('comment', 'Community Comment'),
        ('collaboration', 'Collaboration Project'),
        ('portfolio', 'Portfolio Listing'),
    ]

    REASON_CHOICES = [
        ('spam', 'Spam or Advertising'),
        ('inappropriate', 'Inappropriate or Offensive'),
        ('harassment', 'Harassment or Abuse'),
        ('misinformation', 'Misinformation or Scam'),
        ('other', 'Other Reason'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('resolved', 'Resolved / Action Taken'),
        ('dismissed', 'Dismissed / No Violation'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_reports')
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES)
    object_id = models.PositiveIntegerField()
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} ({self.content_type}) - {self.get_status_display()}"
