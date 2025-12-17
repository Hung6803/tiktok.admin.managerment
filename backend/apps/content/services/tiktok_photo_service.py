"""
TikTok photo posting service
Handles single and multiple photo posts via URL pulling
Supports 1-35 images per post
"""
from typing import Dict, Any, List
import logging
import time
import requests

from config.tiktok_config import TikTokConfig
from core.utils.tiktok_api_client import TikTokAPIClient

logger = logging.getLogger(__name__)


class TikTokPhotoError(Exception):
    """Exception raised when photo posting fails"""
    pass


class TikTokPhotoService:
    """
    TikTok photo posting service (single or multiple images)
    Uses post/publish/content/init/ with PULL_FROM_URL
    Supports 1-35 images per post

    Note: Unaudited apps (sandbox mode) must use MEDIA_UPLOAD mode.
    - DIRECT_POST: Requires audited/approved app (production)
    - MEDIA_UPLOAD: Creates draft in user's TikTok inbox (sandbox)
    When use_inbox=True, uses MEDIA_UPLOAD mode for sandbox compatibility.
    """

    MIN_IMAGES = 1  # TikTok supports single image posts
    MAX_IMAGES = 35

    def __init__(self, access_token: str, use_inbox: bool = False):
        """
        Initialize service with access token

        Args:
            access_token: TikTok OAuth access token
            use_inbox: If True (sandbox mode), force SELF_ONLY privacy for photos
        """
        self.config = TikTokConfig()
        self.client = TikTokAPIClient(access_token)
        self.use_inbox = use_inbox  # Sandbox mode requires private posts

    def validate_image_urls(self, urls: List[str]) -> tuple:
        """Validate image URLs meet requirements"""
        if len(urls) < self.MIN_IMAGES:
            return False, f"Minimum {self.MIN_IMAGES} images required"

        if len(urls) > self.MAX_IMAGES:
            return False, f"Maximum {self.MAX_IMAGES} images allowed"

        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

        for i, url in enumerate(urls):
            if not url.startswith(('http://', 'https://')):
                return False, f"Image {i+1}: Invalid URL format"

            url_lower = url.lower().split('?')[0]
            if not any(url_lower.endswith(ext) for ext in valid_extensions):
                return False, f"Image {i+1}: Must be JPG, PNG, or WebP"

        return True, "Valid"

    def check_url_accessibility(
        self,
        urls: List[str],
        timeout: int = 10
    ) -> Dict[str, bool]:
        """Check if image URLs are accessible"""
        results = {}
        for url in urls:
            try:
                response = requests.head(url, timeout=timeout, allow_redirects=True)
                results[url] = response.status_code == 200
            except requests.RequestException:
                results[url] = False
        return results

    def publish_photos(
        self,
        image_urls: List[str],
        caption: str = '',
        privacy_level: str = 'public',
        disable_comment: bool = False,
        cover_index: int = 0,
        poll_interval: int = 5,
        max_poll_attempts: int = 30
    ) -> Dict[str, Any]:
        """
        Publish photo carousel to TikTok

        Args:
            image_urls: List of publicly accessible image URLs
            caption: Post caption (max 2200 chars)
            privacy_level: 'public', 'friends', or 'private'
            disable_comment: Disable comments
            cover_index: Index of cover image (0-based)
        """
        # Validate inputs
        is_valid, error = self.validate_image_urls(image_urls)
        if not is_valid:
            return {'success': False, 'error': error}

        if cover_index < 0 or cover_index >= len(image_urls):
            cover_index = 0

        # In sandbox mode (unaudited apps):
        # - Must use MEDIA_UPLOAD mode (creates draft in user's TikTok inbox)
        # - DIRECT_POST is only for audited/approved apps
        if self.use_inbox:
            post_mode = 'MEDIA_UPLOAD'
            api_privacy = 'SELF_ONLY'
            logger.info("Sandbox mode: Using MEDIA_UPLOAD (draft to inbox) with SELF_ONLY privacy")
        else:
            post_mode = 'DIRECT_POST'
            api_privacy = self.config.get_api_privacy_level(privacy_level)

        logger.info(f"Publishing photo carousel: {len(image_urls)} images (mode: {post_mode}, privacy: {api_privacy})")

        url = f"{self.config.API_BASE_URL}post/publish/content/init/"

        data = {
            'media_type': 'PHOTO',
            'post_mode': post_mode,
            'post_info': {
                'title': caption[:2200],
                'privacy_level': api_privacy,
                'disable_comment': disable_comment,
            },
            'source_info': {
                'source': 'PULL_FROM_URL',
                'photo_images': image_urls,
                'photo_cover_index': cover_index,
            }
        }

        try:
            response = self.client.post(url, json=data)
            result = response.get('data', {})

            publish_id = result.get('publish_id')
            if not publish_id:
                raise TikTokPhotoError("No publish_id returned")

            logger.info(f"Photo post initiated: {publish_id}")

            # Poll for status
            for attempt in range(max_poll_attempts):
                status = self._check_status(publish_id)
                current_status = status.get('status')

                # Success: Direct post completed
                if current_status == 'PUBLISH_COMPLETE':
                    logger.info(f"Photos published: {status.get('publiclyAvailablePostId')}")
                    return {
                        'success': True,
                        'post_id': status.get('publiclyAvailablePostId'),
                        'publish_id': publish_id,
                    }

                # Success: Sent to user inbox (sandbox mode)
                if current_status == 'SEND_TO_USER_INBOX':
                    logger.info(f"Photos sent to Creator Inbox: {publish_id}")
                    return {
                        'success': True,
                        'post_id': publish_id,
                        'publish_id': publish_id,
                        'inbox_mode': True,
                    }

                # Failure statuses
                if current_status in ['FAILED', 'PUBLISH_FAILED']:
                    reason = status.get('fail_reason', 'Unknown')
                    logger.error(f"Photo publish failed: {reason}")
                    return {
                        'success': False,
                        'error': reason,
                        'publish_id': publish_id,
                    }

                # Processing - keep polling
                if current_status in ['PROCESSING_UPLOAD', 'PROCESSING', 'SENDING_TO_USER_INBOX']:
                    logger.info(f"Photo processing... ({attempt + 1}/{max_poll_attempts})")

                time.sleep(poll_interval)

            return {
                'success': False,
                'error': 'Processing timeout',
                'publish_id': publish_id,
            }

        except Exception as e:
            logger.error(f"Photo publish error: {e}")
            return {'success': False, 'error': str(e)}

    def _check_status(self, publish_id: str) -> Dict[str, Any]:
        """Check publishing status"""
        url = f"{self.config.API_BASE_URL}post/publish/status/fetch/"
        response = self.client.post(url, json={'publish_id': publish_id})
        return response.get('data', {})

    def close(self):
        """Close API client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
