"""
Tests for TikTok OAuth API endpoints
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.tiktok_accounts.api.tiktok_oauth_api import router, authorize, oauth_callback
from apps.tiktok_accounts.models import TikTokAccount

User = get_user_model()


@pytest.fixture
def mock_user(db):
    """Create a test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def request_factory():
    """Django request factory"""
    return RequestFactory()


@pytest.fixture
def authenticated_request(request_factory, mock_user):
    """Create authenticated request"""
    def _create_request(method='GET', path='/', data=None):
        if method == 'GET':
            request = request_factory.get(path, data or {})
        else:
            request = request_factory.post(path, data or {})
        request.user = mock_user
        return request
    return _create_request


@pytest.mark.django_db
class TestTikTokOAuthAPI:
    """Test TikTok OAuth API endpoints"""

    def setup_method(self):
        """Clear cache before each test"""
        cache.clear()

    @patch('apps.tiktok_accounts.api.tiktok_oauth_api.TikTokOAuthService')
    def test_authorize_endpoint_authenticated(self, mock_oauth_service, authenticated_request):
        """Test authorize endpoint with authenticated user"""
        # Mock OAuth service
        mock_service_instance = Mock()
        mock_service_instance.get_authorization_url.return_value = {
            'url': 'https://www.tiktok.com/v2/auth/authorize?client_key=test&state=abc123',
            'state': 'abc123'
        }
        mock_oauth_service.return_value = mock_service_instance

        request = authenticated_request()
        response = authorize(request)

        assert response.status_code == 302  # Redirect
        assert 'tiktok.com' in response.url

    def test_authorize_endpoint_unauthenticated(self, request_factory):
        """Test authorize endpoint without authentication"""
        request = request_factory.get('/authorize')
        request.user = Mock(is_authenticated=False)

        response = authorize(request)

        assert response.status_code == 401
        data = response.json() if hasattr(response, 'json') else {}
        assert 'error' in data

    @patch('apps.tiktok_accounts.api.tiktok_oauth_api.TikTokAccountService')
    @patch('apps.tiktok_accounts.api.tiktok_oauth_api.TikTokOAuthService')
    def test_callback_endpoint_success(self, mock_oauth_service, mock_account_service, authenticated_request, mock_user):
        """Test callback endpoint with valid code"""
        # Setup cache state
        cache_key = f"tiktok_oauth_state:{mock_user.id}"
        cache.set(cache_key, 'valid_state', 300)

        # Mock OAuth service
        mock_service_instance = Mock()
        mock_service_instance.validate_state.return_value = True
        mock_service_instance.exchange_code_for_token.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'token_expires_at': '2025-12-05T00:00:00Z'
        }
        mock_oauth_service.return_value = mock_service_instance

        # Mock Account service
        mock_account_instance = Mock()
        mock_account_instance.get_user_info.return_value = {
            'open_id': 'test_open_id',
            'username': 'test_username',
            'display_name': 'Test User',
            'avatar_url': 'https://example.com/avatar.jpg'
        }
        mock_account_service.return_value = mock_account_instance

        request = authenticated_request(path='/callback?code=test_code&state=valid_state')
        response = oauth_callback(request)

        assert response.status_code == 200
        data = response.json() if hasattr(response, 'json') else {}
        assert data.get('success') is True

    def test_callback_endpoint_unauthenticated(self, request_factory):
        """Test callback endpoint without authentication"""
        request = request_factory.get('/callback?code=test_code&state=test_state')
        request.user = Mock(is_authenticated=False)

        response = oauth_callback(request)

        assert response.status_code == 401

    def test_callback_endpoint_missing_code(self, authenticated_request):
        """Test callback endpoint without authorization code"""
        request = authenticated_request(path='/callback?state=test_state')
        response = oauth_callback(request)

        assert response.status_code == 400
        data = response.json() if hasattr(response, 'json') else {}
        assert 'error' in data

    def test_callback_endpoint_invalid_state(self, authenticated_request, mock_user):
        """Test callback endpoint with invalid state (CSRF protection)"""
        # No state in cache
        request = authenticated_request(path='/callback?code=test_code&state=invalid_state')
        response = oauth_callback(request)

        assert response.status_code == 400
        data = response.json() if hasattr(response, 'json') else {}
        assert 'error' in data
        assert 'state' in data['error'].lower()

    @patch('apps.tiktok_accounts.api.tiktok_oauth_api.TikTokOAuthService')
    def test_callback_endpoint_oauth_error(self, mock_oauth_service, authenticated_request):
        """Test callback endpoint when TikTok returns error"""
        request = authenticated_request(path='/callback?error=access_denied&state=test_state')
        response = oauth_callback(request)

        assert response.status_code == 400
        data = response.json() if hasattr(response, 'json') else {}
        assert 'error' in data
