from django.contrib import admin
from .models import Portfolio, PortfolioProject

class PortfolioProjectInline(admin.TabularInline):
    model = PortfolioProject
    extra = 1

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'username', 'template', 'theme', 'is_public', 'updated_at')
    list_filter = ('template', 'theme', 'is_public')
    search_fields = ('user__username', 'username', 'title', 'about')
    inlines = [PortfolioProjectInline]
    actions = ['make_public', 'make_private']

    @admin.action(description="Mark selected portfolios as Public")
    def make_public(self, request, queryset):
        queryset.update(is_public=True)

    @admin.action(description="Mark selected portfolios as Private")
    def make_private(self, request, queryset):
        queryset.update(is_public=False)

@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'portfolio', 'technologies', 'is_featured', 'display_order')
    list_filter = ('is_featured',)
    search_fields = ('title', 'technologies', 'description')
