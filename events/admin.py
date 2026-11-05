from django.contrib import admin
from .models import Event, SavedEvent

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'category', 'start_date', 'is_online', 'verification_status', 'is_active')
    list_filter = ('category', 'is_online', 'verification_status', 'is_active')
    search_fields = ('title', 'organizer', 'description', 'location')
    actions = ['verify_events', 'deactivate_events']

    @admin.action(description="Verify authentic organizer status")
    def verify_events(self, request, queryset):
        queryset.update(verification_status=True)

    @admin.action(description="Mark selected events as Inactive")
    def deactivate_events(self, request, queryset):
        queryset.update(is_active=False)

@admin.register(SavedEvent)
class SavedEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'reminder_set', 'created_at')
    search_fields = ('user__username', 'event__title')
