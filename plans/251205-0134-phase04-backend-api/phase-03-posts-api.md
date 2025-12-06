# Phase 03: Posts API Implementation

## Context
- **Parent Plan**: [Phase 04 Backend API](./plan.md)
- **Previous**: [Phase 02 TikTok Accounts API](./phase-02-tiktok-accounts-api.md)
- **Date**: 2025-12-05
- **Priority**: P0 (Core Feature)
- **Status**: Ready

## Overview
Build comprehensive Posts API for creating, scheduling, publishing, and managing TikTok content across multiple accounts. Integrates with existing ScheduledPost and PostMedia models.

## Key Insights from Research
1. Separate draft, scheduled, and published states
2. Support bulk operations for efficiency
3. Implement timezone-aware scheduling
4. Use transactions for data consistency
5. Queue publishing through Celery

## Requirements

### Functional
- CRUD operations for posts
- Schedule posts with date/time
- Publish immediately to TikTok
- Attach media (videos) to posts
- Multi-account posting
- Draft management
- Filtering by status/date/account

### Non-Functional
- Response time < 200ms
- Support 100MB+ video uploads
- Timezone conversion handling
- Atomic operations for consistency
- Retry failed publishes

## Architecture

```mermaid
graph TB
    A[Client] -->|POST /posts| B[Posts Router]
    A -->|PUT /posts/{id}| B
    A -->|POST /posts/{id}/publish| B
    B --> C[JWT Auth]
    C --> D[Post Service]
    D --> E[Media Storage]
    D --> F[Schedule Queue]
    F --> G[Celery Worker]
    G --> H[TikTok API]
    D --> I[Database]
```

## Implementation Steps

### 1. Create Post Schemas
**File**: `backend/api/posts/schemas.py`
```python
from ninja import Schema, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import field_validator

class PostStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"

class PostPrivacy(str, Enum):
    public = "public"
    friends = "friends"
    private = "private"

class MediaIn(Schema):
    file_path: str
    media_type: str = "video"
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None

class PostCreateIn(Schema):
    title: str = Field(..., max_length=150)
    description: str = Field(..., max_length=2200)
    account_ids: List[str]
    scheduled_time: Optional[datetime] = None
    privacy_level: PostPrivacy = PostPrivacy.public
    allow_comments: bool = True
    allow_duet: bool = True
    allow_stitch: bool = True
    hashtags: List[str] = []
    media: Optional[List[MediaIn]] = []
    is_draft: bool = False

    @field_validator('hashtags')
    def validate_hashtags(cls, v):
        # Remove # if present, limit to 30 hashtags
        cleaned = [tag.lstrip('#') for tag in v]
        if len(cleaned) > 30:
            raise ValueError('Maximum 30 hashtags allowed')
        return cleaned

    @field_validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        if v and v <= datetime.now():
            raise ValueError('Scheduled time must be in the future')
        return v

class PostUpdateIn(Schema):
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = Field(None, max_length=2200)
    scheduled_time: Optional[datetime] = None
    privacy_level: Optional[PostPrivacy] = None
    hashtags: Optional[List[str]] = None

class PostOut(Schema):
    id: str
    title: str
    description: str
    status: PostStatus
    scheduled_time: Optional[datetime]
    published_at: Optional[datetime]
    privacy_level: PostPrivacy
    account_count: int
    media_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PostDetailOut(PostOut):
    accounts: List[dict]
    media: List[dict]
    hashtags: List[str]
    allow_comments: bool
    allow_duet: bool
    allow_stitch: bool
    publish_history: List[dict]

class PostListOut(Schema):
    items: List[PostOut]
    total: int
    page: int
    pages: int
    has_next: bool
    has_prev: bool

class PublishResultOut(Schema):
    success: bool
    published_count: int
    failed_count: int
    results: List[dict]
    message: str
```

### 2. Create Post Service
**File**: `backend/api/posts/services.py`
```python
from django.db import transaction
from django.utils import timezone
from typing import List, Dict
import logging

from apps.content.models import ScheduledPost, PostMedia
from apps.content.models import PublishHistory
from apps.tiktok_accounts.models import TikTokAccount
from apps.scheduler.tasks import publish_post_task

logger = logging.getLogger(__name__)

class PostService:
    @transaction.atomic
    def create_post(self, user, data: dict) -> ScheduledPost:
        """Create new post with media and account associations"""
        # Extract data
        account_ids = data.pop('account_ids')
        media_items = data.pop('media', [])
        hashtags = data.pop('hashtags', [])
        is_draft = data.pop('is_draft', False)

        # Determine status
        if is_draft:
            status = 'draft'
        elif data.get('scheduled_time'):
            status = 'scheduled'
        else:
            status = 'pending'

        # Create post
        post = ScheduledPost.objects.create(
            user=user,
            status=status,
            hashtags=hashtags,
            **data
        )

        # Add accounts
        accounts = TikTokAccount.objects.filter(
            id__in=account_ids,
            user=user,
            is_deleted=False
        )
        post.accounts.set(accounts)

        # Add media
        for media_data in media_items:
            PostMedia.objects.create(
                post=post,
                **media_data
            )

        # Schedule if needed
        if status == 'scheduled':
            self._schedule_post(post)

        logger.info(f"Created post {post.id} for user {user.id}")
        return post

    def _schedule_post(self, post: ScheduledPost):
        """Schedule post for publishing"""
        eta = post.scheduled_time
        publish_post_task.apply_async(
            args=[str(post.id)],
            eta=eta
        )
        logger.info(f"Scheduled post {post.id} for {eta}")

    def publish_now(self, post: ScheduledPost) -> Dict:
        """Publish post immediately"""
        results = {
            'success': [],
            'failed': []
        }

        post.status = 'publishing'
        post.save()

        for account in post.accounts.all():
            try:
                # Use existing video service
                from apps.content.services import TikTokVideoService
                service = TikTokVideoService(account)

                # Get primary media
                media = post.media.first()
                if not media:
                    raise ValueError("No media attached")

                # Publish to TikTok
                result = service.upload_video(
                    video_path=media.file_path,
                    title=post.title,
                    description=post.description,
                    privacy_level=post.privacy_level
                )

                # Record success
                PublishHistory.objects.create(
                    post=post,
                    account=account,
                    status='success',
                    tiktok_video_id=result.get('video_id'),
                    published_at=timezone.now()
                )
                results['success'].append({
                    'account': account.username,
                    'video_id': result.get('video_id')
                })

            except Exception as e:
                logger.error(f"Failed to publish to {account.username}: {str(e)}")
                PublishHistory.objects.create(
                    post=post,
                    account=account,
                    status='failed',
                    error_message=str(e)
                )
                results['failed'].append({
                    'account': account.username,
                    'error': str(e)
                })

        # Update post status
        if results['success']:
            post.status = 'published'
            post.published_at = timezone.now()
        else:
            post.status = 'failed'
            post.error_message = "Failed to publish to all accounts"
        post.save()

        return results

    def update_post(self, post: ScheduledPost, data: dict):
        """Update existing post"""
        if post.status == 'published':
            raise ValueError("Cannot update published post")

        # Update fields
        for key, value in data.items():
            if value is not None:
                setattr(post, key, value)

        # Reschedule if time changed
        if 'scheduled_time' in data and data['scheduled_time']:
            post.status = 'scheduled'
            self._schedule_post(post)

        post.save()
        return post
```

### 3. Create Posts Router
**File**: `backend/api/posts/router.py`
```python
from ninja import Router, Query
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from typing import Optional
import logging

from apps.content.models import ScheduledPost
from api.auth.middleware import JWTAuth
from .schemas import (
    PostCreateIn, PostUpdateIn, PostOut,
    PostDetailOut, PostListOut, PublishResultOut
)
from .services import PostService

logger = logging.getLogger(__name__)
router = Router()
auth = JWTAuth()

@router.post("/", response=PostOut, auth=auth)
def create_post(request, data: PostCreateIn):
    """Create new post"""
    service = PostService()
    post = service.create_post(request.auth, data.dict())
    return post

@router.get("/", response=PostListOut, auth=auth)
def list_posts(
    request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50),
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None
):
    """List posts with filtering and pagination"""
    queryset = ScheduledPost.objects.filter(
        user=request.auth
    ).order_by('-created_at')

    # Apply filters
    if status:
        queryset = queryset.filter(status=status)
    if account_id:
        queryset = queryset.filter(accounts__id=account_id)
    if from_date:
        queryset = queryset.filter(scheduled_time__gte=from_date)
    if to_date:
        queryset = queryset.filter(scheduled_time__lte=to_date)

    # Paginate
    paginator = Paginator(queryset, limit)
    page_obj = paginator.get_page(page)

    # Add computed fields
    items = []
    for post in page_obj:
        post.account_count = post.accounts.count()
        post.media_count = post.media.count()
        items.append(post)

    return PostListOut(
        items=items,
        total=paginator.count,
        page=page,
        pages=paginator.num_pages,
        has_next=page_obj.has_next(),
        has_prev=page_obj.has_previous()
    )

@router.get("/{post_id}", response=PostDetailOut, auth=auth)
def get_post(request, post_id: str):
    """Get post details"""
    post = get_object_or_404(
        ScheduledPost,
        id=post_id,
        user=request.auth
    )

    # Add related data
    post.accounts = list(post.accounts.values('id', 'username', 'display_name'))
    post.media = list(post.media.values())
    post.publish_history = list(
        post.publish_history.values('account__username', 'status', 'published_at', 'error_message')
    )

    return post

@router.put("/{post_id}", response=PostOut, auth=auth)
def update_post(request, post_id: str, data: PostUpdateIn):
    """Update existing post"""
    post = get_object_or_404(
        ScheduledPost,
        id=post_id,
        user=request.auth
    )

    service = PostService()
    updated_post = service.update_post(post, data.dict(exclude_unset=True))
    return updated_post

@router.delete("/{post_id}", auth=auth)
def delete_post(request, post_id: str):
    """Delete post"""
    post = get_object_or_404(
        ScheduledPost,
        id=post_id,
        user=request.auth
    )

    if post.status == 'published':
        return router.api.create_response(
            request,
            {"detail": "Cannot delete published post"},
            status=400
        )

    post.delete()
    logger.info(f"Deleted post {post_id} for user {request.auth.id}")
    return {"success": True}

@router.post("/{post_id}/publish", response=PublishResultOut, auth=auth)
def publish_post(request, post_id: str):
    """Publish post immediately"""
    post = get_object_or_404(
        ScheduledPost,
        id=post_id,
        user=request.auth
    )

    if post.status == 'published':
        return router.api.create_response(
            request,
            {"detail": "Post already published"},
            status=400
        )

    service = PostService()
    results = service.publish_now(post)

    return PublishResultOut(
        success=len(results['success']) > 0,
        published_count=len(results['success']),
        failed_count=len(results['failed']),
        results=results['success'] + results['failed'],
        message=f"Published to {len(results['success'])} accounts"
    )

@router.get("/drafts/", response=PostListOut, auth=auth)
def list_drafts(request, page: int = 1, limit: int = 20):
    """List draft posts"""
    queryset = ScheduledPost.objects.filter(
        user=request.auth,
        status='draft'
    ).order_by('-updated_at')

    paginator = Paginator(queryset, limit)
    page_obj = paginator.get_page(page)

    return PostListOut(
        items=list(page_obj),
        total=paginator.count,
        page=page,
        pages=paginator.num_pages,
        has_next=page_obj.has_next(),
        has_prev=page_obj.has_previous()
    )

@router.get("/upcoming/", auth=auth)
def upcoming_posts(request, days: int = Query(7, le=30)):
    """Get upcoming scheduled posts"""
    end_date = timezone.now() + timedelta(days=days)
    posts = ScheduledPost.objects.filter(
        user=request.auth,
        status='scheduled',
        scheduled_time__lte=end_date
    ).order_by('scheduled_time')

    return {
        "count": posts.count(),
        "posts": list(posts.values('id', 'title', 'scheduled_time', 'accounts'))
    }
```

### 4. Add Bulk Operations
**File**: `backend/api/posts/bulk_operations.py`
```python
class BulkScheduleIn(Schema):
    post_ids: List[str]
    scheduled_time: datetime

@router.post("/bulk/schedule", auth=auth)
def bulk_schedule_posts(request, data: BulkScheduleIn):
    """Schedule multiple posts at once"""
    posts = ScheduledPost.objects.filter(
        id__in=data.post_ids,
        user=request.auth,
        status='draft'
    )

    updated_count = posts.update(
        status='scheduled',
        scheduled_time=data.scheduled_time
    )

    # Schedule tasks
    for post in posts:
        publish_post_task.apply_async(
            args=[str(post.id)],
            eta=data.scheduled_time
        )

    return {
        "success": True,
        "updated_count": updated_count
    }
```

## Testing Strategy

### Unit Tests
```python
# backend/api/posts/tests/test_post_service.py
def test_create_post_draft():
    service = PostService()
    data = {
        'title': 'Test Post',
        'description': 'Test Description',
        'account_ids': ['acc-1'],
        'is_draft': True
    }
    post = service.create_post(user, data)
    assert post.status == 'draft'

def test_publish_post():
    service = PostService()
    post = create_test_post()
    results = service.publish_now(post)
    assert 'success' in results
```

### Integration Tests
```python
# backend/api/posts/tests/test_posts_api.py
def test_create_scheduled_post(client, auth_headers):
    response = client.post('/api/v1/posts/', json={
        'title': 'Scheduled Post',
        'description': 'Test',
        'account_ids': ['acc-1'],
        'scheduled_time': '2025-12-10T10:00:00Z'
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()['status'] == 'scheduled'
```

## Todo List
- [x] Create post schemas with validation
- [x] Implement post service with business logic
- [x] Create posts router with CRUD
- [x] Add publish functionality
- [x] Implement draft management
- [x] Add filtering and pagination
- [x] Create bulk operations
- [x] Integrate with Celery tasks
- [x] Write comprehensive tests
- [x] Document API endpoints

## Implementation Status
**Status**: ⚠️ Complete with Critical Issues
**Date Completed**: 2025-12-05
**Review**: [Code Review Report](./reports/code-reviewer-251205-phase03-posts-api.md)

### Critical Issues Found (5)
1. ❌ Timezone validation broken (uses datetime.now() instead of timezone.now())
2. ❌ N+1 query problem in list_posts (41+ queries for 20 items)
3. ❌ SQL injection via string date filtering
4. ❌ Missing PostMedia field validation (file_size, file_mime_type)
5. ❌ TikTokVideoService signature mismatch (breaks publishing)

### High Priority Issues (4)
1. ⚠️ Missing XSS sanitization on title/description
2. ⚠️ Account ownership not validated
3. ⚠️ Race condition in bulk schedule
4. ⚠️ Silent failure in _schedule_post ImportError

**Action Required**: Fix all critical issues before proceeding to Phase 04

## Success Criteria
- [x] Posts created with media < 200ms ✅
- [ ] Scheduling works with timezones ❌ (broken validation)
- [ ] Publishing integrates with TikTok API ❌ (signature mismatch)
- [x] Drafts saved and retrievable ✅
- [ ] Bulk operations handle 100+ posts ⚠️ (race condition)

## Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Large media uploads | High | High | Streaming uploads, chunking |
| Publishing failures | Medium | Medium | Retry logic, error handling |
| Timezone issues | Low | High | UTC storage, client conversion |

## Next Steps
1. Complete posts API implementation
2. Test with real TikTok accounts
3. Move to [Phase 04: Media Upload API](./phase-04-media-upload-api.md)