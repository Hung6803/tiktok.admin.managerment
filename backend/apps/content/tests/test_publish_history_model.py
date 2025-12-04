from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from apps.content.models.publish_history_model import PublishHistory
from apps.content.models.scheduled_post_model import ScheduledPost
from apps.tiktok_accounts.models.tiktok_account_model import TikTokAccount

User = get_user_model()

class PublishHistoryModelTestCase(TestCase):
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
            caption='Test post',
            scheduled_time=timezone.now() + timedelta(days=1)
        )

        # Create a publish history entry
        self.publish_history = PublishHistory.objects.create(
            scheduled_post=self.scheduled_post,
            attempt_number=1,
            success=False,
            error_code='RATE_LIMIT',
            error_message='Too many requests',
            api_response={'error': 'Rate limit exceeded'},
            http_status=429
        )

    def test_publish_history_creation(self):
        """Test publish history entry creation"""
        self.assertEqual(self.publish_history.scheduled_post, self.scheduled_post)
        self.assertEqual(self.publish_history.attempt_number, 1)
        self.assertFalse(self.publish_history.success)
        self.assertEqual(self.publish_history.error_code, 'RATE_LIMIT')
        self.assertEqual(self.publish_history.error_message, 'Too many requests')
        self.assertEqual(self.publish_history.http_status, 429)

    def test_started_at_timestamp(self):
        """Test started_at timestamp is set automatically"""
        self.assertIsNotNone(self.publish_history.started_at)
        self.assertTrue(self.publish_history.started_at <= timezone.now())

    def test_completed_at_timestamp(self):
        """Test optional completed_at timestamp"""
        self.assertIsNone(self.publish_history.completed_at)

        # Set completed_at manually
        completed_time = timezone.now() + timedelta(seconds=30)
        self.publish_history.completed_at = completed_time
        self.publish_history.save()
        self.assertEqual(self.publish_history.completed_at, completed_time)

    def test_get_duration(self):
        """Test get_duration method"""
        # Initially no duration (no completed_at)
        self.assertIsNone(self.publish_history.get_duration())

        # Set completed_at to simulate duration
        self.publish_history.started_at = timezone.now() - timedelta(seconds=45)
        self.publish_history.completed_at = self.publish_history.started_at + timedelta(seconds=30)
        self.publish_history.save()

        # Check duration calculation
        expected_duration = 30
        self.assertAlmostEqual(self.publish_history.get_duration(), expected_duration, delta=1)

    def test_api_response_json(self):
        """Test API response JSONField"""
        # Should handle nested dictionaries
        complex_response = {
            'video_id': '12345',
            'metadata': {
                'duration': 60,
                'size': '1080p'
            },
            'errors': []
        }
        self.publish_history.api_response = complex_response
        self.publish_history.save()

        # Retrieve and verify
        retrieved_history = PublishHistory.objects.get(id=self.publish_history.id)
        self.assertEqual(retrieved_history.api_response, complex_response)

    def test_string_representation(self):
        """Test string representation of the model"""
        expected_str = "Attempt 1 - Failed"
        self.assertEqual(str(self.publish_history), expected_str)