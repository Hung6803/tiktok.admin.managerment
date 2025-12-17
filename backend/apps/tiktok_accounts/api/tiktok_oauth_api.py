"""
TikTok OAuth API endpoints
Handles OAuth authorization and callback
"""
from ninja import Router
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect
from django.core.cache import cache
import logging

from apps.tiktok_accounts.services import TikTokOAuthService, TikTokAccountService
from apps.tiktok_accounts.models import TikTokAccount
from api.auth.middleware import JWTAuth

logger = logging.getLogger(__name__)

router = Router()
jwt_auth = JWTAuth()


@router.get("/authorize")
def authorize(request: HttpRequest):
    """
    Initialize OAuth authorization flow
    Accepts JWT token via query param (for browser redirect) or Authorization header

    Returns:
        Redirect to TikTok authorization page
    """
    from api.auth.jwt_handler import JWTHandler

    try:
        # Try to get user from query param token (for browser redirect)
        token = request.GET.get('token')
        user = None

        if token:
            user = JWTHandler.get_user_from_token(token)

        # Fallback to Authorization header (for API calls)
        if not user:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                header_token = auth_header[7:]
                user = JWTHandler.get_user_from_token(header_token)

        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        oauth_service = TikTokOAuthService()
        auth_data = oauth_service.get_authorization_url()

        # Store state->user_id mapping in cache for callback lookup (5 min TTL)
        # Key: state value, Value: user_id
        state_cache_key = f"tiktok_oauth_state:{auth_data['state']}"
        cache.set(state_cache_key, str(user.id), 300)

        logger.info(f"User {user.id} starting OAuth flow")

        # Redirect to TikTok authorization page
        return redirect(auth_data['url'])

    except Exception as e:
        logger.error(f"OAuth authorization error: {str(e)}")
        return JsonResponse({'error': 'Authorization failed'}, status=500)


@router.get("/callback")
def oauth_callback(request: HttpRequest):
    """
    Handle OAuth callback from TikTok
    This endpoint is called by TikTok redirect, not by frontend API
    No JWT auth required - state parameter is used to find user

    Query params:
        code: Authorization code
        state: CSRF state parameter (contains user ID mapping)
        scopes: Granted scopes

    Returns:
        Redirect to frontend with success/error
    """
    from django.conf import settings
    from apps.accounts.models import User

    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

    try:
        # Get parameters
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')

        if error:
            error_description = request.GET.get('error_description', '')
            logger.error(f"OAuth error: {error} - Description: {error_description}")
            return redirect(f"{frontend_url}/auth/callback?error={error}")

        if not code or not state:
            return redirect(f"{frontend_url}/auth/callback?error=missing_params")

        # Look up user_id from state cache (state is the key, user_id is the value)
        state_cache_key = f"tiktok_oauth_state:{state}"
        user_id = cache.get(state_cache_key)

        if not user_id:
            logger.error("OAuth state not found in cache - session may have expired")
            return redirect(f"{frontend_url}/auth/callback?error=session_expired")

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect(f"{frontend_url}/auth/callback?error=user_not_found")

        # Exchange code for token
        oauth_service = TikTokOAuthService()
        token_data = oauth_service.exchange_code_for_token(code)

        # Get TikTok user info (include_profile=True to get real @username)
        account_service = TikTokAccountService(token_data['access_token'])
        user_info = account_service.get_user_info(include_profile=True)

        # Create or update TikTokAccount
        # Reset is_deleted=False to restore previously deleted accounts
        tiktok_account, created = TikTokAccount.objects.update_or_create(
            tiktok_user_id=user_info.get('open_id'),
            defaults={
                'user': user,
                'username': user_info.get('username', ''),
                'display_name': user_info.get('display_name', ''),
                'avatar_url': user_info.get('avatar_url', ''),
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'token_expires_at': token_data['token_expires_at'],
                'status': 'active',
                'is_deleted': False,  # Restore if previously deleted
            }
        )

        # Clean up state from cache
        cache.delete(state_cache_key)

        logger.info(
            f"Successfully connected TikTok account {tiktok_account.username} "
            f"for user {user.id}"
        )

        # Redirect to frontend with success
        return redirect(f"{frontend_url}/auth/callback?success=true&account={tiktok_account.username}")

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        return redirect(f"{frontend_url}/auth/callback?error=connection_failed")
