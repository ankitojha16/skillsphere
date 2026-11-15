from django.contrib import admin
from django.utils import timezone
from .models import (
    Opportunity, SavedOpportunity, OpportunityOrganization,
    OpportunityReport, CandidateShortlist, InterviewInvitation
)

@admin.register(OpportunityOrganization)
class OpportunityOrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'website_url', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('name', 'website_url', 'description')
    actions = ['verify_organizations']

    @admin.action(description="Verify selected organizations")
    def verify_organizations(self, request, queryset):
        queryset.update(is_verified=True)


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'category', 'work_mode', 'deadline', 'verification_status', 'is_active', 'last_verified_at')
    list_filter = ('category', 'work_mode', 'verification_status', 'is_active')
    search_fields = ('title', 'organization', 'description', 'required_skills')
    actions = ['verify_listings', 'deactivate_expired', 'refresh_verification_timestamp']

    @admin.action(description="Verify authentic listing status")
    def verify_listings(self, request, queryset):
        queryset.update(verification_status=True, last_verified_at=timezone.now())

    @admin.action(description="Mark selected listings as Inactive")
    def deactivate_expired(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Refresh verification timestamp to Now")
    def refresh_verification_timestamp(self, request, queryset):
        queryset.update(last_verified_at=timezone.now())


@admin.register(OpportunityReport)
class OpportunityReportAdmin(admin.ModelAdmin):
    list_display = ('opportunity', 'reported_by', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('opportunity__title', 'reported_by__username', 'details')
    actions = ['resolve_and_deactivate_opportunity', 'dismiss_reports']

    @admin.action(description="Resolve report and deactivate reported listing")
    def resolve_and_deactivate_opportunity(self, request, queryset):
        for rep in queryset:
            rep.status = 'resolved'
            rep.admin_notes = f"Deactivated listing by staff action {request.user.username}"
            rep.save(update_fields=['status', 'admin_notes'])
            rep.opportunity.is_active = False
            rep.opportunity.save(update_fields=['is_active'])

    @admin.action(description="Dismiss selected reports as resolved/invalid")
    def dismiss_reports(self, request, queryset):
        queryset.update(status='dismissed', admin_notes=f"Dismissed by {request.user.username}")


@admin.register(SavedOpportunity)
class SavedOpportunityAdmin(admin.ModelAdmin):
    list_display = ('user', 'opportunity', 'application_status', 'applied_at', 'created_at')
    list_filter = ('application_status', 'created_at')
    search_fields = ('user__username', 'opportunity__title')


@admin.register(CandidateShortlist)
class CandidateShortlistAdmin(admin.ModelAdmin):
    list_display = ('recruiter', 'candidate', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('recruiter__username', 'candidate__username')


@admin.register(InterviewInvitation)
class InterviewInvitationAdmin(admin.ModelAdmin):
    list_display = ('recruiter', 'candidate', 'opportunity', 'role_title', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('candidate__username', 'recruiter__username', 'role_title', 'company_name')

