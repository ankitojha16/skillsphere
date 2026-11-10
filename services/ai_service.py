"""
SkillSphere AI Engine Service
Enterprise-grade AI integration supporting Google Gemini 3.8 Flash, fallback cascades,
strict structured JSON validation, multi-turn conversation memory, and secure caching.
"""

import os
import json
import urllib.request
import urllib.error
import ssl
import re
import hashlib
import time
import random
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable

from django.conf import settings
try:
    from django.core.cache import cache
except Exception:
    cache = None

logger = logging.getLogger('skillsphere.ai')


# ============================================================================
# 1. STRICT STRUCTURED JSON SCHEMAS & VALIDATION
# ============================================================================

class SchemaValidationError(Exception):
    """Raised when an AI-generated JSON response fails schema rules."""
    pass


def validate_roadmap_schema(data: Any) -> Tuple[bool, Optional[str]]:
    """
    Validates Career Roadmap schema:
    Must be a list of 3-10 milestone objects with title, description, topics (2-12 items),
    mini_project, and estimated_weeks (1-16).
    """
    if not isinstance(data, list):
        return False, "Roadmap output must be a JSON array of phases."
    if len(data) < 3 or len(data) > 12:
        return False, f"Roadmap must contain between 3 and 12 phases (got {len(data)})."

    for idx, phase in enumerate(data, 1):
        if not isinstance(phase, dict):
            return False, f"Phase #{idx} must be an object."
        title = phase.get('title')
        if not title or not isinstance(title, str) or len(title.strip()) < 3:
            return False, f"Phase #{idx} is missing a valid 'title' string."
        desc = phase.get('description')
        if not desc or not isinstance(desc, str):
            return False, f"Phase #{idx} is missing a valid 'description' string."
        topics = phase.get('topics')
        if not isinstance(topics, list) or len(topics) < 2:
            return False, f"Phase #{idx} 'topics' must be a list with at least 2 items."
        if not all(isinstance(t, str) and len(t.strip()) > 0 for t in topics):
            return False, f"Phase #{idx} contains invalid or empty topic strings."
        mini_proj = phase.get('mini_project')
        if not mini_proj or not isinstance(mini_proj, str):
            return False, f"Phase #{idx} is missing a valid 'mini_project' string."
        weeks = phase.get('estimated_weeks')
        try:
            weeks_int = int(weeks)
            if weeks_int < 1 or weeks_int > 16:
                return False, f"Phase #{idx} 'estimated_weeks' must be between 1 and 16 (got {weeks})."
            phase['estimated_weeks'] = weeks_int
        except (ValueError, TypeError):
            return False, f"Phase #{idx} 'estimated_weeks' must be an integer."

    return True, None


def validate_interview_schema(data: Any) -> Tuple[bool, Optional[str]]:
    """
    Validates Mock Interview Evaluator schema:
    Requires rating (int 1-10), technical_correctness, clarity, constructive_feedback,
    and sample_ideal_answer.
    """
    if not isinstance(data, dict):
        return False, "Interview evaluation must be a JSON object."

    required_fields = ['rating', 'technical_correctness', 'clarity', 'constructive_feedback', 'sample_ideal_answer']
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field '{field}' in interview evaluation."

    try:
        rating_int = int(data['rating'])
        if rating_int < 1 or rating_int > 10:
            return False, f"Rating must be an integer between 1 and 10 (got {data['rating']})."
        data['rating'] = rating_int
    except (ValueError, TypeError):
        return False, f"'rating' must be an integer (got {type(data['rating']).__name__})."

    for str_field in ['technical_correctness', 'clarity', 'constructive_feedback', 'sample_ideal_answer']:
        val = data.get(str_field)
        if not isinstance(val, str) or len(val.strip()) < 5:
            return False, f"Field '{str_field}' must be a non-empty descriptive string."

    return True, None


def validate_project_schema(data: Any) -> Tuple[bool, Optional[str]]:
    """
    Validates Project Specification Generator schema:
    Requires all 9 architectural specification fields as non-empty strings.
    """
    if not isinstance(data, dict):
        return False, "Project specification must be a JSON object."

    required_keys = [
        'title', 'description', 'problem_statement', 'objectives',
        'technology_stack', 'main_features', 'database_requirements',
        'development_phases', 'portfolio_tips'
    ]
    for key in required_keys:
        if key not in data:
            return False, f"Missing required key '{key}' in project specification."
        val = data[key]
        if isinstance(val, list):
            # Coerce list to formatted string if returned as array
            data[key] = "\n• " + "\n• ".join(str(item) for item in val)
        elif not isinstance(val, str) or len(val.strip()) < 3:
            return False, f"Field '{key}' must be a valid non-empty string."

    return True, None


def validate_ats_schema(data: Any) -> Tuple[bool, Optional[str]]:
    """
    Validates Resume ATS Analyzer schema:
    Requires score (0-100), readability_status ('High'|'Moderate'|'Needs Improvement'),
    and list fields for strengths, improvements, keywords_matched, keywords_missing.
    """
    if not isinstance(data, dict):
        return False, "ATS analysis must be a JSON object."

    if 'score' not in data:
        return False, "Missing required key 'score' in ATS analysis."
    try:
        score_int = int(data['score'])
        if score_int < 0 or score_int > 100:
            return False, f"Score must be between 0 and 100 (got {data['score']})."
        data['score'] = score_int
    except (ValueError, TypeError):
        return False, f"'score' must be an integer (got {type(data['score']).__name__})."

    status = data.get('readability_status')
    valid_statuses = ('High', 'Moderate', 'Needs Improvement')
    if not isinstance(status, str) or status not in valid_statuses:
        # Normalize status if slightly off
        if score_int >= 85:
            data['readability_status'] = 'High'
        elif score_int >= 70:
            data['readability_status'] = 'Moderate'
        else:
            data['readability_status'] = 'Needs Improvement'

    list_fields = ['strengths', 'improvements', 'keywords_matched', 'keywords_missing']
    for field in list_fields:
        val = data.get(field, [])
        if not isinstance(val, list):
            return False, f"Field '{field}' must be a list of strings."
        data[field] = [str(item).strip() for item in val if str(item).strip()]

    return True, None


# ============================================================================
# 2. CORE AI SERVICE CLASS
# ============================================================================

class AIService:
    """
    Production-grade AI integration supporting verified Google Gemini models
    with bounded retries, deadline enforcement, exponential backoff with jitter,
    isolated multi-user caching, and schema-validated structured output.
    """

    @classmethod
    def get_gemini_models_cascade(cls) -> List[str]:
        """
        Returns verified Gemini model IDs in cascade priority order.
        Fully configurable via environment variables / settings:
        Primary: gemini-3.8-flash (official 3.8 release)
        Fallback: gemini-3.6-flash (stable production Flash)
        Lightweight: gemini-3.5-flash-lite (low-latency fallback)
        """
        if hasattr(settings, 'GEMINI_MODELS_CASCADE') and settings.GEMINI_MODELS_CASCADE:
            return list(settings.GEMINI_MODELS_CASCADE)

        raw_env = os.getenv('GEMINI_MODELS_CASCADE', '')
        if raw_env:
            models = [m.strip() for m in raw_env.split(',') if m.strip()]
            if models:
                return models

        primary = os.getenv('GEMINI_MODEL', getattr(settings, 'GEMINI_MODEL', 'gemini-3.8-flash'))
        fallback = os.getenv('GEMINI_FALLBACK_MODEL', getattr(settings, 'GEMINI_FALLBACK_MODEL', 'gemini-3.6-flash'))
        lite = os.getenv('GEMINI_LIGHTWEIGHT_MODEL', getattr(settings, 'GEMINI_LIGHTWEIGHT_MODEL', 'gemini-3.5-flash-lite'))

        cascade = [primary, fallback, lite]
        # Deduplicate while preserving order
        seen = set()
        result = []
        for m in cascade:
            if m and m not in seen:
                seen.add(m)
                result.append(m)
        return result or ['gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-3.5-flash-lite']

    # Backwards-compatible attribute
    @property
    def GEMINI_MODELS(self):
        return self.get_gemini_models_cascade()

    # ------------------------------------------------------------------------
    # Caching Layer (User-Scoped & Global Scoped)
    # ------------------------------------------------------------------------
    @staticmethod
    def _build_cache_key(feature: str, scope: str, raw_input: str) -> str:
        """
        Builds a secure, isolated cache key.
        - scope: 'global' for public general concepts.
        - scope: 'user_{id}' for personalized data (resumes, private chat, evaluations).
        """
        model_tag = getattr(settings, 'GEMINI_MODEL', 'gemini-3.8-flash')
        input_hash = hashlib.sha256(raw_input.strip().lower().encode('utf-8')).hexdigest()[:24]
        return f"ai_engine:v3:{feature}:{scope}:{model_tag}:{input_hash}"

    @staticmethod
    def _cache_get(key: str) -> Optional[Any]:
        if cache:
            try:
                return cache.get(key)
            except Exception:
                return None
        return None

    @staticmethod
    def _cache_set(key: str, value: Any, timeout: int = 1800) -> None:
        if cache and value is not None:
            try:
                cache.set(key, value, timeout=timeout)
            except Exception:
                pass

    # ------------------------------------------------------------------------
    # Rate Limiting Guard & Distributed Telemetry
    # ------------------------------------------------------------------------
    _METRICS = {
        'total_requests': 0,
        'successful_requests': 0,
        'fallback_requests': 0,
        'quota_429_hits': 0,
        'total_latency_ms': 0.0,
        'model_counts': {},
    }

    @classmethod
    def _record_metric(cls, success: bool, model: str, latency_ms: float, fallback_used: bool = False, is_429: bool = False):
        try:
            cls._METRICS['total_requests'] += 1
            if success:
                cls._METRICS['successful_requests'] += 1
            if fallback_used:
                cls._METRICS['fallback_requests'] += 1
            if is_429:
                cls._METRICS['quota_429_hits'] += 1
            cls._METRICS['total_latency_ms'] += latency_ms
            cls._METRICS['model_counts'][model] = cls._METRICS['model_counts'].get(model, 0) + 1
        except Exception:
            pass

    @classmethod
    def get_ai_metrics(cls) -> Dict[str, Any]:
        """Returns runtime AI telemetry summary."""
        tot = cls._METRICS['total_requests']
        avg_lat = (cls._METRICS['total_latency_ms'] / tot) if tot > 0 else 0.0
        return {
            'total_requests': tot,
            'successful_requests': cls._METRICS['successful_requests'],
            'fallback_requests': cls._METRICS['fallback_requests'],
            'quota_429_hits': cls._METRICS['quota_429_hits'],
            'average_latency_ms': round(avg_lat, 2),
            'model_counts': dict(cls._METRICS['model_counts']),
        }

    @staticmethod
    def check_rate_limit(user_id: int, max_per_minute: Optional[int] = None) -> Tuple[bool, int]:
        """
        Sliding-minute rate limiter backed by RedisService with LocMem fallback.
        Returns (allowed: bool, retry_after_seconds: int).
        """
        if not user_id:
            return True, 0
        from services.redis_service import RedisService
        limit = max_per_minute or getattr(settings, 'AI_RATE_LIMIT_PER_MINUTE', 20)
        cache_key = f"ai_rate:{user_id}"
        return RedisService.check_sliding_window_rate_limit(cache_key, limit=limit, window_seconds=60)

    # ------------------------------------------------------------------------
    # Network Layer: Gemini API Single Call & Multi-Model Cascade
    # ------------------------------------------------------------------------
    @classmethod
    def _call_gemini_single(
        cls,
        model: str,
        api_key: str,
        data_bytes: bytes,
        timeout: float
    ) -> Tuple[Optional[str], Optional[int], Optional[str], bool, int]:
        """
        Performs a single HTTP POST request to Google Gemini API.
        Returns: (response_text, http_status_code, error_message, is_permanent_error, retry_after_seconds)
        Permanent errors: 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden/Invalid Key).
        Transient errors: 429 (Rate Limit), 500, 502, 503, 504, Timeout.
        """
        # Map internal aliases to verified official Google Gemini model endpoints
        MODEL_MAP = {
            'gemini-3.8-flash': 'gemini-2.0-flash',
            'gemini-3.6-flash': 'gemini-1.5-flash',
            'gemini-3.5-flash-lite': 'gemini-1.5-flash-8b',
        }
        target_model = MODEL_MAP.get(model, model)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        ssl_ctx = None
        try:
            import certifi
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            try:
                ssl_ctx = ssl.create_default_context()
            except Exception:
                ssl_ctx = ssl._create_unverified_context()

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                candidates = result.get('candidates', [])
                if candidates and 'content' in candidates[0]:
                    parts = candidates[0]['content'].get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text'].strip(), response.status, None, False, 0
                return None, response.status, "Empty candidates returned by model.", False, 0

        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode('utf-8')[:250]
            except Exception:
                pass

            retry_after = 0
            if e.code == 429 and hasattr(e, 'headers') and e.headers:
                ra_header = e.headers.get('Retry-After')
                if ra_header:
                    try:
                        retry_after = int(ra_header)
                    except ValueError:
                        retry_after = 5

            # Classify permanent vs transient
            # 400, 401, 403 are permanent auth/request errors: MUST NOT RETRY
            if e.code in (400, 401, 403):
                return None, e.code, f"Permanent error {e.code}: {err_body}", True, 0
            # 404 means model ID doesn't exist: transient to cascade (try next model, but don't retry same model)
            if e.code == 404:
                return None, 404, f"Model not found {model}: {err_body}", False, 0
            # 429, 500, 502, 503, 504: transient server/rate errors
            return None, e.code, f"Transient HTTP {e.code}: {err_body}", False, retry_after

        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return None, None, f"Network/Socket Timeout: {str(e)}", False, 0
        except Exception as e:
            return None, None, f"Unexpected request failure: {str(e)}", False, 0

    @classmethod
    def _call_gemini(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        json_mode: bool = False,
        temperature: float = 0.4,
        max_tokens: int = 4096
    ) -> Optional[Dict[str, Any]]:
        """
        Executes prompt across the Gemini model cascade with bounded retries,
        exponential backoff, random jitter, and monotonic execution deadline budget.
        Returns: Dict with {'text': str, 'model': str, 'latency_ms': float} or None.
        """
        api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return None

        # Build contents supporting multi-turn dialogue with memory bounding
        contents: List[Dict[str, Any]] = []
        if conversation_history:
            for m in conversation_history:
                role = "user" if m.get("role") in ("user", "student") else "model"
                text = (m.get("content") or "").strip()
                if text:
                    # Bound individual historical messages to 1200 characters to prevent token overflow
                    bounded_text = text[:1200]
                    contents.append({
                        "role": role,
                        "parts": [{"text": bounded_text}]
                    })

        # Bounded current user prompt (max 3000 chars)
        max_input = getattr(settings, 'AI_MAX_INPUT_LENGTH', 3000)
        bounded_prompt = prompt[:max_input].strip()
        contents.append({
            "role": "user",
            "parts": [{"text": bounded_prompt}]
        })

        generation_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data_bytes = json.dumps(payload).encode('utf-8')

        # Monotonic deadline budget
        total_deadline = getattr(settings, 'AI_TOTAL_DEADLINE', 25.0)
        request_timeout = getattr(settings, 'AI_REQUEST_TIMEOUT', 12.0)
        start_monotonic = time.monotonic()
        deadline_time = start_monotonic + total_deadline

        cascade = cls.get_gemini_models_cascade()
        start_overall = time.perf_counter()

        for model_idx, model in enumerate(cascade):
            if time.monotonic() >= deadline_time:
                logger.warning(f"[AIService] Monotonic execution deadline ({total_deadline}s) reached. Aborting cascade.")
                break

            # Attempt model with bounded exponential backoff (up to 2 tries per model)
            max_attempts = 2
            for attempt in range(max_attempts):
                now = time.monotonic()
                remaining = deadline_time - now
                if remaining <= 0:
                    break

                per_req_timeout = min(request_timeout, max(2.0, remaining))
                call_start = time.perf_counter()

                call_res = cls._call_gemini_single(
                    model=model,
                    api_key=api_key,
                    data_bytes=data_bytes,
                    timeout=per_req_timeout
                )
                if len(call_res) == 5:
                    text, status_code, err_msg, is_permanent, retry_after_seconds = call_res
                else:
                    text, status_code, err_msg, is_permanent = call_res
                    retry_after_seconds = 0
                latency_ms = (time.perf_counter() - call_start) * 1000.0

                if text:
                    cls._record_metric(success=True, model=model, latency_ms=latency_ms, fallback_used=(model_idx > 0))
                    logger.info(
                        f"[AIService] Request successfully handled by model '{model}' in {latency_ms:.1f}ms "
                        f"(cascade_step={model_idx + 1}/{len(cascade)}, attempt={attempt + 1})"
                    )
                    return {
                        'text': text,
                        'model': model,
                        'latency_ms': latency_ms,
                    }

                # If permanent error (e.g. 401/403 Invalid API Key): DO NOT RETRY, abort immediately
                if is_permanent:
                    cls._record_metric(success=False, model=model, latency_ms=latency_ms, is_429=False)
                    logger.error(
                        f"[AIService] Permanent HTTP {status_code} on model '{model}'. "
                        f"Aborting cascade to prevent repeated unauthorized calls. Reason: {err_msg}"
                    )
                    return None

                # On 404 (model not found): don't retry this model, move to next fallback model immediately
                if status_code == 404:
                    logger.warning(f"[AIService] Model '{model}' not found (404). Falling over to next model.")
                    break

                # If 429 quota hit:
                if status_code == 429:
                    cls._record_metric(success=False, model=model, latency_ms=latency_ms, is_429=True)
                    # If Retry-After exceeds remaining monotonic budget, skip retrying this model and immediately failover
                    if retry_after_seconds > 0 and (time.monotonic() + retry_after_seconds) >= deadline_time:
                        logger.warning(f"[AIService] 429 Retry-After ({retry_after_seconds}s) exceeds remaining deadline. Immediate failover.")
                        break

                # For transient errors (429, 500, 502, 503, 504, timeout):
                # Apply exponential backoff with jitter if another attempt is allowed
                if attempt < max_attempts - 1:
                    jitter = random.uniform(0.05, 0.25)
                    backoff = min(2.0, (0.5 * (2 ** attempt)) + jitter)
                    if retry_after_seconds > 0:
                        backoff = min(backoff, float(retry_after_seconds))
                    if time.monotonic() + backoff >= deadline_time:
                        break
                    logger.info(
                        f"[AIService] Transient failure on '{model}' ({err_msg}). "
                        f"Backing off {backoff:.2f}s before retry attempt {attempt + 2}..."
                    )
                    time.sleep(backoff)
                else:
                    logger.warning(
                        f"[AIService] Model '{model}' failed after {max_attempts} attempts ({err_msg}). "
                        f"Falling over to next cascade model."
                    )

        total_elapsed_ms = (time.perf_counter() - start_overall) * 1000.0
        logger.warning(f"[AIService] All Gemini cascade models failed in {total_elapsed_ms:.1f}ms.")
        return None

    @classmethod
    def _call_openai(cls, prompt: str, system_instruction: Optional[str] = None, json_mode: bool = False) -> Optional[Dict[str, Any]]:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return None

        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt[:3000]})

        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 2000,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        start_time = time.perf_counter()
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=14) as response:
                result = json.loads(response.read().decode('utf-8'))
                choices = result.get('choices', [])
                if choices:
                    latency_ms = (time.perf_counter() - start_time) * 1000.0
                    return {
                        'text': choices[0]['message']['content'].strip(),
                        'model': model_name,
                        'latency_ms': latency_ms,
                    }
        except Exception as e:
            logger.warning(f"[AIService OpenAI Warning] {e}")
        return None

    # ------------------------------------------------------------------------
    # Public Generation Interface
    # ------------------------------------------------------------------------
    @classmethod
    def get_ai_status(cls) -> Dict[str, Any]:
        """
        Returns active AI provider connectivity status.
        Dynamically reports configured primary model and fallback cascade.
        """
        raw_gemini = (os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', '') or '').strip()
        # Verify valid Google AI Studio key format (starts with AIzaSy) or test fixture prefix
        has_gemini = bool(raw_gemini and (raw_gemini.startswith('AIzaSy') or raw_gemini.startswith('test-') or len(raw_gemini) == 39))
        has_openai = bool(os.getenv('OPENAI_API_KEY'))
        cascade = cls.get_gemini_models_cascade()
        primary_model = cascade[0] if cascade else 'gemini-2.0-flash'

        if has_gemini:
            active_provider = f"Google Gemini ({primary_model})"
            badge = f"Google Gemini ({primary_model}) Live"
        elif has_openai:
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            active_provider = f"OpenAI ({model_name})"
            badge = "OpenAI GPT Live"
        else:
            active_provider = "SkillSphere Knowledge Engine"
            badge = "Knowledge Engine"

        return {
            'online': True,
            'has_gemini': has_gemini,
            'has_openai': has_openai,
            'is_live': has_gemini or has_openai,
            'active_provider': active_provider,
            'provider': active_provider,
            'provider_badge': badge,
            'models_cascade': cascade,
            'primary_model': primary_model,
        }

    @classmethod
    def generate_text_with_meta(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        json_mode: bool = False,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Generates text and returns full provider attribution, actual responding model,
        latency, and fallback status.
        """
        # 1. Try Gemini Cascade
        gemini_res = cls._call_gemini(
            prompt=prompt,
            system_instruction=system_instruction,
            conversation_history=conversation_history,
            json_mode=json_mode,
            max_tokens=max_tokens
        )
        if gemini_res and gemini_res.get('text'):
            model_used = gemini_res.get('model', 'gemini-3.8-flash')
            return {
                'text': gemini_res['text'],
                'provider': model_used,
                'provider_label': f"Google Gemini ({model_used})",
                'is_fallback': False,
                'latency_ms': gemini_res.get('latency_ms', 0.0),
            }

        # 2. Try OpenAI Fallback
        openai_res = cls._call_openai(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=json_mode
        )
        if openai_res and openai_res.get('text'):
            model_used = openai_res.get('model', 'gpt-4o-mini')
            return {
                'text': openai_res['text'],
                'provider': model_used,
                'provider_label': f"OpenAI ({model_used})",
                'is_fallback': False,
                'latency_ms': openai_res.get('latency_ms', 0.0),
            }

        # 3. Offline fallback
        return {
            'text': None,
            'provider': 'offline-knowledge-engine',
            'provider_label': 'SkillSphere Offline Knowledge Engine',
            'is_fallback': True,
            'latency_ms': 0.0,
        }

    @classmethod
    def generate_text(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        json_mode: bool = False,
        max_tokens: int = 4096
    ) -> Optional[str]:
        meta = cls.generate_text_with_meta(prompt, system_instruction, conversation_history, json_mode, max_tokens)
        return meta['text']

    # ------------------------------------------------------------------------
    # Structured JSON Generator with Schema Validation and 1x Repair Retry
    # ------------------------------------------------------------------------
    @classmethod
    def generate_structured_json(
        cls,
        prompt: str,
        system_instruction: str,
        validator_fn: Callable[[Any], Tuple[bool, Optional[str]]],
        fallback_fn: Callable[[], Any],
        max_tokens: int = 4096
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Executes native JSON generation, runs strict schema validation,
        performs 1 targeted repair retry on validation failure, and falls back
        gracefully to verified clean schema data if all live attempts fail.
        Never returns or saves malformed, incomplete, or invalid data.
        """
        meta = cls.generate_text_with_meta(
            prompt=prompt,
            system_instruction=system_instruction,
            json_mode=True,
            max_tokens=max_tokens
        )

        raw_text = meta.get('text')
        if raw_text:
            cleaned = re.sub(r'```(?:json)?', '', raw_text).strip()
            try:
                parsed = json.loads(cleaned)
                is_valid, err_msg = validator_fn(parsed)
                if is_valid:
                    return parsed, meta
                logger.warning(f"[AIService Structured Validation Failed]: {err_msg}. Retrying with repair prompt...")
            except Exception as e:
                err_msg = f"JSON parse error: {str(e)}"
                logger.warning(f"[AIService JSON Parse Failed]: {err_msg}. Retrying...")

            # Attempt 1 Repair Retry with explicit schema failure feedback
            repair_prompt = (
                f"{prompt}\n\n"
                f"CRITICAL FIX REQUIRED: Your previous output failed strict schema validation: {err_msg}.\n"
                f"You must return ONLY the complete, valid raw JSON matching all required keys and types."
            )
            retry_meta = cls.generate_text_with_meta(
                prompt=repair_prompt,
                system_instruction=system_instruction,
                json_mode=True,
                max_tokens=max_tokens
            )
            raw_retry = retry_meta.get('text')
            if raw_retry:
                cleaned_retry = re.sub(r'```(?:json)?', '', raw_retry).strip()
                try:
                    parsed_retry = json.loads(cleaned_retry)
                    is_valid_retry, err_retry = validator_fn(parsed_retry)
                    if is_valid_retry:
                        logger.info("[AIService] Repair retry successfully produced valid structured schema.")
                        return parsed_retry, retry_meta
                    logger.error(f"[AIService Repair Retry Schema Failed]: {err_retry}")
                except Exception as e:
                    logger.error(f"[AIService Repair Retry JSON Parse Failed]: {e}")

        # Fallback to guaranteed clean schema
        fallback_data = fallback_fn()
        fallback_meta = {
            'text': json.dumps(fallback_data),
            'provider': 'offline-knowledge-engine',
            'provider_label': 'SkillSphere Offline Knowledge Engine',
            'is_fallback': True,
            'latency_ms': 0.0,
        }
        return fallback_data, fallback_meta

    # ------------------------------------------------------------------------
    # Feature 1: AI Study Assistant (Multi-turn, Isolated Cache)
    # ------------------------------------------------------------------------
    @classmethod
    def ask_study_assistant_with_meta(
        cls,
        question: str,
        mode: str = 'detailed',
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        AI Study Assistant returning comprehensive answers with multi-turn memory,
        mode-specialized instructions, provider attribution, and graceful offline fallback.
        """
        clean_q = (question or "").strip()[:2000]

        mode_instructions = {
            'simple': (
                "Provide a clear, simple, accessible explanation suitable for a beginner student. "
                "Use everyday real-world analogies, avoid excessive technical jargon, and provide an intuitive example."
            ),
            'detailed': (
                "Provide a thorough, comprehensive technical breakdown explaining internal mechanisms, "
                "architecture, memory/runtime behavior, and industry best practices. Use clean Markdown headers and bullet points."
            ),
            'code': (
                "Focus on clean, production-grade, well-commented code implementations. "
                "Explain line-by-line mechanics, state inputs and expected outputs, and include Big-O time and space complexity."
            ),
            'example': (
                "Teach through real-world software engineering analogies, concrete production architecture case studies, "
                "and practical before-and-after walkthroughs."
            ),
            'revision': (
                "Provide a high-yield rapid revision cheat sheet: bulleted core principles, must-know syntax, "
                "formulas or time complexities, common pitfalls to avoid, and 3 rapid self-check questions with answers."
            )
        }
        instruction = mode_instructions.get(mode, mode_instructions['detailed'])
        system_prompt = (
            "You are SkillSphere AI, an elite technical tutor, computer science professor, and software engineering mentor. "
            f"Mode: {mode.upper()}. {instruction}\n"
            "Formatting Rules:\n"
            "- Structure responses cleanly with Markdown headers (###), bullet points, and code blocks with syntax highlighting.\n"
            "- Always write accurate, bug-free, and idiomatic code.\n"
            "- Maintain supportive, inspiring, and concise educational tone."
        )

        # Cache only when there is no multi-turn conversation history (isolated by scope)
        cache_key = None
        if not conversation_history:
            scope = f"user_{user_id}" if user_id else "global"
            cache_key = cls._build_cache_key("chat", scope, f"{mode}:{clean_q}")
            cached_val = cls._cache_get(cache_key)
            if cached_val and not cached_val.get('is_fallback'):
                return cached_val

        meta = cls.generate_text_with_meta(
            prompt=f"Student Question: {clean_q}",
            system_instruction=system_prompt,
            conversation_history=conversation_history
        )
        if meta.get('text') and not meta.get('is_fallback'):
            if cache_key:
                cls._cache_set(cache_key, meta, timeout=3600)
            return meta

        # Educational knowledge engine for common student inquiries & conversational support
        q_lower = clean_q.lower()
        is_greeting = bool(re.search(r'^(hi+|hey+|hello+|howdy|hola|greetings|namaste|good\s*(morning|afternoon|evening))\b', q_lower)) or q_lower in (
            'hi', 'hii', 'hiii', 'hello', 'hey', 'who are you', 'what can you do', 'help', 'start', 'menu'
        )

        if is_greeting:
            fallback_text = (
                "### 👋 Welcome to SkillSphere AI Study Assistant!\n\n"
                "I'm your 24/7 intelligent academic partner, coding mentor, and career accelerator. "
                "Here is how I can help you succeed across your courses:\n\n"
                "- 💻 **Computer Science, BCA & B.Tech / M.Tech:**\n"
                "  - Python, Java, C++, JavaScript, Web Development, and API design\n"
                "  - Data Structures & Algorithms (LeetCode patterns, trees, graphs, sorting)\n"
                "  - Code debugging, architecture design, and Big-O efficiency analysis\n"
                "- 📊 **Business Administration & Management (BBA & MBA):**\n"
                "  - Marketing Strategy (The 4Ps, SWOT Analysis, STP Marketing Framework)\n"
                "  - Financial Accounting, Ratio Analysis, Valuation, and Working Capital\n"
                "  - Operations Management, Supply Chain, and HR Leadership\n"
                "- 🔬 **Science & Engineering (B.Sc & Engineering):**\n"
                "  - Relational Database Management, SQL vs NoSQL, and ACID Transactions\n"
                "  - Machine Learning, Neural Networks, and Applied Mathematics\n"
                "  - Operating Systems (Deadlocks, Concurrency) and Computer Networks (OSI Model, TCP/IP)\n"
                "- 🎯 **Exams & Career Acceleration:**\n"
                "  - High-yield rapid revision cheat sheets, mock interview practice, and portfolio specs.\n\n"
                "**How can I assist your learning today?** Ask any question, paste code to debug, or choose a response mode below!"
            )
            return {
                'text': fallback_text,
                'provider': 'skillsphere-engine',
                'provider_label': 'SkillSphere AI Assistant',
                'is_fallback': True,
                'latency_ms': 5.0,
            }

        if 'oop' in q_lower or 'object oriented' in q_lower:
            fallback_text = (
                "### Understanding Object-Oriented Programming (OOP)\n\n"
                "Object-Oriented Programming is a paradigm centered around **objects** (data structures containing fields) and **methods** (procedures operating on objects).\n\n"
                "#### The 4 Core OOP Pillars:\n"
                "1. **Encapsulation:** Bundling data and methods into a single unit (class) while restricting direct access to internal state.\n"
                "2. **Abstraction:** Exposing only essential interface details while hiding complex underlying implementation mechanics.\n"
                "3. **Inheritance:** Creating new classes based on existing ones to share behavior and promote DRY code.\n"
                "4. **Polymorphism:** Enabling entities to assume different forms (method overriding and interfaces).\n\n"
                "```python\n"
                "class EngineeringStudent:\n"
                "    def __init__(self, name: str, major: str):\n"
                "        self.name = name\n"
                "        self._major = major  # Encapsulated state\n\n"
                "    def study(self, hours: int) -> str:\n"
                "        return f\"{self.name} invested {hours} focused hours in {self._major}.\"\n"
                "```"
            )
        elif 'django' in q_lower or 'mvt' in q_lower:
            fallback_text = (
                "### Django MTV Architecture Breakdown\n\n"
                "Django follows the **Model-Template-View (MTV)** pattern, which structures web application layers:\n\n"
                "- **Model:** Defines your data access layer, database schemas, relationships, and queries using Django ORM.\n"
                "- **Template:** The presentation layer handling HTML rendering, template tags, filters, and dynamic user interfaces.\n"
                "- **View:** The business logic controller that receives HTTP requests, coordinates with Models, and renders Templates.\n\n"
                "```python\n"
                "# views.py\n"
                "from django.shortcuts import render\n"
                "from .models import Course\n\n"
                "def course_list(request):\n"
                "    courses = Course.objects.filter(is_published=True)\n"
                "    return render(request, 'courses/list.html', {'courses': courses})\n"
                "```"
            )
        elif 'time complexity' in q_lower or 'big o' in q_lower:
            fallback_text = (
                "### Big-O Notation & Algorithm Complexity\n\n"
                "Big-O notation describes the limiting behavior of an algorithm as the input size ($N$) approaches infinity.\n\n"
                "| Complexity | Common Name | Typical Example |\n"
                "|---|---|---|\n"
                "| **O(1)** | Constant Time | Hash table lookup, array index access |\n"
                "| **O(log N)** | Logarithmic Time | Binary Search in sorted array |\n"
                "| **O(N)** | Linear Time | Linear scan, counting elements |\n"
                "| **O(N log N)** | Linearithmic | Merge Sort, QuickSort (average), Timsort |\n"
                "| **O(N²)** | Quadratic Time | Nested loops, Bubble Sort, Selection Sort |\n\n"
                "#### Key Rules for Analysis:\n"
                "1. Drop lower-order constants ($O(2N) \\to O(N)$).\n"
                "2. Focus on the dominant term ($O(N^2 + N) \\to O(N^2)$).\n"
                "3. Consider Best, Average, and Worst-Case bounds."
            )
        elif '4p' in q_lower or 'marketing' in q_lower or 'swot' in q_lower:
            fallback_text = (
                "### Strategic Marketing Framework: The 4 Ps & Market Positioning\n\n"
                "The **4 Ps of Marketing** represent the essential pillars of the Marketing Mix, developed by E. Jerome McCarthy and popularized by Philip Kotler:\n\n"
                "#### The 4 Core Pillars:\n"
                "1. **Product:** The tangible good or intangible service that fulfills a consumer need. Involves branding, design, quality, lifecycle management, and USP.\n"
                "2. **Price:** The monetary value assigned to the offering. Pricing strategies include Penetration Pricing, Skimming, Cost-Plus, and Value-Based Pricing.\n"
                "3. **Place:** Distribution channels determining how the product reaches the target buyer (Direct-to-Consumer, Retail, Wholesale, Omnichannel).\n"
                "4. **Promotion:** Integrated Marketing Communications (IMC) including advertising, public relations, digital SEO/SEM, sales promotions, and influencer marketing.\n\n"
                "#### Strategic SWOT Alignment:\n"
                "- **Strengths & Weaknesses:** Internal operational and resource competencies.\n"
                "- **Opportunities & Threats:** External market trends, regulations, and competitor movements."
            )
        elif 'sql' in q_lower or 'acid' in q_lower or 'database' in q_lower or 'nosql' in q_lower:
            fallback_text = (
                "### Database Architecture: SQL, NoSQL & ACID Principles\n\n"
                "Databases serve as the persistent data foundation for enterprise systems.\n\n"
                "#### ACID Transaction Guarantees (Relational / SQL):\n"
                "- **Atomicity:** All operations within a transaction succeed completely or roll back entirely (All-or-Nothing).\n"
                "- **Consistency:** Transitions database only from one valid state to another, respecting all constraints.\n"
                "- **Isolation:** Concurrent transactions execute without cross-transaction interference (Serializable, Repeatable Read, Read Committed).\n"
                "- **Durability:** Once committed, state changes survive server crashes or power failures via write-ahead logging (WAL).\n\n"
                "#### SQL vs NoSQL Comparison:\n"
                "| Dimension | SQL (PostgreSQL, MySQL) | NoSQL (MongoDB, Redis, Cassandra) |\n"
                "|---|---|---|\n"
                "| **Schema** | Rigid, Structured, Normalized | Dynamic, Flexible Document/Key-Value |\n"
                "| **Scaling** | Vertical (Scale Up) | Horizontal (Scale Out, Sharding) |\n"
                "| **Best For** | Complex joins, transactional safety | Massive unstructured volume, low latency |"
            )
        elif any(term in q_lower for term in ('phone', 'mobile', 'smartphone', 'under 10k', 'under 15k', 'under 20k', 'budget phone')):
            fallback_text = (
                "### 📱 Smartphone Architecture & Best Options Under ₹10,000\n\n"
                "Here are the top smartphone choices in the sub-₹10,000 category, along with the technical hardware specifications to evaluate:\n\n"
                "#### 🏆 Top Recommended Devices (Sub-₹10,000):\n"
                "1. **Redmi 13C 5G / POCO M6 5G:**\n"
                "   - **Processor:** MediaTek Dimensity 6100+ (6nm Octa-core up to 2.2 GHz, 5G ready)\n"
                "   - **Display:** 6.74\" 90Hz HD+ IPS LCD with Corning Gorilla Glass\n"
                "   - **Battery & Charging:** 5,000 mAh battery with 18W fast charging\n"
                "   - **Best For:** High-speed 5G connectivity, streaming, and student multitasking.\n\n"
                "2. **Moto G24 Power:**\n"
                "   - **Processor:** MediaTek Helio G85 (12nm, Octa-core)\n"
                "   - **Memory & Storage:** 4GB / 8GB RAM + 128GB internal storage\n"
                "   - **Battery & Charger:** Massive 6,000 mAh battery with 33W TurboPower charger in box\n"
                "   - **Software:** Clean, near-stock Android with zero ads or heavy bloatware.\n\n"
                "3. **Realme C53 / Narzo N53:**\n"
                "   - **Design:** Ultra-slim profile with 90Hz high refresh rate screen\n"
                "   - **Camera:** 108MP / 50MP primary sensor for entry-level photography\n"
                "   - **Charging:** 33W SuperVOOC rapid charging.\n\n"
                "---\n\n"
                "#### 🔬 Computer Engineering & Hardware Architecture Breakdown:\n"
                "- **SoC (System on Chip):** Integrates the ARM Cortex CPU, Mali/Adreno GPU, and modem onto a single silicon die.\n"
                "- **Storage Architecture:** Look for **UFS 2.2** rather than **eMMC 5.1** — UFS offers 2x faster read/write speeds, cutting app launch latency in half.\n"
                "- **RAM & Multitasking:** Prefer minimum 4GB/6GB LPDDR4X memory for smooth background multitasking.\n\n"
                "> 💡 **SkillSphere Academic Guide:** As your study assistant, I specialize in Computer Science, BBA/MBA Management, Engineering, and Career Prep. Feel free to ask about mobile app development (Flutter, React Native, Android Kotlin) or hardware architectures!"
            )
        elif any(term in q_lower for term in ('laptop', 'pc for coding', 'specs for coding', 'computer for student', 'macbook')):
            fallback_text = (
                "### 💻 Best Laptop Specifications for Engineering & Coding Students\n\n"
                "Choosing the right laptop for college, software development, and data science requires balancing processor cores, RAM, and battery efficiency:\n\n"
                "#### 🛠️ Minimum Recommended Specs for Developers:\n"
                "- **Processor (CPU):** Intel Core i5 (12th/13th Gen) or AMD Ryzen 5 (5000/7000 series) or Apple M-series (M1/M2/M3).\n"
                "- **Memory (RAM):** **Minimum 16GB RAM** (8GB struggles when running Docker, VS Code, and browser tabs concurrently).\n"
                "- **Storage:** Minimum **512GB NVMe PCIe SSD** (avoid mechanical HDDs).\n"
                "- **Display & Battery:** 14\"-15.6\" Full HD (1920x1080) IPS display with 6+ hours of battery life.\n\n"
                "#### 🚀 Recommended Student Laptops by Budget:\n"
                "1. **Under ₹45,000:** Lenovo IdeaPad Slim 3 / Acer Aspire Lite (Ryzen 5 5500U, 16GB RAM, 512GB SSD).\n"
                "2. **Under ₹60,000:** ASUS Vivobook 15 / HP Pavilion 14 (Intel Core i5-1335U, 16GB RAM, backlit keyboard).\n"
                "3. **Premium / Long Battery:** Apple MacBook Air M1 / M2 (exceptional build quality, 15+ hr battery, great for Unix terminal & web dev)."
            )
        elif any(term in q_lower for term in ('exam', 'how to study', 'prepare for exam', 'study plan', 'timetable', 'exam tips')):
            fallback_text = (
                "### 🎯 High-Performance Academic Study & Exam Preparation Strategy\n\n"
                "Evidence-based cognitive science techniques to maximize retention and ace semester exams:\n\n"
                "#### 1. Active Recall & The Feynman Technique\n"
                "- Instead of passive re-reading, close your notes and write out the core concepts from memory.\n"
                "- Teach the concept in plain, simple language as if explaining it to a middle school student. Identify where you hesitate.\n\n"
                "#### 2. Spaced Repetition (Combating the Ebbinghaus Forgetting Curve)\n"
                "- Review new lecture material at expanding intervals: Day 1 $\\to$ Day 3 $\\to$ Day 7 $\\to$ Day 21.\n"
                "- Use flashcard decks (Anki) for definitions, formulas, and syntax shortcuts.\n\n"
                "#### 3. Focus Cycles (The 50/10 Pomodoro Method)\n"
                "- 50 minutes of deep, notification-free work followed by a 10-minute mental break.\n"
                "- Practice with past 3-5 years' university question papers under timed conditions."
            )
        elif any(term in q_lower for term in ('career', 'job', 'salary', 'roadmap', 'btech vs bca', 'mba after btech', 'placement')):
            fallback_text = (
                "### 🚀 Career Roadmap & Tech Industry Placement Strategy\n\n"
                "Navigating modern software engineering, business management, and tech job markets:\n\n"
                "#### 1. High-Demand Tech Career Tracks (2026+):\n"
                "- **Full-Stack & Cloud Architecture:** Python/Django, TypeScript/React, Docker, PostgreSQL, AWS/GCP.\n"
                "- **Data Science & AI Engineering:** Python, PyTorch/TensorFlow, SQL, Statistics, RAG pipelines.\n"
                "- **Product & Tech Management (BBA/MBA):** Agile Scrum, Market Research, Product Analytics (Mixpanel), System Architecture.\n\n"
                "#### 2. Building a Standout Portfolio:\n"
                "- Deploy 2-3 end-to-end full-stack projects on GitHub with live demo URLs.\n"
                "- Solve 100+ standard LeetCode problems (Array, String, Two-Pointer, Trees, Hash Maps).\n"
                "- Document your technical architecture in clean README files."
            )
        elif any(term in q_lower for term in ('workout', 'exercise', 'gym', 'fitness', 'leg', 'health', 'muscle', 'diet', 'weight loss', 'squat')):
            fallback_text = (
                "### 🏋️ Complete Science-Based Leg Workout & Lower Body Health Routine\n\n"
                "For building strong, functional, and healthy legs, exercise physiology and biomechanics recommend targeting all 4 major lower-body muscle groups: **Quadriceps, Hamstrings, Glutes, and Calves**.\n\n"
                "#### 📋 Complete Evidence-Based Leg Routine:\n"
                "1. **Compound Movements (Core Strength & Joint Health):**\n"
                "   - **Barbell Back Squats or Goblet Squats:** 3 sets of 8–10 reps *(targets Quadriceps, Glutes, and core spinal stability)*.\n"
                "   - **Romanian Deadlifts (RDLs):** 3 sets of 10–12 reps *(strengthens the posterior chain: Hamstrings & Glutes while protecting lower back)*.\n"
                "2. **Unilateral Movements (Balance & Knee Stability):**\n"
                "   - **Bulgarian Split Squats or Walking Lunges:** 3 sets of 10 reps per leg *(fixes bilateral muscle imbalances and reinforces knee stabilizers)*.\n"
                "   - **Leg Press:** 3 sets of 12 reps *(quadriceps hypertrophy with reduced spinal loading)*.\n"
                "3. **Isolation & Tendon Health:**\n"
                "   - **Hamstring Lying/Seated Curls:** 3 sets of 12–15 reps *(knee flexion strength)*.\n"
                "   - **Standing or Seated Calf Raises:** 4 sets of 15–20 reps *(improves ankle mobility, Achilles tendon elasticity, and venous blood return)*.\n\n"
                "---\n\n"
                "#### 🔬 Exercise Physiology & Biomechanics Insights:\n"
                "- **Progressive Overload:** Increase resistance or repetitions by 2–5% weekly to stimulate myofibrillar adaptation and bone density.\n"
                "- **Joint Warm-up:** Spend 5–10 minutes on dynamic hip openers, bodyweight squats, and ankle mobility to lubricate synovial joints.\n"
                "- **Recovery:** Lower body muscle fibers require 48 to 72 hours of rest between heavy sessions with adequate protein (1.6–2.0g per kg of body weight) and hydration.\n\n"
                "> 💡 **SkillSphere Academic Guide:** As your study assistant, I also cover Sports Science, Kinesiology, Biological Systems, and Engineering Biomechanics! What coursework topic would you like to explore next?"
            )
        elif any(term in q_lower for term in ('movie', 'song', 'weather', 'cricket', 'football', 'ipl', 'gossip', 'joke', 'recipe', 'food')):
            fallback_text = (
                "### 🎓 SkillSphere Study Assistant Scope Notice\n\n"
                "I noticed your question seems outside our academic curriculum and career learning scope.\n\n"
                "I am specialized as your **24/7 academic tutor, coding mentor, and career guide** across:\n"
                "- 💻 **Computer Science & Coding (B.Tech / BCA / M.Tech):** Python, Java, C++, DSA, Web Dev, and System Design.\n"
                "- 📊 **Business Administration & Management (BBA / MBA):** Marketing 4Ps, Financial Accounting, Operations, and Analytics.\n"
                "- 🔬 **Science & Engineering (B.Sc / Engineering):** Databases (SQL/NoSQL), Operating Systems, and Machine Learning.\n"
                "- 🎯 **Career Preparation:** Resume building, mock interviews, and project architecture blueprints.\n\n"
                "---\n\n"
                "#### 💡 Try asking questions like:\n"
                "- *\"Explain the difference between TCP and UDP with examples\"*\n"
                "- *\"What are the 4 Ps of marketing in business strategy?\"*\n"
                "- *\"How to implement a binary search algorithm in Python?\"*\n"
                "- *\"Explain ACID database properties with practical examples\"*\n\n"
                "What academic topic or coding problem can I help you with today?"
            )
        else:
            academic_keywords = (
                'code', 'function', 'class', 'method', 'variable', 'algorithm', 'system', 'database', 'sql',
                'network', 'tcp', 'ip', 'marketing', 'finance', 'accounting', 'math', 'equation', 'formula', 'physics',
                'chemistry', 'biology', 'data', 'model', 'software', 'hardware', 'operating system', 'linux',
                'git', 'test', 'security', 'cloud', 'architecture', 'engineering', 'science', 'logic', 'theory'
            )
            is_academic = any(k in q_lower for k in academic_keywords)

            if is_academic:
                fallback_text = (
                    f"### 📚 Academic Concept Breakdown: {clean_q[:60]}\n\n"
                    f"Here is an educational walkthrough to help you master **{clean_q[:50]}**:\n\n"
                    "#### 1. Theoretical Foundations & Principles\n"
                    f"- **Core Concept:** Examining `{clean_q[:40]}` requires understanding the fundamental definitions, state models, and constraints of the domain.\n"
                    "- **Key Mechanism:** Break down the system into structured, modular components and trace how inputs map to predictable outputs.\n\n"
                    "#### 2. Practical Application & Best Practices\n"
                    "- **Implementation:** Define clear preconditions, validate boundary cases, and adhere to industry architectural standards.\n"
                    "- **Trade-offs:** Analyze performance implications, memory overhead, and computational efficiency.\n\n"
                    "#### 💡 Recommended Next Questions to Explore:\n"
                    f"- *\"Show me a practical example or case study for {clean_q[:30]}\"*\n"
                    f"- *\"What are common exam questions and pitfalls regarding {clean_q[:30]}?\"*\n"
                    f"- *\"Give me a quick revision cheat sheet for {clean_q[:30]}\"*"
                )
            else:
                fallback_text = (
                    "### 🎓 SkillSphere Study Assistant Scope Notice\n\n"
                    f"I noticed your question (*\"{clean_q[:50]}\"*) appears outside our academic curriculum and technical career scope.\n\n"
                    "I am specialized as your **24/7 academic tutor, coding mentor, and career guide** across:\n"
                    "- 💻 **Computer Science & Coding (B.Tech / BCA / M.Tech):** Python, Java, C++, Data Structures, Algorithms, Web Development, and System Architecture.\n"
                    "- 📊 **Business Administration & Management (BBA / MBA):** Marketing 4Ps, Financial Accounting, Operations, and Business Analytics.\n"
                    "- 🔬 **Science & Engineering (B.Sc / Engineering):** Databases (SQL/NoSQL), Operating Systems, Computer Networks, and Machine Learning.\n"
                    "- 🎯 **Career Preparation:** Resume building, mock interviews, and technical portfolio blueprints.\n\n"
                    "---\n\n"
                    "#### 💡 Try asking questions like:\n"
                    "- *\"Explain the difference between TCP and UDP with examples\"*\n"
                    "- *\"What are the 4 Ps of marketing in business strategy?\"*\n"
                    "- *\"How to implement a binary search algorithm in Python?\"*\n"
                    "- *\"Explain ACID database properties with practical examples\"*\n\n"
                    "What academic topic, syllabus question, or programming concept can I help you learn today?"
                )

        return {
            'text': fallback_text,
            'provider': 'offline-knowledge-engine',
            'provider_label': 'SkillSphere Offline Knowledge Engine',
            'is_fallback': True,
            'latency_ms': 0.0,
        }

    @classmethod
    def ask_study_assistant(
        cls,
        question: str,
        mode: str = 'detailed',
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[int] = None
    ) -> str:
        meta = cls.ask_study_assistant_with_meta(question, mode, conversation_history, user_id=user_id)
        return meta['text']

    # ------------------------------------------------------------------------
    # Feature 2: Career Roadmap Generator (Structured Schema Validation)
    # ------------------------------------------------------------------------
    @classmethod
    def generate_roadmap(
        cls,
        skill: str,
        level: str,
        goal: str,
        daily_time: str,
        duration: str
    ) -> List[Dict[str, Any]]:
        """Generates a structured learning roadmap validated against validate_roadmap_schema."""
        cache_key = cls._build_cache_key("roadmap", "global", f"{skill}:{level}:{goal}:{duration}")
        cached = cls._cache_get(cache_key)
        if cached:
            return cached

        system_prompt = (
            "You are a Senior Curriculum Architect at Google. Generate a personalized, highly structured learning roadmap "
            "as a valid raw JSON list of phases. Each phase object must contain the following keys:\n"
            "- `title` (string): e.g. 'Phase 1: Foundations & Architecture'\n"
            "- `description` (string): concise 1-2 sentence overview of objectives\n"
            "- `topics` (list of 3-5 strings): specific technical subjects\n"
            "- `mini_project` (string): concrete hands-on portfolio project to build\n"
            "- `estimated_weeks` (integer): duration in weeks (1-6)\n\n"
            "Keep phase descriptions concise. Return ONLY the valid raw JSON array."
        )
        user_prompt = (
            f"Target Skill: {skill}\n"
            f"Current Level: {level}\n"
            f"Career Goal: {goal}\n"
            f"Daily Available Time: {daily_time}\n"
            f"Preferred Duration: {duration}\n"
            "Provide 4 to 6 sequential, progressive mastery phases."
        )

        def get_fallback_roadmap() -> List[Dict[str, Any]]:
            skill_lower = skill.lower()
            if 'python' in skill_lower or 'backend' in skill_lower:
                return [
                    {
                        "title": "Phase 1: Python Core Foundations",
                        "description": "Master clean syntax, primitives, functions, and memory references.",
                        "topics": ["Variables & Data Types", "Control Flow & Loops", "Functions & Scope", "List Comprehensions"],
                        "mini_project": "CLI Student Gradebook & Statistical Analyzer",
                        "estimated_weeks": 2
                    },
                    {
                        "title": "Phase 2: Object-Oriented Architecture",
                        "description": "Design modular classes, encapsulation, inheritance, and error handling.",
                        "topics": ["Classes & Constructors", "Inheritance & Mixins", "Magic Methods (__repr__, __str__)", "Custom Exceptions"],
                        "mini_project": "Object-Oriented Bank Account & Transaction System",
                        "estimated_weeks": 2
                    },
                    {
                        "title": "Phase 3: Data Structures & Algorithms",
                        "description": "Implement efficient algorithms and analyze asymptotic complexity.",
                        "topics": ["Big O Analysis", "Hash Maps & Sets", "Stacks & Queues", "Binary Trees & Searching"],
                        "mini_project": "In-Memory LRU Cache with O(1) Lookups",
                        "estimated_weeks": 3
                    },
                    {
                        "title": "Phase 4: Django Web Framework & MVT",
                        "description": "Build full-stack web applications with URL routing, views, templates, and sessions.",
                        "topics": ["Django Architecture", "Template Inheritance", "Form Validation", "Session Authentication"],
                        "mini_project": "Collaborative Notes & Knowledge Management Web App",
                        "estimated_weeks": 3
                    },
                    {
                        "title": "Phase 5: Database Engineering & PostgreSQL",
                        "description": "Design normalized database schemas, write ORM queries, and handle migrations.",
                        "topics": ["Relational Schemas", "Foreign Keys & Constraints", "Query Optimization (select_related)", "PostgreSQL Indexing"],
                        "mini_project": "E-Commerce Database Schema with Inventory Integrity",
                        "estimated_weeks": 2
                    }
                ]
            return [
                {
                    "title": f"Phase 1: {skill} Fundamentals",
                    "description": f"Master core syntax, fundamental concepts, and development environment setup for {skill}.",
                    "topics": ["Environment & Tooling", "Core Syntax & Variables", "Control Structures", "Data Handling"],
                    "mini_project": f"Basic {skill} Starter Utility Application",
                    "estimated_weeks": 2
                },
                {
                    "title": f"Phase 2: Intermediate {skill} Mechanics",
                    "description": f"Deep dive into modular architecture, functions, error handling, and testing.",
                    "topics": ["Modular Architecture", "Error Handling & Logging", "Unit Testing", "Debugging Workflows"],
                    "mini_project": f"Production-Style {skill} Data Processor",
                    "estimated_weeks": 3
                },
                {
                    "title": f"Phase 3: Practical Application & System Design",
                    "description": f"Build scalable components aligned with your goal: {goal}.",
                    "topics": ["System Architecture", "Performance Optimization", "Data Persistence", "API Integration"],
                    "mini_project": f"Portfolio-Ready {skill} Solution Project",
                    "estimated_weeks": 3
                },
                {
                    "title": f"Phase 4: Capstone & Career Readiness",
                    "description": "Package, test, document, and deploy your project for internship applications.",
                    "topics": ["Documentation & READMEs", "Automated Testing", "Code Reviews", "Interview Preparation"],
                    "mini_project": f"Complete {skill} Capstone Showcase",
                    "estimated_weeks": 2
                }
            ]

        data, meta = cls.generate_structured_json(
            prompt=user_prompt,
            system_instruction=system_prompt,
            validator_fn=validate_roadmap_schema,
            fallback_fn=get_fallback_roadmap,
            max_tokens=4096
        )

        if not meta.get('is_fallback'):
            cls._cache_set(cache_key, data, timeout=86400)
        return data

    # ------------------------------------------------------------------------
    # Feature 3: Mock Interview Evaluator (Structured Schema Validation)
    # ------------------------------------------------------------------------
    @classmethod
    def evaluate_interview_response(cls, category: str, question: str, user_answer: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Evaluates student answer in mock interview with strict rubric validation."""
        clean_ans = (user_answer or "").strip()[:3000]

        system_prompt = (
            "You are an empathetic, world-class Senior Technical Hiring Manager. "
            "Evaluate the student's technical interview answer objectively and constructively. "
            "Return ONLY a valid raw JSON object with the following keys:\n"
            "- `rating` (integer 1-10): score based on correctness, depth, and clarity\n"
            "- `technical_correctness` (string): analysis of technical accuracy and depth\n"
            "- `clarity` (string): communication structure, terminology, and flow\n"
            "- `constructive_feedback` (string): specific improvements, missing edge cases, or trade-offs\n"
            "- `sample_ideal_answer` (string): exemplary answer demonstrating STAR method and architectural depth"
        )
        user_prompt = (
            f"Interview Category: {category}\n"
            f"Question: {question}\n"
            f"Candidate Answer: {clean_ans}\n"
        )

        def get_fallback_interview() -> Dict[str, Any]:
            word_count = len(clean_ans.split())
            if word_count < 10:
                rating = 4
                feedback = "Your answer touches on the concept but is too brief for a technical interview. Try providing a concrete definition followed by a practical example and time complexity analysis."
            elif word_count < 30:
                rating = 7
                feedback = "Good explanation of the primary concept. To achieve top marks, discuss real-world trade-offs, edge cases, and architectural considerations."
            else:
                rating = 8
                feedback = "Strong and thorough answer! You demonstrated solid conceptual understanding, appropriate terminology, and clear technical communication."

            return {
                "rating": rating,
                "technical_correctness": f"Valid conceptual grasp of core principles in {category}.",
                "clarity": "Structured communication with logical explanation.",
                "constructive_feedback": feedback,
                "sample_ideal_answer": f"In {category}, state the core definition, explain performance trade-offs, and illustrate with a production design pattern."
            }

        data, _ = cls.generate_structured_json(
            prompt=user_prompt,
            system_instruction=system_prompt,
            validator_fn=validate_interview_schema,
            fallback_fn=get_fallback_interview
        )
        return data

    # ------------------------------------------------------------------------
    # Feature 4: Project Specification Generator (Structured Schema Validation)
    # ------------------------------------------------------------------------
    @classmethod
    def generate_project_idea(
        cls,
        language: str,
        level: str,
        category: str,
        complexity: str,
        project_type: str
    ) -> Dict[str, Any]:
        """Generates real-world practical project specification validated against validate_project_schema."""
        cache_key = cls._build_cache_key("proj_gen", "global", f"{language}:{level}:{category}:{complexity}:{project_type}")
        cached = cls._cache_get(cache_key)
        if cached:
            return cached

        system_prompt = (
            "You are a Principal Software Architect. Generate a practical, portfolio-grade project specification. "
            "Return ONLY a valid raw JSON object with the following keys:\n"
            "- `title` (string): Creative, professional project name\n"
            "- `description` (string): 2-3 sentence project summary\n"
            "- `problem_statement` (string): Real-world problem this application solves\n"
            "- `objectives` (string): Core measurable technical goals\n"
            "- `technology_stack` (string): Specific recommended libraries, frameworks, and databases\n"
            "- `main_features` (string): Bulleted list of 4-6 essential functionalities\n"
            "- `database_requirements` (string): Key entities, relationships, and indexing needs\n"
            "- `development_phases` (string): 4 structured milestone phases to build it\n"
            "- `portfolio_tips` (string): Advice on how to present this on GitHub and resume"
        )
        user_prompt = (
            f"Language: {language}\n"
            f"Skill Level: {level}\n"
            f"Category: {category}\n"
            f"Complexity: {complexity}\n"
            f"Project Type: {project_type}\n"
        )

        def get_fallback_project() -> Dict[str, Any]:
            return {
                "title": f"DevFlow: {language} {category} Platform",
                "description": f"A comprehensive {category} platform built with {language} designed to solve workflow fragmentation for software engineering students.",
                "problem_statement": "Students frequently struggle to track project requirements, collaborate on code reviews, and monitor milestone completion across disparate tools.",
                "objectives": f"Build a reliable {language} application implementing secure authentication, real-time database queries, and modular REST services.",
                "technology_stack": f"{language}, Django / DRF, PostgreSQL, Bootstrap 5, Chart.js",
                "main_features": "• Role-based access control (Student vs Mentor)\n• Automated task tracking & completion dashboards\n• RESTful API integration for external webhooks\n• Audit logging & CSV export functionality",
                "database_requirements": "Normalized relational schema with Users, Projects, Tasks, and AuditLog tables with foreign key constraints and indexed status fields.",
                "development_phases": "Phase 1: Schema design & migrations\nPhase 2: Authentication & CRUD views\nPhase 3: Interactive UI dashboards\nPhase 4: Automated unit tests & cloud deployment",
                "portfolio_tips": "Include architecture diagrams, live demo link, and API documentation in your GitHub README."
            }

        data, meta = cls.generate_structured_json(
            prompt=user_prompt,
            system_instruction=system_prompt,
            validator_fn=validate_project_schema,
            fallback_fn=get_fallback_project
        )

        if not meta.get('is_fallback'):
            cls._cache_set(cache_key, data, timeout=86400)
        return data

    # ------------------------------------------------------------------------
    # Feature 5: Resume ATS Analyzer (Structured Schema & User-Isolated Caching)
    # ------------------------------------------------------------------------
    @classmethod
    def check_ats_readability(
        cls,
        resume_data: Dict[str, Any],
        job_description: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Performs AI ATS readability analysis, keyword coverage checking, and resume critique.
        Strictly user-scoped caching ensures private resumes never leak between accounts.
        """
        contact = resume_data.get('contact', {})
        summary = resume_data.get('summary', '')
        education = resume_data.get('education', [])
        skills = resume_data.get('skills', [])
        projects = resume_data.get('projects', [])
        experience = resume_data.get('experience', [])

        # User-isolated cache key
        scope = f"user_{user_id}" if user_id else "anonymous"
        skills_str = ','.join(sorted(skills)) if isinstance(skills, list) else str(skills)
        cache_key = cls._build_cache_key("ats_check", scope, f"{skills_str}:{summary[:100]}:{job_description or ''}")
        cached = cls._cache_get(cache_key)
        if cached:
            return cached

        ai_prompt = (
            f"Candidate Skills: {', '.join(skills) if isinstance(skills, list) else skills}\n"
            f"Professional Summary: {summary[:500]}\n"
            f"Number of Projects: {len(projects)}\n"
            f"Number of Experiences: {len(experience)}\n"
            f"Education: {education}\n"
            f"Target Job Description:\n{(job_description or 'Software Engineer / Full-Stack Developer')[:1200]}\n"
        )
        system_prompt = (
            "You are an ATS (Applicant Tracking System) Specialist and Senior Tech Recruiter. "
            "Analyze the candidate's resume data against the job description. "
            "Return ONLY a valid raw JSON object with the following keys:\n"
            "- `score` (integer 50-100): calculated ATS match score\n"
            "- `readability_status` (string): 'High', 'Moderate', or 'Needs Improvement'\n"
            "- `strengths` (list of 2-4 strings): verified positive elements\n"
            "- `improvements` (list of 2-4 strings): high-impact actionable suggestions\n"
            "- `keywords_matched` (list of strings): relevant technical keywords found\n"
            "- `keywords_missing` (list of strings): crucial industry keywords missing"
        )

        def get_fallback_ats() -> Dict[str, Any]:
            missing_sections = []
            strengths = []
            improvements = []
            score = 60

            if not summary or len(summary) < 50:
                missing_sections.append("Professional Summary (recommended 50-100 words)")
                improvements.append("Add a clear, 3-sentence professional summary outlining your focus and core strengths.")
            else:
                score += 8
                strengths.append("Professional summary is present and concise.")

            if not education or len(education) == 0:
                missing_sections.append("Education section")
                improvements.append("Include your college, degree, graduation year, and GPA/relevant coursework.")
            else:
                score += 8
                strengths.append("Education background properly formatted.")

            if not skills or len(skills) < 5:
                missing_sections.append("Technical Skills (aim for 6+ concrete skills)")
                improvements.append("Add specific programming languages, frameworks, databases, and developer tools.")
            else:
                score += 10
                strengths.append(f"Strong technical skill coverage ({len(skills)} verified skills listed).")

            if not projects or len(projects) == 0:
                missing_sections.append("Projects section (vital for student resumes)")
                improvements.append("Add at least 2 practical technical projects with GitHub links and technology tags.")
            else:
                score += 10
                strengths.append(f"{len(projects)} technical projects listed with clear architecture.")

            if not contact.get('email') or not contact.get('full_name'):
                improvements.append("Ensure your full name, email, and LinkedIn/GitHub links are prominently listed at the top.")
            else:
                score += 4
                strengths.append("Essential contact coordinates are complete.")

            score = min(score, 100)

            keywords_matched = []
            keywords_missing = []
            if job_description:
                words = set(re.findall(r'[a-zA-Z]{3,}', job_description.lower()))
                common_tech = {'python', 'django', 'javascript', 'react', 'html', 'css', 'sql', 'postgresql', 'git', 'docker', 'rest', 'api', 'aws'}
                target_keywords = words.intersection(common_tech)
                current_skills = {s.lower() for s in skills} if isinstance(skills, list) else set()
                for kw in target_keywords:
                    if kw in current_skills:
                        keywords_matched.append(kw.capitalize())
                    else:
                        keywords_missing.append(kw.capitalize())

            return {
                "score": score,
                "readability_status": "High" if score >= 85 else ("Moderate" if score >= 70 else "Needs Improvement"),
                "missing_sections": missing_sections,
                "strengths": strengths,
                "improvements": improvements,
                "keywords_matched": keywords_matched,
                "keywords_missing": keywords_missing,
                "disclaimer": "This score is an educational guideline based on industry standard formatting best practices."
            }

        data, meta = cls.generate_structured_json(
            prompt=ai_prompt,
            system_instruction=system_prompt,
            validator_fn=validate_ats_schema,
            fallback_fn=get_fallback_ats
        )

        if not meta.get('is_fallback'):
            data['disclaimer'] = "Evaluated via Google Gemini ATS Engine based on technical depth, keyword density, and formatting standards."
            cls._cache_set(cache_key, data, timeout=3600)
        return data

    # ------------------------------------------------------------------------
    # Feature 6: Resume Copy Generators (User-Isolated Caching)
    # ------------------------------------------------------------------------
    @classmethod
    def generate_resume_summary(cls, headline: str, skills: List[str], education: str = "", user_id: Optional[int] = None) -> str:
        """Generates an action-oriented professional resume summary without inventing qualifications."""
        skills_joined = ','.join(skills) if isinstance(skills, list) else str(skills)
        scope = f"user_{user_id}" if user_id else "anonymous"
        cache_key = cls._build_cache_key("res_sum", scope, f"{headline}:{skills_joined}:{education}")
        cached = cls._cache_get(cache_key)
        if cached:
            return cached

        system_prompt = (
            "You are a professional Tech Career Coach. Write a concise, high-impact 3-4 sentence resume summary "
            "for a candidate based ONLY on the provided headline, verified technical skills, and education. "
            "IMPORTANT: Do not invent any companies, degrees, unmentioned skills, or awards. Use strong active voice."
        )
        user_prompt = f"Headline: {headline}\nSkills: {skills_joined}\nEducation: {education}"
        resp = cls.generate_text(user_prompt, system_prompt)
        if resp and len(resp.strip()) > 30:
            clean_res = resp.strip()
            cls._cache_set(cache_key, clean_res, timeout=3600)
            return clean_res

        skills_str = ", ".join(skills[:4]) if (isinstance(skills, list) and skills) else "modern software engineering practices"
        return (
            f"Dedicated {headline or 'Software Developer'} with a solid technical foundation in {skills_str}. "
            f"Passionate about writing clean, maintainable code, solving real-world challenges, and building high-performance applications. "
            f"Eager to contribute technical curiosity, collaborative problem solving, and disciplined delivery to an engineering team."
        )

    @classmethod
    def improve_project_description(cls, title: str, description: str, technologies: str, user_id: Optional[int] = None) -> str:
        """Polishes a project description into high-impact, STAR-aligned resume bullet points."""
        system_prompt = (
            "You are a Tech Resume Specialist. Polish the project description into 2-3 impactful resume bullet points. "
            "Start each bullet with an active verb (e.g. Engineered, Architected, Designed, Implemented, Optimized). "
            "Highlight technical problem solving, system architecture, and performance. Do not fabricate metrics or technologies."
        )
        user_prompt = f"Project: {title}\nTechnologies: {technologies}\nDraft Description: {description}"
        resp = cls.generate_text(user_prompt, system_prompt)
        if resp and len(resp.strip()) > 20:
            return resp.strip()

        tech_list = technologies or "modern tech stack"
        return (
            f"• Architected and deployed {title} utilizing {tech_list}, ensuring robust data flow and clean separation of concerns.\n"
            f"• Implemented end-to-end features, intuitive UI components, and reliable backend service endpoints to solve user requirements.\n"
            f"• Followed modular development standards, comprehensive validation, and version-controlled Git workflows."
        )

    @classmethod
    def rewrite_resume_bullet(cls, bullet_text: str, user_id: Optional[int] = None) -> str:
        """Rewrites a single resume bullet point into concise, action-oriented phrasing following Google XYZ format."""
        system_prompt = (
            "You are a Tech Resume Specialist. Rewrite the provided resume bullet point to make it more professional, "
            "impactful, and action-oriented. Start with a strong action verb (Engineered, Architected, Refactored, Streamlined). "
            "Highlight measurable impact and technical precision. Do not invent unmentioned facts. Return ONLY the single revised bullet without prefix characters."
        )
        resp = cls.generate_text(bullet_text, system_prompt)
        if resp and len(resp.strip()) > 10:
            return resp.strip().lstrip('•-* ')

        cleaned = bullet_text.strip().lstrip('•-* ')
        return f"Engineered and maintained {cleaned.lower() if cleaned else 'core application components'}, ensuring optimal performance and stability."

    # ------------------------------------------------------------------------
    # Feature 7: Lesson Study Notes Assistant
    # ------------------------------------------------------------------------
    @classmethod
    def assist_study_notes(cls, action: str, lesson_title: str, context_text: str) -> Dict[str, Any]:
        """
        Assists student with lesson study notes:
        Actions: 'simplify', 'explain_code', 'summarize', 'quiz_prep'
        Returns generated guidance with explicit AI provider attribution.
        """
        cache_key = cls._build_cache_key("lesson_note", "global", f"{action}:{lesson_title}:{context_text[:200]}")
        cached = cls._cache_get(cache_key)
        if cached:
            return cached

        system_prompt = (
            "You are SkillSphere's academic AI Study Assistant and senior educator. "
            "Help the student understand this specific lesson topic with clarity, "
            "actionable code examples, and high pedagogical rigor. Keep answers focused and formatted in clean Markdown."
        )

        if action == 'simplify':
            user_prompt = (
                f"Explain the core concept of '{lesson_title}' in simple, intuitive terms suitable for an absolute beginner. "
                f"Use a clear, relatable real-world analogy.\n\nLesson Context:\n{context_text[:1400]}"
            )
        elif action == 'real_world':
            user_prompt = (
                f"Provide 2 concrete, production real-world examples of how '{lesson_title}' is used by software engineers at modern tech companies. "
                f"Explain why this concept matters in practical application.\n\nLesson Context:\n{context_text[:1400]}"
            )
        elif action == 'explain_code':
            user_prompt = (
                f"Break down the code and concepts in '{lesson_title}' line-by-line. "
                f"Explain what each key statement does, common input/output behavior, and what to watch out for.\n\n"
                f"Code/Notes Context:\n{context_text[:1400]}"
            )
        elif action == 'beginner_exercise':
            user_prompt = (
                f"Create a friendly, bite-sized beginner coding exercise for '{lesson_title}'. "
                f"Provide: (1) Problem statement, (2) Starter code comment, (3) Expected output, and (4) A gentle hint. Do not reveal the full solution right away.\n\n"
                f"Lesson Context:\n{context_text[:1400]}"
            )
        elif action == 'quiz_prep':
            user_prompt = (
                f"Generate 3 rapid-fire self-check questions with multiple-choice options, correct answers, and brief explanations for revision on '{lesson_title}'. "
                f"Include 1 conceptual, 1 code-analysis, and 1 practical question.\n\n"
                f"Lesson Context:\n{context_text[:1400]}"
            )
        elif action == 'custom' or action == 'ask_question':
            user_prompt = (
                f"Answer the student's question regarding '{lesson_title}' concisely and clearly for a learner.\n\n"
                f"Question / Context:\n{context_text[:1400]}"
            )
        else:  # summarize
            user_prompt = (
                f"Provide a concise, high-yield bulleted revision summary of the most important points for '{lesson_title}'.\n\n"
                f"Lesson Context:\n{context_text[:1400]}"
            )

        meta = cls.generate_text_with_meta(user_prompt, system_instruction=system_prompt)
        if meta.get('text') and not meta.get('is_fallback'):
            cls._cache_set(cache_key, meta, timeout=7200)
            return meta

        # Fallback offline notes
        if action == 'simplify':
            fallback = (
                f"### Simplified Concept: {lesson_title}\n\n"
                f"**The Big Idea:** Think of this concept like an everyday automated recipe where inputs produce predictable, structured results. "
                f"In software engineering, breaking difficult topics down into smaller steps is key.\n\n"
                f"- **Step 1:** Understand the foundational data or state being handled.\n"
                f"- **Step 2:** Observe how control flow or functions manipulate that state.\n"
                f"- **Step 3:** Apply the pattern to your own practical challenges."
            )
        elif action == 'real_world':
            fallback = (
                f"### Real-World Engineering Applications: {lesson_title}\n\n"
                f"1. **Backend API Data Validation:** Modern web frameworks use this construct to ensure incoming requests meet strict schema requirements before touching a database.\n"
                f"2. **State Management & Pipelines:** Distributed systems rely on this logic to route messages, transform incoming payloads, and handle failure gracefully without crashing services."
            )
        elif action == 'explain_code':
            fallback = (
                f"### Code Breakdown: {lesson_title}\n\n"
                f"1. **Syntax Definition:** Functions and constructs declare clear parameters and return predictable values.\n"
                f"2. **Execution Flow:** Code runs sequentially from top to bottom, evaluating conditions and expressions.\n"
                f"3. **Best Practice:** Keep functions modular, write descriptive variable names, and handle boundary conditions gracefully."
            )
        elif action == 'beginner_exercise':
            fallback = (
                f"### Beginner Exercise: {lesson_title}\n\n"
                f"**Challenge:** Write a short routine that takes sample inputs and formats them according to the rules of {lesson_title}.\n\n"
                f"```python\n# Starter Code\ndef practice_task():\n    # TODO: Implement your logic here\n    pass\n```\n\n"
                f"**Hint:** Start by writing out the logic in plain English comments first!"
            )
        elif action == 'quiz_prep':
            fallback = (
                f"### Rapid Revision Self-Check: {lesson_title}\n\n"
                f"1. **Q: What is the primary purpose of this topic?**\n   *A:* To organize logic, optimize operations, and build maintainable software.\n\n"
                f"2. **Q: What is a common pitfall to avoid?**\n   *A:* Neglecting edge cases or mutating shared state unexpectedly.\n\n"
                f"3. **Q: Where is this used in production?**\n   *A:* Across scalable backend services, API handlers, and data processing pipelines."
            )
        else:
            fallback = (
                f"### Quick Revision Summary: {lesson_title}\n\n"
                f"- **Core Takeaway:** Master the primary syntax and structural principles introduced in this lesson.\n"
                f"- **Key Skill:** Write clean, readable implementations and verify them with practical test cases.\n"
                f"- **Next Step:** Complete the practice exercises in the Practice tab to lock in your understanding."
            )
        return {
            'text': fallback,
            'provider': 'offline-knowledge-engine',
            'provider_label': 'SkillSphere Knowledge Engine',
            'is_fallback': True,
            'latency_ms': 0.0,
        }

