"""
Celery tasks for TikTok account management
Handles periodic token refresh and cleanup operations
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def refresh_expiring_tokens(self, dry_run: bool = False):
    """
    Periodic task to refresh expiring TikTok tokens

    Args:
        dry_run: If True, only report what would be refreshed

    Returns:
        Dict with status and results
    """
    from apps.tiktok_accounts.services.tiktok_token_refresh_service import (
        TikTokTokenRefreshService
    )

    # Prevent concurrent execution using distributed lock
    lock_key = 'tiktok_token_refresh_lock'
    lock_timeout = 300  # 5 minutes

    if not cache.add(lock_key, 'locked', lock_timeout):
        logger.info("Token refresh already running, skipping")
        return {'status': 'skipped', 'reason': 'already_running'}

    try:
        logger.info("Starting token refresh task")
        service = TikTokTokenRefreshService()
        results = service.refresh_expiring_tokens(dry_run=dry_run)

        # Retry if failures occurred
        if results['failed'] > 0 and not dry_run:
            logger.warning(f"Retrying due to {results['failed']} failures")
            raise self.retry(
                exc=Exception(f"{results['failed']} tokens failed to refresh")
            )

        return {'status': 'success', 'results': results}

    except Exception as e:
        logger.error(f"Token refresh task failed: {str(e)}")
        raise self.retry(exc=e)
    finally:
        cache.delete(lock_key)


@shared_task
def refresh_single_account_token(account_id: int):
    """
    Refresh token for a specific account

    Args:
        account_id: ID of TikTok account to refresh

    Returns:
        Dict with status and account_id
    """
    from apps.tiktok_accounts.services.tiktok_token_refresh_service import (
        TikTokTokenRefreshService
    )

    logger.info(f"Refreshing token for account {account_id}")

    try:
        service = TikTokTokenRefreshService()
        service.refresh_specific_account(account_id)
        return {'status': 'success', 'account_id': account_id}
    except Exception as e:
        logger.error(f"Failed to refresh account {account_id}: {str(e)}")
        return {'status': 'failed', 'account_id': account_id, 'error': str(e)}


@shared_task
def cleanup_expired_tokens():
    """
    Clean up expired tokens and mark accounts as inactive
    Runs periodically to maintain account status accuracy

    Returns:
        Dict with count of expired accounts
    """
    from django.utils import timezone
    from apps.tiktok_accounts.models import TikTokAccount

    logger.info("Starting expired token cleanup")

    expired_count = TikTokAccount.objects.filter(
        token_expires_at__lt=timezone.now(),
        status='active'
    ).update(status='expired')

    logger.info(f"Marked {expired_count} accounts as expired")
    return {'expired_accounts': expired_count}
