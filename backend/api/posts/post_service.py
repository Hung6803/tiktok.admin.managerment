"""
Post service for business logic operations
"""
from django.db import transaction
from django.utils import timezone
from typing import List, Dict
import logging

from apps.content.models import ScheduledPost, PostMedia, PublishHistory
from apps.tiktok_accounts.models import TikTokAccount

logger = logging.getLogger(__name__)


class PostService:
    """Service class for post operations"""

    @transaction.atomic
    def create_post(self, user, data: dict) -> ScheduledPost:
        """
        Create new post with media and account associations

        Args:
            user: User creating the post
            data: Post data dictionary

        Returns:
            Created ScheduledPost instance
        """
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
        """
        Schedule post for publishing via Celery

        Args:
            post: ScheduledPost to schedule
        """
        try:
            from apps.scheduler.tasks import publish_post_task
            eta = post.scheduled_time
            publish_post_task.apply_async(
                args=[str(post.id)],
                eta=eta
            )
            logger.info(f"Scheduled post {post.id} for {eta}")
        except ImportError:
            logger.warning("Scheduler tasks not available, skipping scheduling")

    def publish_now(self, post: ScheduledPost) -> Dict:
        """
        Publish post immediately to all accounts

        Auto-deletes media files after successful upload to TikTok.

        Args:
            post: ScheduledPost to publish

        Returns:
            Dictionary with success and failed results
        """
        results = {
            'success': [],
            'failed': []
        }

        post.status = 'publishing'
        post.save()

        # Track media files for cleanup
        media_files_to_cleanup = []

        for account in post.accounts.all():
            try:
                # Use existing video service
                from apps.content.services import TikTokVideoService
                # Initialize service with account's access token
                service = TikTokVideoService(account.access_token)

                # Get primary media
                media = post.media.first()
                if not media:
                    raise ValueError("No media attached")

                # Track file for cleanup (only add once)
                if media.file_path not in media_files_to_cleanup:
                    media_files_to_cleanup.append(media.file_path)
                    # Also track thumbnail if exists
                    if media.thumbnail_url:
                        # Extract file path from thumbnail URL
                        from pathlib import Path
                        from django.conf import settings
                        thumb_path = Path(settings.MEDIA_ROOT) / media.thumbnail_url.lstrip('/media/')
                        media_files_to_cleanup.append(str(thumb_path))

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

            # Auto-cleanup: Delete media files after successful upload
            if media_files_to_cleanup:
                try:
                    from api.media.processing_service import MediaProcessingService
                    processing_service = MediaProcessingService()
                    deleted_count = processing_service.cleanup_media_files(media_files_to_cleanup)
                    logger.info(f"Post {post.id}: Auto-cleaned {deleted_count} media files after successful publish")
                except Exception as e:
                    logger.error(f"Post {post.id}: Failed to cleanup media files: {str(e)}")
        else:
            post.status = 'failed'
            post.error_message = "Failed to publish to all accounts"
        post.save()

        return results

    @transaction.atomic
    def update_post(self, post: ScheduledPost, data: dict):
        """
        Update existing post

        Args:
            post: ScheduledPost to update
            data: Updated data dictionary

        Returns:
            Updated ScheduledPost instance
        """
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

    @transaction.atomic
    def create_slideshow_post(self, user, data: dict) -> ScheduledPost:
        """
        Create slideshow post from multiple images

        Args:
            user: User creating the post
            data: Slideshow data dictionary with images

        Returns:
            Created ScheduledPost instance with pending conversion
        """
        # Extract data
        account_ids = data.pop('account_ids')
        images = data.pop('images')
        hashtags = data.pop('hashtags', [])
        is_draft = data.pop('is_draft', False)

        # Determine status - always pending until conversion completes
        if is_draft:
            status = 'draft'
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

        # Add source images as PostMedia
        for img_data in images:
            import os
            from django.conf import settings
            import imghdr

            file_path = img_data['file_path']

            # Security: Validate file path is within allowed directory
            media_root = getattr(settings, 'MEDIA_ROOT', '/tmp/media')
            abs_path = os.path.abspath(file_path)
            abs_media = os.path.abspath(media_root)

            if not abs_path.startswith(abs_media):
                raise ValueError(f"Invalid file path: must be within media directory")

            if not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")

            # Security: Validate file size (max 20MB per image)
            file_size = os.path.getsize(file_path)
            max_size = 20 * 1024 * 1024  # 20MB
            if file_size > max_size:
                raise ValueError(f"File too large: {file_size} bytes (max {max_size})")

            # Security: Validate actual file type using magic bytes
            actual_type = imghdr.what(file_path)
            allowed_types = {'jpeg', 'png', 'webp'}
            if actual_type not in allowed_types:
                raise ValueError(f"Invalid image type: {actual_type}")

            # Determine MIME type from validated type
            mime_types = {
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'webp': 'image/webp'
            }
            mime_type = mime_types.get(actual_type, 'image/jpeg')

            PostMedia.objects.create(
                post=post,
                media_type='slideshow_source',
                file_path=abs_path,  # Use sanitized absolute path
                file_size=file_size,
                file_mime_type=mime_type,
                carousel_order=img_data.get('order', 0),
                image_duration_ms=img_data.get('duration_ms', 4000),
                is_slideshow_source=True
            )

        # Queue conversion task if not draft
        if not is_draft:
            self._queue_slideshow_conversion(post)

        logger.info(f"Created slideshow post {post.id} with {len(images)} images for user {user.id}")
        return post

    def _queue_slideshow_conversion(self, post: ScheduledPost):
        """
        Queue slideshow conversion task via Celery

        Args:
            post: ScheduledPost to convert
        """
        try:
            from apps.scheduler.tasks import convert_slideshow
            convert_slideshow.delay(str(post.id))
            logger.info(f"Queued slideshow conversion for post {post.id}")
        except ImportError:
            logger.warning("convert_slideshow task not available, skipping conversion queue")
