# Phase 03: Implement Chunked Video Upload

**Duration:** 2-3 hours
**Priority:** HIGH
**Dependencies:** Phase 02

## Objective

Implement chunked video upload per TikTok API requirements.

## Problem

Current `upload_video_file()` streams entire file - TikTok API requires:
- `video_size`, `chunk_size`, `total_chunk_count` in init request
- Sequential chunk uploads with byte ranges

## Implementation

### Update: `backend/apps/content/services/tiktok_publish_service.py`

Add methods to existing `TikTokPublishService` class:

```python
def upload_video_chunks(
    self,
    upload_url: str,
    video_path: str,
    chunk_size: int,
    total_chunks: int
) -> bool:
    """
    Upload video file in chunks

    Args:
        upload_url: URL from initiate_video_post
        video_path: Path to video file
        chunk_size: Size of each chunk in bytes
        total_chunks: Total number of chunks

    Returns:
        True if all chunks uploaded successfully

    Raises:
        TikTokPublishError: On upload failure
    """
    video_file = Path(video_path)
    file_size = video_file.stat().st_size

    logger.info(f"Starting chunked upload: {total_chunks} chunks")

    try:
        with open(video_path, 'rb') as f:
            for chunk_index in range(total_chunks):
                # Calculate byte range
                start_byte = chunk_index * chunk_size
                end_byte = min(start_byte + chunk_size, file_size) - 1
                current_chunk_size = end_byte - start_byte + 1

                # Read chunk
                f.seek(start_byte)
                chunk_data = f.read(current_chunk_size)

                # Upload chunk
                success = self._upload_single_chunk(
                    upload_url=upload_url,
                    chunk_data=chunk_data,
                    start_byte=start_byte,
                    end_byte=end_byte,
                    file_size=file_size,
                    chunk_index=chunk_index,
                    total_chunks=total_chunks
                )

                if not success:
                    raise TikTokPublishError(
                        f"Chunk {chunk_index + 1}/{total_chunks} failed"
                    )

                logger.info(
                    f"Uploaded chunk {chunk_index + 1}/{total_chunks} "
                    f"({current_chunk_size} bytes)"
                )

        logger.info("Chunked upload completed successfully")
        return True

    except IOError as e:
        logger.error(f"File read error: {e}")
        raise TikTokPublishError(f"File error: {e}")

def _upload_single_chunk(
    self,
    upload_url: str,
    chunk_data: bytes,
    start_byte: int,
    end_byte: int,
    file_size: int,
    chunk_index: int,
    total_chunks: int,
    max_retries: int = 3
) -> bool:
    """
    Upload single chunk with retry logic

    Args:
        upload_url: TikTok upload URL
        chunk_data: Chunk bytes
        start_byte: Start byte position
        end_byte: End byte position
        file_size: Total file size
        chunk_index: Current chunk index
        total_chunks: Total chunk count
        max_retries: Max retry attempts

    Returns:
        True if upload successful
    """
    import requests

    headers = {
        'Content-Type': 'video/mp4',
        'Content-Length': str(len(chunk_data)),
        'Content-Range': f'bytes {start_byte}-{end_byte}/{file_size}',
    }

    for attempt in range(max_retries):
        try:
            response = requests.put(
                upload_url,
                data=chunk_data,
                headers=headers,
                timeout=self.config.UPLOAD_TIMEOUT
            )

            # TikTok returns 200 for success, 206 for partial
            if response.status_code in [200, 201, 206]:
                return True

            logger.warning(
                f"Chunk upload returned {response.status_code}, "
                f"attempt {attempt + 1}/{max_retries}"
            )

        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Chunk upload error: {e}, "
                f"attempt {attempt + 1}/{max_retries}"
            )

            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff

    return False
```

### Add Complete Publish Flow Method

```python
def publish_video(
    self,
    video_path: str,
    caption: str = '',
    privacy_level: str = 'public',
    disable_comment: bool = False,
    disable_duet: bool = False,
    disable_stitch: bool = False,
    poll_interval: int = 5,
    max_poll_attempts: int = 60
) -> Dict[str, Any]:
    """
    Complete video publishing flow

    Args:
        video_path: Path to video file
        caption: Video caption
        privacy_level: Privacy setting
        disable_comment: Disable comments
        disable_duet: Disable duet
        disable_stitch: Disable stitch
        poll_interval: Seconds between status checks
        max_poll_attempts: Max status check attempts

    Returns:
        Dictionary with success status and video_id
    """
    import time

    # Step 1: Initialize post
    init_result = self.initiate_video_post(
        video_path=video_path,
        caption=caption,
        privacy_level=privacy_level,
        disable_comment=disable_comment,
        disable_duet=disable_duet,
        disable_stitch=disable_stitch
    )

    publish_id = init_result['publish_id']
    upload_url = init_result['upload_url']

    # Step 2: Upload chunks
    self.upload_video_chunks(
        upload_url=upload_url,
        video_path=video_path,
        chunk_size=init_result['chunk_size'],
        total_chunks=init_result['total_chunks']
    )

    # Step 3: Poll for status
    for attempt in range(max_poll_attempts):
        status = self.check_publish_status(publish_id)

        if status['status'] == 'PUBLISH_COMPLETE':
            logger.info(f"Video published: {status.get('video_id')}")
            return {
                'success': True,
                'video_id': status.get('video_id'),
                'publish_id': publish_id,
            }

        if status['status'] in ['FAILED', 'PUBLISH_FAILED']:
            reason = status.get('fail_reason', 'Unknown')
            logger.error(f"Publish failed: {reason}")
            return {
                'success': False,
                'error': reason,
                'publish_id': publish_id,
            }

        if status['status'] == 'PROCESSING_UPLOAD':
            logger.info(f"Processing... ({attempt + 1}/{max_poll_attempts})")
            time.sleep(poll_interval)
            continue

        # Unknown status, continue polling
        time.sleep(poll_interval)

    # Timeout
    logger.error(f"Publish timeout after {max_poll_attempts * poll_interval}s")
    return {
        'success': False,
        'error': 'Processing timeout',
        'publish_id': publish_id,
    }
```

## Chunk Upload Protocol

### Headers Required

```
Content-Type: video/mp4
Content-Length: {chunk_size}
Content-Range: bytes {start}-{end}/{total_size}
```

### Example Chunks (50MB file, 5MB chunks)

| Chunk | Content-Range |
|-------|---------------|
| 1 | bytes 0-5242879/52428800 |
| 2 | bytes 5242880-10485759/52428800 |
| 3 | bytes 10485760-15728639/52428800 |
| ... | ... |
| 10 | bytes 47185920-52428799/52428800 |

## Status Values

| Status | Meaning | Action |
|--------|---------|--------|
| PROCESSING_UPLOAD | Video processing | Continue polling |
| PUBLISH_COMPLETE | Success | Return video_id |
| FAILED | Failed | Return error |
| PUBLISH_FAILED | Publish failed | Return error |

## Testing

```python
# Integration test
from apps.content.services import TikTokPublishService

with TikTokPublishService(access_token) as service:
    result = service.publish_video(
        video_path='/path/to/test.mp4',
        caption='Test video #test',
        privacy_level='private'
    )

    if result['success']:
        print(f"Published! Video ID: {result['video_id']}")
    else:
        print(f"Failed: {result['error']}")
```

## Error Handling

- Network errors: Retry with exponential backoff
- Chunk failure: Retry individual chunk (3 attempts)
- Processing timeout: Return error, allow manual retry
- Invalid video: Return TikTok error message
