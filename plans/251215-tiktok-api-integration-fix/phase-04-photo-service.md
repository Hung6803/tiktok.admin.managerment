# Phase 04: Create TikTok Photo Service

**Duration:** 1-2 hours
**Priority:** MEDIUM
**Dependencies:** Phase 01

## Objective

Create `TikTokPhotoService` for posting photo carousels via `PULL_FROM_URL`.

## TikTok Photo API

### Endpoint
```
POST https://open.tiktokapis.com/v2/post/publish/content/init/
```

### Request Body
```json
{
  "media_type": "PHOTO",
  "post_mode": "DIRECT_POST",
  "post_info": {
    "title": "caption #hashtag",
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_comment": false
  },
  "source_info": {
    "source": "PULL_FROM_URL",
    "photo_images": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "photo_cover_index": 0
  }
}
```

### Constraints
- Minimum: 2 images
- Maximum: 35 images
- Images must be publicly accessible URLs
- Supported formats: JPG, PNG, WebP

## Implementation

### New File: `backend/apps/content/services/tiktok_photo_service.py`

```python
"""
TikTok photo carousel posting service
Handles photo post publishing via URL pulling
"""
from typing import Dict, Any, List
import logging
import requests

from config.tiktok_config import TikTokConfig
from core.utils.tiktok_api_client import TikTokAPIClient

logger = logging.getLogger(__name__)


class TikTokPhotoError(Exception):
    """Exception raised when photo posting fails"""
    pass


class TikTokPhotoService:
    """
    TikTok photo carousel posting service
    Uses post/publish/content/init/ with PULL_FROM_URL
    """

    MIN_IMAGES = 2
    MAX_IMAGES = 35

    def __init__(self, access_token: str):
        """Initialize service with access token"""
        self.config = TikTokConfig()
        self.client = TikTokAPIClient(access_token)

    def validate_image_urls(self, urls: List[str]) -> tuple[bool, str]:
        """
        Validate image URLs meet requirements

        Args:
            urls: List of image URLs

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(urls) < self.MIN_IMAGES:
            return False, f"Minimum {self.MIN_IMAGES} images required"

        if len(urls) > self.MAX_IMAGES:
            return False, f"Maximum {self.MAX_IMAGES} images allowed"

        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

        for i, url in enumerate(urls):
            # Check URL format
            if not url.startswith(('http://', 'https://')):
                return False, f"Image {i+1}: Invalid URL format"

            # Check extension
            url_lower = url.lower().split('?')[0]
            if not any(url_lower.endswith(ext) for ext in valid_extensions):
                return False, f"Image {i+1}: Must be JPG, PNG, or WebP"

        return True, "Valid"

    def check_url_accessibility(
        self,
        urls: List[str],
        timeout: int = 10
    ) -> Dict[str, bool]:
        """
        Check if image URLs are accessible

        Args:
            urls: List of image URLs
            timeout: Request timeout

        Returns:
            Dictionary mapping URL to accessibility status
        """
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
            poll_interval: Seconds between status checks
            max_poll_attempts: Max status check attempts

        Returns:
            Dictionary with success status and post details
        """
        import time

        # Validate inputs
        is_valid, error = self.validate_image_urls(image_urls)
        if not is_valid:
            return {'success': False, 'error': error}

        if cover_index < 0 or cover_index >= len(image_urls):
            cover_index = 0

        api_privacy = self.config.get_api_privacy_level(privacy_level)

        logger.info(f"Publishing photo carousel: {len(image_urls)} images")

        url = f"{self.config.API_BASE_URL}post/publish/content/init/"

        data = {
            'media_type': 'PHOTO',
            'post_mode': 'DIRECT_POST',
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

                if status['status'] == 'PUBLISH_COMPLETE':
                    logger.info(f"Photos published: {status.get('post_id')}")
                    return {
                        'success': True,
                        'post_id': status.get('post_id'),
                        'publish_id': publish_id,
                    }

                if status['status'] in ['FAILED', 'PUBLISH_FAILED']:
                    reason = status.get('fail_reason', 'Unknown')
                    logger.error(f"Photo publish failed: {reason}")
                    return {
                        'success': False,
                        'error': reason,
                        'publish_id': publish_id,
                    }

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
```

### Update Exports

**File:** `backend/apps/content/services/__init__.py`

```python
from .tiktok_photo_service import TikTokPhotoService, TikTokPhotoError
```

## Integration with PostMedia

When posting photos, images need to be served via public URLs. Options:

### Option A: Use existing media storage URLs
If media is stored in cloud storage (S3, GCS), use signed URLs.

### Option B: Temporary public endpoint
Create endpoint to serve images temporarily for TikTok to pull.

**File:** `backend/api/media/router.py` (add endpoint)

```python
@router.get("/public/{media_id}", response=dict, tags=["Media"])
def get_public_media_url(request, media_id: str):
    """Generate temporary public URL for TikTok photo pulling"""
    # Implementation depends on storage backend
    pass
```

## Testing

```python
from apps.content.services import TikTokPhotoService

with TikTokPhotoService(access_token) as service:
    result = service.publish_photos(
        image_urls=[
            'https://example.com/photo1.jpg',
            'https://example.com/photo2.jpg',
            'https://example.com/photo3.jpg',
        ],
        caption='Photo carousel test #test',
        privacy_level='private',
        cover_index=0
    )

    if result['success']:
        print(f"Posted! ID: {result['post_id']}")
    else:
        print(f"Failed: {result['error']}")
```

## Notes

- TikTok pulls images from URLs (server must be accessible)
- Processing typically faster than video
- Cover image determines carousel thumbnail
- Privacy levels same as video posts
