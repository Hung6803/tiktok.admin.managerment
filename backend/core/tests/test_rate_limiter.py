"""
Tests for rate limiter utility
"""
import pytest
import threading
import time
from django.core.cache import cache

from core.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test rate limiter"""

    def setup_method(self):
        """Clear cache before each test"""
        cache.clear()

    def test_is_allowed_within_limit(self):
        """Test requests within limit are allowed"""
        limiter = RateLimiter('test', max_calls=3, time_window_seconds=60)

        assert limiter.is_allowed('user1') is True
        assert limiter.is_allowed('user1') is True
        assert limiter.is_allowed('user1') is True

    def test_is_allowed_exceeds_limit(self):
        """Test requests exceeding limit are blocked"""
        limiter = RateLimiter('test', max_calls=2, time_window_seconds=60)

        assert limiter.is_allowed('user1') is True
        assert limiter.is_allowed('user1') is True
        assert limiter.is_allowed('user1') is False  # Exceeded

    def test_get_remaining(self):
        """Test remaining call count"""
        limiter = RateLimiter('test', max_calls=5, time_window_seconds=60)

        assert limiter.get_remaining('user1') == 5
        limiter.is_allowed('user1')
        assert limiter.get_remaining('user1') == 4
        limiter.is_allowed('user1')
        assert limiter.get_remaining('user1') == 3

    def test_reset(self):
        """Test rate limit reset"""
        limiter = RateLimiter('test', max_calls=2, time_window_seconds=60)

        limiter.is_allowed('user1')
        limiter.is_allowed('user1')
        assert limiter.is_allowed('user1') is False

        limiter.reset('user1')
        assert limiter.is_allowed('user1') is True

    def test_separate_identifiers(self):
        """Test different identifiers have separate limits"""
        limiter = RateLimiter('test', max_calls=1, time_window_seconds=60)

        assert limiter.is_allowed('user1') is True
        assert limiter.is_allowed('user2') is True
        assert limiter.is_allowed('user1') is False
        assert limiter.is_allowed('user2') is False

    def test_concurrent_requests_atomicity(self):
        """Test atomicity under concurrent load - NO race conditions"""
        limiter = RateLimiter('test_concurrent', max_calls=5, time_window_seconds=60)
        results = []
        barrier = threading.Barrier(10)  # Synchronize thread start

        def make_request():
            barrier.wait()  # All threads start together
            result = limiter.is_allowed('user_concurrent')
            results.append(result)

        # Create 10 concurrent threads
        threads = [threading.Thread(target=make_request) for _ in range(10)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify exactly 5 allowed, 5 denied (atomic guarantee)
        allowed_count = results.count(True)
        denied_count = results.count(False)

        assert allowed_count == 5, (
            f"Expected exactly 5 allowed requests, got {allowed_count}. "
            f"This indicates a race condition in the rate limiter!"
        )
        assert denied_count == 5, (
            f"Expected exactly 5 denied requests, got {denied_count}"
        )

    def test_high_concurrency_multiple_users(self):
        """Test high concurrency with multiple users"""
        limiter = RateLimiter('test_multi', max_calls=3, time_window_seconds=60)
        results = {'user_a': [], 'user_b': [], 'user_c': []}
        barrier = threading.Barrier(15)

        def make_request(user_id):
            barrier.wait()
            result = limiter.is_allowed(user_id)
            results[user_id].append(result)

        # 5 threads per user (15 total)
        threads = []
        for user_id in ['user_a', 'user_b', 'user_c']:
            for _ in range(5):
                threads.append(threading.Thread(target=make_request, args=(user_id,)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Each user should have exactly 3 allowed, 2 denied
        for user_id, user_results in results.items():
            allowed = user_results.count(True)
            denied = user_results.count(False)
            assert allowed == 3, (
                f"{user_id}: Expected 3 allowed, got {allowed}"
            )
            assert denied == 2, (
                f"{user_id}: Expected 2 denied, got {denied}"
            )

    def test_key_expiration(self):
        """Test key expiration and automatic reset"""
        limiter = RateLimiter('test_expiry', max_calls=2, time_window_seconds=1)

        # Use up limit
        assert limiter.is_allowed('user_expiry') is True
        assert limiter.is_allowed('user_expiry') is True
        assert limiter.is_allowed('user_expiry') is False

        # Wait for expiration
        time.sleep(1.2)

        # Should reset automatically
        assert limiter.is_allowed('user_expiry') is True
        assert limiter.is_allowed('user_expiry') is True
        assert limiter.is_allowed('user_expiry') is False

    def test_cache_clear_edge_case(self):
        """Test behavior when cache is cleared mid-operation"""
        limiter = RateLimiter('test_clear', max_calls=3, time_window_seconds=60)

        # Make some requests
        assert limiter.is_allowed('user_clear') is True
        assert limiter.is_allowed('user_clear') is True

        # Clear cache (simulates cache flush/restart)
        cache.clear()

        # Should handle gracefully and start fresh
        assert limiter.is_allowed('user_clear') is True
        assert limiter.get_remaining('user_clear') == 2

    def test_race_condition_on_first_request(self):
        """Test race condition specifically on first request (key creation)"""
        limiter = RateLimiter('test_first', max_calls=5, time_window_seconds=60)
        results = []
        barrier = threading.Barrier(5)

        def make_first_request():
            barrier.wait()
            result = limiter.is_allowed('user_first')
            results.append(result)

        threads = [threading.Thread(target=make_first_request) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All 5 should succeed (at limit)
        assert results.count(True) == 5
        # Next request should fail
        assert limiter.is_allowed('user_first') is False
