from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from analytics.models.account_analytics_model import AccountAnalytics
from tiktok_accounts.models.tiktok_account_model import TikTokAccount

User = get_user_model()

class AccountAnalyticsModelTestCase(TestCase):
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

        # Create an account analytics entry
        today = date.today()
        self.account_analytics = AccountAnalytics.objects.create(
            tiktok_account=self.tiktok_account,
            date=today,
            follower_count=1000,
            following_count=500,
            video_count=50,
            total_likes=10000,
            total_views=50000,
            total_shares=1000,
            total_comments=500,
            follower_growth=50,
            engagement_rate=0.0
        )

    def test_account_analytics_creation(self):
        """Test account analytics entry creation"""
        self.assertEqual(self.account_analytics.tiktok_account, self.tiktok_account)
        self.assertEqual(self.account_analytics.date, date.today())
        self.assertEqual(self.account_analytics.follower_count, 1000)
        self.assertEqual(self.account_analytics.total_views, 50000)

    def test_unique_together_constraint(self):
        """Test unique_together constraint for (tiktok_account, date)"""
        with self.assertRaises(Exception):
            AccountAnalytics.objects.create(
                tiktok_account=self.tiktok_account,
                date=date.today(),  # duplicate date for same TikTok account
                follower_count=2000
            )

    def test_calculate_engagement_rate(self):
        """Test engagement rate calculation method"""
        # Test with existing values
        engagement_rate = self.account_analytics.calculate_engagement_rate()
        expected_rate = round(((10000 + 500 + 1000) / 50000) * 100, 2)
        self.assertEqual(engagement_rate, expected_rate)

        # Test with no views
        self.account_analytics.total_views = 0
        engagement_rate = self.account_analytics.calculate_engagement_rate()
        self.assertEqual(engagement_rate, 0.0)

    def test_manual_engagement_rate_update(self):
        """Test manually updating engagement rate"""
        # Update engagement rate manually
        manual_rate = 2.5
        self.account_analytics.engagement_rate = manual_rate
        self.account_analytics.save()

        retrieved_analytics = AccountAnalytics.objects.get(id=self.account_analytics.id)
        self.assertEqual(retrieved_analytics.engagement_rate, manual_rate)

    def test_string_representation(self):
        """Test string representation of the model"""
        expected_str = f"{self.tiktok_account.username} - {date.today()}"
        self.assertEqual(str(self.account_analytics), expected_str)