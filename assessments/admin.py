from django.contrib import admin
from .models import SkillAssessment, AssessmentQuestion, AssessmentAttempt, AssessmentResponse

class AssessmentQuestionInline(admin.StackedInline):
    model = AssessmentQuestion
    extra = 1

@admin.register(SkillAssessment)
class SkillAssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'time_limit_minutes', 'is_active')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('title',)
    inlines = [AssessmentQuestionInline]

@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'score', 'total_questions', 'percentage', 'completed_at')
    list_filter = ('assessment__category', 'completed_at')
    search_fields = ('user__username', 'assessment__title')
    readonly_fields = ('completed_at',)
