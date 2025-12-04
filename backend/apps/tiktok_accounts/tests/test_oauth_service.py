"""
Tests for TikTok OAuth service
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from django.utils import timezone

from apps.tiktok_accounts.services.tiktok_oauth_service import TikTokOAuthService


class TestTikTokOAuthService:
    """Test TikTok OAuth service"""

    def test_get_authorization_url_generates_state(self):
        """Test authorization URL generation with auto-generated state"""
        service = TikTokOAuthService()
        result = service.get_authorization_url()

        assert 'url' in result
        assert 'state' in result
        assert len(result['state']) > 20  # Secure random state
        assert 'client_key=' in result['url']
        assert 'redirect_uri=' in result['url']
        assert 'state=' in result['url']

    def test_get_authorization_url_with_custom_state(self):
        """Test authorization URL generation with custom state"""
        service = TikTokOAuthService()
        custom_state = 'custom_state_12345'
        result = service.get_authorization_url(state=custom_state)

        assert result['state'] == custom_state
        assert f'state={custom_state}' in result['url']

    def test_validate_state_success(self):
        """Test state validation succeeds with matching states"""
        service = TikTokOAuthService()
        state = 'test_state_12345'

        assert service.validate_state(state, state) is True

    def test_validate_state_failure(self):
        """Test state validation fails with different states"""
        service = TikTokOAuthService()

        assert service.validate_state('state1', 'state2') is False

    @patch('apps.tiktok_accounts.services.tiktok_oauth_service.TikTokAPIClient')
    def test_exchange_code_for_token(self, mock_client_class):
        """Test authorization code exchange for token"""
        # Mock API response
        mock_client = Mock()
        mock_client.post.return_value = {
            'data': {
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'expires_in': 86400,
                'open_id': 'test_open_id',
                'scope': 'user.info.basic,video.upload'
            }
        }
        mock_client_class.return_value = mock_client

        service = TikTokOAuthService()
        result = service.exchange_code_for_token('test_code')

        assert result['access_token'] == 'test_access_token'
        assert result['refresh_token'] == 'test_refresh_token'
        assert result['expires_in'] == 86400
        assert 'token_expires_at' in result
        mock_client.post.assert_called_once()

    @patch('apps.tiktok_accounts.services.tiktok_oauth_service.TikTokAPIClient')
    def test_refresh_access_token(self, mock_client_class):
        """Test token refresh"""
        # Mock API response
        mock_client = Mock()
        mock_client.post.return_value = {
            'data': {
                'access_token': 'new_access_token',
                'refresh_token': 'new_refresh_token',
                'expires_in': 86400
            }
        }
        mock_client_class.return_value = mock_client

        service = TikTokOAuthService()
        result = service.refresh_access_token('old_refresh_token')

        assert result['access_token'] == 'new_access_token'
        assert 'token_expires_at' in result
        mock_client.post.assert_called_once()
