"""
SkillSphere Enterprise Resilience & Fault-Tolerance Framework
Provides:
  1. CircuitBreaker: Thread-safe circuit breaker with CLOSED, OPEN, HALF_OPEN states.
     - Coordinates per-process via threading.Lock with optional distributed cache synchronization.
     - Strictly limits trial requests in HALF_OPEN to a single concurrent probe.
     - Seamlessly degrades to in-process memory if Redis/cache is unavailable.
  2. retry_with_jitter: Exponential backoff with full randomized jitter.
  3. Bulkhead: Process-local or distributed concurrency limiter with safe permit release.

SYNCHRONIZATION SCOPE DOCUMENTATION:
- CircuitBreaker: Hybrid scope. Thread-safe per process via `threading.Lock`.
  When distributed cache (Redis) is active, failure counts and state transitions are fleet-wide.
  If cache is unavailable, degrades cleanly to process-local state without interrupting requests.
- Bulkhead: Process-local scope via `threading.BoundedSemaphore` with strict per-worker capacity limits,
  or distributed via Redis with automatic permit TTL expiration for crash recovery.
"""

import time
import random
import logging
import functools
import threading
from typing import Callable, Any, Optional
from contextlib import contextmanager
from django.core.cache import cache

logger = logging.getLogger('skillsphere.resilience')

class CircuitBreakerOpenException(Exception):
    """Raised when execution is attempted while circuit breaker is OPEN."""
    pass


class CircuitBreaker:
    """
    Thread-safe, high-concurrency Circuit Breaker.
    - CLOSED: Normal operation. Successes reset failure count. Failures increment counter.
    - OPEN: Tripped after failure_threshold consecutive failures. Downstream calls fail-fast.
    - HALF_OPEN: Probe state entered after recovery_timeout seconds.
      STRICT CONCURRENCY: Permits exactly ONE trial request. All concurrent requests during
      a trial request fail-fast to prevent thundering herd against an already wounded dependency.
    """
    STATE_CLOSED = 'CLOSED'
    STATE_OPEN = 'OPEN'
    STATE_HALF_OPEN = 'HALF_OPEN'

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 45.0,
        cache_prefix: str = 'circuit_breaker'
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.cache_prefix = f"{cache_prefix}:{name}"
        self._lock = threading.Lock()
        self._trial_in_progress = False

        # In-process local fallbacks if cache backend is unavailable
        self._local_state = self.STATE_CLOSED
        self._local_fail_count = 0
        self._local_last_failure = 0.0

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
        with self._lock:
            cached_state = None
            try:
                cached_state = cache.get(self.state_key)
            except Exception:
                pass

            state = cached_state or self._local_state

            if state == self.STATE_OPEN:
                last_fail = 0.0
                try:
                    last_fail = cache.get(self.last_failure_key) or self._local_last_failure
                except Exception:
                    last_fail = self._local_last_failure

                if (time.time() - last_fail) >= self.recovery_timeout:
                    self._set_state_unlocked(self.STATE_HALF_OPEN)
                    return self.STATE_HALF_OPEN

            return state

    def _set_state_unlocked(self, state: str):
        """Sets breaker state across both local process memory and shared cache."""
        self._local_state = state
        ttl = max(60, int(self.recovery_timeout * 2))
        try:
            cache.set(self.state_key, state, timeout=ttl)
        except Exception:
            pass

    def can_execute(self, consume_permit: bool = False) -> bool:
        """
        Thread-safe check to determine if an execution is permitted.
        In HALF_OPEN, permits only 1 trial request; rejects concurrent threads.
        If consume_permit is True, marks the single trial permit as consumed.
        """
        with self._lock:
            state = self._local_state
            # Check cached state
            try:
                cs = cache.get(self.state_key)
                if cs:
                    state = cs
            except Exception:
                pass

            if state == self.STATE_OPEN:
                last_fail = self._local_last_failure
                try:
                    lf = cache.get(self.last_failure_key)
                    if lf:
                        last_fail = float(lf)
                except Exception:
                    pass

                if (time.time() - last_fail) >= self.recovery_timeout:
                    state = self.STATE_HALF_OPEN
                    self._set_state_unlocked(self.STATE_HALF_OPEN)
                else:
                    return False

            if state == self.STATE_CLOSED:
                return True

            if state == self.STATE_HALF_OPEN:
                # Strictly permit only 1 concurrent trial request
                if not self._trial_in_progress:
                    if consume_permit:
                        self._trial_in_progress = True
                        logger.info(f"[CircuitBreaker:{self.name}] Entering HALF_OPEN trial probe. 1 request permitted.")
                    return True
                else:
                    # Another thread is already testing the upstream service; fail-fast
                    return False

            return False

    def record_success(self):
        """Records a successful operation, transitioning breaker back to CLOSED."""
        with self._lock:
            self._trial_in_progress = False
            self._local_fail_count = 0
            self._set_state_unlocked(self.STATE_CLOSED)
            try:
                cache.delete(self.fail_count_key)
            except Exception:
                pass

    def record_failure(self):
        """Records a failed operation. Trips to OPEN on threshold reach or failed probe."""
        with self._lock:
            now = time.time()
            self._local_last_failure = now
            try:
                cache.set(self.last_failure_key, now, timeout=int(self.recovery_timeout * 3))
            except Exception:
                pass

            if self._local_state == self.STATE_HALF_OPEN or self._trial_in_progress:
                # Trial probe failed; trip immediately back to OPEN
                self._trial_in_progress = False
                self._set_state_unlocked(self.STATE_OPEN)
                logger.warning(f"[CircuitBreaker:{self.name}] Probe failed in HALF_OPEN. Tripped back to OPEN.")
                return

            self._local_fail_count += 1
            fails = self._local_fail_count
            try:
                cached_fails = cache.get(self.fail_count_key, 0) + 1
                cache.set(self.fail_count_key, cached_fails, timeout=int(self.recovery_timeout * 3))
                fails = max(fails, cached_fails)
            except Exception:
                pass

            if fails >= self.failure_threshold:
                self._set_state_unlocked(self.STATE_OPEN)
                logger.error(
                    f"[CircuitBreaker:{self.name}] Tripped to OPEN after {fails} consecutive failures. "
                    f"Fast-failing downstream calls for {self.recovery_timeout}s."
                )

    def call(self, fn: Callable, fallback_fn: Optional[Callable] = None, *args, **kwargs) -> Any:
        """
        Executes fn with circuit breaker protection, fast-failing to fallback_fn if OPEN
        or if another thread is currently running the HALF_OPEN probe.
        """
        if not self.can_execute(consume_permit=True):
            logger.info(f"[CircuitBreaker:{self.name}] Circuit is OPEN or trial in flight. Executing fast fallback.")
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
    Decorator applying full-jitter exponential backoff:
    delay = random.uniform(0, min(max_delay, base_delay * (2 ** attempt)))
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
                    # Canonical full jitter calculation
                    backoff_limit = min(max_delay, base_delay * (2 ** attempt))
                    delay = random.uniform(0.0, backoff_limit)
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
    Thread-safe concurrency bulkhead isolating downstream dependencies.
    Uses a threading.BoundedSemaphore per application process to strictly bound
    simultaneous executions per worker, preventing thread exhaustion.
    Guarantees safe permit release via context manager pattern.

    MULTI-INSTANCE CAPACITY MODELING:
    - Scope: Process-local.
    - Behavior across N instances: Independent. Total fleet concurrency is:
        C_fleet = N_instances * C_local
    - Upstream sizing rule: To protect an upstream service with a global concurrency ceiling
      of C_upstream across an auto-scaling cluster with up to N_max instances, set:
        C_local = max(1, floor(C_upstream / N_max))
    - Failure mode: If Redis or shared infrastructure is unavailable, local Bulkheads continue
      to operate with zero interruption to student learning workflows.
    """
    def __init__(self, name: str, max_concurrent: int = 15):
        self.name = name
        self.max_concurrent = max_concurrent
        self._semaphore = threading.BoundedSemaphore(value=max_concurrent)
        self._active_count = 0
        self._lock = threading.Lock()

    def acquire(self, timeout: float = 0.0) -> bool:
        """Attempts to acquire a bulkhead permit within timeout seconds."""
        if timeout > 0.0:
            acquired = self._semaphore.acquire(blocking=True, timeout=timeout)
        else:
            acquired = self._semaphore.acquire(blocking=False)
        if acquired:
            with self._lock:
                self._active_count += 1
        return acquired

    def release(self):
        """Releases an acquired bulkhead permit safely."""
        try:
            self._semaphore.release()
            with self._lock:
                if self._active_count > 0:
                    self._active_count -= 1
        except ValueError:
            # Prevent semaphore over-release errors
            pass

    @contextmanager
    def acquire_context(self, timeout: float = 0.0):
        """Context manager guaranteeing permit release even if exceptions occur."""
        acquired = self.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError(f"Bulkhead '{self.name}' capacity of {self.max_concurrent} exceeded.")
        try:
            yield
        finally:
            self.release()

    @property
    def active_permits(self) -> int:
        with self._lock:
            return self._active_count


class DistributedBulkhead:
    """
    Fleet-wide distributed concurrency limiter coordinating across all application instances.
    Backed by Redis atomic token counters with lease TTLs to prevent leaks on worker crashes.

    HIGH-AVAILABILITY & FAIL-SAFE DEGRADATION:
    If Redis is down, unreachable, or unconfigured, DistributedBulkhead automatically
    degrades to an internal process-local Bulkhead (threading.BoundedSemaphore).
    Core learning operations (assessments, enrollments, lessons) NEVER crash due to Redis failure.
    Degraded mode is explicitly tracked and logged; fleet-wide limits are NOT claimed when degraded.
    """
    LUA_ACQUIRE = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local lease_ttl = tonumber(ARGV[2])
    local max_fleet = tonumber(ARGV[3])
    local token = ARGV[4]

    -- 1. Remove expired tokens from crashed workers (lease expiration)
    redis.call('ZREMRANGEBYSCORE', key, '-inf', now - lease_ttl)

    -- 2. Check active concurrency against fleet limit
    local current_active = redis.call('ZCARD', key)
    if current_active < max_fleet then
        redis.call('ZADD', key, now, token)
        redis.call('EXPIRE', key, lease_ttl * 2)
        return 1
    else
        return 0
    end
    """

    LUA_RENEW = """
    local key = KEYS[1]
    local token = ARGV[1]
    local now = tonumber(ARGV[2])
    local lease_ttl = tonumber(ARGV[3])

    local score = redis.call('ZSCORE', key, token)
    if score then
        redis.call('ZADD', key, now, token)
        redis.call('EXPIRE', key, lease_ttl * 2)
        return 1
    else
        return 0
    end
    """

    LUA_RELEASE = """
    local key = KEYS[1]
    local token = ARGV[1]
    return redis.call('ZREM', key, token)
    """

    def __init__(
        self,
        name: str,
        max_fleet_concurrent: int = 50,
        lease_ttl_seconds: int = 30,
        fallback_local_concurrent: int = 15
    ):
        self.name = name
        self.max_fleet_concurrent = max_fleet_concurrent
        self.lease_ttl_seconds = lease_ttl_seconds
        self.fallback_local_concurrent = fallback_local_concurrent
        self.key_prefix = f"bulkhead:fleet:{name}"
        self._local_fallback = Bulkhead(name=f"{name}_local_fallback", max_concurrent=fallback_local_concurrent)
        self._is_degraded = False

    @property
    def is_degraded(self) -> bool:
        """Returns True if operating in local fallback mode because Redis is offline."""
        return self._is_degraded

    def _get_redis_client(self):
        try:
            from services.redis_service import RedisService
            client = RedisService.get_client()
            if not client:
                self._is_degraded = True
            else:
                self._is_degraded = False
            return client
        except Exception:
            self._is_degraded = True
            return None

    def acquire(self, token_id: Optional[str] = None, timeout: float = 0.0) -> Optional[str]:
        """
        Attempts to acquire a fleet-wide permit atomically via Redis Lua script.
        Returns token_id string if acquired, or None if capacity exceeded.
        """
        client = self._get_redis_client()
        if not client:
            logger.warning(
                f"[DistributedBulkhead:{self.name}] Redis unavailable; degraded to process-local "
                f"Bulkhead (capacity={self.fallback_local_concurrent}). Fleet-wide enforcement is INACTIVE."
            )
            acquired = self._local_fallback.acquire(timeout=timeout)
            return f"local_{time.time()}_{random.randint(1000, 9999)}" if acquired else None

        token = token_id or f"tok_{time.time()}_{random.randint(1000, 9999)}"
        key = f"{self.key_prefix}:active"
        now = time.time()
        start_time = now

        while True:
            try:
                res = client.eval(
                    self.LUA_ACQUIRE,
                    1,
                    key,
                    now,
                    self.lease_ttl_seconds,
                    self.max_fleet_concurrent,
                    token
                )
                if res == 1:
                    return token

                if res != 0:
                    logger.warning(f"[DistributedBulkhead:{self.name}] Non-standard Redis response ({res!r}), degrading to local fallback.")
                    self._is_degraded = True
                    acquired = self._local_fallback.acquire(timeout=timeout)
                    return f"local_{time.time()}_{random.randint(1000, 9999)}" if acquired else None

                if (time.time() - start_time) >= timeout:
                    return None

                time.sleep(0.05)
                now = time.time()
            except Exception as e:
                logger.warning(
                    f"[DistributedBulkhead:{self.name}] Redis Lua error ({e}); "
                    f"degraded to process-local fallback."
                )
                self._is_degraded = True
                acquired = self._local_fallback.acquire(timeout=timeout)
                return f"local_{time.time()}_{random.randint(1000, 9999)}" if acquired else None

    def renew_lease(self, token: Optional[str], extension_seconds: Optional[int] = None) -> bool:
        """
        Renews an active lease for long-running operations, preventing premature eviction.
        Returns True if lease was successfully renewed.
        """
        if not token or token.startswith("local_"):
            return True

        client = self._get_redis_client()
        if not client:
            return False

        key = f"{self.key_prefix}:active"
        ttl = extension_seconds or self.lease_ttl_seconds
        now = time.time()
        try:
            res = client.eval(self.LUA_RENEW, 1, key, token, now, ttl)
            return bool(res == 1)
        except Exception as e:
            logger.warning(f"[DistributedBulkhead:{self.name}] Lease renewal failed for token '{token}': {e}")
            return False

    def release(self, token: Optional[str]) -> bool:
        """
        Releases the acquired permit after verifying token ownership.
        Returns True if token was released.
        """
        if not token:
            return False

        if token.startswith("local_"):
            self._local_fallback.release()
            return True

        client = self._get_redis_client()
        if client:
            try:
                key = f"{self.key_prefix}:active"
                res = client.eval(self.LUA_RELEASE, 1, key, token)
                return bool(res == 1)
            except Exception as e:
                logger.warning(f"[DistributedBulkhead:{self.name}] Failed to release token '{token}' in Redis: {e}")
                return False
        return False

    @contextmanager
    def acquire_context(self, timeout: float = 0.0):
        """Context manager guaranteeing token release across distributed or local execution."""
        token = self.acquire(timeout=timeout)
        if not token:
            raise TimeoutError(f"Fleet bulkhead '{self.name}' capacity of {self.max_fleet_concurrent} exceeded.")
        try:
            yield token
        finally:
            self.release(token)
