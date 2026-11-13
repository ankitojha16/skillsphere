import logging
from django.utils import timezone
from .models import ProductEvent

logger = logging.getLogger(__name__)

# Sensitive keys that must NEVER be persisted in analytics metadata
FORBIDDEN_METADATA_KEYS = {
    'password', 'password1', 'password2', 'token', 'secret',
    'auth', 'api_key', 'authorization', 'email', 'phone',
    'credit_card', 'cookie', 'session', 'sessionid', 'csrftoken'
}


def sanitize_metadata(meta):
    """
    Strips any sensitive or PII fields from metadata before storage.
    Ensures metadata is a clean JSON-serializable dictionary.
    """
    if not isinstance(meta, dict):
        return {}
    sanitized = {}
    for k, v in meta.items():
        k_lower = str(k).lower().strip()
        if any(bad in k_lower for bad in FORBIDDEN_METADATA_KEYS):
            continue
        # Convert non-serializable objects to safe string representations
        if isinstance(v, (int, float, bool, str)) or v is None:
            sanitized[k] = v
        elif isinstance(v, (list, tuple)):
            sanitized[k] = [str(item) for item in v[:20]]
        else:
            sanitized[k] = str(v)[:200]
    return sanitized


def track_event(user=None, event_type='', metadata=None, session_key='', idempotent=False, event_key=''):
    """
    Privacy-first telemetry recording.
    - Never raises exceptions that interrupt user flows.
    - Honors user analytics opt-out preference on StudentProfile.
    - Enforces metadata sanitization to protect user privacy.
    - Supports idempotency keys to prevent duplicate event inflation.
    """
    try:
        # Check if user is authenticated
        auth_user = user if (user and getattr(user, 'is_authenticated', False)) else None

        # Respect user's explicit analytics opt-out choice
        if auth_user:
            profile = getattr(auth_user, 'profile', None)
            if profile and getattr(profile, 'analytics_opt_out', False):
                return None
            try:
                from accounts.models import StudentProfile
                if StudentProfile.objects.filter(user=auth_user, analytics_opt_out=True).exists():
                    return None
            except Exception:
                pass

        # Sanitize metadata
        clean_meta = sanitize_metadata(metadata)

        # Idempotency check
        if event_key:
            existing = ProductEvent.objects.filter(event_key=event_key).first()
            if existing:
                return existing

        # Create record
        event = ProductEvent.objects.create(
            user=auth_user,
            event_type=event_type,
            event_key=event_key or '',
            metadata=clean_meta,
            session_key=(session_key or '')[:40],
            timestamp=timezone.now()
        )
        return event
    except Exception as e:
        logger.warning(f"[Analytics] Fail-safe caught event tracking error: {e}", exc_info=False)
        return None
