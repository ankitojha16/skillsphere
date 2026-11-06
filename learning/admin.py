from django.contrib import admin
from .models import (
    Lesson, LessonProgress, VideoProgress, LessonBookmark,
    StudentNote, Exercise, ExerciseSubmission, Assignment, AssignmentSubmission
)

class ExerciseInline(admin.StackedInline):
    model = Exercise
    extra = 0
    fields = ('order', 'title', 'instructions', 'starter_code', 'expected_output', 'hint')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'module', 'lesson_order', 'video_type', 'estimated_minutes', 'created_at')
    list_filter = ('course', 'module', 'video_type')
    search_fields = ('title', 'content', 'course__title')
    ordering = ('course', 'lesson_order')
    inlines = [ExerciseInline]

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'completed_at', 'lesson__course')
    search_fields = ('user__username', 'lesson__title', 'lesson__course__title')
    readonly_fields = ('completed_at',)

@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'last_position_seconds', 'watched_seconds', 'total_duration_seconds', 'is_completed', 'last_accessed')
    list_filter = ('is_completed', 'last_accessed')
    search_fields = ('user__username', 'lesson__title')

@admin.register(LessonBookmark)
class LessonBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'lesson__title')

@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'updated_at')
    search_fields = ('user__username', 'lesson__title', 'content')

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'order')
    list_filter = ('lesson__course',)
    search_fields = ('title', 'instructions')

@admin.register(ExerciseSubmission)
class ExerciseSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'exercise', 'is_passed', 'submitted_at')
    list_filter = ('is_passed', 'submitted_at')
    search_fields = ('user__username', 'exercise__title')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'max_score', 'due_days_after_enroll')
    list_filter = ('course',)
    search_fields = ('title', 'instructions')

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'assignment', 'status', 'score', 'submitted_at')
    list_filter = ('status', 'submitted_at')
    search_fields = ('user__username', 'assignment__title')
