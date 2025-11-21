"""
In-memory caching with TTL support for analytics and frequently accessed data.
"""
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from collections import OrderedDict

from app.core.config import settings


class CacheEntry:
    """Represents a cached entry with expiration time."""

    def __init__(self, value: Any, ttl_seconds: int):
        """
        Initialize cache entry.

        Args:
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        self.value = value
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.utcnow() > self.expires_at


class InMemoryCache:
    """
    Simple in-memory cache with TTL and LRU eviction.
    Thread-safe for asyncio operations.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        async with self._lock:
            ttl = ttl or self._default_ttl
            self._cache[key] = CacheEntry(value, ttl)
            self._cache.move_to_end(key)

            # Evict oldest entry if cache is full
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    async def delete(self, key: str) -> None:
        """
        Delete entry from cache.

        Args:
            key: Cache key
        """
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Pattern to match (simple string contains)

        Returns:
            Number of invalidated entries
        """
        async with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if pattern in key
            ]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of removed entries
        """
        async with self._lock:
            keys_to_delete = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


# Global cache instance
cache = InMemoryCache(
    max_size=settings.cache_max_size,
    default_ttl=settings.cache_ttl_seconds
)


def cache_result(key_prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache async function results.

    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds (uses default if None)

    Example:
        @cache_result("analytics:summary", ttl=300)
        async def get_summary(org_id: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Build cache key from function arguments
            key_parts = [key_prefix]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator


async def invalidate_cache_for_organization(org_id: str) -> int:
    """
    Invalidate all cache entries for an organization.

    Args:
        org_id: Organization ID

    Returns:
        Number of invalidated entries
    """
    return await cache.invalidate_pattern(f":{org_id}:")
