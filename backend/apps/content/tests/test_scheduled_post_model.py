from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from apps.content.models.scheduled_post_model import ScheduledPost
from apps.tiktok_accounts.models.tiktok_account_model import TikTokAccount

User = get_user_model()

class ScheduledPostModelTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # Create a TikTok account
        self.tiktok_account = TikTokAccount.objects.create(
            user=self.user,
            tiktok_user_id='12345',
            username='testtiktokuser',
            display_name='Test TikTok User',
            access_token='encrypted_token_value',
            token_expires_at=timezone.now() + timedelta(hours=2)
        )

        # Create a scheduled post
        self.scheduled_post = ScheduledPost.objects.create(
            tiktok_account=self.tiktok_account,
            caption='Test post caption',
            hashtags=['test', 'automation'],
            mentions=['@testuser'],
            scheduled_time=timezone.now() + timedelta(days=1),
            status='draft'
        )

    def test_model_creation(self):
        """Test model creation with required fields"""
        self.assertEqual(self.scheduled_post.tiktok_account, self.tiktok_account)
        self.assertEqual(self.scheduled_post.caption, 'Test post caption')
        self.assertEqual(self.scheduled_post.hashtags, ['test', 'automation'])
        self.assertEqual(self.scheduled_post.status, 'draft')

    def test_status_transitions(self):
        """Test status transitions"""
        valid_statuses = [
            'draft', 'scheduled', 'queued', 'processing',
            'published', 'failed', 'cancelled'
        ]
        for status in valid_statuses:
            self.scheduled_post.status = status
            self.scheduled_post.save()
            self.assertEqual(self.scheduled_post.status, status)

    def test_can_retry(self):
        """Test retry logic"""
        # Initially, post is draft
        self.assertFalse(self.scheduled_post.can_retry())

        # Change status to failed
        self.scheduled_post.status = 'failed'

        # Retry within max_retries
        self.scheduled_post.retry_count = 2
        self.assertTrue(self.scheduled_post.can_retry())

        # Exceed max_retries
        self.scheduled_post.retry_count = 3
        self.assertFalse(self.scheduled_post.can_retry())

    def test_is_ready_to_publish(self):
        """Test is_ready_to_publish method"""
        # Initially draft - not ready
        self.assertFalse(self.scheduled_post.is_ready_to_publish())

        # Change to scheduled with past time
        self.scheduled_post.status = 'scheduled'
        self.scheduled_post.scheduled_time = timezone.now() - timedelta(hours=1)
        self.assertTrue(self.scheduled_post.is_ready_to_publish())

        # Soft delete prevents publishing
        self.scheduled_post.is_deleted = True
        self.assertFalse(self.scheduled_post.is_ready_to_publish())

    def test_privacy_choices(self):
        """Test privacy level choices"""
        valid_privacies = ['public', 'friends', 'private']
        for privacy in valid_privacies:
            self.scheduled_post.privacy_level = privacy
            self.scheduled_post.save()
            self.assertEqual(self.scheduled_post.privacy_level, privacy)

    def test_string_representation(self):
        """Test string representation of the model"""
        expected_str = (
            f"{self.tiktok_account.username} - {self.scheduled_post.scheduled_time} "
            f"({self.scheduled_post.status})"
        )
        self.assertEqual(str(self.scheduled_post), expected_str)