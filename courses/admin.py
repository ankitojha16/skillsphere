from django.contrib import admin
from .models import Category, Course, Enrollment
from learning.models import Lesson

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('lesson_order', 'chapter_name', 'title', 'estimated_minutes')
    ordering = ('lesson_order',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'instructor_name', 'is_published', 'created_at')
    list_filter = ('category', 'difficulty', 'is_published', 'created_at')
    search_fields = ('title', 'description', 'instructor_name')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline]

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')
    list_filter = ('course', 'enrolled_at')
    search_fields = ('user__username', 'user__email', 'course__title')
    readonly_fields = ('enrolled_at',)
