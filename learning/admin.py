from django.contrib import admin
from .models import Lesson, LessonProgress

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'chapter_name', 'lesson_order', 'estimated_minutes', 'created_at')
    list_filter = ('course', 'chapter_name')
    search_fields = ('title', 'content', 'course__title')
    ordering = ('course', 'lesson_order')

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'completed_at', 'lesson__course')
    search_fields = ('user__username', 'lesson__title', 'lesson__course__title')
    readonly_fields = ('completed_at',)
