"""
Celery task for checking and queuing scheduled posts ready for publishing
Runs every minute via Celery Beat
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from apps.content.models import ScheduledPost
from .publish_post_task import publish_post

logger = logging.getLogger(__name__)


@shared_task
def check_scheduled_posts():
    """
    Check for posts scheduled for publishing and queue them

    This task runs every minute (configured in Celery Beat).
    It finds posts scheduled within a 5-minute time window and queues them
    for immediate publishing.

    Returns:
        dict: Statistics about posts checked and queued
    """
    now = timezone.now()
    time_window = now + timedelta(minutes=5)  # 5 minute buffer

    logger.debug(f"Checking scheduled posts at {now}")

    # Find posts scheduled for publishing
    posts = ScheduledPost.objects.filter(
        status='scheduled',
        scheduled_time__lte=time_window,
        scheduled_time__gte=now - timedelta(hours=1),  # Don't publish posts older than 1 hour
        is_deleted=False,
        retry_count__lt=3  # Don't retry posts that already failed 3 times
    ).select_related('user')

    posts_count = posts.count()
    queued_count = 0

    if posts_count == 0:
        logger.debug("No posts ready for publishing")
        return {
            'checked': 0,
            'queued': 0,
            'skipped': 0
        }

    logger.info(f"Found {posts_count} posts ready for publishing")

    for post in posts:
        try:
            # Check if post time has arrived
            if post.scheduled_time <= now:
                # Update status to pending (queued for publishing)
                post.status = 'pending'
                post.save(update_fields=['status', 'updated_at'])

                # Queue async publishing task
                publish_post.delay(str(post.id))
                queued_count += 1

                logger.info(
                    f"Queued post {post.id} ('{post.title}') for user {post.user.username} "
                    f"scheduled at {post.scheduled_time}"
                )

        except Exception as e:
            logger.error(f"Failed to queue post {post.id}: {str(e)}")

    skipped = posts_count - queued_count

    logger.info(f"Checked {posts_count} posts, queued {queued_count}, skipped {skipped}")

    return {
        'checked': posts_count,
        'queued': queued_count,
        'skipped': skipped
    }
