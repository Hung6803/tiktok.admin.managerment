"""
Celery task for publishing scheduled posts to TikTok
Handles retry logic with exponential backoff
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import logging

from apps.content.models import ScheduledPost, PublishHistory
from apps.content.services import TikTokPublishService, TikTokPhotoService
from apps.tiktok_accounts.services.tiktok_token_refresh_service import TikTokTokenRefreshService
from api.media.processing_service import MediaProcessingService
import os.path
import shutil

logger = logging.getLogger(__name__)


def sanitize_media_path(file_path: str) -> str:
    """
    Sanitize media path to prevent path traversal attacks
    Returns relative path from MEDIA_ROOT, or None if invalid

    Handles:
    - Absolute paths within MEDIA_ROOT (converts to relative)
    - Relative paths (validates and returns as-is)
    - Paths already starting with /media/ (strips prefix)
    """
    if not file_path:
        return None

    # Normalize path
    normalized = os.path.normpath(file_path)

    # Reject paths with .. (path traversal attempt)
    if '..' in normalized:
        logger.warning(f"Path traversal attempt detected: {file_path}")
        return None

    # Handle absolute paths - check if within MEDIA_ROOT
    if os.path.isabs(normalized):
        media_root = os.path.normpath(str(settings.MEDIA_ROOT))
        if normalized.startswith(media_root):
            # Extract relative path from MEDIA_ROOT
            relative_path = normalized[len(media_root):].lstrip(os.sep)
            # Convert backslashes to forward slashes for URL
            relative_path = relative_path.replace('\\', '/')
            return relative_path
        else:
            logger.warning(f"Path outside MEDIA_ROOT: {file_path}")
            return None

    # Handle paths starting with /media/
    if normalized.startswith('/media/') or normalized.startswith('\\media\\'):
        relative_path = normalized[7:]  # Remove /media/ prefix
        relative_path = relative_path.replace('\\', '/')
        return relative_path

    # Already a relative path - validate characters
    # Allow alphanumeric, dash, underscore, dot, slash, space, and common chars
    safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./\\ ')
    normalized_for_check = normalized.replace('\\', '/')
    if not all(c in safe_chars for c in normalized_for_check):
        logger.warning(f"Invalid characters in file path: {file_path}")
        return None

    return normalized.replace('\\', '/')


def get_valid_access_token(account) -> str:
    """Get valid access token, refreshing if needed"""
    if account.needs_refresh():
        logger.info(f"Refreshing token for account {account.username}")
        refresh_service = TikTokTokenRefreshService()
        refresh_service.refresh_account_token(account)
        account.refresh_from_db()
    return account.access_token


def transcode_video_if_needed(video_path: str) -> tuple:
    """
    Transcode video for TikTok compatibility if needed

    Args:
        video_path: Path to video file

    Returns:
        Tuple of (final_video_path, transcoded_temp_dir or None)
    """
    try:
        processing_service = MediaProcessingService()
        result = processing_service.transcode_for_tiktok(video_path)

        if result['transcoded']:
            logger.info(f"Video transcoded: {result['reason']}")
            # Return transcoded path and temp dir for cleanup
            transcoded_path = result['path']
            temp_dir = os.path.dirname(transcoded_path)
            return transcoded_path, temp_dir
        else:
            logger.info("Video meets TikTok requirements, no transcoding needed")
            return video_path, None

    except Exception as e:
        logger.warning(f"Transcoding check/process failed: {e}, using original")
        return video_path, None


def publish_video_to_tiktok(account, post, video_path: str) -> dict:
    """Publish video to TikTok account with automatic transcoding"""
    from config.tiktok_config import TikTokConfig

    transcoded_temp_dir = None

    try:
        access_token = get_valid_access_token(account)

        # Transcode video if needed for TikTok compatibility
        final_video_path, transcoded_temp_dir = transcode_video_if_needed(video_path)

        # Use Creator Inbox API in sandbox mode, Direct Post in production
        use_inbox = TikTokConfig.use_inbox_api()

        with TikTokPublishService(access_token, use_inbox=use_inbox) as service:
            result = service.publish_video(
                video_path=final_video_path,
                caption=post.description,
                privacy_level=post.privacy_level,
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
        return {'success': False, 'error': str(e)}

    finally:
        # Cleanup transcoded temp directory if exists
        if transcoded_temp_dir and os.path.exists(transcoded_temp_dir):
            try:
                shutil.rmtree(transcoded_temp_dir)
                logger.info(f"Cleaned up transcoded temp dir: {transcoded_temp_dir}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp dir: {cleanup_error}")


def publish_photos_to_tiktok(account, post, image_urls: list) -> dict:
    """Publish photo carousel to TikTok account"""
    from config.tiktok_config import TikTokConfig

    try:
        access_token = get_valid_access_token(account)

        # Use inbox mode in sandbox (forces SELF_ONLY privacy for unaudited apps)
        use_inbox = TikTokConfig.use_inbox_api()

        with TikTokPhotoService(access_token, use_inbox=use_inbox) as service:
            result = service.publish_photos(
                image_urls=image_urls,
                caption=post.description,
                privacy_level=post.privacy_level,
                disable_comment=not post.allow_comments,
            )

        if result['success']:
            return {
                'success': True,
                'video_id': result['post_id'],
                'share_url': f"https://tiktok.com/@{account.username}",
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
            }

    except Exception as e:
        logger.error(f"Photo publish error: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def publish_post(self, post_id: str):
    """
    Publish scheduled post to TikTok with retry logic

    Args:
        post_id: UUID of the scheduled post

    Returns:
        dict: Status and result information

    Retry logic:
        - Attempt 1: Immediate
        - Attempt 2: 5 minutes later (300s)
        - Attempt 3: 15 minutes later (900s)
        - Attempt 4: 30 minutes later (1800s)
    """
    try:
        # Get post with select_for_update to prevent race conditions
        with transaction.atomic():
            post = ScheduledPost.objects.select_for_update().get(
                id=post_id,
                is_deleted=False
            )

            # Check if already published
            if post.status == 'published':
                logger.info(f"Post {post_id} already published")
                return {'status': 'already_published'}

            # Update status to publishing
            post.status = 'publishing'
            post.save()

        # Get all accounts to publish to
        accounts = post.accounts.filter(is_deleted=False)

        if not accounts.exists():
            logger.error(f"No active accounts found for post {post_id}")
            post.status = 'failed'
            post.error_message = "No active TikTok accounts configured"
            post.save()
            return {'status': 'no_accounts'}

        # Track publishing results
        results = []
        all_success = True

        # Get media for this post
        media_items = post.media.filter(is_deleted=False)
        video_media = media_items.filter(
            media_type__in=['video', 'slideshow_video']
        ).first()
        photo_media = list(media_items.filter(
            media_type='image',
            is_slideshow_source=False
        ).order_by('carousel_order'))

        # Publish to each account
        for account in accounts:
            try:
                # Create history record
                history = PublishHistory.objects.create(
                    post=post,
                    account=account,
                    status='failed'  # Default to failed, update on success
                )

                # Determine content type and publish using real TikTok API
                # Check post_type first for explicit photo posts
                if post.post_type == 'photo' and len(photo_media) >= 1:
                    # Photo post (1-35 images)
                    backend_url = getattr(settings, 'BACKEND_PUBLIC_URL', '')
                    image_urls = []
                    for m in photo_media:
                        safe_path = sanitize_media_path(m.file_path)
                        if safe_path:
                            image_urls.append(f"{backend_url}/media/{safe_path}")

                    if len(image_urls) < 1:
                        result = {
                            'success': False,
                            'error': 'Invalid media paths detected'
                        }
                    else:
                        result = publish_photos_to_tiktok(
                            account=account,
                            post=post,
                            image_urls=image_urls
                        )
                elif video_media:
                    # Video post (including slideshow-generated video)
                    result = publish_video_to_tiktok(
                        account=account,
                        post=post,
                        video_path=video_media.file_path
                    )
                elif len(photo_media) >= 1:
                    # Fallback: Images without explicit photo post_type
                    backend_url = getattr(settings, 'BACKEND_PUBLIC_URL', '')
                    image_urls = []
                    for m in photo_media:
                        safe_path = sanitize_media_path(m.file_path)
                        if safe_path:
                            image_urls.append(f"{backend_url}/media/{safe_path}")

                    if len(image_urls) < 1:
                        result = {
                            'success': False,
                            'error': 'Invalid media paths detected'
                        }
                    else:
                        result = publish_photos_to_tiktok(
                            account=account,
                            post=post,
                            image_urls=image_urls
                        )
                else:
                    result = {
                        'success': False,
                        'error': 'No publishable media found (need video or 1+ photos)'
                    }

                if result['success']:
                    # Update history
                    history.status = 'success'
                    history.tiktok_video_id = result.get('video_id')
                    history.published_at = timezone.now()
                    history.save()

                    results.append({
                        'account_id': str(account.id),
                        'username': account.username,
                        'status': 'success',
                        'video_id': result.get('video_id')
                    })
                    logger.info(f"Published post {post_id} to account {account.username}")
                else:
                    all_success = False
                    error_msg = result.get('error', 'Unknown error')
                    history.error_message = error_msg
                    history.save()

                    results.append({
                        'account_id': str(account.id),
                        'username': account.username,
                        'status': 'failed',
                        'error': error_msg
                    })
                    logger.error(f"Failed to publish post {post_id} to {account.username}: {error_msg}")

            except Exception as e:
                all_success = False
                error_msg = str(e)

                # Update history if exists
                if 'history' in locals():
                    history.error_message = error_msg
                    history.save()

                results.append({
                    'account_id': str(account.id),
                    'username': account.username,
                    'status': 'error',
                    'error': error_msg
                })
                logger.error(f"Exception publishing post {post_id} to {account.username}: {error_msg}")

        # Update post status based on results
        if all_success:
            post.status = 'published'
            post.published_at = timezone.now()
            post.error_message = None
            post.save()
            logger.info(f"Post {post_id} published successfully to all accounts")
            return {
                'status': 'success',
                'accounts_published': len(results),
                'results': results
            }
        else:
            # At least one failure occurred
            post.status = 'failed'
            post.error_message = f"Publishing failed for some accounts. See publish history for details."
            post.retry_count += 1
            post.save()

            # Retry if under max retries
            if post.retry_count < post.max_retries:
                # Exponential backoff: 5min (300s), 15min (900s), 30min (1800s)
                retry_delays = [300, 900, 1800]
                retry_delay = retry_delays[min(post.retry_count, len(retry_delays) - 1)]

                logger.info(f"Retrying post {post_id} in {retry_delay}s (attempt {post.retry_count + 1}/{post.max_retries})")
                raise self.retry(countdown=retry_delay, exc=Exception("Publishing failed"))
            else:
                logger.error(f"Post {post_id} exceeded max retries ({post.max_retries})")
                return {
                    'status': 'max_retries_exceeded',
                    'retry_count': post.retry_count,
                    'results': results
                }

    except ScheduledPost.DoesNotExist:
        logger.error(f"Post {post_id} not found")
        return {'status': 'not_found'}

    except Exception as e:
        logger.error(f"Unexpected error publishing post {post_id}: {str(e)}")

        # Try to update post status
        try:
            post = ScheduledPost.objects.get(id=post_id)
            post.status = 'failed'
            post.error_message = str(e)
            post.retry_count += 1
            post.save()

            # Retry if under max retries
            if post.retry_count < post.max_retries:
                retry_delays = [300, 900, 1800]
                retry_delay = retry_delays[min(post.retry_count, len(retry_delays) - 1)]
                raise self.retry(countdown=retry_delay, exc=e)

        except Exception as update_error:
            logger.error(f"Failed to update post status: {str(update_error)}")

        return {
            'status': 'error',
            'error': str(e)
        }
