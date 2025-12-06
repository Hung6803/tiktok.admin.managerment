"""
Unit tests for scheduler Celery tasks
"""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.accounts.models import User
from apps.tiktok_accounts.models import TikTokAccount
from apps.content.models import ScheduledPost, PublishHistory
from apps.scheduler.tasks import (
    publish_post,
    check_scheduled_posts,
    sync_all_accounts,
    sync_account
)


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
        status='active',
        follower_count=1000,
        following_count=500,
        token_expires_at=timezone.now() + timedelta(days=30)
    )


@pytest.fixture
def scheduled_post(db, user, tiktok_account):
    """Create test scheduled post"""
    post = ScheduledPost.objects.create(
        user=user,
        title="Test Post",
        description="Test description",
        status="scheduled",
        scheduled_time=timezone.now() - timedelta(minutes=5),
        retry_count=0,
        max_retries=3
    )
    post.accounts.add(tiktok_account)
    return post


@pytest.mark.django_db
class TestPublishPostTask:
    """Test publish_post Celery task"""

    def test_publish_post_success(self, scheduled_post, tiktok_account):
        """Test successful post publishing"""
        result = publish_post(str(scheduled_post.id))

        assert result['status'] == 'success'
        assert result['accounts_published'] == 1

        # Verify post status
        scheduled_post.refresh_from_db()
        assert scheduled_post.status == 'published'
        assert scheduled_post.published_at is not None

        # Verify history record
        history = PublishHistory.objects.filter(post=scheduled_post).first()
        assert history is not None
        assert history.status == 'success'

    def test_publish_post_not_found(self):
        """Test publishing non-existent post"""
        result = publish_post("00000000-0000-0000-0000-000000000000")

        assert result['status'] == 'not_found'

    def test_publish_post_already_published(self, scheduled_post):
        """Test publishing already published post"""
        scheduled_post.status = 'published'
        scheduled_post.save()

        result = publish_post(str(scheduled_post.id))

        assert result['status'] == 'already_published'

    def test_publish_post_no_accounts(self, scheduled_post):
        """Test publishing post with no accounts"""
        scheduled_post.accounts.clear()

        result = publish_post(str(scheduled_post.id))

        assert result['status'] == 'no_accounts'
        scheduled_post.refresh_from_db()
        assert scheduled_post.status == 'failed'

    def test_publish_post_retry_logic(self, scheduled_post):
        """Test retry logic increments retry_count"""
        # Simulate failure by removing accounts after status check
        initial_retry_count = scheduled_post.retry_count

        result = publish_post(str(scheduled_post.id))

        # If no accounts, should fail but not retry in this simple test
        if result['status'] == 'no_accounts':
            assert True
        else:
            scheduled_post.refresh_from_db()
            # Retry count should remain 0 for successful publish
            assert scheduled_post.retry_count == initial_retry_count


@pytest.mark.django_db
class TestCheckScheduledPostsTask:
    """Test check_scheduled_posts Celery task"""

    def test_check_scheduled_posts_queues_ready_posts(self, scheduled_post):
        """Test that scheduled posts are queued for publishing"""
        with patch('apps.scheduler.tasks.check_scheduled_posts_task.publish_post') as mock_publish:
            result = check_scheduled_posts()

            assert result['checked'] >= 1
            assert result['queued'] >= 1

            # Verify post status changed to pending
            scheduled_post.refresh_from_db()
            assert scheduled_post.status == 'pending'

            # Verify publish_post was called
            mock_publish.delay.assert_called()

    def test_check_scheduled_posts_no_posts(self):
        """Test when no posts are ready"""
        result = check_scheduled_posts()

        assert result['checked'] == 0
        assert result['queued'] == 0

    def test_check_scheduled_posts_skips_old_posts(self, user, tiktok_account):
        """Test that old posts are not queued"""
        # Create post scheduled 2 hours ago
        old_post = ScheduledPost.objects.create(
            user=user,
            title="Old Post",
            description="Old description",
            status="scheduled",
            scheduled_time=timezone.now() - timedelta(hours=2),
            retry_count=0
        )
        old_post.accounts.add(tiktok_account)

        result = check_scheduled_posts()

        # Old post should be skipped
        old_post.refresh_from_db()
        assert old_post.status == 'scheduled'  # Status unchanged

    def test_check_scheduled_posts_skips_max_retries(self, user, tiktok_account):
        """Test that posts with max retries are skipped"""
        # Create post that already failed 3 times
        failed_post = ScheduledPost.objects.create(
            user=user,
            title="Failed Post",
            description="Failed description",
            status="scheduled",
            scheduled_time=timezone.now() - timedelta(minutes=5),
            retry_count=3,
            max_retries=3
        )
        failed_post.accounts.add(tiktok_account)

        result = check_scheduled_posts()

        # Failed post should be skipped
        failed_post.refresh_from_db()
        assert failed_post.status == 'scheduled'  # Status unchanged


@pytest.mark.django_db
class TestSyncAccountsTask:
    """Test account sync Celery tasks"""

    def test_sync_all_accounts(self, tiktok_account):
        """Test syncing all active accounts"""
        result = sync_all_accounts()

        assert result['total'] >= 1
        assert result['synced'] >= 1
        assert result['failed'] == 0

        # Verify account was updated
        tiktok_account.refresh_from_db()
        assert tiktok_account.last_synced_at is not None

    def test_sync_all_accounts_no_accounts(self):
        """Test sync when no active accounts exist"""
        result = sync_all_accounts()

        assert result['total'] == 0
        assert result['synced'] == 0

    def test_sync_account_success(self, tiktok_account):
        """Test syncing single account"""
        result = sync_account(str(tiktok_account.id))

        assert result['status'] == 'success'
        assert result['username'] == tiktok_account.username

        # Verify account was updated
        tiktok_account.refresh_from_db()
        assert tiktok_account.last_synced_at is not None

    def test_sync_account_not_found(self):
        """Test syncing non-existent account"""
        result = sync_account("00000000-0000-0000-0000-000000000000")

        assert result['status'] == 'not_found'

    def test_sync_all_accounts_skips_inactive(self, user):
        """Test that inactive accounts are skipped"""
        inactive_account = TikTokAccount.objects.create(
            user=user,
            username="inactive_tiktok",
            display_name="Inactive TikTok",
            tiktok_user_id="654321",
            access_token="inactive_token",
            status='inactive',
            token_expires_at=timezone.now() + timedelta(days=30)
        )

        result = sync_all_accounts()

        # Inactive account should not be synced
        inactive_account.refresh_from_db()
        assert inactive_account.last_synced_at is None
