"""
Integration tests for analytics API
"""
import pytest
from datetime import date, datetime, timedelta
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.tiktok_accounts.models import TikTokAccount
from apps.analytics.models import AccountAnalytics
from apps.content.models import ScheduledPost, PublishHistory


@pytest.fixture
def client():
    """Create test client"""
    return Client()


@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create(
        email="test@example.com",
        username="testuser"
    )


@pytest.fixture
def auth_token(user):
    """Create auth token for user"""
    import jwt
    from django.conf import settings

    payload = {
        'user_id': str(user.id),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers"""
    return {'HTTP_AUTHORIZATION': f'Bearer {auth_token}'}


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
class TestAnalyticsAPI:
    """Test Analytics API endpoints"""

    def test_get_account_metrics(self, client, auth_headers, tiktok_account, account_analytics):
        """Test GET /analytics/accounts/{id}/metrics"""
        response = client.get(
            f'/api/v1/analytics/accounts/{tiktok_account.id}/metrics',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['account_id'] == str(tiktok_account.id)
        assert data['username'] == tiktok_account.username
        assert data['total_followers'] == 1000
        assert 'engagement_rate' in data
        assert 'follower_growth' in data

    def test_get_account_metrics_not_found(self, client, auth_headers):
        """Test GET /analytics/accounts/{id}/metrics with invalid ID"""
        response = client.get(
            '/api/v1/analytics/accounts/invalid-id/metrics',
            **auth_headers
        )

        assert response.status_code == 404

    def test_get_time_series(self, client, auth_headers, tiktok_account, account_analytics):
        """Test GET /analytics/accounts/{id}/timeseries"""
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

        response = client.get(
            f'/api/v1/analytics/accounts/{tiktok_account.id}/timeseries',
            {'metric': 'follower_count', 'period': 'week'},
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['metric'] == 'follower_count'
        assert data['period'] == 'week'
        assert len(data['data']) > 0
        assert 'total' in data
        assert 'average' in data
        assert data['trend'] in ['up', 'down', 'stable']

    def test_get_post_analytics(self, client, auth_headers, scheduled_post, publish_history):
        """Test GET /analytics/posts/{id}"""
        response = client.get(
            f'/api/v1/analytics/posts/{scheduled_post.id}',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['post_id'] == str(scheduled_post.id)
        assert data['title'] == scheduled_post.title
        assert data['views'] == 10000
        assert data['likes'] == 500
        assert data['engagement_rate'] > 0
        assert 'viral_score' in data

    def test_get_best_posting_times(self, client, auth_headers, user, publish_history):
        """Test GET /analytics/insights/best-times"""
        # Create more historical data
        for i in range(10):
            pub_time = timezone.now() - timedelta(days=i)
            PublishHistory.objects.create(
                post=publish_history.post,
                account=publish_history.account,
                status="success",
                published_at=pub_time,
                views=10000,
                likes=500,
                comments=50,
                shares=25
            )

        response = client.get(
            '/api/v1/analytics/insights/best-times',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'best_hours' in data
        assert 'best_days' in data
        assert 'optimal_frequency' in data
        assert len(data['best_hours']) <= 5
        assert len(data['best_days']) <= 3

    def test_get_analytics_dashboard(self, client, auth_headers, tiktok_account, account_analytics, publish_history):
        """Test GET /analytics/dashboard"""
        response = client.get(
            f'/api/v1/analytics/dashboard?account_id={tiktok_account.id}',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'summary' in data
        assert 'recent_posts' in data
        assert 'growth_trend' in data
        assert 'engagement_trend' in data
        assert 'top_posts' in data
        assert 'upcoming_schedule' in data
        assert data['summary']['account_id'] == str(tiktok_account.id)

    def test_get_dashboard_without_account_id(self, client, auth_headers, tiktok_account, account_analytics):
        """Test GET /analytics/dashboard without account_id (uses primary)"""
        response = client.get(
            '/api/v1/analytics/dashboard',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['summary']['account_id'] == str(tiktok_account.id)

    def test_compare_accounts(self, client, auth_headers, user):
        """Test GET /analytics/compare"""
        # Create two accounts with analytics
        account1 = TikTokAccount.objects.create(
            user=user,
            username="account1",
            display_name="Account 1",
            tiktok_user_id="111",
            access_token="token1",
            follower_count=1000
        )
        AccountAnalytics.objects.create(
            tiktok_account=account1,
            date=date.today(),
            follower_count=1000,
            video_count=50,
            total_likes=50000,
            total_views=100000,
            total_shares=5000,
            total_comments=2000
        )

        account2 = TikTokAccount.objects.create(
            user=user,
            username="account2",
            display_name="Account 2",
            tiktok_user_id="222",
            access_token="token2",
            follower_count=2000
        )
        AccountAnalytics.objects.create(
            tiktok_account=account2,
            date=date.today(),
            follower_count=2000,
            video_count=100,
            total_likes=100000,
            total_views=200000,
            total_shares=10000,
            total_comments=4000
        )

        response = client.get(
            f'/api/v1/analytics/compare?account_1={account1.id}&account_2={account2.id}',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'account_1' in data
        assert 'account_2' in data
        assert 'comparison' in data
        assert 'total_followers' in data['comparison']

    def test_refresh_analytics(self, client, auth_headers, tiktok_account, account_analytics):
        """Test POST /analytics/refresh/{id}"""
        response = client.post(
            f'/api/v1/analytics/refresh/{tiktok_account.id}',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'metrics' in data
        assert data['metrics']['account_id'] == str(tiktok_account.id)

    def test_export_analytics(self, client, auth_headers):
        """Test GET /analytics/export"""
        response = client.get(
            '/api/v1/analytics/export?format=csv',
            **auth_headers
        )

        # Currently returns 501 (not implemented)
        assert response.status_code == 501
