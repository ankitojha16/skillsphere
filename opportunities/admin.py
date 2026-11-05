from django.contrib import admin
from .models import Opportunity, SavedOpportunity

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'category', 'work_mode', 'deadline', 'verification_status', 'is_active')
    list_filter = ('category', 'work_mode', 'verification_status', 'is_active')
    search_fields = ('title', 'organization', 'description', 'required_skills')
    actions = ['verify_listings', 'deactivate_expired']

    @admin.action(description="Verify authentic listing status")
    def verify_listings(self, request, queryset):
        queryset.update(verification_status=True)

    @admin.action(description="Mark selected listings as Inactive")
    def deactivate_expired(self, request, queryset):
        queryset.update(is_active=False)

@admin.register(SavedOpportunity)
class SavedOpportunityAdmin(admin.ModelAdmin):
    list_display = ('user', 'opportunity', 'application_status', 'applied_at', 'created_at')
    list_filter = ('application_status', 'created_at')
    search_fields = ('user__username', 'opportunity__title')
