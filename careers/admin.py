from django.contrib import admin
from .models import CareerProfile

@admin.register(CareerProfile)
class CareerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_career_path', 'professional_headline', 'updated_at')
    search_fields = ('user__username', 'user__email', 'professional_headline', 'professional_summary')
    list_filter = ('target_career_path', 'updated_at')
