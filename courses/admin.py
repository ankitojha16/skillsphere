from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Course, Enrollment,
    CourseModule, CourseAssessment, CourseAssessmentQuestion,
    CourseAssessmentAttempt, CourseCompletion,
    CourseBookmark, CourseReview
)
from learning.models import Lesson

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('lesson_order', 'module', 'title', 'estimated_minutes', 'video_type')
    ordering = ('lesson_order',)

class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 1
    fields = ('order', 'title', 'description')
    ordering = ('order',)

class CourseAssessmentInline(admin.TabularInline):
    model = CourseAssessment
    extra = 1
    fields = ('assessment_type', 'title', 'duration_minutes', 'passing_percentage', 'is_active')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'lesson_count')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')
    ordering = ('course', 'order')

    def lesson_count(self, obj):
        return obj.lessons.count()
    lesson_count.short_description = "Lessons"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'difficulty', 'instructor_name',
        'module_count', 'lesson_count', 'completeness_badge', 'is_published'
    )
    list_filter = ('category', 'difficulty', 'is_published', 'created_at')
    search_fields = ('title', 'description', 'instructor_name')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CourseModuleInline, LessonInline, CourseAssessmentInline]

    def module_count(self, obj):
        return obj.modules.count()
    module_count.short_description = "Modules"

    def lesson_count(self, obj):
        return obj.total_lessons_count
    lesson_count.short_description = "Lessons"

    def completeness_badge(self, obj):
        has_mods = obj.modules.exists()
        has_lessons = obj.lessons.exists()
        has_assessments = obj.course_assessments.count() >= 2
        if has_mods and has_lessons and has_assessments:
            return format_html('<span style="color: #22c55e; font-weight: bold;">✔ Complete</span>')
        return format_html('<span style="color: #f59e0b; font-weight: bold;">Incomplete</span>')
    completeness_badge.short_description = "Curriculum Status"

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')
    list_filter = ('course', 'enrolled_at')
    search_fields = ('user__username', 'user__email', 'course__title')
    readonly_fields = ('enrolled_at',)

class QuestionInline(admin.StackedInline):
    model = CourseAssessmentQuestion
    extra = 1
    fields = ('order', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'topic', 'explanation')
    ordering = ('order',)

@admin.register(CourseAssessment)
class CourseAssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'assessment_type', 'duration_minutes', 'passing_percentage', 'question_count', 'is_active')
    list_filter = ('assessment_type', 'is_active', 'course')
    search_fields = ('title', 'course__title')
    inlines = [QuestionInline]

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = "Questions"

@admin.register(CourseAssessmentQuestion)
class CourseAssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'assessment', 'order', 'question_text_short', 'correct_answer', 'topic')
    list_filter = ('assessment__course', 'assessment__assessment_type', 'topic')
    search_fields = ('question_text', 'explanation')
    ordering = ('assessment', 'order')

    def question_text_short(self, obj):
        return obj.question_text[:60] + "..." if len(obj.question_text) > 60 else obj.question_text

@admin.register(CourseAssessmentAttempt)
class CourseAssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'attempt_number', 'score', 'total_questions', 'percentage', 'is_passed', 'completed_at')
    list_filter = ('is_passed', 'assessment__assessment_type', 'assessment__course')
    search_fields = ('user__username', 'assessment__title')
    readonly_fields = ('started_at', 'completed_at')

@admin.register(CourseCompletion)
class CourseCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'learning_progress', 'is_assessment_unlocked', 'is_completed', 'quiz_passed', 'mock_passed', 'updated_at')
    list_filter = ('is_completed', 'is_assessment_unlocked', 'quiz_passed', 'mock_passed')
    search_fields = ('user__username', 'course__title')


@admin.register(CourseBookmark)
class CourseBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('user__username', 'course__title')
    readonly_fields = ('created_at',)


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at', 'course')
    search_fields = ('user__username', 'course__title', 'comment')
    actions = ['approve_reviews', 'disapprove_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = "Hide/Disapprove selected reviews"

