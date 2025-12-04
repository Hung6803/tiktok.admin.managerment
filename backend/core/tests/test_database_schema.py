import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.accounts.models.user_model import User
from apps.tiktok_accounts.models.tiktok_account_model import TikTokAccount
from apps.content.models.scheduled_post_model import ScheduledPost
from apps.content.models.post_media_model import PostMedia
from apps.content.models.publish_history_model import PublishHistory
from apps.analytics.models.account_analytics_model import AccountAnalytics
from core.models.audit_log_model import AuditLog

class DatabaseSchemaTestCase(TestCase):
    def setUp(self):
        # Create a base user for testing
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

    def test_base_model_fields(self):
        """Test BaseModel common fields"""
        user = self.user
        self.assertIsNotNone(user.id)
        self.assertTrue(isinstance(user.id, uuid.UUID))
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
        self.assertFalse(user.is_deleted)
        self.assertIsNone(user.deleted_at)

    def test_user_model(self):
        """Test User model creation and constraints"""
        # Check unique email constraint
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='duplicateuser',
                email='test@example.com',  # Same email as setUp user
                password='testpassword2'
            )

        # Check email indexing and verifiable fields
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertFalse(self.user.is_email_verified)
        self.assertIsNone(self.user.last_login_ip)

    def test_tiktok_account_model(self):
        """Test TikTokAccount model creation and relationships"""
        tiktok_account = TikTokAccount.objects.create(
            user=self.user,
            tiktok_user_id='tiktok_123',
            username='testaccount',
            display_name='Test TikTok Account',
            access_token='fake_token',
            refresh_token='fake_refresh_token',
            token_expires_at=timezone.now() + timedelta(days=30)
        )

        # Check relationships and field constraints
        self.assertEqual(tiktok_account.user, self.user)
        self.assertEqual(tiktok_account.status, 'active')
        self.assertEqual(tiktok_account.tiktok_user_id, 'tiktok_123')

        # Check unique tiktok_user_id
        with self.assertRaises(IntegrityError):
            TikTokAccount.objects.create(
                user=self.user,
                tiktok_user_id='tiktok_123',  # Duplicate
                username='duplicateaccount',
                access_token='another_fake_token',
                token_expires_at=timezone.now() + timedelta(days=30)
            )

    def test_scheduled_post_model(self):
        """Test ScheduledPost model creation"""
        tiktok_account = TikTokAccount.objects.create(
            user=self.user,
            tiktok_user_id='tiktok_456',
            username='postaccount',
            access_token='post_token',
            token_expires_at=timezone.now() + timedelta(days=30)
        )

        scheduled_post = ScheduledPost.objects.create(
            tiktok_account=tiktok_account,
            caption='Test Post Caption',
            scheduled_time=timezone.now() + timedelta(days=1),
            hashtags=['test', 'tiktok'],
            mentions=['@friend']
        )

        # Validate relationships and defaults
        self.assertEqual(scheduled_post.tiktok_account, tiktok_account)
        self.assertEqual(scheduled_post.status, 'draft')
        self.assertEqual(scheduled_post.privacy_level, 'public')
        self.assertEqual(scheduled_post.retry_count, 0)
        self.assertEqual(scheduled_post.max_retries, 3)

    def test_post_media_model(self):
        """Test PostMedia model creation"""
        tiktok_account = TikTokAccount.objects.create(
            user=self.user,
            tiktok_user_id='tiktok_789',
            username='mediaaccount',
            access_token='media_token',
            token_expires_at=timezone.now() + timedelta(days=30)
        )

        scheduled_post = ScheduledPost.objects.create(
            tiktok_account=tiktok_account,
            caption='Media Test Post',
            scheduled_time=timezone.now() + timedelta(days=1)
        )

        post_media = PostMedia.objects.create(
            scheduled_post=scheduled_post,
            media_type='video',
            file_path='/test/video.mp4',
            file_size=1024000,  # 1MB
            file_mime_type='video/mp4',
            duration=30,
            width=1920,
            height=1080
        )

        # Validate media attributes
        self.assertEqual(post_media.scheduled_post, scheduled_post)
        self.assertEqual(post_media.media_type, 'video')
        self.assertFalse(post_media.is_processed)

    def test_publish_history_model(self):
        """Test PublishHistory model"""
        tiktok_account = TikTokAccount.objects.create(
            user=self.user,
            tiktok_user_id='tiktok_history',
            username='historyaccount',
            access_token='history_token',
            token_expires_at=timezone.now() + timedelta(days=30)
        )

        scheduled_post = ScheduledPost.objects.create(
            tiktok_account=tiktok_account,
            caption='History Test Post',
            scheduled_time=timezone.now() + timedelta(days=1)
        )

        publish_history = PublishHistory.objects.create(
            scheduled_post=scheduled_post,
            attempt_number=1,
            success=False,
            error_code='NETWORK_ERROR',
            error_message='Connection timeout'
        )

        self.assertEqual(publish_history.scheduled_post, scheduled_post)
        self.assertEqual(publish_history.attempt_number, 1)
        self.assertFalse(publish_history.success)

    def test_account_analytics_model(self):
        """Test AccountAnalytics model"""
        tiktok_account = TikTokAccount.objects.create(
            user=self.user,
            tiktok_user_id='tiktok_analytics',
            username='analyticsaccount',
            access_token='analytics_token',
            token_expires_at=timezone.now() + timedelta(days=30)
        )

        today = timezone.now().date()
        analytics = AccountAnalytics.objects.create(
            tiktok_account=tiktok_account,
            date=today,
            follower_count=1000,
            total_likes=5000,
            engagement_rate=4.5
        )

        self.assertEqual(analytics.tiktok_account, tiktok_account)
        self.assertEqual(analytics.date, today)
        self.assertEqual(analytics.total_likes, 5000)

    def test_audit_log_model(self):
        """Test AuditLog model"""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='login',
            resource_type='User',
            resource_id=self.user.id,
            ip_address='127.0.0.1',
            changes={'login_status': 'successful'}
        )

        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'login')
        self.assertEqual(audit_log.resource_type, 'User')

    def test_soft_delete(self):
        """Test soft delete functionality"""
        tiktok_account = TikTokAccount.objects.create(
            user=self.user,
            tiktok_user_id='tiktok_softdelete',
            username='softdeleteaccount',
            access_token='softdelete_token',
            token_expires_at=timezone.now() + timedelta(days=30)
        )

        # Mark as deleted
        tiktok_account.is_deleted = True
        tiktok_account.deleted_at = timezone.now()
        tiktok_account.save()

        # Verify soft delete
        self.assertTrue(tiktok_account.is_deleted)
        self.assertIsNotNone(tiktok_account.deleted_at)

        # Verify soft delete prevents retrieval
        existing_accounts = TikTokAccount.objects.filter(is_deleted=False)
        self.assertNotIn(tiktok_account, existing_accounts)