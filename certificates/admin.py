from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'recipient_name', 'title', 'issued_at', 'verification_status')
    list_filter = ('verification_status', 'issued_at')
    search_fields = ('certificate_id', 'recipient_name', 'title', 'user__username', 'user__email')
    readonly_fields = ('certificate_id', 'issued_at')
    actions = ['revoke_certificates', 'restore_certificates']

    @admin.action(description="Revoke certificate validity")
    def revoke_certificates(self, request, queryset):
        queryset.update(verification_status=False)

    @admin.action(description="Restore certificate validity")
    def restore_certificates(self, request, queryset):
        queryset.update(verification_status=True)
