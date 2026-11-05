from django.contrib import admin
from .models import LearningRoadmap, RoadmapMilestone

class RoadmapMilestoneInline(admin.TabularInline):
    model = RoadmapMilestone
    extra = 1

@admin.register(LearningRoadmap)
class LearningRoadmapAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'target_skill', 'current_level', 'duration', 'updated_at')
    list_filter = ('current_level', 'created_at')
    search_fields = ('title', 'target_skill', 'user__username')
    inlines = [RoadmapMilestoneInline]
