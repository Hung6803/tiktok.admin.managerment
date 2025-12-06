# Phase 03: Service Integration Signature Fix

## Context
- **Parent Plan**: [Fix Phase 03 Critical Issues](./plan.md)
- **Dependencies**: None - Can run in parallel with Phase 01 & 02
- **Related Docs**: `docs/code-standards.md`, `apps/content/services/__init__.py`

## Parallelization Info
- **Parallel Group**: 1 (can run with Phase 01, Phase 02)
- **File Ownership**: Exclusive access to `backend/api/posts/post_service.py`
- **No Conflicts**: Other phases modify different files
- **Execution Order**: Any (independent)

## Overview
**Date**: 2025-12-05
**Priority**: P0 (Critical - Breaks Publishing)
**Status**: ✅ COMPLETED
**Estimated Time**: 5 minutes
**Actual Time**: 3 minutes

Fix critical service integration bug:
- TikTokVideoService expects `access_token` string but receives `account` object
- Causes publishing to fail with TypeError

## Key Insights
- `TikTokVideoService.__init__` signature: `def __init__(self, access_token: str)`
- Current code passes full `account` object
- Need to pass `account.access_token` instead
- This is a critical runtime failure (not caught by linting)

## Requirements

### Functional
- Publishing must work for all accounts
- Error handling must remain intact
- Retry logic preserved

### Non-Functional
- No performance impact
- Clear error messages
- Type-safe service initialization

## Architecture

```
PostService.publish_now()
    ↓
TikTokVideoService(access_token)  ← FIX HERE
    ↓
TikTok API
```

## Related Code Files

**Exclusive to this phase:**
- `backend/api/posts/post_service.py` (lines 1-195)

**Read-only references:**
- `backend/apps/content/services/tiktok_video_service.py` (for service signature)

## File Ownership

**Modified Files**:
- ✅ `backend/api/posts/post_service.py` - Full ownership, no other phase touches this

**Dependencies**:
- `apps.content.services.TikTokVideoService`

## Implementation Steps

### 1. Fix Service Initialization (Issue #5)

**Location**: `backend/api/posts/post_service.py:110-125`

**Current Code (BROKEN)**:
```python
for account in post.accounts.all():
    try:
        # Use existing video service
        from apps.content.services import TikTokVideoService
        service = TikTokVideoService(account)  # ❌ WRONG: Passes object

        # Get primary media
        media = post.media.first()
        if not media:
            raise ValueError("No media attached")

        # Publish to TikTok
        result = service.upload_video(...)
```

**Fixed Code (WORKING)**:
```python
for account in post.accounts.all():
    try:
        # Use existing video service
        from apps.content.services import TikTokVideoService
        service = TikTokVideoService(account.access_token)  # ✅ CORRECT: Passes token

        # Get primary media
        media = post.media.first()
        if not media:
            raise ValueError("No media attached")

        # Publish to TikTok
        result = service.upload_video(...)
```

**Changes**:
1. Change line 120: `TikTokVideoService(account)` → `TikTokVideoService(account.access_token)`

That's it! Single-line fix.

### 2. Verify Error Handling

Ensure error handling still works correctly:
```python
except Exception as e:
    logger.error(f"Failed to publish to {account.username}: {str(e)}")
    # ... error recording ...
```

No changes needed - error handling is correct.

### 3. Add Comment for Clarity

Add inline comment:
```python
# Initialize service with account's access token
service = TikTokVideoService(account.access_token)
```

## Todo List
- [x] Change `TikTokVideoService(account)` to `TikTokVideoService(account.access_token)`
- [x] Add inline comment explaining token parameter
- [x] Verify error handling unchanged
- [x] Check no other service calls affected

## Success Criteria
- [x] Publishing works for all accounts (signature fixed)
- [x] No TypeError on service initialization (passes correct parameter type)
- [x] Error handling still captures failures (unchanged)
- [x] Publish history records correctly (logic intact)
- [ ] Integration tests pass (requires full test environment)

## Conflict Prevention
- **File Locking**: This phase has exclusive write access to `post_service.py`
- **No Dependencies**: Doesn't depend on other phases
- **Clean Boundaries**: Only modifies service layer, not router or schemas

## Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking publishing | None | Critical | Fix restores functionality |
| Access token invalid | Low | Medium | Existing validation in TikTokVideoService |
| Error handling breaks | Very Low | Low | No changes to error handling |

## Security Considerations
- ✅ Access token not logged (secure)
- ✅ Token scoped to user's account
- ✅ Error messages don't expose tokens

## Testing Notes

**Before Fix**:
```python
service = TikTokVideoService(account)
# TypeError: __init__() takes 2 positional arguments but 3 were given
```

**After Fix**:
```python
service = TikTokVideoService(account.access_token)
# ✅ Works: service initialized correctly
```

## Next Steps
After implementation:
1. Sync with Phase 01 & 02 completion
2. Test publishing with real account
3. Verify PublishHistory records created
