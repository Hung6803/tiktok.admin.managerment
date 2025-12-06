"""
Celery tasks for syncing TikTok account data
Handles periodic account updates and token refresh
"""
from celery import shared_task
from django.utils import timezone
import logging

from apps.tiktok_accounts.models import TikTokAccount

logger = logging.getLogger(__name__)


@shared_task
def sync_all_accounts():
    """
    Sync all active TikTok accounts

    This task runs daily at 2 AM (configured in Celery Beat).
    It updates account metadata like follower counts, video counts, etc.

    Returns:
        dict: Statistics about sync operations
    """
    logger.info("Starting sync_all_accounts task")

    accounts = TikTokAccount.objects.filter(
        status='active',
        is_deleted=False
    )

    total_accounts = accounts.count()
    synced = 0
    failed = 0

    logger.info(f"Found {total_accounts} active accounts to sync")

    for account in accounts:
        try:
            # TODO: Check token expiry and refresh if needed
            # In production, implement token refresh logic:
            # if account.token_expires_at and account.token_expires_at <= timezone.now():
            #     from apps.tiktok_accounts.services.tiktok_token_service import TikTokTokenService
            #     token_service = TikTokTokenService()
            #     token_service.refresh_token(account)

            # TODO: Sync account data from TikTok API
            # In production, implement actual API sync:
            # from apps.tiktok_accounts.services.tiktok_account_service import TikTokAccountService
            # account_service = TikTokAccountService(account.access_token)
            # user_info = account_service.get_user_info()
            #
            # account.username = user_info.get('username', account.username)
            # account.display_name = user_info.get('display_name', account.display_name)
            # account.follower_count = user_info.get('follower_count', account.follower_count)
            # account.video_count = user_info.get('video_count', account.video_count)

            # For now, just update last_synced_at
            account.last_synced_at = timezone.now()
            account.save(update_fields=['last_synced_at', 'updated_at'])

            synced += 1
            logger.info(f"Synced account {account.id} ({account.username})")

        except Exception as e:
            failed += 1
            logger.error(f"Failed to sync account {account.id} ({account.username}): {str(e)}")

    logger.info(f"Sync completed: {synced} synced, {failed} failed out of {total_accounts} accounts")

    return {
        'total': total_accounts,
        'synced': synced,
        'failed': failed
    }


@shared_task
def sync_account(account_id: str):
    """
    Sync a single TikTok account

    Args:
        account_id: UUID of the TikTok account

    Returns:
        dict: Sync status and result
    """
    try:
        account = TikTokAccount.objects.get(
            id=account_id,
            is_deleted=False
        )

        logger.info(f"Starting sync for account {account.id} ({account.username})")

        # TODO: Implement actual TikTok API sync
        # In production, replace with:
        # from apps.tiktok_accounts.services.tiktok_account_service import TikTokAccountService
        # account_service = TikTokAccountService(account.access_token)
        # user_info = account_service.get_user_info()
        #
        # account.username = user_info.get('username', account.username)
        # account.display_name = user_info.get('display_name', account.display_name)
        # account.follower_count = user_info.get('follower_count', account.follower_count)
        # account.video_count = user_info.get('video_count', account.video_count)

        # For now, just update last_synced_at
        account.last_synced_at = timezone.now()
        account.save(update_fields=['last_synced_at', 'updated_at'])

        logger.info(f"Successfully synced account {account.id}")

        return {
            'status': 'success',
            'account_id': str(account.id),
            'username': account.username
        }

    except TikTokAccount.DoesNotExist:
        logger.error(f"Account {account_id} not found")
        return {
            'status': 'not_found',
            'account_id': account_id
        }

    except Exception as e:
        logger.error(f"Failed to sync account {account_id}: {str(e)}")
        return {
            'status': 'failed',
            'account_id': account_id,
            'error': str(e)
        }
