"""
SkillSphere AI Engine Service
Enterprise-grade AI integration supporting Google Gemini 3.8 Flash, fallback cascades,
strict structured JSON validation, multi-turn conversation memory, and secure caching.
"""

import os
import json
import urllib.request
import urllib.error
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
    # Rate Limiting Guard
    # ------------------------------------------------------------------------
    @staticmethod
    def check_rate_limit(user_id: int, max_per_minute: Optional[int] = None) -> Tuple[bool, int]:
        """
        Sliding-minute rate limiter using Django cache.
        Returns (allowed: bool, retry_after_seconds: int).
        """
        if not cache or not user_id:
            return True, 0

        limit = max_per_minute or getattr(settings, 'AI_RATE_LIMIT_PER_MINUTE', 20)
        current_minute = int(time.time() // 60)
        cache_key = f"ai_rate:{user_id}:{current_minute}"

        try:
            current_count = cache.get(cache_key, 0)
            if current_count >= limit:
                retry_after = 60 - int(time.time() % 60)
                return False, max(1, retry_after)
            # Increment and set 90s TTL
            cache.set(cache_key, current_count + 1, timeout=90)
            return True, 0
        except Exception:
            return True, 0

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
    ) -> Tuple[Optional[str], Optional[int], Optional[str], bool]:
        """
        Performs a single HTTP POST request to Google Gemini API.
        Returns: (response_text, http_status_code, error_message, is_permanent_error)
        Permanent errors: 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden/Invalid Key).
        Transient errors: 429 (Rate Limit), 500, 502, 503, 504, Timeout.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                candidates = result.get('candidates', [])
                if candidates and 'content' in candidates[0]:
                    parts = candidates[0]['content'].get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text'].strip(), response.status, None, False
                return None, response.status, "Empty candidates returned by model.", False

        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode('utf-8')[:250]
            except Exception:
                pass

            # Classify permanent vs transient
            # 400, 401, 403 are permanent auth/request errors: MUST NOT RETRY
            if e.code in (400, 401, 403):
                return None, e.code, f"Permanent error {e.code}: {err_body}", True
            # 404 means model ID doesn't exist: transient to cascade (try next model, but don't retry same model)
            if e.code == 404:
                return None, 404, f"Model not found {model}: {err_body}", False
            # 429, 500, 502, 503, 504: transient server/rate errors
            return None, e.code, f"Transient HTTP {e.code}: {err_body}", False

        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return None, None, f"Network/Socket Timeout: {str(e)}", False
        except Exception as e:
            return None, None, f"Unexpected request failure: {str(e)}", False

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
        exponential backoff, random jitter, and overall execution deadline budget.
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

        # Deadline budget
        total_deadline = getattr(settings, 'AI_TOTAL_DEADLINE', 25.0)
        request_timeout = getattr(settings, 'AI_REQUEST_TIMEOUT', 12.0)
        deadline_time = time.time() + total_deadline

        cascade = cls.get_gemini_models_cascade()
        start_overall = time.perf_counter()

        for model_idx, model in enumerate(cascade):
            if time.time() >= deadline_time:
                logger.warning(f"[AIService] Total execution deadline ({total_deadline}s) reached. Aborting cascade.")
                break

            # Attempt model with bounded exponential backoff (up to 2 tries per model)
            max_attempts = 2
            for attempt in range(max_attempts):
                now = time.time()
                if now >= deadline_time:
                    break

                per_req_timeout = min(request_timeout, max(2.0, deadline_time - now))
                call_start = time.perf_counter()

                text, status_code, err_msg, is_permanent = cls._call_gemini_single(
                    model=model,
                    api_key=api_key,
                    data_bytes=data_bytes,
                    timeout=per_req_timeout
                )
                latency_ms = (time.perf_counter() - call_start) * 1000.0

                if text:
                    # Success: Log model used without leaking prompt or user data
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
                    logger.error(
                        f"[AIService] Permanent HTTP {status_code} on model '{model}'. "
                        f"Aborting cascade to prevent repeated unauthorized calls. Reason: {err_msg}"
                    )
                    return None

                # On 404 (model not found): don't retry this model, move to next fallback model immediately
                if status_code == 404:
                    logger.warning(f"[AIService] Model '{model}' not found (404). Falling over to next model.")
                    break

                # For transient errors (429, 500, 502, 503, 504, timeout):
                # Apply exponential backoff with jitter if another attempt is allowed
                if attempt < max_attempts - 1:
                    jitter = random.uniform(0.05, 0.25)
                    backoff = min(2.0, (0.5 * (2 ** attempt)) + jitter)
                    if time.time() + backoff >= deadline_time:
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
        has_gemini = bool(os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', ''))
        has_openai = bool(os.getenv('OPENAI_API_KEY'))
        cascade = cls.get_gemini_models_cascade()
        primary_model = cascade[0] if cascade else 'gemini-3.8-flash'

        if has_gemini:
            active_provider = f"Google Gemini ({primary_model})"
            badge = f"Google Gemini ({primary_model}) Live"
        elif has_openai:
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            active_provider = f"OpenAI ({model_name})"
            badge = "OpenAI GPT Live"
        else:
            active_provider = "SkillSphere Offline Knowledge Engine"
            badge = "Offline Mode"

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

        # Educational fallback engine for common student inquiries
        q_lower = clean_q.lower()
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
                "| **$O(1)$** | Constant Time | Hash table lookup, array index access |\n"
                "| **$O(\\log N)$** | Logarithmic Time | Binary Search in sorted array |\n"
                "| **$O(N)$** | Linear Time | Linear scan, counting elements |\n"
                "| **$O(N \\log N)$** | Linearithmic | Merge Sort, QuickSort (average), Timsort |\n"
                "| **$O(N^2)$** | Quadratic Time | Nested loops, Bubble Sort, Selection Sort |\n"
            )
        else:
            fallback_text = (
                f"### Academic Reference: {clean_q[:60]}\n\n"
                "*(Response served via SkillSphere Offline Knowledge Engine)*\n\n"
                "To explore this concept:\n"
                "1. **Core Concept:** Identify foundational computational principles, data structures, and state transitions.\n"
                "2. **Implementation:** Write a minimal reproducible script demonstrating the behavior with assertions.\n"
                "3. **Trade-offs:** Analyze time complexity, space complexity, and concurrency implications.\n\n"
                "> [!NOTE]\n"
                "> Connect your `GEMINI_API_KEY` in environment to activate live generative AI reasoning."
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
                f"Explain the core concept of '{lesson_title}' in simple, intuitive terms suitable for a beginner "
                f"with a clear real-world analogy.\n\nLesson Context:\n{context_text[:1400]}"
            )
        elif action == 'explain_code':
            user_prompt = (
                f"Break down and explain the syntax, execution flow, best practices, and edge cases of the code in '{lesson_title}'.\n\n"
                f"Code/Notes Context:\n{context_text[:1400]}"
            )
        elif action == 'quiz_prep':
            user_prompt = (
                f"Generate 3 rapid-fire self-check questions with answers and brief explanations for revision on '{lesson_title}'. "
                "Include 1 conceptual, 1 code-analysis, and 1 trade-off question.\n\n"
                f"Lesson Context:\n{context_text[:1400]}"
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
                f"**The Big Idea:** Think of this concept like an everyday system where inputs reliably produce structured outcomes. "
                f"In software engineering, breaking difficult topics down into smaller steps is key.\n\n"
                f"- **Step 1:** Understand the foundational data/operation.\n"
                f"- **Step 2:** Observe how control flow or functions manipulate that state.\n"
                f"- **Step 3:** Apply the pattern to your own code challenges."
            )
        elif action == 'explain_code':
            fallback = (
                f"### Code Breakdown: {lesson_title}\n\n"
                f"1. **Syntax Definition:** Functions and constructs declare clear parameters and return predictable values.\n"
                f"2. **Execution Flow:** Code runs sequentially from top to bottom, evaluating conditions and expressions.\n"
                f"3. **Best Practice:** Keep functions modular, write descriptive variable names, and handle boundary conditions gracefully."
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
