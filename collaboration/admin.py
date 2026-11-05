from django.contrib import admin
from .models import CollaborationProject, CollaborationMembership, CollaborationRequest

class CollaborationMembershipInline(admin.TabularInline):
    model = CollaborationMembership
    extra = 1

@admin.register(CollaborationProject)
class CollaborationProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'difficulty', 'team_size', 'status', 'created_at')
    list_filter = ('category', 'difficulty', 'status')
    search_fields = ('title', 'description', 'technologies', 'required_roles', 'owner__username')
    inlines = [CollaborationMembershipInline]

@admin.register(CollaborationRequest)
class CollaborationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role_requested', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'project__title', 'message')
