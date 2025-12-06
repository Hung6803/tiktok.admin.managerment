"""
Celery task for publishing scheduled posts to TikTok
Handles retry logic with exponential backoff
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

from apps.content.models import ScheduledPost, PublishHistory

logger = logging.getLogger(__name__)


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

        # Publish to each account
        for account in accounts:
            try:
                # Create history record
                history = PublishHistory.objects.create(
                    post=post,
                    account=account,
                    status='failed'  # Default to failed, update on success
                )

                # TODO: Implement actual TikTok API publishing
                # For now, simulate success
                # In production, replace with:
                # from apps.tiktok_accounts.services.tiktok_publish_service import TikTokPublishService
                # publish_service = TikTokPublishService(account)
                # result = publish_service.publish_video(post)

                # Simulated success (replace with actual API call)
                result = {
                    'success': True,
                    'video_id': f'simulated_{account.id}_{timezone.now().timestamp()}',
                    'share_url': f'https://tiktok.com/@{account.username}/video/12345'
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
