# Phase 01: Fix OAuth Scopes

**Duration:** 30 minutes
**Priority:** HIGH
**Dependencies:** None

## Objective

Add missing `video.publish` scope required for direct video posting.

## Current State

File: `backend/config/tiktok_config.py` (lines 22-28)

```python
SCOPES = [
    'user.info.basic',
    'user.info.profile',
    'user.info.stats',
    'video.upload',      # Only allows draft upload
    'video.list',
]
```

## Target State

```python
SCOPES = [
    'user.info.basic',
    'user.info.profile',
    'user.info.stats',
    'video.upload',
    'video.publish',     # ADD: Required for direct posting
    'video.list',
]
```

## Implementation Steps

### Step 1: Update TikTokConfig

**File:** `backend/config/tiktok_config.py`

```python
# Line 21-29 - Add video.publish scope
SCOPES = [
    'user.info.basic',       # Basic user information
    'user.info.profile',     # Profile info
    'user.info.stats',       # Stats (followers, videos)
    'video.upload',          # Video upload (draft)
    'video.publish',         # Direct video posting (NEW)
    'video.list',            # List user videos
]
```

### Step 2: Add Privacy Level Constants

**File:** `backend/config/tiktok_config.py`

Add below existing constants (after line 58):

```python
# TikTok Privacy Levels (for API compatibility)
PRIVACY_LEVELS = {
    'public': 'PUBLIC_TO_EVERYONE',
    'friends': 'MUTUAL_FOLLOW_FRIENDS',
    'private': 'SELF_ONLY',
}

@classmethod
def get_api_privacy_level(cls, privacy: str) -> str:
    """Map internal privacy to TikTok API privacy level"""
    return cls.PRIVACY_LEVELS.get(privacy, 'PUBLIC_TO_EVERYONE')
```

## Impact Assessment

### Re-authorization Required

Existing TikTok accounts will need re-authorization to gain `video.publish` scope:

1. Current tokens lack `video.publish` permission
2. Users must disconnect and reconnect accounts
3. Or implement scope upgrade flow (optional enhancement)

### Migration Strategy

**Option A (Simple):**
- Notify users scope change
- Direct to re-authorize accounts

**Option B (Advanced):**
- Add `has_publish_scope` field to TikTokAccount
- Track which accounts have new scope
- Prompt upgrade when publishing

## Verification

```bash
# Verify scope string includes video.publish
cd backend
python -c "from config.tiktok_config import TikTokConfig; print(TikTokConfig.get_scope_string())"
# Expected: user.info.basic,user.info.profile,user.info.stats,video.upload,video.publish,video.list
```

## TikTok Developer Portal

Ensure `video.publish` scope is enabled in TikTok Developer Portal:
1. Go to TikTok Developer Portal > Your App
2. Navigate to Scopes section
3. Enable `video.publish` if not already enabled
4. Submit for review if required

## Notes

- `video.publish` may require additional app review by TikTok
- Scope enables direct posting (bypasses creator's inbox)
- Users see published content immediately on their profile
