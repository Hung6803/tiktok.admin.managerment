"""
Unit tests for JWT handler
"""
import pytest
from datetime import datetime, timedelta
from django.conf import settings
from api.auth.jwt_handler import JWTHandler
from apps.accounts.models import User


@pytest.mark.django_db
class TestJWTHandler:
    """Test JWT token generation and validation"""

    def setup_method(self):
        """Create test user"""
        self.user = User.objects.create(
            email='test@example.com',
            username='testuser',
            password='hashedpass123'
        )
        self.handler = JWTHandler()

    def test_generate_tokens(self):
        """Test token generation returns all required fields"""
        tokens = self.handler.generate_tokens(self.user.id)

        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert 'token_type' in tokens
        assert 'expires_in' in tokens
        assert tokens['token_type'] == 'Bearer'
        assert tokens['expires_in'] == int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds())

    def test_decode_valid_access_token(self):
        """Test decoding valid access token"""
        tokens = self.handler.generate_tokens(self.user.id)
        payload = self.handler.decode_token(tokens['access_token'])

        assert payload is not None
        assert payload['user_id'] == str(self.user.id)
        assert payload['type'] == 'access'
        assert 'exp' in payload
        assert 'iat' in payload

    def test_decode_valid_refresh_token(self):
        """Test decoding valid refresh token"""
        tokens = self.handler.generate_tokens(self.user.id)
        payload = self.handler.decode_token(tokens['refresh_token'])

        assert payload is not None
        assert payload['user_id'] == str(self.user.id)
        assert payload['type'] == 'refresh'

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None"""
        payload = self.handler.decode_token('invalid.token.here')
        assert payload is None

    def test_decode_expired_token(self):
        """Test decoding expired token returns None"""
        import jwt

        # Create expired token
        payload = {
            'user_id': str(self.user.id),
            'type': 'access',
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        result = self.handler.decode_token(expired_token)
        assert result is None

    def test_get_user_from_valid_token(self):
        """Test extracting user from valid access token"""
        tokens = self.handler.generate_tokens(self.user.id)
        user = self.handler.get_user_from_token(tokens['access_token'])

        assert user is not None
        assert user.id == self.user.id
        assert user.email == self.user.email

    def test_get_user_from_refresh_token_fails(self):
        """Test refresh token cannot be used for user extraction"""
        tokens = self.handler.generate_tokens(self.user.id)
        user = self.handler.get_user_from_token(tokens['refresh_token'])

        assert user is None

    def test_get_user_from_invalid_token(self):
        """Test invalid token returns None"""
        user = self.handler.get_user_from_token('invalid.token')
        assert user is None

    def test_get_user_deleted_user(self):
        """Test soft-deleted user returns None"""
        tokens = self.handler.generate_tokens(self.user.id)

        # Soft delete user
        self.user.is_deleted = True
        self.user.save()

        user = self.handler.get_user_from_token(tokens['access_token'])
        assert user is None
