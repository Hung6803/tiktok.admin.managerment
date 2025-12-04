"""
JWT token generation and validation handler
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
from django.conf import settings


class JWTHandler:
    """Handle JWT token creation and validation"""

    @staticmethod
    def generate_tokens(user_id: str) -> dict:
        """
        Generate access and refresh tokens for a user

        Args:
            user_id: User's unique identifier

        Returns:
            dict: Contains access_token, refresh_token, token_type, expires_in
        """
        now = datetime.utcnow()

        # Access token payload
        access_payload = {
            'user_id': str(user_id),
            'type': 'access',
            'exp': now + settings.JWT_ACCESS_TOKEN_LIFETIME,
            'iat': now
        }

        # Refresh token payload
        refresh_payload = {
            'user_id': str(user_id),
            'type': 'refresh',
            'exp': now + settings.JWT_REFRESH_TOKEN_LIFETIME,
            'iat': now
        }

        access_token = jwt.encode(
            access_payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )

        refresh_token = jwt.encode(
            refresh_payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds())
        }

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """
        Decode and validate JWT token

        Args:
            token: JWT token string

        Returns:
            dict: Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def get_user_from_token(token: str):
        """
        Extract user from token

        Args:
            token: JWT token string

        Returns:
            User: User object if valid, None otherwise
        """
        from apps.accounts.models import User

        payload = JWTHandler.decode_token(token)
        if not payload or payload.get('type') != 'access':
            return None

        try:
            user = User.objects.get(id=payload['user_id'], is_deleted=False)
            return user
        except User.DoesNotExist:
            return None
