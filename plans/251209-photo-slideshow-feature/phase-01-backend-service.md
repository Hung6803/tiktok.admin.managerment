# Phase 01: Backend Service & Model Updates

**Status:** Pending
**Priority:** High

## Context

Create backend service to convert images to video slideshow using FFmpeg.

## Requirements

1. PhotoSlideShowService - converts images to MP4
2. Update PostMedia model for slideshow metadata
3. Celery task for async conversion
4. Image validation (format, size, dimensions)

## Implementation Steps

### 1.1 Create PhotoSlideShowService

**File:** `backend/apps/content/services/photo_slideshow_service.py`

```python
# Service that:
# - Validates images (JPG, PNG, WebP)
# - Resizes to 1080x1920 (9:16)
# - Converts to MP4 using FFmpeg
# - Returns video file path
```

Key methods:
- `validate_images()` - Check format, size, count (2-10)
- `prepare_images()` - Resize/pad to 1080x1920
- `create_slideshow()` - FFmpeg conversion
- `cleanup()` - Remove temp files

### 1.2 Update PostMedia Model

**File:** `backend/apps/content/models/post_media_model.py`

Add fields:
- `carousel_order` - Image sequence position
- `image_duration_ms` - Display time per image
- `is_slideshow_source` - Flag for source images

### 1.3 Create Celery Task

**File:** `backend/apps/scheduler/tasks/convert_slideshow_task.py`

```python
# Async task that:
# - Fetches source images
# - Calls PhotoSlideShowService
# - Updates post with converted video
# - Cleans up temp files
```

### 1.4 Update TikTok Config

**File:** `backend/config/tiktok_config.py`

Add slideshow constants:
- `SLIDESHOW_IMAGE_DURATION_MS = 4000`
- `SLIDESHOW_MIN_IMAGES = 2`
- `SLIDESHOW_MAX_IMAGES = 10`
- `SLIDESHOW_OUTPUT_FORMAT = 'mp4'`

## Related Files

- `backend/apps/content/services/tiktok_video_service.py` - Existing video upload
- `backend/api/media/processing_service.py` - Media processing utils
- `backend/config/tiktok_config.py` - Config constants

## Success Criteria

- [ ] Images validated correctly
- [ ] FFmpeg converts images to MP4
- [ ] Video meets TikTok specs (1080x1920, H.264)
- [ ] Celery task runs async
- [ ] Temp files cleaned up
