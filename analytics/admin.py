from django.contrib import admin
from .models import ProductEvent, BetaFeedback


@admin.register(ProductEvent)
class ProductEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_type', 'user', 'timestamp', 'session_key')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('user__username', 'event_type', 'event_key')
    readonly_fields = ('timestamp', 'user', 'event_type', 'event_key', 'metadata', 'session_key')

    def has_add_permission(self, request):
        return False


@admin.register(BetaFeedback)
class BetaFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'status', 'rating', 'user', 'page_url', 'created_at')
    list_filter = ('status', 'category', 'rating', 'created_at')
    search_fields = ('description', 'admin_notes', 'user__username', 'page_url')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'screenshot_data_uri')
