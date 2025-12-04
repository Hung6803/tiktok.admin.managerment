"""
Tests for TikTok token refresh service and tasks
"""
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

from apps.tiktok_accounts.models import TikTokAccount
from apps.tiktok_accounts.services.tiktok_token_refresh_service import TikTokTokenRefreshService
from apps.tiktok_accounts.tasks import refresh_expiring_tokens, refresh_single_account_token


@pytest.mark.django_db
class TestTikTokTokenRefreshService:
    """Test suite for TikTokTokenRefreshService"""

    def test_get_expiring_accounts(self, user):
        """Test fetching accounts with expiring tokens"""
        # Create test accounts
        expiring_account = TikTokAccount.objects.create(
            user=user,
            tiktok_user_id='user_expiring',
            username='expiring_user',
            display_name='Expiring User',
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expires_at=timezone.now() + timedelta(minutes=30),
            status='active'
        )

        not_expiring_account = TikTokAccount.objects.create(
            user=user,
            tiktok_user_id='user_not_expiring',
            username='not_expiring_user',
            display_name='Not Expiring User',
            access_token='test_access_token_2',
            refresh_token='test_refresh_token_2',
            token_expires_at=timezone.now() + timedelta(hours=24),
            status='active'
        )

        # Test service
        service = TikTokTokenRefreshService(hours_before_expiry=1)
        threshold = timezone.now() + timedelta(hours=1)
        accounts = service.get_expiring_accounts(threshold)

        assert expiring_account in accounts
        assert not_expiring_account not in accounts

    def test_get_expiring_accounts_excludes_inactive(self, user):
        """Test that inactive accounts are not included"""
        TikTokAccount.objects.create(
            user=user,
            tiktok_user_id='user_expired',
            username='expired_user',
            display_name='Expired User',
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expires_at=timezone.now() + timedelta(minutes=30),
            status='expired'
        )

        service = TikTokTokenRefreshService()
        threshold = timezone.now() + timedelta(hours=1)
        accounts = service.get_expiring_accounts(threshold)

        assert len(accounts) == 0

    @patch('apps.tiktok_accounts.services.tiktok_token_refresh_service.TikTokOAuthService.refresh_access_token')
    def test_refresh_account_token_success(self, mock_refresh, user):
        """Test successful token refresh for single account"""
        new_expiry = timezone.now() + timedelta(hours=24)
        mock_refresh.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'token_expires_at': new_expiry,
            'expires_in': 86400
        }

        account = TikTokAccount.objects.create(
            user=user,
            tiktok_user_id='user_test',
            username='test_user',
            display_name='Test User',
            access_token='old_access_token',
            refresh_token='old_refresh_token',
            token_expires_at=timezone.now() + timedelta(minutes=30),
            status='active'
        )

        service = TikTokTokenRefreshService()
        success = service.refresh_account_token(account)

        assert success is True
        mock_refresh.assert_called_once_with('old_refresh_token')

        # Verify account updated
        account.refresh_from_db()
        assert account.access_token == 'new_access_token'
        assert account.refresh_token == 'new_refresh_token'
        assert account.status == 'active'
        assert account.last_refreshed is not None

    @patch('apps.tiktok_accounts.services.tiktok_token_refresh_service.TikTokOAuthService.refresh_access_token')
    def test_refresh_account_token_no_refresh_token(self, mock_refresh, user):
        """Test error when no refresh token available"""
        account = TikTokAccount.objects.create(
            user=user,
            tiktok_user_id='user_no_refresh',
            username='no_refresh_user',
            display_name='No Refresh User',
            access_token='test_access_token',
            refresh_token='',  # No refresh token
            token_expires_at=timezone.now() + timedelta(minutes=30),
            status='active'
        )

        service = TikTokTokenRefreshService()

        with pytest.raises(ValueError, match="No refresh token available"):
            service.refresh_account_token(account)

        mock_refresh.assert_not_called()

    @patch('apps.tiktok_accounts.services.tiktok_token_refresh_service.TikTokOAuthService.refresh_access_token')
    def test_refresh_account_token_api_failure(self, mock_refresh, user):
        """Test handling of API failure during refresh"""
        mock_refresh.side_effect = Exception("API Error")

        account = TikTokAccount.objects.create(
            user=user,
            tiktok_user_id='user_api_fail',
            username='api_fail_user',
            display_name='API Fail User',
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_expires_at=timezone.now() + timedelta(minutes=30),
            status='active'
        )

        service = TikTokTokenRefreshService()

        with pytest.raises(Exception, match="API Error"):
            service.refresh_account_token(account)

    @patch('apps.tiktok_accounts.services.tiktok_token_refresh_service.TikTokOAuthService.refresh_access_token')
    def test_refresh_expiring_tokens_success(self, mock_refresh, user):
        """Test refreshing multiple expiring tokens"""
        new_expiry = timezone.now() + timedelta(hours=24)
        mock_refresh.return_value = {
            'access_token': 'new_token',
            'refresh_token': 'new_refresh',
            'token_expires_at': new_expiry
        }

        # Create multiple expiring accounts
        for i in range(3):
            TikTokAccount.objects.create(
                user=user,
                tiktok_user_id=f'user_{i}',
                username=f'user_{i}',
                display_name=f'User {i}',
                access_token=f'token_{i}',
                refresh_token=f'refresh_{i}',
                token_expires_at=timezone.now() + timedelta(minutes=30),
                status='active'
            )

        service = TikTokTokenRefreshService()
        results = service.refresh_expiring_tokens()

        assert results['total'] == 3
        assert results['refreshed'] == 3
        assert results['failed'] == 0
        assert len(results['errors']) == 0

    @patch('apps.tiktok_accounts.services.tiktok_token_refresh_service.TikTokOAuthService.refresh_access_token')
    def test_refresh_expiring_tokens_dry_run(self, mock_refresh, user):
        """Test dry run mode does not actually refresh"""
        TikTokAccount.objects.create(
            user=user,
            tiktok_user_id='user_dry',
            username='dry_user',
            display_name='Dry User',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(minutes=30),
            status='active'
        )

        service = TikTokTokenRefreshService()
        results = service.refresh_expiring_tokens(dry_run=True)

        assert results['total'] == 1
        assert results['refreshed'] == 1
        assert results['failed'] == 0
        mock_refresh.assert_not_called()

    @patch('apps.tiktok_accounts.services.tiktok_token_refresh_service.TikTokOAuthService.refresh_access_token')
    def test_refresh_expiring_tokens_handles_failures(self, mock_refresh, user):
        """Test that failures are handled gracefully"""
        mock_refresh.side_effect = Exception("Refresh failed")

        account = TikTokAccount.objects.create(
            user=user,
            tiktok_user_id='user_fail',
            username='fail_user',
            display_name='Fail User',
            access_token='test_token',
            refresh_token='test_refresh',
            token_expires_at=timezone.now() + timedelta(minutes=30),
            status='active'
        )

        service = TikTokTokenRefreshService()
        results = service.refresh_expiring_tokens()

        assert results['total'] == 1
        assert results['refreshed'] == 0
        assert results['failed'] == 1
        assert len(results['errors']) == 1

        # Verify account marked as expired
        account.refresh_from_db()
        assert account.status == 'expired'
        assert 'Refresh failed' in account.last_error

    def test_refresh_specific_account_not_found(self):
        """Test refreshing non-existent account"""
        service = TikTokTokenRefreshService()

        with pytest.raises(TikTokAccount.DoesNotExist):
            service.refresh_specific_account(99999)


@pytest.mark.django_db
class TestTokenRefreshTasks:
    """Test suite for Celery tasks"""

    @patch('apps.tiktok_accounts.services.tiktok_token_refresh_service.TikTokTokenRefreshService')
    def test_refresh_expiring_tokens_task(self, mock_service_class, user):
        """Test Celery task for refreshing tokens"""
        mock_service = MagicMock()
        mock_service.refresh_expiring_tokens.return_value = {
            'total': 2,
            'refreshed': 2,
            'failed': 0,
            'errors': []
        }
        mock_service_class.return_value = mock_service

        # Clear cache to avoid lock issues
        cache.clear()

        result = refresh_expiring_tokens(dry_run=False)

        assert result['status'] == 'success'
        assert result['results']['refreshed'] == 2
        mock_service.refresh_expiring_tokens.assert_called_once_with(dry_run=False)

    @patch('apps.tiktok_accounts.services.tiktok_token_refresh_service.TikTokTokenRefreshService')
    def test_refresh_single_account_token_task(self, mock_service_class, user):
        """Test task for refreshing single account"""
        mock_service = MagicMock()
        mock_service.refresh_specific_account.return_value = True
        mock_service_class.return_value = mock_service

        result = refresh_single_account_token(account_id=123)

        assert result['status'] == 'success'
        assert result['account_id'] == 123
        mock_service.refresh_specific_account.assert_called_once_with(123)

    @patch('apps.tiktok_accounts.services.tiktok_token_refresh_service.TikTokTokenRefreshService')
    def test_refresh_single_account_token_task_failure(self, mock_service_class, user):
        """Test task handles failure gracefully"""
        mock_service = MagicMock()
        mock_service.refresh_specific_account.side_effect = Exception("Refresh failed")
        mock_service_class.return_value = mock_service

        result = refresh_single_account_token(account_id=123)

        assert result['status'] == 'failed'
        assert result['account_id'] == 123
        assert 'Refresh failed' in result['error']
