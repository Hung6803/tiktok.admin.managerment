"""
TikTok Token Refresh Service
Manages automatic token refresh for TikTok accounts
"""
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from typing import List, Dict, Any
import logging

from apps.tiktok_accounts.models import TikTokAccount
from apps.tiktok_accounts.services.tiktok_oauth_service import TikTokOAuthService

logger = logging.getLogger(__name__)


class TikTokTokenRefreshService:
    """Service for automatic TikTok token refresh management"""

    def __init__(self, hours_before_expiry: int = 1):
        """
        Initialize token refresh service

        Args:
            hours_before_expiry: Hours before expiry to trigger refresh
        """
        self.hours_before_expiry = hours_before_expiry
        self.oauth_service = TikTokOAuthService()

    def refresh_expiring_tokens(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Refresh all tokens expiring soon

        Args:
            dry_run: If True, only report what would be refreshed

        Returns:
            Summary of refresh operations with counts and errors
        """
        expiring_threshold = timezone.now() + timedelta(hours=self.hours_before_expiry)
        accounts = self.get_expiring_accounts(expiring_threshold)

        logger.info(f"Found {len(accounts)} accounts with expiring tokens")

        results = {
            'total': len(accounts),
            'refreshed': 0,
            'failed': 0,
            'errors': []
        }

        for account in accounts:
            try:
                if not dry_run:
                    self.refresh_account_token(account)
                    results['refreshed'] += 1
                    logger.info(f"Token refreshed for account {account.id}")
                else:
                    logger.info(f"[DRY RUN] Would refresh token for account {account.id}")
                    results['refreshed'] += 1

            except Exception as e:
                results['failed'] += 1
                error_msg = f"Token refresh failed for account {account.id}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

                if not dry_run:
                    self._handle_refresh_failure(account, str(e))

        logger.info(
            f"Token refresh completed: {results['refreshed']} refreshed, "
            f"{results['failed']} failed"
        )
        return results

    def get_expiring_accounts(self, threshold: timezone.datetime) -> List[TikTokAccount]:
        """
        Get accounts with tokens expiring before threshold

        Args:
            threshold: Datetime threshold for expiry check

        Returns:
            List of TikTokAccount instances needing refresh
        """
        # Note: select_for_update is handled per-account in refresh_account_token
        # to avoid holding locks for the entire batch operation
        return list(TikTokAccount.objects.filter(
            token_expires_at__lte=threshold,
            status='active',
            is_deleted=False
        ))

    def refresh_account_token(self, account: TikTokAccount) -> bool:
        """
        Refresh single account token

        Args:
            account: TikTokAccount instance to refresh

        Returns:
            True if successful

        Raises:
            ValueError: If no refresh token available
            Exception: On API errors
        """
        logger.info(f"Refreshing token for account {account.username}")

        # Use transaction with select_for_update to prevent concurrent refresh
        with transaction.atomic():
            # Re-fetch account with lock to prevent race conditions
            try:
                locked_account = TikTokAccount.objects.select_for_update(
                    skip_locked=True
                ).get(id=account.id, is_deleted=False)
            except TikTokAccount.DoesNotExist:
                logger.warning(f"Account {account.id} not found or already being refreshed")
                return False

            # Get decrypted refresh token (auto-decrypted by field)
            refresh_token = locked_account.refresh_token
            if not refresh_token:
                raise ValueError("No refresh token available")

            # Call OAuth service to refresh
            token_data = self.oauth_service.refresh_access_token(refresh_token)

            # Update account with new tokens (auto-encrypted on save)
            locked_account.access_token = token_data['access_token']
            locked_account.refresh_token = token_data.get('refresh_token', refresh_token)
            locked_account.token_expires_at = token_data['token_expires_at']
            locked_account.status = 'active'
            locked_account.last_refreshed = timezone.now()
            locked_account.save(update_fields=[
                'access_token', 'refresh_token', 'token_expires_at',
                'status', 'last_refreshed'
            ])

            logger.info(
                f"Token refreshed successfully for {locked_account.username}, "
                f"expires at {locked_account.token_expires_at}"
            )
            return True

    def _handle_refresh_failure(self, account: TikTokAccount, error: str) -> None:
        """
        Handle token refresh failure by updating account status

        Args:
            account: TikTokAccount that failed to refresh
            error: Error message
        """
        account.status = 'expired'
        account.last_error = f"Token refresh failed: {error}"
        account.save(update_fields=['status', 'last_error'])

        logger.warning(f"Account {account.id} marked as expired due to refresh failure")

    def refresh_specific_account(self, account_id: int) -> bool:
        """
        Refresh token for specific account by ID

        Args:
            account_id: ID of account to refresh

        Returns:
            True if successful

        Raises:
            TikTokAccount.DoesNotExist: If account not found
            Exception: On refresh errors
        """
        try:
            account = TikTokAccount.objects.get(id=account_id, is_deleted=False)
            return self.refresh_account_token(account)
        except TikTokAccount.DoesNotExist:
            logger.error(f"Account {account_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to refresh account {account_id}: {str(e)}")
            raise
