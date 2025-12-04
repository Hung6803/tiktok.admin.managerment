"""
Rate limiting utility for API calls
Prevents exceeding TikTok API rate limits
"""
from django.core.cache import cache
import time
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter using Django cache
    Tracks API calls per identifier within time window
    """

    def __init__(self, key_prefix: str, max_calls: int, time_window_seconds: int):
        """
        Initialize rate limiter

        Args:
            key_prefix: Cache key prefix for this limiter
            max_calls: Maximum calls allowed
            time_window_seconds: Time window in seconds
        """
        self.key_prefix = key_prefix
        self.max_calls = max_calls
        self.time_window = time_window_seconds

    def _get_cache_key(self, identifier: str) -> str:
        """Get cache key for identifier"""
        return f"rate_limit:{self.key_prefix}:{identifier}"

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed within rate limit (atomic operation)

        Args:
            identifier: Unique identifier (user_id, token, etc.)

        Returns:
            True if allowed, False if rate limit exceeded
        """
        cache_key = self._get_cache_key(identifier)

        # Atomic increment with graceful initialization
        try:
            # Try atomic increment first
            new_count = cache.incr(cache_key)
            logger.debug(f"Incremented existing key {cache_key}: {new_count}")
        except ValueError:
            # Key doesn't exist, try atomic add
            # add() returns True only if key didn't exist
            logger.debug(f"Key {cache_key} doesn't exist, attempting atomic add")
            if cache.add(cache_key, 1, self.time_window):
                # Successfully added, this is the first request
                new_count = 1
                logger.debug(f"Successfully added new key {cache_key}: {new_count}")
            else:
                # Another thread created it, try increment again
                try:
                    new_count = cache.incr(cache_key)
                    logger.debug(f"Incremented after add conflict: {new_count}")
                except ValueError:
                    # Extremely rare: key expired between operations
                    # Fallback to set (non-atomic but acceptable in edge case)
                    cache.set(cache_key, 1, self.time_window)
                    new_count = 1
                    logger.debug(f"Fallback to set after race: {new_count}")

        # Check against limit
        if new_count > self.max_calls:
            logger.warning(
                f"Rate limit exceeded for {identifier}: "
                f"{new_count}/{self.max_calls} in {self.time_window}s"
            )
            return False

        logger.debug(f"Request allowed for {identifier}: {new_count}/{self.max_calls}")
        return True

    def get_remaining(self, identifier: str) -> int:
        """
        Get remaining calls for identifier (read-only, safe for concurrent use)

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining calls
        """
        cache_key = self._get_cache_key(identifier)
        current_count = cache.get(cache_key, 0)
        remaining = max(0, self.max_calls - current_count)
        logger.debug(f"Remaining calls for {identifier}: {remaining}/{self.max_calls}")
        return remaining

    def reset(self, identifier: str):
        """
        Reset rate limit for identifier

        Args:
            identifier: Unique identifier
        """
        cache_key = self._get_cache_key(identifier)
        cache.delete(cache_key)
        logger.info(f"Rate limit reset for {identifier}")

    def wait_if_needed(self, identifier: str, max_wait_seconds: int = 60) -> bool:
        """
        Wait if rate limit exceeded (blocking)

        Args:
            identifier: Unique identifier
            max_wait_seconds: Maximum time to wait

        Returns:
            True if allowed after waiting, False if timeout
        """
        wait_start = time.time()

        while not self.is_allowed(identifier):
            elapsed = time.time() - wait_start

            if elapsed >= max_wait_seconds:
                logger.error(
                    f"Rate limit wait timeout for {identifier} "
                    f"after {elapsed:.1f}s"
                )
                return False

            time.sleep(1)

        return True


# Pre-configured rate limiters for TikTok API
class TikTokRateLimiters:
    """TikTok API rate limiters"""

    # Per-user token rate limit (6 req/min)
    USER_TOKEN = RateLimiter(
        key_prefix='tiktok_user_token',
        max_calls=6,
        time_window_seconds=60
    )

    # Per-endpoint rate limit (600 req/min)
    ENDPOINT = RateLimiter(
        key_prefix='tiktok_endpoint',
        max_calls=600,
        time_window_seconds=60
    )

    # Video upload daily limit (15 uploads/24hrs)
    VIDEO_UPLOAD = RateLimiter(
        key_prefix='tiktok_video_upload',
        max_calls=15,
        time_window_seconds=86400  # 24 hours
    )
