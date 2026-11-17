import re
import logging
from django.utils import timezone
from .models import ProductEvent

logger = logging.getLogger(__name__)

# Sensitive keys that must NEVER be persisted in analytics metadata
FORBIDDEN_METADATA_KEYS = {
    'password', 'password1', 'password2', 'token', 'secret',
    'auth', 'api_key', 'authorization', 'email', 'phone',
    'credit_card', 'cookie', 'session', 'sessionid', 'csrftoken',
    'invite', 'invite_code', 'code', 'token_hash', 'raw_token',
    'full_name', 'first_name', 'last_name', 'student_name',
    'guardian', 'guardian_email', 'address', 'ssn', 'credentials',
    'private_key', 'file_path', 'absolute_path'
}

RE_EMAIL = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
RE_TOKEN = re.compile(r'\b(c1_[A-Za-z0-9_\-]{16,}|BETA-C1-[A-Za-z0-9_\-]+)\b')
RE_PATH = re.compile(r'(/Users/[^\s]+|/home/[^\s]+|/var/[^\s]+|/tmp/[^\s]+)')


def redact_sensitive_string(val):
    """
    Scans and redacts emails, invite tokens, credentials, and system paths from strings.
    """
    if not isinstance(val, str):
        return val
    val = RE_TOKEN.sub('[REDACTED_TOKEN]', val)
    val = RE_EMAIL.sub('[REDACTED_EMAIL]', val)
    val = RE_PATH.sub('[REDACTED_PATH]', val)
    return val


def sanitize_metadata(meta):
    """
    Strips sensitive keys and deeply redacts PII/tokens from values before storage.
    Ensures metadata is a clean, privacy-shielded JSON-serializable dictionary.
    """
    if not isinstance(meta, dict):
        return {}
    sanitized = {}
    for k, v in meta.items():
        k_lower = str(k).lower().strip()
        if any(bad in k_lower for bad in FORBIDDEN_METADATA_KEYS):
            continue
        # Redact and clean values
        if isinstance(v, str):
            sanitized[k] = redact_sensitive_string(v)[:250]
        elif isinstance(v, (int, float, bool)) or v is None:
            sanitized[k] = v
        elif isinstance(v, (list, tuple)):
            sanitized[k] = [redact_sensitive_string(str(item))[:150] for item in v[:20]]
        elif isinstance(v, dict):
            sanitized[k] = sanitize_metadata(v)
        else:
            sanitized[k] = redact_sensitive_string(str(v))[:200]
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
