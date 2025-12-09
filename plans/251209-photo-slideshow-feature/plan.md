# Photo Slideshow Posting Feature

**Created:** 2025-12-09
**Status:** In Progress (Phase 02 Complete)
**Last Updated:** 2025-12-10
**Priority:** High

## Overview

Implement photo slideshow posting to TikTok. Since TikTok API doesn't support native photo carousels, images are converted to video using FFmpeg before upload.

## Architecture

```
Images → Validation → FFmpeg Conversion → Video File → TikTok Video Upload API
```

## Phases

| Phase | Description | Status | Link |
|-------|-------------|--------|------|
| 01 | Backend Service & Model Updates | Pending | [phase-01-backend-service.md](phase-01-backend-service.md) |
| 02 | API Endpoints | Complete | [phase-02-api-endpoints.md](phase-02-api-endpoints.md) |
| 03 | Frontend Components | Pending | [phase-03-frontend-components.md](phase-03-frontend-components.md) |

## Key Decisions

1. **Conversion Approach:** FFmpeg CLI (reliable, well-tested)
2. **Processing:** Async via Celery (non-blocking)
3. **Image Limits:** 2-10 images per slideshow
4. **Duration:** 3-5 seconds per image (configurable)
5. **Output:** MP4 H.264, 1080x1920 (9:16)

## Dependencies

- FFmpeg installed on server
- Existing TikTokVideoService
- Celery for async processing
