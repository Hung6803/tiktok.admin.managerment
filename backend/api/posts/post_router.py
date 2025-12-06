"""
Posts router for CRUD and publishing operations
"""
from ninja import Router, Query
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count
from datetime import datetime, timedelta
from typing import Optional
import logging

from apps.content.models import ScheduledPost
from api.auth.middleware import JWTAuth
from .schemas import (
    PostCreateIn, PostUpdateIn, PostOut,
    PostDetailOut, PostListOut, PublishResultOut, BulkScheduleIn
)
from .post_service import PostService

logger = logging.getLogger(__name__)
router = Router()
auth = JWTAuth()


@router.post("/", response=PostOut, auth=auth)
def create_post(request, data: PostCreateIn):
    """Create new post"""
    service = PostService()
    post = service.create_post(request.auth, data.dict())

    # Add computed fields
    post.account_count = post.accounts.count()
    post.media_count = post.media.count()

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
        user=request.auth,
        is_deleted=False
    ).prefetch_related('accounts', 'media').annotate(
        account_count=Count('accounts'),
        media_count=Count('media')
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

    # Computed fields already annotated
    items = list(page_obj)

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
        user=request.auth,
        is_deleted=False
    )

    # Add related data
    post.accounts = list(post.accounts.values('id', 'username', 'display_name'))
    post.media = list(post.media.values())
    post.publish_history = list(
        post.publish_history.values(
            'account__username', 'status',
            'published_at', 'error_message'
        )
    )
    post.account_count = len(post.accounts)
    post.media_count = len(post.media)

    return post


@router.put("/{post_id}", response=PostOut, auth=auth)
def update_post(request, post_id: str, data: PostUpdateIn):
    """Update existing post"""
    post = get_object_or_404(
        ScheduledPost,
        id=post_id,
        user=request.auth,
        is_deleted=False
    )

    service = PostService()
    updated_post = service.update_post(post, data.dict(exclude_unset=True))

    # Add computed fields
    updated_post.account_count = updated_post.accounts.count()
    updated_post.media_count = updated_post.media.count()

    return updated_post


@router.delete("/{post_id}", auth=auth)
def delete_post(request, post_id: str):
    """Delete post (soft delete)"""
    post = get_object_or_404(
        ScheduledPost,
        id=post_id,
        user=request.auth,
        is_deleted=False
    )

    if post.status == 'published':
        return router.api.create_response(
            request,
            {"detail": "Cannot delete published post"},
            status=400
        )

    post.is_deleted = True
    post.save()
    logger.info(f"Deleted post {post_id} for user {request.auth.id}")

    return {"success": True}


@router.post("/{post_id}/publish", response=PublishResultOut, auth=auth)
def publish_post(request, post_id: str):
    """Publish post immediately"""
    post = get_object_or_404(
        ScheduledPost,
        id=post_id,
        user=request.auth,
        is_deleted=False
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


@router.get("/drafts/list", response=PostListOut, auth=auth)
def list_drafts(
    request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50)
):
    """List draft posts"""
    queryset = ScheduledPost.objects.filter(
        user=request.auth,
        status='draft',
        is_deleted=False
    ).prefetch_related('accounts', 'media').annotate(
        account_count=Count('accounts'),
        media_count=Count('media')
    ).order_by('-updated_at')

    paginator = Paginator(queryset, limit)
    page_obj = paginator.get_page(page)

    # Computed fields already annotated
    items = list(page_obj)

    return PostListOut(
        items=items,
        total=paginator.count,
        page=page,
        pages=paginator.num_pages,
        has_next=page_obj.has_next(),
        has_prev=page_obj.has_previous()
    )


@router.get("/upcoming/list", auth=auth)
def upcoming_posts(request, days: int = Query(7, le=30)):
    """Get upcoming scheduled posts"""
    end_date = timezone.now() + timedelta(days=days)
    posts = ScheduledPost.objects.filter(
        user=request.auth,
        status='scheduled',
        scheduled_time__lte=end_date,
        is_deleted=False
    ).prefetch_related('accounts', 'media').order_by('scheduled_time')

    return {
        "count": posts.count(),
        "posts": list(posts.values('id', 'title', 'scheduled_time'))
    }


@router.post("/bulk/schedule", auth=auth)
def bulk_schedule_posts(request, data: BulkScheduleIn):
    """Schedule multiple posts at once"""
    posts = ScheduledPost.objects.filter(
        id__in=data.post_ids,
        user=request.auth,
        status='draft',
        is_deleted=False
    )

    updated_count = posts.update(
        status='scheduled',
        scheduled_time=data.scheduled_time
    )

    # Schedule tasks
    service = PostService()
    for post in posts:
        service._schedule_post(post)

    return {
        "success": True,
        "updated_count": updated_count
    }
