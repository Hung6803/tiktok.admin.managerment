"""
TikTok Accounts API router
Handles CRUD operations for connected TikTok accounts
"""
from ninja import Router, Query, Schema
from typing import Optional, List
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
import logging

from apps.tiktok_accounts.models import TikTokAccount
from apps.tiktok_accounts.services import TikTokAccountService
from core.models import AuditLog
from api.auth.middleware import JWTAuth
from .schemas import (
    TikTokAccountOut,
    AccountDetailOut,
    AccountListOut,
    SyncResultOut,
    ErrorOut
)

logger = logging.getLogger(__name__)
router = Router()
auth = JWTAuth()


@router.get("/", response=AccountListOut, auth=auth, tags=["TikTok Accounts"])
def list_accounts(
    request,
    cursor: Optional[str] = None,
    limit: int = Query(20, le=50),
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """
    List user's TikTok accounts with pagination and filters

    Args:
        cursor: Pagination cursor (account ID)
        limit: Number of items per page (max 50)
        status: Filter by account status (active/inactive/expired)
        search: Search by username or display name
    """
    user = request.auth

    # Build query
    queryset = TikTokAccount.objects.filter(
        user=user,
        is_deleted=False
    )

    # Apply filters
    if status:
        queryset = queryset.filter(status=status)

    if search:
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(display_name__icontains=search)
        )

    # Order by created_at for consistent pagination
    queryset = queryset.order_by('-created_at')

    # Apply cursor (simple implementation using ID)
    if cursor:
        queryset = queryset.filter(id__lt=cursor)

    # Get total count before pagination
    total_count = queryset.count()

    # Get results with limit + 1 to check for more pages
    accounts = list(queryset[:limit + 1])
    has_more = len(accounts) > limit

    if has_more:
        accounts = accounts[:limit]
        next_cursor = str(accounts[-1].id)
    else:
        next_cursor = None

    return AccountListOut(
        items=accounts,
        total=total_count,
        cursor=next_cursor,
        has_more=has_more
    )


# Specific routes MUST come before parameterized routes
@router.get("/stats/summary", response=dict, auth=auth, tags=["TikTok Accounts"])
def get_accounts_summary(request):
    """
    Get summary statistics for all user accounts

    Returns aggregate statistics across all connected TikTok accounts
    """
    user = request.auth
    accounts = TikTokAccount.objects.filter(
        user=user,
        is_deleted=False
    )

    total_followers = sum(a.follower_count for a in accounts)
    total_videos = sum(a.video_count for a in accounts)

    return {
        "total_accounts": accounts.count(),
        "active_accounts": accounts.filter(status='active').count(),
        "total_followers": total_followers,
        "total_videos": total_videos
    }


# Batch Operations
class BatchSyncIn(Schema):
    """Input schema for batch sync operation"""
    account_ids: List[str]


class BatchResultOut(Schema):
    """Result of batch operation"""
    success: List[str]
    failed: List[dict]
    total: int


@router.post("/batch/sync", response=BatchResultOut, auth=auth, tags=["Batch Operations"])
def batch_sync_accounts(request, data: BatchSyncIn):
    """
    Sync multiple TikTok accounts in one request

    Attempts to sync all provided account IDs and returns success/failure status for each

    Args:
        data: List of account IDs to sync
    """
    user = request.auth
    success_ids = []
    failed_items = []

    for account_id in data.account_ids:
        try:
            account = TikTokAccount.objects.get(
                id=account_id,
                user=user,
                is_deleted=False
            )

            # Perform sync
            service = TikTokAccountService(account.access_token)
            user_info = service.get_user_info()

            # Update account data
            account.display_name = user_info.get('display_name', account.display_name)
            account.avatar_url = user_info.get('avatar_url', account.avatar_url)
            account.follower_count = user_info.get('follower_count', 0)
            account.following_count = user_info.get('following_count', 0)
            account.video_count = user_info.get('video_count', 0)
            account.last_synced_at = timezone.now()
            account.save()

            # Audit log
            AuditLog.objects.create(
                user=user,
                action='update',
                resource_type='TikTokAccount',
                resource_id=account.id,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'username': account.username,
                    'follower_count': account.follower_count,
                    'operation': 'batch_sync'
                }
            )

            success_ids.append(account_id)
            logger.info(f"Successfully synced account {account.username} in batch")

        except TikTokAccount.DoesNotExist:
            failed_items.append({
                'id': account_id,
                'error': 'Account not found'
            })
            logger.warning(f"Account {account_id} not found for user {user.id}")

        except Exception as e:
            failed_items.append({
                'id': account_id,
                'error': str(e)
            })
            logger.error(f"Failed to sync account {account_id}: {str(e)}")

    logger.info(f"Batch sync completed: {len(success_ids)} success, {len(failed_items)} failed")

    return BatchResultOut(
        success=success_ids,
        failed=failed_items,
        total=len(data.account_ids)
    )


# Parameterized routes come AFTER specific routes
@router.get("/{account_id}", response={200: AccountDetailOut, 404: ErrorOut}, auth=auth, tags=["TikTok Accounts"])
def get_account(request, account_id: str):
    """
    Get single TikTok account details

    Args:
        account_id: UUID of the TikTok account
    """
    user = request.auth

    account = get_object_or_404(
        TikTokAccount,
        id=account_id,
        user=user,
        is_deleted=False
    )
    return 200, account


@router.delete("/{account_id}", response={200: dict, 404: ErrorOut}, auth=auth, tags=["TikTok Accounts"])
def delete_account(request, account_id: str):
    """
    Disconnect and soft-delete TikTok account

    Args:
        account_id: UUID of the TikTok account
    """
    user = request.auth

    account = get_object_or_404(
        TikTokAccount,
        id=account_id,
        user=user,
        is_deleted=False
    )

    # Soft delete
    account.soft_delete()

    # Audit log
    AuditLog.objects.create(
        user=user,
        action='delete',
        resource_type='TikTokAccount',
        resource_id=account.id,
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={
            'username': account.username,
            'display_name': account.display_name
        }
    )

    logger.info(f"User {user.id} deleted TikTok account {account.username}")

    return 200, {"success": True, "message": "Account disconnected successfully"}


@router.post("/{account_id}/sync", response={200: SyncResultOut, 404: ErrorOut, 500: ErrorOut}, auth=auth, tags=["TikTok Accounts"])
def sync_account(request, account_id: str):
    """
    Sync account data from TikTok API

    Fetches latest user information from TikTok and updates local database

    Args:
        account_id: UUID of the TikTok account
    """
    user = request.auth

    try:
        account = get_object_or_404(
            TikTokAccount,
            id=account_id,
            user=user,
            is_deleted=False
        )
    except Exception:
        return 404, ErrorOut(detail="Account not found", code="ACCOUNT_NOT_FOUND")

    try:
        # Use existing service to sync
        service = TikTokAccountService(account.access_token)
        user_info = service.get_user_info()

        # Update account data
        account.display_name = user_info.get('display_name', account.display_name)
        account.avatar_url = user_info.get('avatar_url', account.avatar_url)
        account.follower_count = user_info.get('follower_count', 0)
        account.following_count = user_info.get('following_count', 0)
        account.video_count = user_info.get('video_count', 0)
        account.last_synced_at = timezone.now()
        account.save()

        # Audit log
        AuditLog.objects.create(
            user=user,
            action='update',
            resource_type='TikTokAccount',
            resource_id=account.id,
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'username': account.username,
                'follower_count': account.follower_count,
                'operation': 'sync'
            }
        )

        logger.info(f"User {user.id} synced TikTok account {account.username}")

        return 200, SyncResultOut(
            success=True,
            synced_at=account.last_synced_at,
            follower_count=account.follower_count,
            following_count=account.following_count,
            video_count=account.video_count
        )

    except Exception as e:
        logger.error(f"Failed to sync account {account.username}: {str(e)}")
        return 500, ErrorOut(
            detail="Failed to sync account",
            code="SYNC_FAILED"
        )
