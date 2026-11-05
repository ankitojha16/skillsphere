from django.contrib import admin
from .models import CommunityPost, CommunityComment, CommunityLike, ContentReport

@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'is_approved', 'created_at')
    list_filter = ('category', 'is_approved', 'created_at')
    search_fields = ('title', 'content', 'user__username')
    actions = ['approve_posts', 'unapprove_posts']

    @admin.action(description="Approve selected discussion posts")
    def approve_posts(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Hide/Reject selected discussion posts")
    def unapprove_posts(self, request, queryset):
        queryset.update(is_approved=False)

@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('content', 'user__username', 'post__title')

@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'content_type', 'reason', 'status', 'created_at')
    list_filter = ('content_type', 'reason', 'status')
    search_fields = ('reporter__username', 'description')
    actions = ['mark_resolved', 'mark_dismissed']

    @admin.action(description="Mark selected reports as Resolved")
    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved')

    @admin.action(description="Mark selected reports as Dismissed")
    def mark_dismissed(self, request, queryset):
        queryset.update(status='dismissed')
