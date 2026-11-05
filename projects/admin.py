from django.contrib import admin
from .models import ProjectIdea

@admin.register(ProjectIdea)
class ProjectIdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'difficulty', 'created_at')
    list_filter = ('category', 'difficulty', 'created_at')
    search_fields = ('title', 'description', 'user__username', 'technology_stack')
