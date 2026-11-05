from django.db import models
from django.contrib.auth.models import User

class MockInterview(models.Model):
    CATEGORY_CHOICES = [
        ('Python Developer', 'Python Developer'),
        ('Django Developer', 'Django Developer'),
        ('Frontend Developer', 'Frontend Developer'),
        ('Backend Developer', 'Backend Developer'),
        ('SQL Developer', 'SQL Developer'),
        ('General Programming', 'General Programming'),
        ('HR Interview', 'Behavioral & HR Interview'),
    ]

    DIFFICULTY_CHOICES = [
        ('Junior', 'Junior / Entry-Level (College Learner)'),
        ('Mid-Level', 'Mid-Level (1-3 years experience)'),
        ('Senior', 'Senior (Architectural focus)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mock_interviews')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(max_length=30, choices=DIFFICULTY_CHOICES, default='Junior')
    total_questions = models.PositiveIntegerField(default=3)
    is_completed = models.BooleanField(default=False)
    overall_score = models.PositiveIntegerField(default=0)
    overall_feedback = models.TextField(blank=True)
    strong_areas = models.TextField(blank=True)
    improvement_areas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.user.username} - {self.category} ({status})"

    def completed_count(self):
        return self.responses.exclude(user_answer="").count()


class InterviewResponse(models.Model):
    interview = models.ForeignKey(MockInterview, on_delete=models.CASCADE, related_name='responses')
    question_order = models.PositiveIntegerField()
    question_text = models.TextField()
    user_answer = models.TextField(blank=True)
    ai_feedback = models.TextField(blank=True)
    technical_rating = models.PositiveIntegerField(default=0)  # 1 to 10
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question_order']

    def __str__(self):
        return f"Interview #{self.interview.id} - Q#{self.question_order}"
