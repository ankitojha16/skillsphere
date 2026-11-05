from django.contrib import admin
from .models import Resume

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'template', 'ats_score', 'is_primary', 'updated_at')
    list_filter = ('template', 'is_primary', 'created_at')
    search_fields = ('title', 'user__username', 'user__email')
