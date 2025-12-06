"""
Unit tests for analytics service
"""
import pytest
from datetime import date, datetime, timedelta
from django.core.cache import cache
from django.utils import timezone

from api.analytics.services import AnalyticsService
from apps.analytics.models import AccountAnalytics
from apps.content.models import PublishHistory, ScheduledPost
from apps.tiktok_accounts.models import TikTokAccount
from apps.accounts.models import User


@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create(
        email="test@example.com",
        username="testuser"
    )


@pytest.fixture
def tiktok_account(db, user):
    """Create test TikTok account"""
    return TikTokAccount.objects.create(
        user=user,
        username="test_tiktok",
        display_name="Test TikTok",
        tiktok_user_id="123456",
        access_token="test_token",
        follower_count=1000,
        following_count=500
    )


@pytest.fixture
def account_analytics(db, tiktok_account):
    """Create test account analytics"""
    return AccountAnalytics.objects.create(
        tiktok_account=tiktok_account,
        date=date.today(),
        follower_count=1000,
        following_count=500,
        video_count=50,
        total_likes=50000,
        total_views=100000,
        total_shares=5000,
        total_comments=2000,
        follower_growth=100,
        engagement_rate=5.7
    )


@pytest.fixture
def scheduled_post(db, user, tiktok_account):
    """Create test scheduled post"""
    post = ScheduledPost.objects.create(
        user=user,
        title="Test Post",
        description="Test description",
        status="published",
        published_at=timezone.now()
    )
    post.accounts.add(tiktok_account)
    return post


@pytest.fixture
def publish_history(db, scheduled_post, tiktok_account):
    """Create test publish history"""
    return PublishHistory.objects.create(
        post=scheduled_post,
        account=tiktok_account,
        status="success",
        published_at=timezone.now(),
        views=10000,
        likes=500,
        comments=50,
        shares=25
    )


@pytest.mark.django_db
class TestAnalyticsService:
    """Test AnalyticsService class"""

    def setup_method(self):
        """Setup test method"""
        cache.clear()
        self.service = AnalyticsService()

    def test_get_account_metrics_success(self, tiktok_account, account_analytics):
        """Test getting account metrics successfully"""
        metrics = self.service.get_account_metrics(str(tiktok_account.id))

        assert metrics['account_id'] == str(tiktok_account.id)
        assert metrics['username'] == tiktok_account.username
        assert metrics['total_followers'] == 1000
        assert metrics['total_videos'] == 50
        assert metrics['total_likes'] == 50000
        assert metrics['engagement_rate'] > 0
        assert 'follower_growth' in metrics
        assert 'growth_rate' in metrics

    def test_get_account_metrics_with_cache(self, tiktok_account, account_analytics):
        """Test caching of account metrics"""
        # First call - should cache
        metrics_1 = self.service.get_account_metrics(str(tiktok_account.id))

        # Second call - should use cache
        metrics_2 = self.service.get_account_metrics(str(tiktok_account.id))

        assert metrics_1 == metrics_2

        # Verify cache was used
        cache_key = f"analytics:account:{tiktok_account.id}"
        assert cache.get(cache_key) is not None

    def test_get_account_metrics_without_cache(self, tiktok_account, account_analytics):
        """Test getting account metrics without cache"""
        metrics = self.service.get_account_metrics(str(tiktok_account.id), use_cache=False)

        assert metrics['account_id'] == str(tiktok_account.id)

        # Verify no cache entry
        cache_key = f"analytics:account:{tiktok_account.id}"
        assert cache.get(cache_key) is not None  # Still cached after retrieval

    def test_get_account_metrics_not_found(self):
        """Test getting metrics for non-existent account"""
        with pytest.raises(ValueError, match="not found"):
            self.service.get_account_metrics("non-existent-id")

    def test_calculate_viral_score(self):
        """Test viral score calculation"""
        # High engagement
        score1 = self.service._calculate_viral_score(
            views=10000,
            engagement=500,
            account_count=2
        )
        assert 0 <= score1 <= 100

        # Low engagement
        score2 = self.service._calculate_viral_score(
            views=10000,
            engagement=50,
            account_count=2
        )
        assert score2 < score1

        # Zero views
        score3 = self.service._calculate_viral_score(
            views=0,
            engagement=100,
            account_count=2
        )
        assert score3 == 0.0

    def test_get_time_series_data(self, tiktok_account, account_analytics):
        """Test getting time series data"""
        # Create historical data
        for i in range(7):
            date_val = date.today() - timedelta(days=i)
            AccountAnalytics.objects.create(
                tiktok_account=tiktok_account,
                date=date_val,
                follower_count=1000 + (i * 10),
                video_count=50,
                total_likes=50000,
                total_views=100000,
                total_shares=5000,
                total_comments=2000
            )

        data = self.service.get_time_series_data(
            str(tiktok_account.id),
            'follower_count',
            'week'
        )

        assert data['metric'] == 'follower_count'
        assert data['period'] == 'week'
        assert len(data['data']) > 0
        assert data['trend'] in ['up', 'down', 'stable']
        assert 'total' in data
        assert 'average' in data

    def test_get_post_analytics(self, scheduled_post, publish_history):
        """Test getting post analytics"""
        analytics = self.service.get_post_analytics(str(scheduled_post.id))

        assert analytics['post_id'] == str(scheduled_post.id)
        assert analytics['title'] == scheduled_post.title
        assert analytics['views'] == 10000
        assert analytics['likes'] == 500
        assert analytics['comments'] == 50
        assert analytics['shares'] == 25
        assert analytics['engagement_rate'] > 0
        assert 0 <= analytics['viral_score'] <= 100

    def test_get_post_analytics_not_found(self):
        """Test getting analytics for non-existent post"""
        with pytest.raises(ValueError, match="not found"):
            self.service.get_post_analytics("non-existent-id")

    def test_get_best_posting_times_with_data(self, user, publish_history):
        """Test best posting times with historical data"""
        # Create more publish history
        for i in range(10):
            pub_time = timezone.now() - timedelta(days=i)
            PublishHistory.objects.create(
                post=publish_history.post,
                account=publish_history.account,
                status="success",
                published_at=pub_time,
                views=10000,
                likes=500 + (i * 10),
                comments=50,
                shares=25
            )

        best_times = self.service.get_best_posting_times(str(user.id))

        assert 'best_hours' in best_times
        assert 'best_days' in best_times
        assert 'optimal_frequency' in best_times
        assert len(best_times['best_hours']) <= 5
        assert len(best_times['best_days']) <= 3
        assert 3 <= best_times['optimal_frequency'] <= 7

    def test_get_best_posting_times_no_data(self, user):
        """Test best posting times without historical data"""
        best_times = self.service.get_best_posting_times(str(user.id))

        # Should return defaults
        assert len(best_times['best_hours']) > 0
        assert len(best_times['best_days']) > 0
        assert best_times['optimal_frequency'] == 5

    def test_clear_cache(self, tiktok_account, account_analytics):
        """Test cache clearing"""
        # Cache some data
        self.service.get_account_metrics(str(tiktok_account.id))

        cache_key = f"analytics:account:{tiktok_account.id}"
        assert cache.get(cache_key) is not None

        # Clear cache
        self.service.clear_cache(str(tiktok_account.id))

        # Verify cache cleared
        assert cache.get(cache_key) is None
