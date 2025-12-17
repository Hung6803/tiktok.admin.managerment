# Phase 02: Create TikTok Publish Service

**Duration:** 2 hours
**Priority:** CRITICAL
**Dependencies:** Phase 01

## Objective

Create `TikTokPublishService` for direct video posting using correct endpoint.

## Problem

Current `TikTokVideoService.initiate_upload()` uses wrong endpoint:
- **Current:** `post/publish/inbox/video/init/` (draft to inbox)
- **Correct:** `post/publish/video/init/` (direct post)

## Implementation

### New File: `backend/apps/content/services/tiktok_publish_service.py`

```python
"""
TikTok direct publishing service
Handles video posting with chunked upload support
"""
from typing import Dict, Any, Optional
from pathlib import Path
import logging
import math

from config.tiktok_config import TikTokConfig
from core.utils.tiktok_api_client import TikTokAPIClient

logger = logging.getLogger(__name__)


class TikTokPublishError(Exception):
    """Exception raised when publishing fails"""
    pass


class TikTokPublishService:
    """
    TikTok direct publishing service
    Uses post/publish/video/init/ endpoint for direct posting
    """

    # Chunk size: 5MB (recommended by TikTok)
    DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024

    def __init__(self, access_token: str):
        """
        Initialize service with access token

        Args:
            access_token: Decrypted OAuth access token
        """
        self.config = TikTokConfig()
        self.client = TikTokAPIClient(access_token)

    def _calculate_chunks(self, file_size: int) -> tuple[int, int]:
        """
        Calculate chunk parameters for upload

        Args:
            file_size: Video file size in bytes

        Returns:
            Tuple of (chunk_size, total_chunk_count)
        """
        chunk_size = self.DEFAULT_CHUNK_SIZE
        total_chunks = math.ceil(file_size / chunk_size)
        return chunk_size, total_chunks

    def initiate_video_post(
        self,
        video_path: str,
        caption: str = '',
        privacy_level: str = 'public',
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False
    ) -> Dict[str, Any]:
        """
        Initialize direct video post session

        Args:
            video_path: Path to video file
            caption: Video caption (max 2200 chars)
            privacy_level: 'public', 'friends', or 'private'
            disable_comment: Disable comments
            disable_duet: Disable duet
            disable_stitch: Disable stitch

        Returns:
            Dictionary with publish_id and upload_url
        """
        video_file = Path(video_path)
        if not video_file.exists():
            raise ValueError(f"Video file not found: {video_path}")

        file_size = video_file.stat().st_size
        chunk_size, total_chunks = self._calculate_chunks(file_size)

        # Map privacy to API format
        api_privacy = self.config.get_api_privacy_level(privacy_level)

        logger.info(f"Initiating video post: {file_size} bytes, {total_chunks} chunks")

        url = f"{self.config.API_BASE_URL}post/publish/video/init/"

        data = {
            'post_info': {
                'title': caption[:2200],  # TikTok limit
                'privacy_level': api_privacy,
                'disable_comment': disable_comment,
                'disable_duet': disable_duet,
                'disable_stitch': disable_stitch,
            },
            'source_info': {
                'source': 'FILE_UPLOAD',
                'video_size': file_size,
                'chunk_size': chunk_size,
                'total_chunk_count': total_chunks,
            }
        }

        try:
            response = self.client.post(url, json=data)
            result = response.get('data', {})

            publish_id = result.get('publish_id')
            upload_url = result.get('upload_url')

            if not publish_id or not upload_url:
                raise TikTokPublishError("Missing publish_id or upload_url")

            logger.info(f"Video post initiated: {publish_id}")

            return {
                'publish_id': publish_id,
                'upload_url': upload_url,
                'file_size': file_size,
                'chunk_size': chunk_size,
                'total_chunks': total_chunks,
            }

        except Exception as e:
            logger.error(f"Failed to initiate video post: {e}")
            raise TikTokPublishError(f"Init failed: {e}")

    def check_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """
        Check video processing and publishing status

        Args:
            publish_id: Publishing session ID

        Returns:
            Status dictionary with processing state
        """
        url = f"{self.config.API_BASE_URL}post/publish/status/fetch/"

        try:
            response = self.client.post(url, json={'publish_id': publish_id})
            status_data = response.get('data', {})

            status = status_data.get('status', 'UNKNOWN')
            logger.info(f"Publish status for {publish_id}: {status}")

            return {
                'status': status,
                'fail_reason': status_data.get('fail_reason'),
                'video_id': status_data.get('publiclyAvailablePostId'),
            }

        except Exception as e:
            logger.error(f"Failed to check status: {e}")
            raise

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

Add export:
```python
from .tiktok_publish_service import TikTokPublishService, TikTokPublishError
```

## API Reference

### Initialize Video Post

```
POST /v2/post/publish/video/init/
Authorization: Bearer {token}

Request:
{
  "post_info": {
    "title": "My video caption #hashtag",
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_comment": false,
    "disable_duet": false,
    "disable_stitch": false
  },
  "source_info": {
    "source": "FILE_UPLOAD",
    "video_size": 52428800,
    "chunk_size": 5242880,
    "total_chunk_count": 10
  }
}

Response:
{
  "data": {
    "publish_id": "v_pub_xxx",
    "upload_url": "https://upload.tiktok.com/video/?..."
  },
  "error": {
    "code": "ok",
    "message": ""
  }
}
```

### Privacy Levels

| Internal | TikTok API |
|----------|------------|
| public | PUBLIC_TO_EVERYONE |
| friends | MUTUAL_FOLLOW_FRIENDS |
| private | SELF_ONLY |

## Testing

```python
# Manual test
from apps.content.services import TikTokPublishService

with TikTokPublishService(access_token) as service:
    result = service.initiate_video_post(
        video_path='/path/to/video.mp4',
        caption='Test post #test',
        privacy_level='private'  # Use private for testing
    )
    print(result)
```

## Notes

- Service does NOT upload the video (Phase 03)
- Returns upload_url for chunked upload
- Status check polls for processing completion
