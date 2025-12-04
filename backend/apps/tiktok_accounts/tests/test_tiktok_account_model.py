from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from apps.tiktok_accounts.models.tiktok_account_model import TikTokAccount

User = get_user_model()

class TikTokAccountModelTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # Create a TikTok account with a specific expiration time
        self.tiktok_account = TikTokAccount.objects.create(
            user=self.user,
            tiktok_user_id='12345',
            username='testtiktokuser',
            display_name='Test TikTok User',
            avatar_url='https://example.com/avatar.jpg',
            status='active',
            access_token='encrypted_token_value',
            refresh_token='encrypted_refresh_token',
            token_expires_at=timezone.now() + timedelta(hours=2),
            follower_count=100,
            following_count=50,
            video_count=10
        )

    def test_tiktok_account_creation(self):
        """Test TikTok account is created successfully with all required fields"""
        self.assertEqual(self.tiktok_account.user, self.user)
        self.assertEqual(self.tiktok_account.tiktok_user_id, '12345')
        self.assertEqual(self.tiktok_account.username, 'testtiktokuser')
        self.assertEqual(self.tiktok_account.status, 'active')

    def test_unique_tiktok_user_id(self):
        """Test unique constraint on tiktok_user_id"""
        with self.assertRaises(Exception):
            TikTokAccount.objects.create(
                user=self.user,
                tiktok_user_id='12345',  # duplicate tiktok_user_id
                username='another_user',
                access_token='another_token',
                token_expires_at=timezone.now() + timedelta(hours=1)
            )

    def test_status_choices(self):
        """Test status choices"""
        valid_statuses = ['active', 'expired', 'revoked', 'error']
        for status in valid_statuses:
            self.tiktok_account.status = status
            self.tiktok_account.save()
            self.assertEqual(self.tiktok_account.status, status)

    def test_token_expiration(self):
        """Test is_token_expired method"""
        # Token valid for 2 hours
        self.assertFalse(self.tiktok_account.is_token_expired())

        # Set token expiration to the past
        self.tiktok_account.token_expires_at = timezone.now() - timedelta(hours=1)
        self.assertTrue(self.tiktok_account.is_token_expired())

    def test_token_needs_refresh(self):
        """Test needs_refresh method"""
        # Set token to expire in 30 minutes
        self.tiktok_account.token_expires_at = timezone.now() + timedelta(minutes=30)
        self.assertTrue(self.tiktok_account.needs_refresh())

        # Set token to expire in 2 hours
        self.tiktok_account.token_expires_at = timezone.now() + timedelta(hours=2)
        self.assertFalse(self.tiktok_account.needs_refresh())

    def test_string_representation(self):
        """Test string representation of the model"""
        expected_str = f"{self.tiktok_account.username} (@{self.tiktok_account.tiktok_user_id})"
        self.assertEqual(str(self.tiktok_account), expected_str)