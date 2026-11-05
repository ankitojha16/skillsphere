from django.contrib import admin
from .models import LearningGoal, LearningActivity

@admin.register(LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'target_date', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'target_date', 'created_at')
    search_fields = ('title', 'description', 'user__username')

@admin.register(LearningActivity)
class LearningActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('created_at',)
