# Phase 05: Integrate Services with Celery Task

**Duration:** 1-2 hours
**Priority:** CRITICAL
**Dependencies:** Phase 02, Phase 03, Phase 04

## Objective

Replace simulated success in `publish_post_task.py` with actual TikTok API calls.

## Current Problem

**File:** `backend/apps/scheduler/tasks/publish_post_task.py` (lines 73-85)

```python
# TODO: Implement actual TikTok API publishing
# For now, simulate success
result = {
    'success': True,
    'video_id': f'simulated_{account.id}_{timezone.now().timestamp()}',
    'share_url': f'https://tiktok.com/@{account.username}/video/12345'
}
```

## Implementation

### Step 1: Create Helper Function for Token Refresh

**File:** `backend/apps/scheduler/tasks/publish_post_task.py`

Add at top of file after imports:

```python
from apps.content.services import TikTokPublishService, TikTokPhotoService
from apps.tiktok_accounts.services import TikTokTokenRefreshService


def get_valid_access_token(account) -> str:
    """
    Get valid access token, refreshing if needed

    Args:
        account: TikTokAccount model instance

    Returns:
        Decrypted access token

    Raises:
        Exception: If token refresh fails
    """
    if account.needs_refresh():
        logger.info(f"Refreshing token for account {account.username}")
        refresh_service = TikTokTokenRefreshService()
        refresh_service.refresh_token(account)
        account.refresh_from_db()

    return account.access_token  # EncryptedTextField auto-decrypts
```

### Step 2: Create Video Publishing Function

```python
def publish_video_to_tiktok(
    account,
    post,
    video_path: str
) -> dict:
    """
    Publish video to TikTok account

    Args:
        account: TikTokAccount instance
        post: ScheduledPost instance
        video_path: Path to video file

    Returns:
        Dictionary with success, video_id, share_url, or error
    """
    try:
        access_token = get_valid_access_token(account)

        # Map internal privacy to API
        privacy_map = {
            'public': 'public',
            'friends': 'friends',
            'private': 'private',
        }
        privacy = privacy_map.get(post.privacy_level, 'public')

        with TikTokPublishService(access_token) as service:
            result = service.publish_video(
                video_path=video_path,
                caption=post.description,
                privacy_level=privacy,
                disable_comment=not post.allow_comments,
                disable_duet=not post.allow_duet,
                disable_stitch=not post.allow_stitch,
            )

        if result['success']:
            return {
                'success': True,
                'video_id': result['video_id'],
                'share_url': f"https://tiktok.com/@{account.username}/video/{result['video_id']}",
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
            }

    except Exception as e:
        logger.error(f"Video publish error: {e}")
        return {
            'success': False,
            'error': str(e),
        }
```

### Step 3: Create Photo Publishing Function

```python
def publish_photos_to_tiktok(
    account,
    post,
    image_urls: list
) -> dict:
    """
    Publish photo carousel to TikTok account

    Args:
        account: TikTokAccount instance
        post: ScheduledPost instance
        image_urls: List of image URLs

    Returns:
        Dictionary with success, post_id, or error
    """
    try:
        access_token = get_valid_access_token(account)

        privacy_map = {
            'public': 'public',
            'friends': 'friends',
            'private': 'private',
        }
        privacy = privacy_map.get(post.privacy_level, 'public')

        with TikTokPhotoService(access_token) as service:
            result = service.publish_photos(
                image_urls=image_urls,
                caption=post.description,
                privacy_level=privacy,
                disable_comment=not post.allow_comments,
            )

        if result['success']:
            return {
                'success': True,
                'video_id': result['post_id'],  # Use video_id field for consistency
                'share_url': f"https://tiktok.com/@{account.username}",
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
            }

    except Exception as e:
        logger.error(f"Photo publish error: {e}")
        return {
            'success': False,
            'error': str(e),
        }
```

### Step 4: Update Main Task

Replace lines 64-85 in `publish_post` function:

```python
# Get media for this post
media_items = post.media.filter(is_deleted=False)
video_media = media_items.filter(
    media_type__in=['video', 'slideshow_video']
).first()
photo_media = list(media_items.filter(
    media_type='image',
    is_slideshow_source=False
))

# Publish to each account
for account in accounts:
    try:
        # Create history record
        history = PublishHistory.objects.create(
            post=post,
            account=account,
            status='failed'  # Default, update on success
        )

        # Determine content type and publish
        if video_media:
            # Video post
            result = publish_video_to_tiktok(
                account=account,
                post=post,
                video_path=video_media.file_path
            )
        elif len(photo_media) >= 2:
            # Photo carousel (requires 2+ images)
            image_urls = [m.file_path for m in photo_media]  # Or generate URLs
            result = publish_photos_to_tiktok(
                account=account,
                post=post,
                image_urls=image_urls
            )
        else:
            result = {
                'success': False,
                'error': 'No publishable media found'
            }

        # Process result (existing code continues...)
        if result['success']:
            history.status = 'success'
            history.tiktok_video_id = result.get('video_id')
            history.published_at = timezone.now()
            history.save()
            # ... rest of success handling
        else:
            # ... error handling
```

## Complete Updated Task File

See `publish_post_task_updated.py` in this plan folder for complete implementation.

## Media URL Handling

For photo posts, images need accessible URLs. Options:

### If using local storage:
```python
# Generate temporary public URL
from django.conf import settings
image_urls = [
    f"{settings.MEDIA_URL}{m.file_path}"
    for m in photo_media
]
```

### If using cloud storage (S3):
```python
# Generate signed URLs
image_urls = [
    generate_signed_url(m.file_path, expires_in=3600)
    for m in photo_media
]
```

## Testing

### Manual Test
```python
from apps.scheduler.tasks import publish_post

# Create test post with media
post = ScheduledPost.objects.create(
    user=user,
    title='Test Post',
    description='Test description #test',
    status='scheduled',
    privacy_level='private',  # Use private for testing
)
post.accounts.add(tiktok_account)

# Trigger task
result = publish_post.apply(args=[str(post.id)])
print(result.get())
```

### Celery Worker Test
```bash
cd backend
celery -A core worker -l debug
# In another terminal:
python manage.py shell
>>> from apps.scheduler.tasks import publish_post
>>> publish_post.delay('post-uuid-here')
```

## Error Handling

| Error | Handling |
|-------|----------|
| Token expired | Auto-refresh before publish |
| Token refresh fails | Mark account status as 'expired' |
| Video too large | Return specific error message |
| Photo URL inaccessible | Pre-validate URLs |
| Rate limit | Respect TikTok limits, queue retry |
| API error | Log full response, user-friendly message |

## Monitoring

Add metrics tracking:
```python
# Optional: Add to task
import time

start_time = time.time()
# ... publishing logic ...
duration = time.time() - start_time

logger.info(f"Publish completed in {duration:.2f}s", extra={
    'post_id': str(post.id),
    'account_id': str(account.id),
    'duration': duration,
    'success': result['success'],
})
```
