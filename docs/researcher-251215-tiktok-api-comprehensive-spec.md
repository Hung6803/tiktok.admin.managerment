# TikTok API Comprehensive Technical Specification
## Research Report | December 15, 2025

---

## Executive Summary

This document provides authoritative technical specifications for TikTok Login Kit Web, OAuth 2.0 token management, and Content Posting API (direct post and uploads). Based on official TikTok developer documentation, this guide covers exact endpoints, headers, request/response formats, error handling, rate limits, and implementation best practices.

**Key Focus Areas:**
- OAuth 2.0 authorization code flow
- Token lifecycle management (access, refresh, expiration)
- Direct video/photo posting endpoints
- Content upload mechanisms (chunked file upload)
- Error codes and failure scenarios
- Rate limiting and retry strategies

---

## Part 1: OAuth 2.0 Authentication

### 1.1 Authorization Flow Overview

TikTok implements standard OAuth 2.0 authorization code flow with PKCE-optional support. The flow consists of:
1. User redirects to TikTok authorization endpoint
2. User grants permissions (scopes)
3. TikTok redirects back with authorization code
4. Backend exchanges code for access token + refresh token
5. Store tokens securely (encrypted at rest)

### 1.2 Authorization Endpoint

**URL:** `https://www.tiktok.com/v2/auth/authorize/`

**Method:** GET (user-facing redirect)

**Required Query Parameters:**

| Parameter | Type | Required | Max Length | Description |
|-----------|------|----------|------------|-------------|
| `client_key` | string | Yes | - | Your app's unique identifier (issued by TikTok) |
| `scope` | string | Yes | - | Comma-separated permissions (no spaces) |
| `response_type` | string | Yes | - | Always `code` |
| `redirect_uri` | string | Yes | 512 chars | Must be HTTPS, pre-registered, no query params/fragments |
| `state` | string | Yes | - | CSRF token - must be cryptographically random |
| `disable_auto_auth` | integer | No | - | 0 = skip auth if session valid; 1 = always show auth page |

**Authorization URL Example:**

```
https://www.tiktok.com/v2/auth/authorize/?client_key=YOUR_CLIENT_KEY&scope=user.info.basic,video.publish&response_type=code&redirect_uri=https%3A%2F%2Fyourappdomain.com%2Fcallback&state=RANDOM_STATE_TOKEN&disable_auto_auth=0
```

### 1.3 State Parameter Requirements

**CRITICAL for CSRF Protection:**

- Generate using cryptographically secure random source
- Minimum 32 characters recommended (e.g., `secrets.token_urlsafe(32)` in Python)
- Must be compared using constant-time comparison on callback (prevent timing attacks)
- Store in session/cache with expiration (15-30 minutes recommended)
- Reject if state doesn't match OR expired

**Implementation Reference:**
```python
import secrets
from datetime import datetime, timedelta

# Generation
state = secrets.token_urlsafe(32)  # 43-character URL-safe string

# Storage (with expiration)
cache.set(f'oauth_state:{state}', {
    'timestamp': datetime.now(),
    'expires_in': 30  # minutes
})

# Validation
stored_state = cache.get(f'oauth_state:{received_state}')
if not stored_state or datetime.now() - stored_state['timestamp'] > timedelta(minutes=30):
    raise ValueError("State expired or invalid")

if not secrets.compare_digest(received_state, state):
    raise ValueError("CSRF: State mismatch")
```

### 1.4 Redirect URI Constraints

- Must be absolute HTTPS URL (no HTTP in production)
- Cannot include query parameters or URL fragments
- Maximum 10 URIs per app (configured in Developer Portal)
- Length limit: 512 characters
- Must match EXACTLY what's registered (case-sensitive, protocol-sensitive)
- If using multiple URIs: each must be separately registered

**Valid Examples:**
- ✅ `https://myapp.com/oauth/callback`
- ✅ `https://api.myapp.com/v1/tiktok/auth/callback`
- ✅ `https://myapp.com:8080/oauth/callback` (explicit port)

**Invalid Examples:**
- ❌ `https://myapp.com/oauth/callback?param=value` (query params)
- ❌ `https://myapp.com/oauth/callback#section` (fragments)
- ❌ `http://myapp.com/oauth/callback` (not HTTPS)
- ❌ `myapp.com/oauth/callback` (missing protocol)

### 1.5 Required Scopes

All scopes must be requested upfront (during app registration) and user must authorize. Cannot request additional scopes later without re-authorization.

**Core User Information Scopes:**

| Scope | Description | Notes |
|-------|-------------|-------|
| `user.info.basic` | Open ID, avatar, display name | Most basic; required for most flows |
| `user.info.profile` | Website link, bio, verification status | Profile customization info |
| `user.info.stats` | Follower count, following, likes, video count | Analytics data |

**Content Management Scopes:**

| Scope | Description | Notes |
|-------|-------------|-------|
| `video.upload` | Upload videos as draft (not published) | Use for draft videos |
| `video.list` | List user's published videos | Query existing content |
| `video.publish` | Direct publish videos/photos (full API) | **Critical for posting** |

**Content Posting Scope Detail:**
- `video.publish` is primary scope for Content Posting API
- Required for direct post endpoints
- Required for draft uploads that become published
- Both developer AND user must authorize

**Scope Request Format:**
```
scope=user.info.basic,user.info.profile,video.publish
```
**Important:** No spaces, comma-separated, exact names

### 1.6 OAuth Callback Handling

**TikTok Redirects User Back To Your Registered URI With:**

**Success Case:**
```
https://yourappdomain.com/callback?code=AUTH_CODE_HERE&scopes=user.info.basic,video.publish&state=YOUR_STATE_TOKEN
```

**Parameters Returned:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Authorization code (valid ~10 minutes) |
| `scopes` | string | Comma-separated actually-granted scopes (may differ from request if user denies some) |
| `state` | string | Your state parameter echoed back |

**Error Case:**
```
https://yourappdomain.com/callback?error=access_denied&error_description=user+canceled+auth&state=YOUR_STATE_TOKEN
```

**Error Parameters:**
| Parameter | Description |
|-----------|-------------|
| `error` | Error code (access_denied, server_error, etc.) |
| `error_description` | User-friendly error description |
| `state` | Your state parameter echoed back |

### 1.7 Token Exchange Endpoint

**URL:** `https://open.tiktokapis.com/v2/oauth/token/`

**Method:** POST

**Content-Type:** `application/json`

**Request Body (Authorization Code Exchange):**
```json
{
  "client_key": "your_client_key",
  "client_secret": "your_client_secret_keep_private",
  "code": "authorization_code_from_callback",
  "grant_type": "authorization_code",
  "redirect_uri": "https://yourappdomain.com/callback"
}
```

**Required Fields:**
- `client_key`: App ID from TikTok Developer Portal
- `client_secret`: **NEVER expose to frontend** - server-side only
- `code`: From OAuth callback (10-minute validity)
- `grant_type`: Literal string `"authorization_code"`
- `redirect_uri`: Must match the URI where user landed

**Success Response (200 OK):**
```json
{
  "data": {
    "access_token": "v.XXXXXXXXXXX",
    "refresh_token": "v.XXXXXXXXXXX",
    "expires_in": 86400,
    "scope": "user.info.basic,video.publish",
    "open_id": "1234567890123456789",
    "token_type": "Bearer"
  },
  "error": {
    "code": "ok",
    "log_id": "log_identifier_for_support"
  }
}
```

**Token Field Details:**
| Field | Type | Lifetime | Notes |
|-------|------|----------|-------|
| `access_token` | string | 86400 sec (24 hrs) | Use in Authorization header |
| `refresh_token` | string | 365 days | Use to renew access_token |
| `expires_in` | integer | - | Seconds until access_token expires |
| `open_id` | string | N/A | TikTok user identifier |
| `scope` | string | - | Granted scopes (may differ from request) |

**Error Response (400 Bad Request):**
```json
{
  "data": null,
  "error": {
    "code": "invalid_grant",
    "log_id": "log_id_here"
  }
}
```

**Common Error Codes:**
| Code | Cause | Action |
|------|-------|--------|
| `invalid_grant` | Code expired (>10 min), already used, or invalid | Restart OAuth flow |
| `invalid_request` | Missing/invalid parameters | Verify all required fields |
| `invalid_client` | Invalid client_key or client_secret | Check credentials in portal |
| `access_denied` | User denied during authorization | Inform user; retry required |

---

## Part 2: Token Management & Refresh

### 2.1 Token Lifecycle

**Access Token Lifespan:**
- **Default:** 86,400 seconds (24 hours)
- **Strategy:** Always use `expires_in` from response (don't hardcode 24h)
- **Proactive Refresh:** Refresh 5 minutes before expiration (86,100 seconds)

**Refresh Token Lifespan:**
- **Duration:** 365 days (approximately 1 year)
- **Rotation:** May be rotated on refresh (some providers do, TikTok may)
- **Storage:** Encrypt at rest using application key material
- **Invalidation:** Token revoked if user disconnects account or changes password

### 2.2 Token Refresh Flow

**When to Refresh:**
1. **Proactive:** Before expiration (5 min buffer)
2. **Reactive:** When API returns 401 Unauthorized

**Refresh Token Endpoint:**

**URL:** `https://open.tiktokapis.com/v2/oauth/token/`

**Method:** POST

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "client_key": "your_client_key",
  "client_secret": "your_client_secret",
  "grant_type": "refresh_token",
  "refresh_token": "existing_refresh_token_from_storage"
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "access_token": "v.NEW_ACCESS_TOKEN",
    "refresh_token": "v.POSSIBLY_NEW_REFRESH_TOKEN",
    "expires_in": 86400,
    "scope": "user.info.basic,video.publish",
    "token_type": "Bearer"
  },
  "error": {
    "code": "ok"
  }
}
```

**Key Behavior:**
- New `access_token` is always issued
- `refresh_token` may be rotated (use the new one if provided)
- If no new refresh_token in response, keep using the old one
- `expires_in` always in response (use for calculating expiration)

**Error Response on Invalid Refresh Token:**
```json
{
  "data": null,
  "error": {
    "code": "invalid_grant",
    "log_id": "..."
  }
}
```

**Failure Handling:**
- Refresh token invalid/expired → Restart OAuth flow
- Server error (5xx) → Retry with exponential backoff
- Network timeout → Retry with exponential backoff
- Max retries exceeded → Mark token as invalid; notify user

### 2.3 Token Storage Security

**DO:**
- ✅ Store refresh_token encrypted at rest (AES-256 recommended)
- ✅ Use application-level encryption keys (rotate annually)
- ✅ Hash token values before storing in audit logs
- ✅ Use HTTPS for all token transmission
- ✅ Implement access control (tokens tied to specific user account)
- ✅ Set secure HTTP-only cookies if using session-based approach
- ✅ Implement token rotation policy (refresh every 90 days minimum)
- ✅ Log token access attempts (for security monitoring)

**DON'T:**
- ❌ Store tokens in browser localStorage (XSS vulnerable)
- ❌ Log plaintext tokens anywhere
- ❌ Hardcode tokens in code
- ❌ Send tokens in URL query parameters
- ❌ Transmit over HTTP
- ❌ Store multiple years of token history
- ❌ Share tokens between users
- ❌ Trust token values from client-submitted requests

**Database Schema Pattern (Encrypted):**
```sql
CREATE TABLE user_tiktok_accounts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    open_id VARCHAR(255) NOT NULL UNIQUE,

    -- Encrypted at application layer
    access_token_encrypted BYTEA NOT NULL,
    refresh_token_encrypted BYTEA NOT NULL,

    -- Metadata (unencrypted, for operational queries)
    token_expires_at TIMESTAMP NOT NULL,
    token_refreshed_at TIMESTAMP NOT NULL,

    -- Tracking
    scopes_granted TEXT[] NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_error TEXT,
    error_count INT DEFAULT 0,

    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_token_expires (token_expires_at)
);
```

### 2.4 Proactive Token Refresh Strategy

**Recommended Approach:**

1. **Calculate Refresh Time:**
```python
from datetime import datetime, timedelta
from django.utils import timezone

def calculate_refresh_time(expires_in_seconds: int) -> datetime:
    """Calculate when to refresh (5 min before expiration)"""
    buffer_seconds = 300  # 5 minutes
    return timezone.now() + timedelta(seconds=expires_in_seconds - buffer_seconds)
```

2. **Background Job (Celery Task):**
```python
@periodic_task(run_every=crontab(minute='*/5'))  # Check every 5 minutes
def refresh_expiring_tokens():
    """Proactively refresh tokens expiring soon"""
    now = timezone.now()

    accounts = TikTokAccount.objects.filter(
        token_expires_at__lte=now + timedelta(seconds=300),  # Refresh window
        token_expires_at__gt=now  # Not already expired
    )

    for account in accounts:
        try:
            new_tokens = refresh_access_token(account.refresh_token)
            account.access_token = new_tokens['access_token']
            account.refresh_token = new_tokens.get('refresh_token')
            account.token_expires_at = calculate_expiration_time(new_tokens['expires_in'])
            account.save()
        except Exception as e:
            account.error_count += 1
            account.last_error = str(e)
            account.save()
            logger.error(f"Failed to refresh token for {account.open_id}: {e}")
```

3. **Reactive Fallback:**
```python
def api_call_with_retry(endpoint: str, access_token: str) -> dict:
    """Make API call with automatic retry on 401"""
    try:
        return make_api_call(endpoint, access_token)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            # Token likely expired; refresh and retry once
            new_token = refresh_access_token(account.refresh_token)
            account.access_token = new_token['access_token']
            account.save()
            return make_api_call(endpoint, new_token['access_token'])
        raise
```

---

## Part 3: Content Posting API - Overview

### 3.1 API Prerequisites & Requirements

**Application Requirements:**
- Registered app in TikTok Developer Portal
- Content Posting API product added to app
- `video.publish` scope approved AND authorized by user
- User access token (from OAuth flow above)
- User open_id (returned during token exchange)

**Content Restrictions:**
- **Unaudited clients:** All posts restricted to PRIVATE (visible only to user)
- **Audited clients:** Can post to PUBLIC_TO_EVERYONE
- **Audit Process:** Apply via developer portal; requires compliance review (1-4 weeks typically)
- **Public vs. Private:** Determined by `privacy_level` in request

**Rate Limits (Critical):**
| Resource | Limit | Window | Notes |
|----------|-------|--------|-------|
| Token initialization requests | 6 requests | Per minute | Per user access token |
| Video uploads per account | 15 videos | Per 24 hours | Daily quota |
| Status checks | Included in general limit | - | Counts toward 6/min limit |

**Key Point:** All 6 requests/minute limit is for initialization. Upload itself doesn't count, only init requests.

### 3.2 Authentication Headers (All Endpoints)

```
Authorization: Bearer {user_access_token}
Content-Type: application/json; charset=UTF-8
```

**Example:**
```
GET https://open.tiktokapis.com/v2/post/publish/status/fetch/
Authorization: Bearer v.c0e1234567890abcdef
Content-Type: application/json; charset=UTF-8
```

### 3.3 Base API URL

```
https://open.tiktokapis.com/v2/
```

All endpoint paths are relative to this base.

---

## Part 4: Direct Video Posting

### 4.1 Direct Video Post Initialization Endpoint

**Purpose:** Initialize a direct video post (bypass draft upload step). Used when posting pre-transcoded videos.

**URL:** `https://open.tiktokapis.com/v2/post/publish/video/init/`

**Method:** POST

**Scope Required:** `video.publish`

**Rate Limit:** 6 requests per minute per user access token

### 4.2 Request Body Structure

```json
{
  "post_info": {
    "title": "Your video caption here",
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_comment": false,
    "disable_duet": false,
    "disable_stitch": false,
    "video_cover_timestamp_ms": 1000,
    "brand_content_toggle": false,
    "brand_organic_toggle": false,
    "is_aigc": false
  },
  "source_info": {
    "source": "FILE_UPLOAD",
    "video_size": 52428800,
    "chunk_size": 5242880,
    "total_chunk_count": 10
  }
}
```

### 4.3 Post Info Parameters

| Parameter | Type | Required | Max Length | Notes |
|-----------|------|----------|------------|-------|
| `title` | string | No | 2200 UTF-16 runes | Video caption/description |
| `privacy_level` | string | Yes | - | Must match creator's options from creator_info API |
| `disable_comment` | boolean | No | - | Disable user comments (default false) |
| `disable_duet` | boolean | No | - | Disable duet feature (default false) |
| `disable_stitch` | boolean | No | - | Disable stitch feature (default false) |
| `video_cover_timestamp_ms` | integer | No | - | Frame to use as cover (milliseconds) |
| `brand_content_toggle` | boolean | No | - | Mark as branded content (requires brand partnership) |
| `brand_organic_toggle` | boolean | No | - | Mark as brand organic content |
| `is_aigc` | boolean | No | - | Mark as AI-generated content (transparency) |

**Privacy Level Options:**
- `PRIVATE` - Only visible to user
- `FRIENDS_ONLY` - Only visible to friends
- `PUBLIC_TO_EVERYONE` - Publicly visible (unaudited apps get PRIVATE)

**Caption Length Calculation:**
- 2200 UTF-16 runes (not characters)
- Emoji count as 2+ runes each
- Best practice: Keep under 1500 characters for safety

### 4.4 Source Info Parameters (FILE_UPLOAD)

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `source` | string | Yes | Literal `"FILE_UPLOAD"` |
| `video_size` | integer | Yes | Total file size in bytes |
| `chunk_size` | integer | Yes | Size of each chunk in bytes |
| `total_chunk_count` | integer | Yes | Number of chunks (size / chunk_count = chunk_size) |

**Chunk Size Recommendations:**
- Standard: 5-10 MB chunks (5242880 - 10485760 bytes)
- Minimum: 1 MB (1048576 bytes)
- Maximum: 50 MB (52428800 bytes)
- For reliable streaming: 5 MB chunks

**Calculation Example:**
```
File: 52 MB video
Chunk size: 5 MB (5242880 bytes)
Total size: 52428800 bytes (52 * 1024 * 1024)
Chunk count: 52428800 / 5242880 = 10 chunks
```

### 4.5 Source Info (PULL_FROM_URL)

For posting video from URL (domain must be pre-verified):

```json
{
  "source_info": {
    "source": "PULL_FROM_URL",
    "video_url": "https://verified-domain.com/videos/my_video.mp4"
  }
}
```

### 4.6 Success Response (200 OK)

```json
{
  "data": {
    "publish_id": "p_pub_url~v2.XXXXXXXXXXXXXXXXXX",
    "upload_url": "https://upload.tiktokapis.com/upload/v1/video/?upload_id=XXXXX",
    "upload_url_expires_in": 3600
  },
  "error": {
    "code": "ok",
    "log_id": "REQUEST_ID_FOR_SUPPORT"
  }
}
```

**Response Fields:**
| Field | Type | Notes |
|-------|------|-------|
| `publish_id` | string | Unique identifier for this publishing session (max 64 chars) |
| `upload_url` | string | Pre-signed URL for uploading video (valid 1 hour) |
| `upload_url_expires_in` | integer | URL validity in seconds |

**Critical:** Upload must complete within 1 hour or URL becomes invalid (need to re-initialize).

### 4.7 Error Responses

**403 Unaudited Client:**
```json
{
  "data": null,
  "error": {
    "code": "forbidden",
    "message": "Unaudited client can only post to private accounts",
    "log_id": "..."
  }
}
```

**Action:** Only post to PRIVATE privacy_level until app is audited.

**403 Privacy Level Mismatch:**
```json
{
  "data": null,
  "error": {
    "code": "forbidden",
    "message": "Privacy level option mismatch",
    "log_id": "..."
  }
}
```

**Action:** Query creator info to get available privacy levels.

**401 Scope Not Authorized:**
```json
{
  "data": null,
  "error": {
    "code": "unauthorized",
    "message": "The scope video.publish is not authorized for this user",
    "log_id": "..."
  }
}
```

**Action:** User must re-authorize with `video.publish` scope.

**429 Rate Limit Exceeded:**
```json
{
  "data": null,
  "error": {
    "code": "too_many_requests",
    "message": "Rate limit exceeded: 6 requests per minute",
    "log_id": "..."
  }
}
```

**Action:** Wait 60 seconds, retry with exponential backoff.

**400 Invalid Parameters:**
```json
{
  "data": null,
  "error": {
    "code": "invalid_request",
    "message": "Invalid video_size: must be between 100 and 52428800 bytes",
    "log_id": "..."
  }
}
```

### 4.8 HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Process response normally |
| 400 | Bad request (validation error) | Fix request parameters |
| 401 | Unauthorized (token/scope issue) | Refresh token or re-auth |
| 403 | Forbidden (audit/privacy issue) | Check app status; check privacy level |
| 429 | Rate limit | Retry with exponential backoff |
| 500 | Server error | Retry with exponential backoff |
| 502 | Bad gateway | Retry with exponential backoff |
| 503 | Service unavailable | Retry with exponential backoff |

---

## Part 5: Direct Photo Posting

### 5.1 Photo Post Initialization Endpoint

**URL:** `https://open.tiktokapis.com/v2/post/publish/content/init/`

**Method:** POST

**Scope Required:** `video.publish`

**Rate Limit:** 6 requests per minute per user access token

### 5.2 Request Body Structure

```json
{
  "media_type": "PHOTO",
  "post_mode": "DIRECT_POST",
  "post_info": {
    "title": "Your photo caption",
    "description": "Longer description of the photo",
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_comment": false
  },
  "source_info": {
    "source": "PULL_FROM_URL",
    "photo_images": [
      "https://verified-domain.com/photos/photo1.jpg",
      "https://verified-domain.com/photos/photo2.jpg"
    ],
    "photo_cover_index": 0
  }
}
```

### 5.3 Photo Parameters

| Parameter | Type | Required | Limits | Notes |
|-----------|------|----------|--------|-------|
| `media_type` | string | Yes | - | Literal `"PHOTO"` |
| `post_mode` | string | Yes | - | `"DIRECT_POST"` or `"MEDIA_UPLOAD"` |
| `title` | string | No | 90 chars | Caption (shorter than video) |
| `description` | string | No | 4000 chars | Extended description |
| `privacy_level` | string | Yes | - | PRIVATE, FRIENDS_ONLY, PUBLIC_TO_EVERYONE |
| `disable_comment` | boolean | No | - | Disable comments |
| `photo_images` | array | Yes | 1-35 URLs | URLs to photos (publicly accessible) |
| `photo_cover_index` | integer | No | 0-34 | Which photo to show as cover (0-indexed) |

**Photo URL Requirements:**
- Must be publicly accessible (HTTPS)
- From verified domain (same pre-verification as video URLs)
- Supported formats: JPG, PNG, WEBP, BMP, GIF (static)
- Max 35 images per post (carousel)
- Minimum 1 image

**Image Specifications (TikTok Optimized):**
- Recommended: 1080x1440 (9:16 aspect ratio)
- Minimum: 720x1080
- Maximum: 4096x4096
- JPEG quality: 85-95% recommended

### 5.4 Success Response

```json
{
  "data": {
    "publish_id": "p_pub_url~v2.XXXXXXXXXXXXXXXXXX"
  },
  "error": {
    "code": "ok",
    "log_id": "..."
  }
}
```

**No upload URL needed** - TikTok pulls from provided URLs directly.

### 5.5 Status Check for Photos

Use same status endpoint as videos (see Section 6).

---

## Part 6: Content Upload (Draft/Inbox)

### 6.1 Upload vs. Direct Post

| Aspect | Direct Post | Upload |
|--------|-------------|--------|
| User Flow | Immediate publish | Draft first, publish later |
| Endpoint | `/video/init/` | `/inbox/video/init/` |
| Use Case | Batch scheduling | User reviews before publish |
| Status Transitions | PROCESSING → POSTED | UPLOAD_COMPLETED → User publishes |
| Scope | video.publish | video.upload OR video.publish |

### 6.2 Video Upload Initialization

**URL:** `https://open.tiktokapis.com/v2/post/publish/inbox/video/init/`

**Method:** POST

**Scope Required:** `video.upload` (or `video.publish`)

**Rate Limit:** 6 requests per minute per user access token

**Request Body:**

```json
{
  "upload_source": "FILE_UPLOAD",
  "post_info": {
    "title": "",
    "privacy_level": "PRIVATE",
    "brand_organic_toggle": false
  },
  "source_info": {
    "source": "FILE_UPLOAD",
    "video_size": 52428800,
    "chunk_size": 5242880,
    "total_chunk_count": 10
  }
}
```

### 6.3 Success Response

```json
{
  "data": {
    "publish_id": "p_inbox~v2.XXXXXXXXXXXXXXXXXX",
    "upload_url": "https://upload.tiktokapis.com/upload/v1/video/?upload_id=XXXXX&part_number=1",
    "upload_token": "UPLOAD_TOKEN_IF_NEEDED"
  },
  "error": {
    "code": "ok"
  }
}
```

### 6.4 Video Upload Process (Chunked)

**Step 1: Upload Each Chunk**

For each chunk (1 to total_chunk_count):

```
PUT {upload_url}?part_number=1&upload_id=XXXXX
Content-Type: video/mp4
Content-Length: 5242880
Content-Range: bytes 0-5242879/52428800

[BINARY VIDEO CHUNK DATA]
```

**Headers Required:**

| Header | Value | Example |
|--------|-------|---------|
| `Content-Type` | video/mp4, video/quicktime, video/webm | `video/mp4` |
| `Content-Length` | Exact bytes in this chunk | `5242880` |
| `Content-Range` | `bytes START-END/TOTAL` | `bytes 0-5242879/52428800` |

**Content-Range Calculation:**
```
Chunk 1: bytes 0-5242879/52428800 (first chunk, 0-indexed end inclusive)
Chunk 2: bytes 5242880-10485759/52428800
Chunk 3: bytes 10485760-15728639/52428800
...
Chunk 10: bytes 47185920-52428799/52428800 (last chunk)
```

**Formula:**
```
START = (chunk_number - 1) * chunk_size
END = START + chunk_size - 1
```

**Upload Response (For Each Chunk):**
```
HTTP 200 OK
```

No body needed (some SDKs return empty JSON).

**Step 2: Verify Upload Complete**

After all chunks uploaded, check status:

```
POST https://open.tiktokapis.com/v2/post/publish/status/fetch/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "publish_id": "p_inbox~v2.XXXXXXXXXXXXXXXXXX"
}
```

---

## Part 7: Publishing Status

### 7.1 Status Check Endpoint

**URL:** `https://open.tiktokapis.com/v2/post/publish/status/fetch/`

**Method:** POST

**Scope Required:** `video.publish` or `video.upload`

**Request Body:**

```json
{
  "publish_id": "p_pub_url~v2.XXXXXXXXXXXXXXXXXX"
}
```

### 7.2 Status Response

```json
{
  "data": {
    "status": "POSTED",
    "publiclyAvailablePostId": "7284629384759284729",
    "create_time": 1702656000,
    "posted_time": 1702656120,
    "posted_url": "https://www.tiktok.com/@username/video/7284629384759284729"
  },
  "error": {
    "code": "ok"
  }
}
```

### 7.3 Status Values

| Status | Meaning | Action |
|--------|---------|--------|
| PROCESSING | Transcoding/validation | Poll every 5-10 seconds |
| POSTED | Video published successfully | Complete |
| UPLOAD_FAILED | Upload error | Retry upload |
| PUBLISH_FAILED | Published but with restrictions | Check logs; may need audit |
| SUBMITTED | Awaiting processing | Normal state during encoding |
| FAILED | Permanent failure | Check error logs |

**Polling Strategy:**
```python
import time

def wait_for_publish(publish_id: str, max_wait_seconds: int = 300) -> dict:
    """Poll until video is processed"""
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        status = check_status(publish_id)

        if status['status'] in ['POSTED', 'FAILED', 'UPLOAD_FAILED']:
            return status

        # Exponential backoff: 2s, 4s, 8s, 16s
        wait_time = min(16, 2 ** (iteration + 1))
        time.sleep(wait_time)
```

### 7.4 Failure Handling

**UPLOAD_FAILED Response:**
```json
{
  "data": {
    "status": "UPLOAD_FAILED",
    "fail_reason": "Unsupported video codec"
  },
  "error": {
    "code": "ok"
  }
}
```

**Reasons for failure:**
- Unsupported video codec (must be H.264)
- Invalid video dimensions
- Corrupted file
- Timeout during upload

**Action:** Re-encode video and retry.

---

## Part 8: Video Specifications & Constraints

### 8.1 Video Codec Requirements

**Required:**
- **Codec:** H.264 (AVC)
- **Profile:** Main Profile or High Profile
- **Bitrate:** 1000-6000 kbps recommended
- **Frame Rate:** 24-60 fps

**Container:**
- **Format:** MP4 (MPEG-4 Part 14)
- **Box Structure:** Standard ftyp → moov → mdat

**Audio:**
- **Codec:** AAC or MP3
- **Bitrate:** 128-320 kbps
- **Sample Rate:** 44.1 kHz or 48 kHz

### 8.2 Video Resolution & Aspect Ratio

**Recommended Specs:**
- **Resolution:** 1080x1920 (9:16 vertical)
- **Aspect Ratio:** 9:16 (portrait)
- **Minimum:** 720x1080
- **Maximum:** 4096x4096

**Common Resolutions:**
- 1080x1920 (9:16) - TikTok default
- 1440x1920 (4:5) - Instagram vertical
- 720x1280 (9:16) - Lower quality fallback

### 8.3 File Size & Duration

**Size Limits:**
- **Maximum:** 500 MB
- **Minimum:** > 100 KB (empty files rejected)

**Duration:**
- **Minimum:** ~3 seconds
- **Maximum:** 10 minutes (600 seconds)
- **Recommended:** 15-60 seconds (for engagement)

### 8.4 Video Preparation (FFmpeg Example)

```bash
# Convert video to TikTok specifications
ffmpeg -i input.mov \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black" \
  -vcodec libx264 \
  -preset medium \
  -b:v 2500k \
  -r 30 \
  -acodec aac \
  -b:a 128k \
  -ar 48000 \
  output.mp4
```

**Explanation:**
- `scale=1080:1920` - Resize to 9:16
- `libx264` - H.264 codec
- `-preset medium` - Quality/speed tradeoff
- `-b:v 2500k` - Video bitrate
- `-r 30` - Frame rate 30 fps
- `aac` - Audio codec
- `-b:a 128k` - Audio bitrate

---

## Part 9: Error Handling & Retry Strategy

### 9.1 Comprehensive Error Taxonomy

**Authentication Errors (401):**
```
code: "unauthorized"
message: "Unauthorized" / "The scope X is not authorized"
Action: Refresh token or request user re-auth
```

**Authorization Errors (403):**
```
code: "forbidden"
message: "Unaudited client can only post to private accounts"
Action: Wait for app audit or post to PRIVATE only
```

**Validation Errors (400):**
```
code: "invalid_request"
message: "Invalid video_size: must be between X and Y"
Action: Fix request parameters; don't retry
```

**Rate Limit (429):**
```
code: "too_many_requests"
message: "Rate limit exceeded"
Action: Retry with exponential backoff; respect Retry-After header
```

**Server Errors (5xx):**
```
code: "internal_server_error"
message: "Internal Server Error"
Action: Retry with exponential backoff
```

### 9.2 Retry Strategy

```python
import time
import random

def exponential_backoff_with_jitter(attempt: int, base_delay: int = 1) -> int:
    """Calculate backoff with jitter to prevent thundering herd"""
    exponential_delay = base_delay * (2 ** attempt)
    jitter = random.uniform(0, exponential_delay * 0.1)  # 10% jitter
    return int(exponential_delay + jitter)

def api_call_with_retry(
    func,
    *args,
    max_retries: int = 3,
    base_delay: int = 1,
    **kwargs
):
    """Execute API call with retry logic"""

    retryable_codes = [429, 500, 502, 503, 504]
    non_retryable_codes = [400, 401, 403]

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code

            # Non-retryable errors
            if status in non_retryable_codes:
                raise

            # Retryable errors
            if status in retryable_codes:
                if attempt < max_retries:
                    delay = exponential_backoff_with_jitter(attempt, base_delay)
                    logger.warning(f"Attempt {attempt + 1} failed; retrying in {delay}s")
                    time.sleep(delay)
                else:
                    raise
            else:
                raise

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                delay = exponential_backoff_with_jitter(attempt, base_delay)
                logger.warning(f"Timeout on attempt {attempt + 1}; retrying in {delay}s")
                time.sleep(delay)
            else:
                raise
```

### 9.3 Rate Limit Handling

**Detecting Rate Limits:**
- HTTP 429 status code
- Response header: `Retry-After: 60` (seconds to wait)
- Error code: `too_many_requests`

**Implementation:**
```python
def handle_rate_limit(response: requests.Response) -> int:
    """Extract retry delay from rate limit response"""

    # Check Retry-After header
    retry_after = response.headers.get('Retry-After')
    if retry_after:
        try:
            return int(retry_after)
        except ValueError:
            pass

    # Default: 1 minute for 6 requests/min limit
    return 60

# Use in retry loop
if response.status_code == 429:
    wait_seconds = handle_rate_limit(response)
    logger.warning(f"Rate limited; waiting {wait_seconds}s")
    time.sleep(wait_seconds)
    # Retry
```

---

## Part 10: Creator Info Query (Prerequisite)

### 10.1 Query Creator Info Endpoint

**Before publishing, query what privacy levels are available:**

**URL:** `https://open.tiktokapis.com/v2/creator_info/query/`

**Method:** GET

**Query Parameters:**

```
?fields=avatar_size,avatar_large_url,avatar_medium_url,avatar_small_url,display_name,open_id,bio_description,bio_link,profile_deep_link,is_verified,follower_count,following_count,video_count,like_count
```

**Response Example:**
```json
{
  "data": {
    "user": {
      "open_id": "1234567890123456789",
      "display_name": "TikTok User",
      "avatar_large_url": "https://...",
      "is_verified": true,
      "bio_description": "My bio",
      "bio_link": "https://...",
      "profile_deep_link": "https://www.tiktok.com/@username",
      "follower_count": 50000,
      "following_count": 100,
      "video_count": 150,
      "like_count": 2000000
    }
  },
  "error": {
    "code": "ok"
  }
}
```

**Use Case:** Verify user information before posting.

---

## Part 11: Request/Response Format Specifications

### 11.1 General Request Format

**All requests follow this pattern:**

```
POST/GET {BASE_URL}{ENDPOINT}
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json; charset=UTF-8
User-Agent: YourApp/1.0

{
  "param1": "value1",
  "nested": {
    "param2": "value2"
  }
}
```

### 11.2 General Response Format

**All responses follow this envelope:**

```json
{
  "data": {
    "field1": "value1",
    "field2": 123
  },
  "error": {
    "code": "ok",
    "log_id": "request_identifier_for_support"
  }
}
```

**Fields:**
- `data` - Response payload (null on error)
- `error.code` - Error identifier ("ok" = success)
- `error.log_id` - Support reference ID for debugging

### 11.3 Pagination (Where Applicable)

Not typically used in posting API. Videos returned via separate endpoints use:

```json
{
  "data": {
    "videos": [
      { "id": "...", "title": "..." },
      { "id": "...", "title": "..." }
    ],
    "cursor": "CURSOR_FOR_NEXT_PAGE"
  }
}
```

---

## Part 12: Recent Changes & Deprecations

### 12.1 Known Recent Changes (As of 2025)

**1. Unified Content Posting Endpoint**
- Previously separate `/video/` and `/photo/` flows
- Now consolidated to `/content/init/` for photos
- Videos still use `/video/init/` (direct) and `/inbox/video/init/` (upload)

**2. Enhanced Privacy Controls**
- `FRIENDS_ONLY` privacy level added (previously PRIVATE/PUBLIC only)
- Requires latest API version

**3. AI-Generated Content Transparency**
- New `is_aigc` flag in request body
- TikTok encourages marking AI-generated content
- May improve visibility/reduce suppression

**4. Brand Content Integration**
- `brand_content_toggle` and `brand_organic_toggle` added
- For creators in brand partnership program

**5. Video Cover Timestamp (Milliseconds)**
- Changed from seconds to milliseconds (`video_cover_timestamp_ms`)
- Better precision for frame selection

### 12.2 Deprecated Features

**1. OAuth 1.0**
- **Status:** Deprecated, removed
- **Use:** OAuth 2.0 only

**2. Legacy Token URL Structure**
- **Old:** `/auth/access_token/`
- **New:** `/oauth/token/`
- Migrate to new endpoint

**3. User-Provided Upload URLs**
- **Status:** Deprecated for videos
- **Use:** FILE_UPLOAD chunked upload instead
- **Photo:** PULL_FROM_URL still supported

### 12.3 Known Issues

**1. Audit Delay**
- App audit takes 1-4 weeks
- No way to expedite
- Test with PRIVATE posts first

**2. Rate Limit on Upload Initialization**
- 6 requests/minute limit affects entire flow
- Can't parallelize multiple uploads
- Plan accordingly

**3. Token Refresh Token Rotation**
- May or may not rotate on refresh
- Always use returned token (if provided)

**4. Upload URL 1-Hour Expiration**
- Strict limit; cannot extend
- Must complete upload within 60 minutes
- Plan chunking strategy accordingly

---

## Part 13: Implementation Patterns & Best Practices

### 13.1 Complete OAuth Implementation Pattern

```python
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django_cache_backend import cache
from apps.tiktok_accounts.models import TikTokAccount
from apps.tiktok_accounts.services import TikTokOAuthService

oauth_service = TikTokOAuthService()

def initiate_login(request: HttpRequest) -> HttpResponse:
    """Step 1: Redirect user to TikTok login"""
    auth_url_data = oauth_service.get_authorization_url()

    # Cache state for validation (30-minute expiration)
    cache.set(
        f'oauth_state:{auth_url_data["state"]}',
        {
            'created_at': timezone.now(),
            'user_id': request.user.id if request.user.is_authenticated else None
        },
        timeout=1800
    )

    return redirect(auth_url_data['url'])

def oauth_callback(request: HttpRequest) -> HttpResponse:
    """Step 2: Handle OAuth callback"""
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')

    # Error handling
    if error:
        return HttpResponse(f"Authorization failed: {error}", status=400)

    # Validate state (CSRF protection)
    state_data = cache.get(f'oauth_state:{state}')
    if not state_data:
        return HttpResponse("State validation failed", status=401)

    if timezone.now() - state_data['created_at'] > timedelta(minutes=30):
        return HttpResponse("State expired", status=401)

    try:
        # Exchange code for token
        token_data = oauth_service.exchange_code_for_token(code)

        # Store account
        tiktok_account = TikTokAccount.objects.update_or_create(
            user_id=request.user.id,
            open_id=token_data['open_id'],
            defaults={
                'access_token': encrypt_token(token_data['access_token']),
                'refresh_token': encrypt_token(token_data['refresh_token']),
                'token_expires_at': token_data['token_expires_at'],
                'scopes': ','.join(token_data['scope'].split(',')),
            }
        )

        return redirect('/dashboard/')

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return HttpResponse(f"Authentication failed: {str(e)}", status=500)
```

### 13.2 Complete Video Publishing Pattern

```python
from pathlib import Path
from apps.content.services import TikTokVideoService

def publish_video_async(video_file_path: str, caption: str, account_id: int):
    """Publish video with full error handling"""

    account = TikTokAccount.objects.get(id=account_id)
    access_token = decrypt_token(account.access_token)

    with TikTokVideoService(access_token) as service:
        try:
            # Step 1: Initialize upload
            upload_data = service.initiate_upload(
                privacy_level='PRIVATE',  # Safe for unaudited
                disable_comment=False
            )

            publish_id = upload_data['publish_id']
            upload_url = upload_data['upload_url']

            # Step 2: Upload video file
            service.upload_video_file(upload_url, video_file_path)

            # Step 3: Poll for completion
            max_polls = 60
            poll_interval = 5

            for i in range(max_polls):
                status = service.check_publish_status(publish_id)

                if status['status'] == 'POSTED':
                    # Success
                    update_content_status(
                        account_id,
                        publish_id,
                        'PUBLISHED',
                        status.get('publiclyAvailablePostId')
                    )
                    return

                elif status['status'] in ['FAILED', 'UPLOAD_FAILED']:
                    raise Exception(f"Publishing failed: {status.get('fail_reason')}")

                if i < max_polls - 1:
                    time.sleep(poll_interval)

            # Polling timeout
            raise Exception("Video processing timeout (5+ minutes)")

        except Exception as e:
            logger.error(f"Video publish error for {publish_id}: {e}")
            update_content_status(
                account_id,
                publish_id,
                'FAILED',
                error_message=str(e)
            )
            raise
```

### 13.3 Proactive Token Refresh Pattern (Celery)

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task(bind=True, max_retries=3)
def refresh_tiktok_tokens(self):
    """Proactively refresh tokens expiring soon"""

    now = timezone.now()
    refresh_window = now + timedelta(seconds=600)  # Next 10 minutes

    accounts = TikTokAccount.objects.filter(
        token_expires_at__lte=refresh_window,
        token_expires_at__gt=now
    )

    for account in accounts:
        try:
            refresh_token_plaintext = decrypt_token(account.refresh_token)
            oauth_service = TikTokOAuthService()

            new_tokens = oauth_service.refresh_access_token(refresh_token_plaintext)

            account.access_token = encrypt_token(new_tokens['access_token'])
            account.refresh_token = encrypt_token(
                new_tokens.get('refresh_token', refresh_token_plaintext)
            )
            account.token_expires_at = new_tokens['token_expires_at']
            account.error_count = 0
            account.last_error = None
            account.save()

            logger.info(f"Token refreshed for account {account.id}")

        except Exception as e:
            account.error_count += 1
            account.last_error = str(e)
            account.save()

            if account.error_count >= 3:
                # Notify user to re-authenticate
                notify_user_reauthenticate(account.user_id)

            logger.error(f"Token refresh failed for {account.id}: {e}")

            if self.request.retries < self.max_retries:
                self.retry(countdown=300)  # Retry in 5 minutes
```

---

## Part 14: Security Considerations

### 14.1 Token Security

**Storage:**
- Encrypt at rest using AES-256-GCM
- Use application-managed keys (rotate annually)
- Never log plaintext tokens
- Use HTTPS for all token transmission

**Access:**
- Limit token access to authenticated users
- Implement database-level row security if using PostgreSQL
- Audit all token access attempts
- Implement rate limiting on token refresh

### 14.2 OAuth Security

**State Parameter:**
- Generate using `secrets.token_urlsafe(32)` or equivalent
- Store in server-side session (not browser)
- Validate constant-time comparison (prevent timing attacks)
- Expire after 30 minutes

**HTTPS Enforcement:**
- Require HTTPS for all endpoints
- Use HSTS headers (Strict-Transport-Security)
- Reject all HTTP callback URIs

**CSRF Protection:**
- State parameter (described above)
- SameSite cookie attribute set to Strict
- Implement standard Django CSRF middleware

### 14.3 API Security

**Rate Limiting:**
- Implement per-user token rate limits (respect TikTok's 6/min)
- Implement per-IP rate limits (prevent abuse)
- Use circuit breaker pattern for cascading failures

**Input Validation:**
- Validate all caption text (2200 char limit, no injection attacks)
- Validate file sizes/types before upload
- Validate privacy levels against allowed values

**Error Messages:**
- Never expose token values in error messages
- Never expose internal system details
- Use generic error messages in client responses
- Log full errors on server side only

---

## Part 15: Troubleshooting & Support

### 15.1 Common Issues & Solutions

**Issue: "Rate limit exceeded"**
- **Cause:** Exceeded 6 requests/minute per token
- **Solution:** Implement queue system; space out initialization requests
- **Prevention:** Use proactive token refresh to avoid repeated attempts

**Issue: "Unaudited client can only post to private"**
- **Cause:** App not yet audited by TikTok
- **Solution:** Post to PRIVATE privacy_level; apply for audit
- **Prevention:** Set up with PRIVATE posts first; iterate on audit process

**Issue: "Privacy level option mismatch"**
- **Cause:** Requested privacy level not available for user
- **Solution:** Query creator_info API first; use returned privacy levels
- **Prevention:** Always validate privacy level availability

**Issue: "Scope not authorized"**
- **Cause:** User didn't authorize requested scope
- **Solution:** Redirect user to re-authorize with required scope
- **Prevention:** Check token scopes after exchange

**Issue: "Upload timeout"**
- **Cause:** Large file; slow network; 5-minute timeout
- **Solution:** Use smaller chunks; increase chunk size strategically
- **Prevention:** Test with target file sizes; optimize chunk strategy

**Issue: "Invalid video codec"**
- **Cause:** Video not in H.264/MP4 format
- **Solution:** Re-encode using FFmpeg (see Section 8.4)
- **Prevention:** Pre-validate format before upload

### 15.2 Debugging Checklist

- [ ] Verify app is registered in TikTok Developer Portal
- [ ] Confirm CLIENT_KEY and CLIENT_SECRET are correct
- [ ] Verify REDIRECT_URI matches exactly (case-sensitive)
- [ ] Confirm user authorized required scopes
- [ ] Check token isn't expired (use expires_at timestamp)
- [ ] Verify privacy_level matches creator_info query
- [ ] Confirm file is MP4 with H.264 codec
- [ ] Check file size is within 100 KB - 500 MB range
- [ ] Verify chunk_size calculation (total_size / total_chunks)
- [ ] Check Content-Range header format on uploads
- [ ] Confirm HTTPS used for all requests
- [ ] Verify rate limit: 6 requests/minute per token

---

## Summary & Key Takeaways

### Critical Implementation Points

1. **OAuth State Parameter:** Always generate cryptographically random; validate with constant-time comparison; expire after 30 minutes.

2. **Token Refresh:** Proactively refresh 5 minutes before expiration; implement reactive fallback on 401; store refresh tokens encrypted at rest.

3. **Privacy Levels:** Always query creator_info first; unaudited apps restricted to PRIVATE; must apply for audit for PUBLIC posting.

4. **Rate Limiting:** 6 requests/minute per token for initialization; queue uploads; use exponential backoff with jitter.

5. **Video Format:** H.264 codec in MP4 container; 1080x1920 resolution; 100 KB - 500 MB file size.

6. **Chunked Upload:** Divide video into 5 MB chunks; PUT each with Content-Range header; verify upload_url 1-hour expiration.

7. **Error Handling:** Non-retryable (400, 401, 403); retryable (429, 5xx); implement exponential backoff; respect Retry-After header.

8. **Security:** HTTPS only; encrypt tokens at rest; validate state parameter; implement CSRF protection; audit token access.

---

## Unresolved Questions

1. **Token rotation frequency:** Does TikTok rotate refresh tokens on every refresh, or only occasionally? Current implementation assumes optional rotation (handles both cases).

2. **Audit timeline:** What's typical timeline for app audit? Documentation states 1-4 weeks but doesn't provide SLA.

3. **Chunked upload resumability:** If upload fails mid-stream, can we resume from last successful chunk, or must we restart entire upload?

4. **Video transcoding delay:** What's typical processing time for POSTED status? Documentation doesn't specify.

5. **Photo carousel publishing:** Can all 35 photos be in single post, or are there account restrictions?

6. **Concurrent uploads:** Can one token support multiple simultaneous uploads, or must they be sequential?

---

## References

- TikTok Login Kit Web: https://developers.tiktok.com/doc/login-kit-web
- Manage User Access Tokens: https://developers.tiktok.com/doc/login-kit-manage-user-access-tokens
- Content Posting API Get Started: https://developers.tiktok.com/doc/content-posting-api-get-started
- Direct Post Video: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Direct Post Photo: https://developers.tiktok.com/doc/content-posting-api-reference-photo-post
- Upload Content: https://developers.tiktok.com/doc/content-posting-api-get-started-upload-content
- Upload Video Reference: https://developers.tiktok.com/doc/content-posting-api-reference-upload-video

---

**Document Version:** 1.0
**Last Updated:** December 15, 2025
**Status:** FINAL
