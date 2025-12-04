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

logger = logging.getLogger(__name__)

router = Router()


@router.get("/authorize")
def authorize(request: HttpRequest):
    """
    Initialize OAuth authorization flow

    Returns:
        Redirect to TikTok authorization page
    """
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        oauth_service = TikTokOAuthService()
        auth_data = oauth_service.get_authorization_url()

        # Store state in cache for validation (5 min TTL)
        cache_key = f"tiktok_oauth_state:{request.user.id}"
        cache.set(cache_key, auth_data['state'], 300)

        logger.info(f"User {request.user.id} starting OAuth flow")

        # Redirect to TikTok authorization page
        return redirect(auth_data['url'])

    except Exception as e:
        logger.error(f"OAuth authorization error: {str(e)}")
        return JsonResponse({'error': 'Authorization failed'}, status=500)


@router.get("/callback")
def oauth_callback(request: HttpRequest):
    """
    Handle OAuth callback from TikTok

    Query params:
        code: Authorization code
        state: CSRF state parameter
        scopes: Granted scopes

    Returns:
        Success/error response
    """
    try:
        # Check authentication
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        # Get parameters
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')

        if error:
            logger.error(f"OAuth error: {error}")
            return JsonResponse({'error': f'OAuth error: {error}'}, status=400)

        if not code or not state:
            return JsonResponse({'error': 'Missing code or state'}, status=400)

        # Validate state (CSRF protection)
        cache_key = f"tiktok_oauth_state:{request.user.id}"
        stored_state = cache.get(cache_key)

        if not stored_state:
            logger.error("OAuth state not found in cache")
            return JsonResponse({'error': 'Invalid state - session expired'}, status=400)

        oauth_service = TikTokOAuthService()
        if not oauth_service.validate_state(state, stored_state):
            return JsonResponse({'error': 'Invalid state - CSRF check failed'}, status=403)

        # Exchange code for token
        token_data = oauth_service.exchange_code_for_token(code)

        # SECURITY WARNING: token_data contains plaintext tokens
        # Do not log or expose until after model encryption (line 106)
        # Tokens encrypted automatically on model save
        account_service = TikTokAccountService(token_data['access_token'])
        user_info = account_service.get_user_info()

        # Create or update TikTokAccount
        tiktok_account, created = TikTokAccount.objects.update_or_create(
            tiktok_user_id=user_info.get('open_id'),
            defaults={
                'user': request.user,
                'username': user_info.get('username', ''),
                'display_name': user_info.get('display_name', ''),
                'avatar_url': user_info.get('avatar_url', ''),
                'access_token': token_data['access_token'],  # Will be encrypted by model
                'refresh_token': token_data['refresh_token'],  # Will be encrypted
                'token_expires_at': token_data['token_expires_at'],
                'status': 'active'
            }
        )

        # Clean up state from cache
        cache.delete(cache_key)

        logger.info(
            f"Successfully connected TikTok account {tiktok_account.username} "
            f"for user {request.user.id}"
        )

        return JsonResponse({
            'success': True,
            'account': {
                'id': str(tiktok_account.id),
                'username': tiktok_account.username,
                'display_name': tiktok_account.display_name,
                'created': created
            }
        })

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Failed to connect TikTok account'}, status=500)
