# Phase 02: TikTok Accounts API Implementation

## Context
- **Parent Plan**: [Phase 04 Backend API](./plan.md)
- **Previous**: [Phase 01 JWT Authentication](./phase-01-jwt-authentication.md)
- **Date**: 2025-12-05
- **Priority**: P0 (Core Feature)
- **Status**: Ready

## Overview
Build TikTok Accounts API endpoints for listing, retrieving, deleting, and syncing connected TikTok accounts. Leverages existing OAuth service and account models.

## Key Insights from Research
1. Use existing TikTokAccountService for business logic
2. Implement cursor-based pagination for scalability
3. Add filtering by status and search by username
4. Secure endpoints with JWT authentication
5. Return consistent response formats

## Requirements

### Functional
- List user's TikTok accounts with pagination
- Get single account details
- Delete/disconnect account
- Sync account data from TikTok
- Filter by status (active/inactive)
- Search by username

### Non-Functional
- Response time < 150ms
- Pagination: 20 items default, 50 max
- Soft delete for data retention
- Audit logging for all operations

## Architecture

```mermaid
graph TB
    A[Client] -->|GET /accounts| B[Accounts Router]
    A -->|GET /accounts/{id}| B
    A -->|DELETE /accounts/{id}| B
    A -->|POST /accounts/{id}/sync| B
    B --> C[JWT Auth]
    C --> D[Account Service]
    D --> E[TikTok API]
    D --> F[Database]
    B --> G[Audit Logger]
```

## Implementation Steps

### 1. Create Account Schemas
**File**: `backend/api/accounts/schemas.py`
```python
from ninja import Schema
from datetime import datetime
from typing import Optional, List
from enum import Enum

class AccountStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    expired = "expired"

class TikTokAccountOut(Schema):
    id: str
    username: str
    display_name: str
    avatar_url: Optional[str]
    status: AccountStatus
    follower_count: int
    following_count: int
    video_count: int
    last_synced_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class AccountDetailOut(TikTokAccountOut):
    tiktok_user_id: str
    token_expires_at: datetime
    last_error: Optional[str]
    updated_at: datetime

class AccountListOut(Schema):
    items: List[TikTokAccountOut]
    total: int
    cursor: Optional[str] = None
    has_more: bool = False

class SyncResultOut(Schema):
    success: bool
    synced_at: datetime
    follower_count: int
    following_count: int
    video_count: int
    message: Optional[str] = None

class ErrorOut(Schema):
    detail: str
    code: Optional[str] = None
```

### 2. Create Accounts Router
**File**: `backend/api/accounts/router.py`
```python
from ninja import Router, Query
from typing import Optional
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
import logging

from apps.tiktok_accounts.models import TikTokAccount
from apps.tiktok_accounts.services import TikTokAccountService
from apps.core.models import AuditLog
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

@router.get("/", response=AccountListOut, auth=auth)
def list_accounts(
    request,
    cursor: Optional[str] = None,
    limit: int = Query(20, le=50),
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """List user's TikTok accounts with pagination and filters"""
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

    # Get results
    accounts = list(queryset[:limit + 1])
    has_more = len(accounts) > limit

    if has_more:
        accounts = accounts[:limit]
        next_cursor = str(accounts[-1].id)
    else:
        next_cursor = None

    return AccountListOut(
        items=accounts,
        total=queryset.count(),
        cursor=next_cursor,
        has_more=has_more
    )

@router.get("/{account_id}", response=AccountDetailOut, auth=auth)
def get_account(request, account_id: str):
    """Get single TikTok account details"""
    user = request.auth
    account = get_object_or_404(
        TikTokAccount,
        id=account_id,
        user=user,
        is_deleted=False
    )
    return account

@router.delete("/{account_id}", auth=auth)
def delete_account(request, account_id: str):
    """Disconnect and soft-delete TikTok account"""
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
        action='delete_tiktok_account',
        model_name='TikTokAccount',
        object_id=str(account.id),
        details={
            'username': account.username,
            'display_name': account.display_name
        }
    )

    logger.info(f"User {user.id} deleted TikTok account {account.username}")

    return {"success": True, "message": "Account disconnected successfully"}

@router.post("/{account_id}/sync", response=SyncResultOut, auth=auth)
def sync_account(request, account_id: str):
    """Sync account data from TikTok API"""
    user = request.auth
    account = get_object_or_404(
        TikTokAccount,
        id=account_id,
        user=user,
        is_deleted=False
    )

    try:
        # Use existing service to sync
        service = TikTokAccountService(account.get_access_token())
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
            action='sync_tiktok_account',
            model_name='TikTokAccount',
            object_id=str(account.id),
            details={
                'username': account.username,
                'follower_count': account.follower_count
            }
        )

        return SyncResultOut(
            success=True,
            synced_at=account.last_synced_at,
            follower_count=account.follower_count,
            following_count=account.following_count,
            video_count=account.video_count
        )

    except Exception as e:
        logger.error(f"Failed to sync account {account.username}: {str(e)}")
        return router.api.create_response(
            request,
            ErrorOut(
                detail="Failed to sync account",
                code="SYNC_FAILED"
            ),
            status=500
        )

@router.get("/stats/summary", auth=auth)
def get_accounts_summary(request):
    """Get summary statistics for all user accounts"""
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
```

### 3. Add Batch Operations
**File**: `backend/api/accounts/batch_operations.py`
```python
from ninja import Router, Schema
from typing import List
from api.auth.middleware import JWTAuth

router = Router()
auth = JWTAuth()

class BatchSyncIn(Schema):
    account_ids: List[str]

class BatchResultOut(Schema):
    success: List[str]
    failed: List[dict]
    total: int

@router.post("/batch/sync", response=BatchResultOut, auth=auth)
def batch_sync_accounts(request, data: BatchSyncIn):
    """Sync multiple accounts in one request"""
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
            # Sync logic here
            success_ids.append(account_id)
        except Exception as e:
            failed_items.append({
                'id': account_id,
                'error': str(e)
            })

    return BatchResultOut(
        success=success_ids,
        failed=failed_items,
        total=len(data.account_ids)
    )
```

### 4. Update URL Configuration
**File**: `backend/config/urls.py` (update)
```python
from api.accounts.router import router as accounts_router
from api.accounts.batch_operations import router as batch_router

# Add after auth router
api.add_router("/accounts/", accounts_router, tags=["TikTok Accounts"])
api.add_router("/accounts/", batch_router, tags=["Batch Operations"])
```

## Testing Strategy

### Unit Tests
```python
# backend/api/accounts/tests/test_schemas.py
def test_account_out_schema():
    account = TikTokAccount(
        username="testuser",
        display_name="Test User",
        status="active"
    )
    schema = TikTokAccountOut.from_orm(account)
    assert schema.username == "testuser"
```

### Integration Tests
```python
# backend/api/accounts/tests/test_accounts_api.py
def test_list_accounts(client, auth_headers):
    response = client.get(
        '/api/v1/accounts/',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'total' in data

def test_sync_account(client, auth_headers, account_id):
    response = client.post(
        f'/api/v1/accounts/{account_id}/sync',
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()['success'] is True
```

## Database Optimizations

### Add Indexes
```python
# Migration file
class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name='tiktokaccount',
            index=models.Index(
                fields=['user', 'status', '-created_at'],
                name='user_status_created_idx'
            ),
        ),
    ]
```

## Todo List
- [ ] Create account schemas with Pydantic
- [ ] Implement accounts router with CRUD
- [ ] Add pagination with cursor
- [ ] Implement search and filtering
- [ ] Add batch sync operations
- [ ] Create audit logging
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Add database indexes
- [ ] Document API endpoints

## Success Criteria
- [ ] List returns paginated results < 150ms
- [ ] Sync updates account data correctly
- [ ] Soft delete preserves data
- [ ] Audit logs track all operations
- [ ] Tests achieve >85% coverage

## Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| TikTok API rate limits | High | Medium | Implement caching, queue syncs |
| Token expiration | Medium | Low | Auto-refresh tokens |
| Large account lists | Low | Medium | Cursor pagination, indexes |

## Performance Considerations
1. Use select_related for user joins
2. Add database indexes on filter fields
3. Cache account lists for 5 minutes
4. Implement async sync operations
5. Use bulk operations for batch updates

## Next Steps
1. Complete accounts API implementation
2. Test with multiple accounts
3. Move to [Phase 03: Posts API](./phase-03-posts-api.md)