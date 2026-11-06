import logging
from django.core.cache.backends.redis import RedisCache
from django.core.cache.backends.locmem import LocMemCache

logger = logging.getLogger('skillsphere.cache')

class FaultTolerantRedisCache(RedisCache):
    """
    Production-hardened Redis cache backend that gracefully handles transient
    network drops, timeouts, or Redis maintenance by failing over to a local
    in-memory cache instead of raising 500 Server Errors.
    """
    def __init__(self, server, params):
        super().__init__(server, params)
        # Create an internal fallback LocMemCache with same timeout and options
        fallback_params = {
            'TIMEOUT': params.get('TIMEOUT', 300),
            'OPTIONS': {'MAX_ENTRIES': params.get('OPTIONS', {}).get('MAX_ENTRIES', 2000)},
            'KEY_PREFIX': params.get('KEY_PREFIX', 'skillsphere_fallback'),
            'VERSION': params.get('VERSION', 1),
        }
        self._fallback = LocMemCache('skillsphere-redis-fallback', fallback_params)

    def _call_with_fallback(self, method_name, *args, **kwargs):
        try:
            method = getattr(super(), method_name)
            return method(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"Redis cache '{method_name}' failed ({type(e).__name__}: {e}). "
                f"Failing over to LocMemCache fallback."
            )
            fallback_method = getattr(self._fallback, method_name)
            return fallback_method(*args, **kwargs)

    def add(self, key, value, timeout=None, version=None):
        return self._call_with_fallback('add', key, value, timeout=timeout, version=version)

    def get(self, key, default=None, version=None):
        return self._call_with_fallback('get', key, default=default, version=version)

    def set(self, key, value, timeout=None, version=None):
        return self._call_with_fallback('set', key, value, timeout=timeout, version=version)

    def touch(self, key, timeout=None, version=None):
        return self._call_with_fallback('touch', key, timeout=timeout, version=version)

    def delete(self, key, version=None):
        return self._call_with_fallback('delete', key, version=version)

    def get_many(self, keys, version=None):
        return self._call_with_fallback('get_many', keys, version=version)

    def set_many(self, data, timeout=None, version=None):
        return self._call_with_fallback('set_many', data, timeout=timeout, version=version)

    def delete_many(self, keys, version=None):
        return self._call_with_fallback('delete_many', keys, version=version)

    def clear(self):
        return self._call_with_fallback('clear')

    def has_key(self, key, version=None):
        return self._call_with_fallback('has_key', key, version=version)

    def incr(self, key, delta=1, version=None):
        return self._call_with_fallback('incr', key, delta=delta, version=version)

    def decr(self, key, delta=1, version=None):
        return self._call_with_fallback('decr', key, delta=delta, version=version)
