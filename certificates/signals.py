from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.db import transaction
from .models import Certificate

@receiver(post_save, sender=Certificate)
@receiver(post_delete, sender=Certificate)
def invalidate_certificate_pdf_cache(sender, instance, **kwargs):
    """
    Invalidates the cached PDF binary when a certificate is updated, reissued, or revoked.
    Uses transaction.on_commit to ensure DB changes persist before cache purge.
    """
    if instance and instance.certificate_id:
        keys_to_clear = [
            f"cert_pdf_{instance.certificate_id}",
            f"cert_pdf_v6_{instance.certificate_id}",
        ]
        def do_delete():
            for k in keys_to_clear:
                cache.delete(k)
        try:
            transaction.on_commit(do_delete)
        except Exception:
            do_delete()
