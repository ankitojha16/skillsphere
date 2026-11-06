import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_certificates')
    title = models.CharField(max_length=255)
    certificate_id = models.CharField(max_length=64, unique=True, db_index=True)
    issued_at = models.DateTimeField(default=timezone.now)
    verification_status = models.BooleanField(default=True, help_text="Certificate authenticity status")
    criteria_met = models.TextField(blank=True, default="Successfully completed all course lessons, exercises, and assessments.")
    recipient_name = models.CharField(max_length=255, blank=True)
    recipient_title = models.CharField(max_length=150, blank=True, default="Certified Specialist")

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-issued_at']

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            # Deterministic/readable verification ID e.g. SS-CERT-2026-8F3A92D1
            self.certificate_id = f"SS-CERT-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}"
        if not self.recipient_name and self.user:
            profile = getattr(self.user, 'profile', None)
            self.recipient_name = profile.full_name if (profile and profile.full_name) else self.user.get_full_name() or self.user.username
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.certificate_id} ({self.recipient_name})"

    def get_verify_url(self):
        return f"/certificates/verify/{self.certificate_id}/"
