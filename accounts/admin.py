from django.contrib import admin
from .models import StudentProfile

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'role', 'education_level', 'learning_level', 'institution', 'created_at')
    list_filter = ('role', 'learning_level', 'education_level', 'created_at')
    search_fields = ('user__username', 'user__email', 'full_name', 'institution')
    readonly_fields = ('created_at', 'updated_at')
