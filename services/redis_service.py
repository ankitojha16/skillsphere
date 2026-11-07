import logging
import os
import time
import uuid
from typing import Tuple, Optional, Any, Dict
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('skillsphere.redis')

class RedisService:
    """
    Distributed Redis coordination service for multi-instance serverless environments.
    Provides atomic distributed locks with token verification, sliding-window rate limiters,
    automatic connection recovery without restart, and graceful zero-crash fallback to LocMemCache.
    Never exposes credentials or full URLs.
    """
    _client = None
    _last_failure_time = 0.0
    _reconnect_interval_sec = 3.0  # Attempt reconnection every 3s if disconnected

    @classmethod
    def get_client(cls):
        """
        Returns a connected Redis client if configured and reachable, or None.
        Automatically attempts reconnection if connection was previously dropped.
        Never logs or exposes the connection string or credentials.
        """
        now = time.monotonic()
        if cls._client is not None:
            return cls._client

        # If recently failed, honor cooldown interval before re-trying
        if cls._last_failure_time > 0 and (now - cls._last_failure_time) < cls._reconnect_interval_sec:
            return None

        redis_url = os.environ.get('REDIS_URL') or os.environ.get('CACHE_URL') or getattr(settings, 'REDIS_URL', None)
        if not redis_url:
            cls._last_failure_time = now
            return None

        try:
            import redis
            client = redis.from_url(
                redis_url,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
                decode_responses=True
            )
            # Ping to verify actual connectivity
            client.ping()
            cls._client = client
            cls._last_failure_time = 0.0
            logger.info("[RedisService] Redis connection established. Distributed multi-instance synchronization active.")
            return cls._client
        except Exception as e:
            cls._client = None
            cls._last_failure_time = now
            logger.warning(
                f"[RedisService] Redis unavailable ({type(e).__name__}). "
                f"Degraded to local fallback. Distributed cross-instance rate limiting and locking are INACTIVE."
            )
            return None

    @classmethod
    def reset_client(cls):
        """Reset cached client connection (useful in tests and reconfigurations)."""
        cls._client = None
        cls._last_failure_time = 0.0

    @classmethod
    def is_redis_available(cls) -> bool:
        """Checks if live Redis connection is responsive; marks degraded on failure."""
        client = cls.get_client()
        if not client:
            return False
        try:
            return bool(client.ping())
        except Exception as e:
            cls._client = None
            cls._last_failure_time = time.monotonic()
            logger.warning(
                f"[RedisService] Redis ping failed ({type(e).__name__}). "
                f"Degraded to local fallback. Distributed rate-limiting is INACTIVE."
            )
            return False

    @classmethod
    def get_backend_status(cls) -> Dict[str, Any]:
        """
        Returns safe telemetry about the active backend without sensitive URLs or credentials.
        Accurately reports whether distributed coordination is active or operating in degraded mode.
        """
        is_avail = cls.is_redis_available()
        return {
            'backend_type': 'redis' if is_avail else 'locmem_fallback',
            'redis_connected': is_avail,
            'distributed_ready': is_avail,
            'protection_mode': 'distributed_redis' if is_avail else 'degraded_local_fallback',
            'warning': None if is_avail else 'Operating in degraded mode with local cache. Cross-instance rate-limiting and locks are INACTIVE.',
        }

    # ------------------------------------------------------------------------
    # Sliding-Window Rate Limiter (Rolling 60s, max 20 requests)
    # ------------------------------------------------------------------------
    LUA_SLIDING_WINDOW = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])
    local clearBefore = now - window

    redis.call('ZREMRANGEBYSCORE', key, '-inf', clearBefore)
    local currentRequests = redis.call('ZCARD', key)
    if currentRequests < limit then
        redis.call('ZADD', key, now, now .. '-' .. redis.call('INCR', key .. ':seq'))
        redis.call('EXPIRE', key, window + 10)
        return {1, 0}
    else
        local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
        local oldestTime = tonumber(oldest[2]) or now
        local retryAfter = math.max(1, math.ceil(oldestTime + window - now))
        return {0, retryAfter}
    end
    """

    @classmethod
    def check_sliding_window_rate_limit(
        cls,
        key: str,
        limit: int = 20,
        window_seconds: int = 60
    ) -> Tuple[bool, int]:
        """
        Sliding-window rate limiter.
        Returns: (allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        client = cls.get_client()
        if client:
            try:
                res = client.eval(cls.LUA_SLIDING_WINDOW, 1, key, now, window_seconds, limit)
                allowed = bool(res[0] == 1)
                retry_after = int(res[1])
                return allowed, retry_after
            except Exception as e:
                logger.warning(f"[RedisService] Lua sliding window failed ({e}), falling back to cache.")

        # Fallback using Django cache
        try:
            timestamps = cache.get(key, [])
            if not isinstance(timestamps, list):
                timestamps = []
            clear_before = now - window_seconds
            valid_timestamps = [t for t in timestamps if t > clear_before]

            if len(valid_timestamps) < limit:
                valid_timestamps.append(now)
                cache.set(key, valid_timestamps, timeout=window_seconds + 10)
                return True, 0
            else:
                oldest = valid_timestamps[0] if valid_timestamps else now
                retry_after = max(1, int(oldest + window_seconds - now))
                return False, retry_after
        except Exception:
            return True, 0

    # ------------------------------------------------------------------------
    # Distributed Atomic Lock with Token & Safe Release
    # ------------------------------------------------------------------------
    LUA_RELEASE_LOCK = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    else
        return 0
    end
    """

    @classmethod
    def acquire_lock(cls, key: str, token: Optional[str] = None, ttl_seconds: int = 3) -> Tuple[bool, str]:
        """
        Attempts to atomically acquire a lock for 'key' with a unique token.
        Prevents concurrent duplicate submissions across serverless instances.
        Returns: (acquired: bool, token: str)
        """
        lock_token = token or str(uuid.uuid4())
        client = cls.get_client()
        if client:
            try:
                # Atomic SET key token NX EX ttl
                ok = client.set(key, lock_token, nx=True, ex=ttl_seconds)
                return bool(ok), lock_token
            except Exception as e:
                logger.warning(f"[RedisService] Lock acquisition failed on Redis ({e}), using fallback.")

        # Fallback using cache.add which is atomic SETNX
        try:
            acquired = cache.add(key, lock_token, timeout=ttl_seconds)
            return bool(acquired), lock_token
        except Exception:
            return True, lock_token

    @classmethod
    def release_lock(cls, key: str, token: str) -> bool:
        """
        Safely releases lock only if the token matches (prevents releasing someone else's expired lock).
        """
        client = cls.get_client()
        if client:
            try:
                res = client.eval(cls.LUA_RELEASE_LOCK, 1, key, token)
                return bool(res == 1)
            except Exception as e:
                logger.warning(f"[RedisService] Lua lock release failed ({e}), using fallback.")

        try:
            val = cache.get(key)
            if val == token:
                cache.delete(key)
                return True
            return False
        except Exception:
            return False
