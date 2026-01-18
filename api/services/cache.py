import time
from functools import wraps

class Cache:
    """Simple in-memory cache with TTL."""

    def __init__(self):
        self._cache = {}

    def get(self, key):
        """Get value from cache if not expired."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key, value, ttl=300):
        """Set value in cache with TTL in seconds."""
        self._cache[key] = (value, time.time() + ttl)

    def delete(self, key):
        """Delete a key from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear_pattern(self, pattern):
        """Clear all keys matching pattern."""
        keys_to_delete = [k for k in self._cache if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]

    def clear_all(self):
        """Clear entire cache."""
        self._cache.clear()


# Global cache instance
cache = Cache()


def cached(ttl=300, key_prefix=""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
