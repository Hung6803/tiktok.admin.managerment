# TikTok API Integration Fix - Implementation Plan

**Date:** 2025-12-15
**Status:** ⚠️ SECURITY REVIEW COMPLETE - CRITICAL ISSUES FOUND
**Priority:** CRITICAL
**Estimated Effort:** 2-3 days
**Review Date:** 2025-12-15
**Review Report:** `reports/code-reviewer-251215-tiktok-api-security-review.md`

## Executive Summary

This plan addresses critical issues in TikTok API integration preventing actual video/photo publishing. Current implementation uses simulated success responses instead of real API calls, wrong endpoints, missing OAuth scopes, and lacks chunked upload support.

## Current Issues Analysis

| # | Issue | Severity | File | Line |
|---|-------|----------|------|------|
| 1 | Celery task returns simulated success | CRITICAL | `publish_post_task.py` | 73-85 |
| 2 | Wrong video endpoint (inbox vs direct) | HIGH | `tiktok_video_service.py` | 106 |
| 3 | Missing `video.publish` scope | HIGH | `tiktok_config.py` | 22-28 |
| 4 | No chunked upload support | MEDIUM | `tiktok_video_service.py` | 138-190 |
| 5 | Photo posting service missing | MEDIUM | N/A | N/A |

## Implementation Phases

### Phase 1: Fix OAuth Scopes (30 min)
- Update `TikTokConfig.SCOPES` to include `video.publish`
- Verify existing tokens need re-authorization

### Phase 2: Create Publish Service (2 hours)
- New `TikTokPublishService` for direct posting
- Correct endpoint: `post/publish/video/init/`
- Proper privacy level mapping

### Phase 3: Implement Chunked Upload (2-3 hours)
- Calculate video_size, chunk_size, total_chunk_count
- Upload video in 5-10MB chunks
- Handle chunk upload responses

### Phase 4: Create Photo Service (1-2 hours)
- New `TikTokPhotoService` for photo carousel posting
- Endpoint: `post/publish/content/init/`
- Support up to 35 images via PULL_FROM_URL

### Phase 5: Integrate with Celery (1-2 hours)
- Replace simulated success with real API calls
- Proper error handling and status tracking
- Polling for publish status

### Phase 6: Testing & Documentation (1-2 hours)
- Unit tests for new services
- Integration test flow
- Update documentation

## Detailed File Changes

See individual phase files for implementation details:
- `phase-01-fix-scopes.md`
- `phase-02-publish-service.md`
- `phase-03-chunked-upload.md`
- `phase-04-photo-service.md`
- `phase-05-celery-integration.md`
- `phase-06-testing.md`

## TikTok API Reference

### Direct Video Post
```
POST https://open.tiktokapis.com/v2/post/publish/video/init/
Authorization: Bearer {access_token}

{
  "post_info": {
    "title": "caption",
    "privacy_level": "PUBLIC_TO_EVERYONE|MUTUAL_FOLLOW_FRIENDS|SELF_ONLY",
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
```

### Photo Carousel Post
```
POST https://open.tiktokapis.com/v2/post/publish/content/init/
Authorization: Bearer {access_token}

{
  "media_type": "PHOTO",
  "post_mode": "DIRECT_POST",
  "post_info": {
    "title": "caption",
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_comment": false
  },
  "source_info": {
    "source": "PULL_FROM_URL",
    "photo_images": ["url1", "url2", ...],
    "photo_cover_index": 0
  }
}
```

### Required Scopes
- `video.publish` - Direct video posting
- `user.info.basic` - Basic user info
- `user.info.profile` - Profile info
- `video.upload` - Upload videos (draft)
- `video.list` - List videos

## Dependencies

- Existing: `TikTokAPIClient`, `TikTokConfig`, `TikTokVideoService`
- New: `TikTokPublishService`, `TikTokPhotoService`

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Token re-auth required | Document scope change impact, notify users |
| API rate limits | Implement backoff, respect daily limits |
| Large file upload failures | Chunked upload with retry per chunk |
| Photo URL accessibility | Validate URLs accessible before API call |

## Success Criteria

1. Videos publish successfully to TikTok from scheduled posts
2. Photos/carousels publish successfully
3. Publish status accurately tracked in PublishHistory
4. Error messages provide actionable feedback
5. All existing tests pass + new tests for services

## Security Review Status

**Review Completed:** 2025-12-15
**Verdict:** ⚠️ NOT READY FOR PRODUCTION

### Critical Issues (MUST FIX)
- **C1:** Path traversal vulnerability in photo URL generation
- **C2:** Missing CRYPTOGRAPHY_KEY in .env.example
- **C3:** Unsafe token decryption fallback

### High Priority Issues
- **H1:** Missing security headers (CSP, HSTS, X-Frame-Options)
- **H2:** No rate limiting enforcement
- **H3:** Logging sensitive data (PII, IDs)

**See:** `reports/code-reviewer-251215-tiktok-api-security-review.md` for full details and fixes.

### Required Actions Before Deployment
1. Implement `sanitize_media_path()` for path traversal protection
2. Update `.env.example` with all required variables
3. Fix token decryption to raise errors (not fallback)
4. Add production security headers
5. Implement Redis-based rate limiting
6. Sanitize logs to remove PII
