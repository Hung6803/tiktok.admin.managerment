"""
Celery task for converting slideshow images to video
Handles async conversion using FFmpeg via PhotoSlideshowService
"""
import os
import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from apps.content.models import ScheduledPost, PostMedia
from apps.content.services.photo_slideshow_service import (
    PhotoSlideshowService,
    SlideshowConversionError
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def convert_slideshow(self, post_id: str):
    """
    Convert slideshow images to video for a post

    Args:
        post_id: UUID of the scheduled post

    Returns:
        dict: Status and result information

    Retry logic:
        - Attempt 1: Immediate
        - Attempt 2: 2 minutes later
        - Attempt 3: 5 minutes later
    """
    logger.info(f"Starting slideshow conversion for post {post_id}")

    try:
        # Get post
        post = ScheduledPost.objects.get(id=post_id, is_deleted=False)

        # Get source images ordered by carousel_order
        source_images = PostMedia.objects.filter(
            post=post,
            is_slideshow_source=True,
            is_deleted=False
        ).order_by('carousel_order')

        if not source_images.exists():
            logger.error(f"No slideshow source images found for post {post_id}")
            return {'status': 'no_images', 'error': 'No source images found'}

        image_count = source_images.count()
        logger.info(f"Found {image_count} source images for slideshow")

        # Get image paths and duration
        image_paths = []
        duration_ms = 4000  # Default

        for img in source_images:
            if not os.path.exists(img.file_path):
                logger.error(f"Source image not found: {img.file_path}")
                return {
                    'status': 'file_not_found',
                    'error': f'Image file not found: {img.file_path}'
                }
            image_paths.append(img.file_path)
            if img.image_duration_ms:
                duration_ms = img.image_duration_ms

        # Create service and convert
        service = PhotoSlideshowService()

        if not service.ffmpeg_available:
            logger.error("FFmpeg not available for slideshow conversion")
            return {'status': 'ffmpeg_unavailable', 'error': 'FFmpeg not installed'}

        # Generate output path
        media_root = getattr(settings, 'MEDIA_ROOT', '/tmp/media')
        output_dir = os.path.join(media_root, 'slideshows')
        os.makedirs(output_dir, exist_ok=True)

        output_filename = f"slideshow_{post_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(output_dir, output_filename)

        # Convert images to video
        result = service.create_slideshow(
            image_paths=image_paths,
            output_path=output_path,
            duration_per_image_ms=duration_ms
        )

        # Create PostMedia record for generated video
        with transaction.atomic():
            video_media = PostMedia.objects.create(
                post=post,
                media_type='slideshow_video',
                file_path=result['path'],
                file_size=result['size'],
                file_mime_type='video/mp4',
                duration=int(result['duration']),
                width=result['width'],
                height=result['height'],
                is_processed=True,
                is_slideshow_source=False
            )

            # Link source images to generated video
            source_images.update(slideshow_video=video_media)

            logger.info(
                f"Slideshow conversion complete for post {post_id}: "
                f"{result['duration']:.1f}s video from {image_count} images"
            )

        return {
            'status': 'success',
            'post_id': str(post_id),
            'video_media_id': str(video_media.id),
            'video_path': result['path'],
            'duration': result['duration'],
            'size': result['size'],
            'image_count': image_count
        }

    except ScheduledPost.DoesNotExist:
        logger.error(f"Post {post_id} not found")
        return {'status': 'not_found', 'error': 'Post not found'}

    except SlideshowConversionError as e:
        logger.error(f"Slideshow conversion failed for post {post_id}: {str(e)}")

        # Retry with backoff
        retry_delays = [120, 300]  # 2 min, 5 min
        if self.request.retries < self.max_retries:
            retry_delay = retry_delays[min(self.request.retries, len(retry_delays) - 1)]
            logger.info(
                f"Retrying slideshow conversion for {post_id} in {retry_delay}s "
                f"(attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(countdown=retry_delay, exc=e)

        return {
            'status': 'conversion_failed',
            'error': str(e),
            'retries_exhausted': True
        }

    except Exception as e:
        logger.error(f"Unexpected error in slideshow conversion for {post_id}: {str(e)}")

        # Retry for unexpected errors
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=120, exc=e)

        return {
            'status': 'error',
            'error': str(e),
            'retries_exhausted': True
        }


@shared_task
def cleanup_slideshow_temp_files(post_id: str, keep_video: bool = True):
    """
    Clean up temporary slideshow source images after successful publish

    Args:
        post_id: UUID of the scheduled post
        keep_video: Whether to keep the generated video file

    Returns:
        dict: Cleanup result
    """
    logger.info(f"Cleaning up slideshow temp files for post {post_id}")

    try:
        post = ScheduledPost.objects.get(id=post_id)

        # Get source images
        source_images = PostMedia.objects.filter(
            post=post,
            is_slideshow_source=True
        )

        deleted_count = 0
        for img in source_images:
            try:
                if os.path.exists(img.file_path):
                    os.remove(img.file_path)
                    deleted_count += 1
                    logger.debug(f"Deleted source image: {img.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete {img.file_path}: {str(e)}")

        # Optionally mark source images as deleted in DB
        source_images.update(is_deleted=True)

        logger.info(f"Cleaned up {deleted_count} slideshow source files for post {post_id}")

        return {
            'status': 'success',
            'deleted_files': deleted_count
        }

    except ScheduledPost.DoesNotExist:
        logger.error(f"Post {post_id} not found for cleanup")
        return {'status': 'not_found'}

    except Exception as e:
        logger.error(f"Error cleaning up slideshow files: {str(e)}")
        return {'status': 'error', 'error': str(e)}
