"""
TikTok OAuth 2.0 authentication service
Handles authorization flow, token exchange, and token refresh
"""
from urllib.parse import urlencode
from typing import Dict, Any
from datetime import datetime, timedelta
from django.utils import timezone
import secrets
import logging

from config.tiktok_config import TikTokConfig
from core.utils.tiktok_api_client import TikTokAPIClient

logger = logging.getLogger(__name__)


class TikTokOAuthService:
    """
    TikTok OAuth 2.0 service
    Manages OAuth authorization flow and token lifecycle
    """

    def __init__(self):
        self.config = TikTokConfig()
        self.client = TikTokAPIClient()

    def get_authorization_url(self, state: str = None) -> Dict[str, str]:
        """
        Generate OAuth authorization URL with state parameter

        Args:
            state: Optional CSRF state parameter (generated if not provided)

        Returns:
            Dictionary with 'url' and 'state'
        """
        if not state:
            # Generate cryptographically secure random state
            state = secrets.token_urlsafe(32)

        params = {
            'client_key': self.config.CLIENT_KEY,
            'scope': self.config.get_scope_string(),
            'response_type': 'code',
            'redirect_uri': self.config.REDIRECT_URI,
            'state': state,
            'disable_auto_auth': '1',  # Always show authorization page for multiple accounts
        }

        auth_url = f"{self.config.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

        logger.info(f"Generated authorization URL with state: {state[:8]}...")
        logger.info(f"OAuth scopes requested: {self.config.get_scope_string()}")
        logger.info(f"Full authorization URL: {auth_url}")

        return {
            'url': auth_url,
            'state': state
        }

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Dictionary with token information:
            - access_token: Plaintext access token (to be encrypted by model)
            - refresh_token: Plaintext refresh token (to be encrypted by model)
            - expires_in: Token lifetime in seconds
            - token_expires_at: Datetime when token expires

        Raises:
            requests.exceptions.RequestException: On API error
        """
        logger.info("Exchanging authorization code for access token")

        data = {
            'client_key': self.config.CLIENT_KEY,
            'client_secret': self.config.CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.config.REDIRECT_URI,
        }

        try:
            # TikTok token endpoint requires application/x-www-form-urlencoded
            response = self.client.post(
                self.config.OAUTH_TOKEN_URL,
                data=data  # Use data= for form-urlencoded, not json=
            )

            # Log response for debugging (redact sensitive data)
            logger.debug(f"Token response keys: {response.keys() if response else 'None'}")

            # Extract token data from response
            # TikTok v2 API wraps token in 'data' field, but may also return at root level
            token_data = response.get('data', {}) or response

            if 'access_token' not in token_data:
                # Log error details for debugging
                error_info = response.get('error', {}) if response else {}
                logger.error(f"Token exchange failed: No access_token. Error: {error_info}")
                raise ValueError("No access_token in response")

            expires_in = token_data.get('expires_in', 86400)  # Default 24 hours
            token_expires_at = timezone.now() + timedelta(seconds=expires_in)

            logger.info("Successfully exchanged code for token")

            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', ''),
                'expires_in': expires_in,
                'token_expires_at': token_expires_at,
                'open_id': token_data.get('open_id', ''),
                'scope': token_data.get('scope', ''),
            }

        except Exception as e:
            logger.error(f"Token exchange failed: {str(e)}")
            raise

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token

        Args:
            refresh_token: Current refresh token (plaintext/decrypted)

        Returns:
            Dictionary with new token information

        Raises:
            requests.exceptions.RequestException: On API error
        """
        logger.info("Refreshing access token")

        data = {
            'client_key': self.config.CLIENT_KEY,
            'client_secret': self.config.CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        try:
            # TikTok token endpoint requires application/x-www-form-urlencoded
            response = self.client.post(
                self.config.OAUTH_TOKEN_URL,
                data=data  # Use data= for form-urlencoded, not json=
            )

            # TikTok v2 API wraps token in 'data' field
            token_data = response.get('data', {}) or response

            if 'access_token' not in token_data:
                error_info = response.get('error', {}) if response else {}
                logger.error(f"Token refresh failed: No access_token. Error: {error_info}")
                raise ValueError("No access_token in response")

            expires_in = token_data.get('expires_in', 86400)
            token_expires_at = timezone.now() + timedelta(seconds=expires_in)

            logger.info("Successfully refreshed access token")

            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', refresh_token),  # Use old if not rotated
                'expires_in': expires_in,
                'token_expires_at': token_expires_at,
            }

        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise

    def validate_state(self, received_state: str, stored_state: str) -> bool:
        """
        Validate OAuth state parameter to prevent CSRF attacks

        Args:
            received_state: State from OAuth callback
            stored_state: State stored in session/cache

        Returns:
            True if states match
        """
        is_valid = secrets.compare_digest(received_state, stored_state)

        if not is_valid:
            logger.warning("OAuth state validation failed - possible CSRF attack")
        else:
            logger.info("OAuth state validated successfully")

        return is_valid
