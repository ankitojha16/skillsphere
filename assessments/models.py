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


class CodingChallenge(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]
    CATEGORY_CHOICES = [
        ('Arrays', 'Arrays & Hashing'),
        ('Two_Pointers', 'Two Pointers'),
        ('Sliding_Window', 'Sliding Window'),
        ('Stack', 'Stack & Queues'),
        ('Binary_Search', 'Binary Search'),
        ('Linked_List', 'Linked List'),
        ('Trees', 'Trees & Graphs'),
        ('DP', 'Dynamic Programming'),
        ('Math', 'Math & Geometry'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Easy')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Arrays')
    description = models.TextField(help_text="Detailed problem description markdown or HTML")
    constraints = models.TextField(blank=True, help_text="Constraints list")
    hints = models.TextField(blank=True, help_text="Newline-separated hints")
    python_starter = models.TextField(default="def solution():\n    pass")
    javascript_starter = models.TextField(default="function solution() {\n    // Write your code here\n}")
    function_name = models.CharField(max_length=100, default="solution", help_text="Target function name invoked by test harness")
    xp_reward = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['difficulty', 'title']

    def __str__(self):
        return f"[{self.difficulty}] {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def acceptance_rate(self):
        total = self.submissions.count()
        if total == 0:
            return 85.0
        accepted = self.submissions.filter(status='Accepted').count()
        return round((accepted / total) * 100, 1)

    def get_hints_list(self):
        if not self.hints:
            return []
        return [h.strip() for h in self.hints.split('\n') if h.strip()]

    def get_constraints_list(self):
        if not self.constraints:
            return []
        return [c.strip() for c in self.constraints.split('\n') if c.strip()]


class CodingTestCase(models.Model):
    challenge = models.ForeignKey(CodingChallenge, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField(help_text="JSON serialized argument list, e.g. [[2,7,11,15], 9]")
    expected_output = models.TextField(help_text="JSON serialized expected return value, e.g. [0, 1]")
    is_hidden = models.BooleanField(default=False, help_text="If True, only tested on Submit, hidden on Run Code")
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        visibility = "Hidden" if self.is_hidden else "Visible"
        return f"{self.challenge.title} - Case #{self.order} ({visibility})"


class ChallengeSubmission(models.Model):
    STATUS_CHOICES = [
        ('Accepted', 'Accepted'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Time Limit Exceeded', 'Time Limit Exceeded'),
        ('Runtime Error', 'Runtime Error'),
    ]
    LANGUAGE_CHOICES = [
        ('python', 'Python 3'),
        ('javascript', 'JavaScript ES6'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coding_submissions')
    challenge = models.ForeignKey(CodingChallenge, on_delete=models.CASCADE, related_name='submissions')
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python')
    code = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Accepted')
    runtime_ms = models.PositiveIntegerField(default=25)
    memory_kb = models.PositiveIntegerField(default=14200)
    passed_cases = models.PositiveIntegerField(default=0)
    total_cases = models.PositiveIntegerField(default=0)
    percentile_beats = models.FloatField(default=80.0, help_text="Percentile beats vs all submissions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} ({self.status}) [{self.runtime_ms}ms]"

