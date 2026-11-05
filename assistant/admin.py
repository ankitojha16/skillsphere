from django.contrib import admin
from .models import AIConversation, AIMessage

class AIMessageInline(admin.TabularInline):
    model = AIMessage
    extra = 0
    readonly_fields = ('role', 'content', 'created_at')

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'mode', 'created_at', 'updated_at')
    list_filter = ('mode', 'created_at')
    search_fields = ('title', 'user__username')
    inlines = [AIMessageInline]
