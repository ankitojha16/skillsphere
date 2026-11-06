from django.contrib import admin
from .models import UserGamification, Badge, UserBadge, XPTransaction

@admin.register(UserGamification)
class UserGamificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_xp', 'current_level', 'current_streak', 'longest_streak', 'last_activity_date')
    list_filter = ('current_level', 'last_activity_date')
    search_fields = ('user__username', 'user__email')

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'xp_requirement', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')
    list_filter = ('badge', 'awarded_at')
    search_fields = ('user__username', 'badge__name')

@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_key', 'amount', 'reason', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'activity_key', 'reason')
    readonly_fields = ('created_at',)

