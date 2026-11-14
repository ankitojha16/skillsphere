"""
SkillSphere Enterprise Resilience & Fault-Tolerance Framework
Provides:
  1. CircuitBreaker: Distributed circuit breaker pattern with CLOSED, OPEN, HALF_OPEN states.
  2. retry_with_jitter: Exponential backoff with randomized jitter for safe idempotent retries.
  3. Bulkhead: Concurrency limiter isolating downstream dependencies from exhausting server resources.
"""

import time
import random
import logging
import functools
from typing import Callable, Any, Optional
from django.core.cache import cache

logger = logging.getLogger('skillsphere.resilience')

class CircuitBreakerOpenException(Exception):
    """Raised when an execution is attempted while the circuit breaker is OPEN."""
    pass


class CircuitBreaker:
    """
    Distributed Circuit Breaker pattern.
    - CLOSED: Normal operation. Successes reset failure count. Failures increment counter.
    - OPEN: Tripped after failure_threshold consecutive failures. Requests fail fast without calling downstream.
    - HALF_OPEN: Probe state after recovery_timeout seconds. A single test request is permitted.
    """
    STATE_CLOSED = 'CLOSED'
    STATE_OPEN = 'OPEN'
    STATE_HALF_OPEN = 'HALF_OPEN'

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        cache_prefix: str = 'circuit_breaker'
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.cache_prefix = f"{cache_prefix}:{name}"

    @property
    def state_key(self) -> str:
        return f"{self.cache_prefix}:state"

    @property
    def fail_count_key(self) -> str:
        return f"{self.cache_prefix}:failures"

    @property
    def last_failure_key(self) -> str:
        return f"{self.cache_prefix}:last_fail"

    def get_state(self) -> str:
        state = cache.get(self.state_key)
        if not state:
            return self.STATE_CLOSED

        if state == self.STATE_OPEN:
            last_fail = cache.get(self.last_failure_key) or 0.0
            if (time.time() - last_fail) >= self.recovery_timeout:
                self._set_state(self.STATE_HALF_OPEN)
                return self.STATE_HALF_OPEN

        return state

    def _set_state(self, state: str):
        ttl = int(self.recovery_timeout * 2)
        cache.set(self.state_key, state, timeout=ttl)

    def can_execute(self) -> bool:
        state = self.get_state()
        if state == self.STATE_CLOSED:
            return True
        if state == self.STATE_HALF_OPEN:
            return True
        return False

    def record_success(self):
        cache.delete(self.fail_count_key)
        self._set_state(self.STATE_CLOSED)

    def record_failure(self):
        now = time.time()
        cache.set(self.last_failure_key, now, timeout=int(self.recovery_timeout * 3))

        state = self.get_state()
        if state == self.STATE_HALF_OPEN:
            # Probe failed; immediately re-open
            self._set_state(self.STATE_OPEN)
            logger.warning(f"[CircuitBreaker:{self.name}] Probe failed in HALF_OPEN. Tripped back to OPEN.")
            return

        fails = cache.get(self.fail_count_key, 0) + 1
        cache.set(self.fail_count_key, fails, timeout=int(self.recovery_timeout * 3))

        if fails >= self.failure_threshold:
            self._set_state(self.STATE_OPEN)
            logger.error(
                f"[CircuitBreaker:{self.name}] Tripped to OPEN after {fails} consecutive failures. "
                f"Fast-failing downstream calls for {self.recovery_timeout}s."
            )

    def call(self, fn: Callable, fallback_fn: Optional[Callable] = None, *args, **kwargs) -> Any:
        if not self.can_execute():
            logger.info(f"[CircuitBreaker:{self.name}] Circuit is OPEN. Executing fast fallback.")
            if fallback_fn:
                return fallback_fn(*args, **kwargs)
            raise CircuitBreakerOpenException(f"Circuit '{self.name}' is OPEN. Service unavailable.")

        try:
            result = fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            if fallback_fn:
                logger.info(f"[CircuitBreaker:{self.name}] Call failed ({e}). Returning fallback result.")
                return fallback_fn(*args, **kwargs)
            raise


def retry_with_jitter(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    retryable_exceptions: tuple = (Exception,)
):
    """
    Decorator that applies exponential backoff with full randomized jitter to idempotent calls.
    Delay = min(max_delay, (2 ** attempt) * base_delay) + random.uniform(0, base_delay)
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exc = e
                    if attempt == max_attempts - 1:
                        logger.error(f"[retry_with_jitter] '{fn.__name__}' failed all {max_attempts} attempts: {e}")
                        raise
                    delay = min(max_delay, (2 ** attempt) * base_delay) + random.uniform(0.05, base_delay)
                    logger.warning(
                        f"[retry_with_jitter] '{fn.__name__}' failed attempt {attempt+1}/{max_attempts} ({e}). "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator


class Bulkhead:
    """
    In-memory or distributed concurrency bulkhead.
    Caps max simultaneous executions of an external integration to protect web worker capacity.
    """
    def __init__(self, name: str, max_concurrent: int = 15):
        self.name = name
        self.max_concurrent = max_concurrent
        self.key = f"bulkhead:{name}:active"

    def acquire(self) -> bool:
        current = cache.get(self.key, 0)
        if current >= self.max_concurrent:
            return False
        cache.set(self.key, current + 1, timeout=30)
        return True

    def release(self):
        current = cache.get(self.key, 0)
        if current > 0:
            cache.set(self.key, current - 1, timeout=30)
        else:
            cache.delete(self.key)
