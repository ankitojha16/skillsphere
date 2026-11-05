from django.contrib import admin
from .models import MockInterview, InterviewResponse

class InterviewResponseInline(admin.StackedInline):
    model = InterviewResponse
    extra = 0
    readonly_fields = ('question_order', 'question_text', 'user_answer', 'ai_feedback', 'technical_rating')

@admin.register(MockInterview)
class MockInterviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'difficulty', 'overall_score', 'is_completed', 'created_at')
    list_filter = ('category', 'difficulty', 'is_completed', 'created_at')
    search_fields = ('user__username', 'category')
    inlines = [InterviewResponseInline]
