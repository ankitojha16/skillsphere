from django.db import models
from django.contrib.auth.models import User

class SkillAssessment(models.Model):
    CATEGORY_CHOICES = [
        ('Python', 'Python Programming'),
        ('C', 'C Programming'),
        ('CPP', 'C++ Programming'),
        ('Java', 'Java Programming'),
        ('HTML_CSS', 'HTML & CSS'),
        ('JavaScript', 'JavaScript'),
        ('SQL', 'SQL & Databases'),
        ('DSA', 'Data Structures & Algorithms'),
        ('Django', 'Django Web Framework'),
        ('CS_Fundamentals', 'Computer Science Fundamentals'),
    ]

    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Beginner')
    time_limit_minutes = models.PositiveIntegerField(default=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'difficulty']

    def __str__(self):
        return f"{self.title} ({self.difficulty})"

    def question_count(self):
        return self.questions.count()


class AssessmentQuestion(models.Model):
    assessment = models.ForeignKey(SkillAssessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    topic_tag = models.CharField(max_length=100, default='Core Fundamentals')
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    explanation = models.TextField()

    def __str__(self):
        return f"{self.assessment.title} - Q#{self.id}: {self.question_text[:50]}"


class AssessmentAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_attempts')
    assessment = models.ForeignKey(SkillAssessment, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    percentage = models.PositiveIntegerField(default=0)
    ai_feedback = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.username} - {self.assessment.title}: {self.score}/{self.total_questions} ({self.percentage}%)"


class AssessmentResponse(models.Model):
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        status = "Correct" if self.is_correct else "Incorrect"
        return f"Attempt #{self.attempt.id} - Q#{self.question.id}: {status}"
