# TikTok API Endpoints Reference
## Complete Endpoint Catalog

---

## Base URL
```
https://open.tiktokapis.com/v2/
```

All endpoints are relative to this base (unless otherwise noted).

---

## OAuth Endpoints

### 1. Authorization URL (User Redirect)
```
GET https://www.tiktok.com/v2/auth/authorize/
```

**Query Parameters:**
```
client_key=YOUR_CLIENT_KEY
scope=user.info.basic,video.publish
response_type=code
redirect_uri=https://yourdomain.com/callback
state=RANDOM_CSRF_TOKEN
disable_auto_auth=0
```

**Complete URL Example:**
```
https://www.tiktok.com/v2/auth/authorize/?client_key=abc123&scope=user.info.basic,video.publish&response_type=code&redirect_uri=https%3A%2F%2Fyourdomain.com%2Fcallback&state=xyz789&disable_auto_auth=0
```

**Returns:** Redirect to `redirect_uri` with `code` and `state`

---

### 2. Token Exchange / Refresh
```
POST /oauth/token/
```

**Full URL:**
```
https://open.tiktokapis.com/v2/oauth/token/
```

**Headers:**
```
Content-Type: application/json
```

**Request Body (Authorization Code):**
```json
{
  "client_key": "YOUR_CLIENT_KEY",
  "client_secret": "YOUR_CLIENT_SECRET",
  "code": "authorization_code_from_callback",
  "grant_type": "authorization_code",
  "redirect_uri": "https://yourdomain.com/callback"
}
```

**Request Body (Refresh):**
```json
{
  "client_key": "YOUR_CLIENT_KEY",
  "client_secret": "YOUR_CLIENT_SECRET",
  "grant_type": "refresh_token",
  "refresh_token": "existing_refresh_token"
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "access_token": "v.c0e1234567890abcdef",
    "refresh_token": "v.c0e1234567890abcdef",
    "expires_in": 86400,
    "scope": "user.info.basic,video.publish",
    "open_id": "1234567890123456789",
    "token_type": "Bearer"
  },
  "error": {
    "code": "ok",
    "log_id": "1234567890"
  }
}
```

---

## Content Publishing Endpoints

### 3. Direct Video Post (Initialization)
```
POST /post/publish/video/init/
```

**Full URL:**
```
https://open.tiktokapis.com/v2/post/publish/video/init/
```

**Headers:**
```
Authorization: Bearer v.c0e1234567890abcdef
Content-Type: application/json; charset=UTF-8
```

**Request Body (FILE_UPLOAD):**
```json
{
  "post_info": {
    "title": "My Video Caption",
    "privacy_level": "PRIVATE",
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

**Request Body (PULL_FROM_URL):**
```json
{
  "post_info": {
    "title": "My Video Caption",
    "privacy_level": "PRIVATE"
  },
  "source_info": {
    "source": "PULL_FROM_URL",
    "video_url": "https://verified-domain.com/video.mp4"
  }
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "publish_id": "p_pub_url~v2.1234567890",
    "upload_url": "https://upload.tiktokapis.com/upload/v1/video/?upload_id=abc123",
    "upload_url_expires_in": 3600
  },
  "error": {
    "code": "ok",
    "log_id": "1234567890"
  }
}
```

**Error Response Examples:**

Unaudited client:
```json
{
  "data": null,
  "error": {
    "code": "forbidden",
    "message": "Unaudited client can only post to private accounts"
  }
}
```

Rate limit exceeded:
```json
{
  "data": null,
  "error": {
    "code": "too_many_requests",
    "message": "Rate limit exceeded"
  }
}
```

---

### 4. Video File Upload (Streaming)
```
PUT {upload_url}?part_number=1
```

**Dynamic URL from Step 3 response**

**Headers:**
```
Content-Type: video/mp4 (or video/quicktime, video/webm)
Content-Length: 5242880
Content-Range: bytes 0-5242879/52428800
```

**Body:**
```
[BINARY VIDEO DATA - FIRST 5MB CHUNK]
```

**Success Response (200 OK):**
```
(empty body or minimal JSON)
```

**Upload URL Examples:**
```
https://upload.tiktokapis.com/upload/v1/video/?upload_id=abc123&part_number=1
https://upload.tiktokapis.com/upload/v1/video/?upload_id=abc123&part_number=2
...
```

**Multi-Chunk Upload Formula:**
```
For chunk N (1-indexed):
  START = (N - 1) * chunk_size
  END = START + chunk_size - 1
  Content-Range: bytes {START}-{END}/{total_size}

Example (5MB chunks, 52MB file):
  Chunk 1: bytes 0-5242879/52428800
  Chunk 2: bytes 5242880-10485759/52428800
  Chunk 3: bytes 10485760-15728639/52428800
  ...
  Chunk 10: bytes 47185920-52428799/52428800
```

---

### 5. Photo Post (Direct)
```
POST /post/publish/content/init/
```

**Full URL:**
```
https://open.tiktokapis.com/v2/post/publish/content/init/
```

**Headers:**
```
Authorization: Bearer v.c0e1234567890abcdef
Content-Type: application/json; charset=UTF-8
```

**Request Body:**
```json
{
  "media_type": "PHOTO",
  "post_mode": "DIRECT_POST",
  "post_info": {
    "title": "Photo Caption (Max 90 chars)",
    "description": "Longer description (Max 4000 chars)",
    "privacy_level": "PUBLIC_TO_EVERYONE",
    "disable_comment": false
  },
  "source_info": {
    "source": "PULL_FROM_URL",
    "photo_images": [
      "https://verified-domain.com/photo1.jpg",
      "https://verified-domain.com/photo2.jpg",
      "https://verified-domain.com/photo3.jpg"
    ],
    "photo_cover_index": 0
  }
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "publish_id": "p_pub_url~v2.1234567890"
  },
  "error": {
    "code": "ok",
    "log_id": "1234567890"
  }
}
```

---

### 6. Video Upload to Inbox (Draft Upload)
```
POST /post/publish/inbox/video/init/
```

**Full URL:**
```
https://open.tiktokapis.com/v2/post/publish/inbox/video/init/
```

**Headers:**
```
Authorization: Bearer v.c0e1234567890abcdef
Content-Type: application/json; charset=UTF-8
```

**Request Body:**
```json
{
  "upload_source": "FILE_UPLOAD",
  "post_info": {
    "title": "",
    "privacy_level": "PRIVATE"
  },
  "source_info": {
    "source": "FILE_UPLOAD",
    "video_size": 52428800,
    "chunk_size": 5242880,
    "total_chunk_count": 10
  }
}
```

**Success Response (200 OK):**
```json
{
  "data": {
    "publish_id": "p_inbox~v2.1234567890",
    "upload_url": "https://upload.tiktokapis.com/upload/v1/video/?upload_id=abc123&part_number=1"
  },
  "error": {
    "code": "ok"
  }
}
```

---

### 7. Check Publishing Status
```
POST /post/publish/status/fetch/
```

**Full URL:**
```
https://open.tiktokapis.com/v2/post/publish/status/fetch/
```

**Headers:**
```
Authorization: Bearer v.c0e1234567890abcdef
Content-Type: application/json; charset=UTF-8
```

**Request Body:**
```json
{
  "publish_id": "p_pub_url~v2.1234567890"
}
```

**Success Response (200 OK):**
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

**During Processing:**
```json
{
  "data": {
    "status": "PROCESSING"
  },
  "error": {
    "code": "ok"
  }
}
```

**On Failure:**
```json
{
  "data": {
    "status": "FAILED",
    "fail_reason": "Unsupported video codec"
  },
  "error": {
    "code": "ok"
  }
}
```

---

## Query Endpoints

### 8. Query Creator Info
```
GET /creator_info/query/
```

**Full URL:**
```
https://open.tiktokapis.com/v2/creator_info/query/?fields=avatar_size,avatar_large_url,avatar_medium_url,avatar_small_url,display_name,open_id,bio_description,bio_link,profile_deep_link,is_verified,follower_count,following_count,video_count,like_count
```

**Headers:**
```
Authorization: Bearer v.c0e1234567890abcdef
Content-Type: application/json; charset=UTF-8
```

**Query Parameters:**
```
fields=avatar_size,avatar_large_url,display_name,open_id,bio_description,is_verified,follower_count,following_count,video_count,like_count
```

**Success Response (200 OK):**
```json
{
  "data": {
    "user": {
      "open_id": "1234567890123456789",
      "display_name": "TikTok User",
      "avatar_large_url": "https://p16-sign.tiktokcdn.com/...",
      "avatar_medium_url": "https://p16-sign.tiktokcdn.com/...",
      "avatar_small_url": "https://p16-sign.tiktokcdn.com/...",
      "avatar_size": 100,
      "is_verified": true,
      "bio_description": "My bio text",
      "bio_link": "https://example.com",
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

---

## Rate Limits & Headers

### Rate Limit Response
```
HTTP 429 Too Many Requests

{
  "data": null,
  "error": {
    "code": "too_many_requests",
    "message": "Rate limit exceeded"
  }
}

Response Headers:
Retry-After: 60
```

### Limits
| Resource | Limit | Notes |
|----------|-------|-------|
| Initialization requests | 6/minute | Per access token |
| Video uploads | 15/day | Per account |
| Photo posts | Included in 6/min | Per access token |

---

## Error Response Format (All Endpoints)

**Standard Error Envelope:**
```json
{
  "data": null,
  "error": {
    "code": "error_code_here",
    "message": "Human readable message",
    "log_id": "REQUEST_ID_FOR_SUPPORT"
  }
}
```

**Common Error Codes:**

| Code | HTTP | Cause | Action |
|------|------|-------|--------|
| `invalid_request` | 400 | Missing/invalid params | Fix request |
| `invalid_grant` | 400 | Code/token invalid | Restart OAuth |
| `invalid_client` | 400 | Bad credentials | Check client_key/secret |
| `access_denied` | 400 | User denied auth | User must re-approve |
| `unauthorized` | 401 | Token expired/invalid | Refresh token |
| `scope_not_authorized` | 401 | Missing scope | User must re-auth |
| `forbidden` | 403 | Unaudited/privacy issue | Check app status |
| `too_many_requests` | 429 | Rate limit hit | Wait & retry |
| `internal_server_error` | 500 | TikTok error | Retry with backoff |
| `bad_gateway` | 502 | TikTok error | Retry with backoff |
| `service_unavailable` | 503 | TikTok down | Retry with backoff |

---

## Example Complete Flows

### Flow 1: Direct Video Post (File Upload)

```
1. POST /post/publish/video/init/
   ↓ Returns: publish_id, upload_url

2. PUT {upload_url}?part_number=1
   PUT {upload_url}?part_number=2
   ...
   PUT {upload_url}?part_number=N
   ↓ All chunks uploaded

3. POST /post/publish/status/fetch/
   ↓ Returns: status (POSTING, POSTED, or FAILED)

4. POLL /post/publish/status/fetch/ every 5 seconds
   ↓ Until status = POSTED or FAILED
```

### Flow 2: Direct Photo Post

```
1. POST /post/publish/content/init/
   (media_type: PHOTO, source: PULL_FROM_URL)
   ↓ Returns: publish_id

2. POST /post/publish/status/fetch/
   ↓ Returns: status (POSTED or FAILED)
```

### Flow 3: OAuth Flow

```
1. GET /auth/authorize/ (with state parameter)
   ↓ User redirects to TikTok login

2. User authorizes → TikTok redirects to callback
   ?code=AUTH_CODE&state=STATE&scopes=...

3. POST /oauth/token/
   (code, client_key, client_secret, grant_type)
   ↓ Returns: access_token, refresh_token, expires_in

4. Store tokens (encrypted)
   Calculate expiration: now + expires_in - 300 seconds

5. Before expiration, POST /oauth/token/
   (grant_type: refresh_token, refresh_token)
   ↓ Returns: new access_token, new refresh_token
```

---

## Python/requests Examples

### Example 1: OAuth Token Exchange

```python
import requests

response = requests.post(
    'https://open.tiktokapis.com/v2/oauth/token/',
    json={
        'client_key': 'YOUR_CLIENT_KEY',
        'client_secret': 'YOUR_CLIENT_SECRET',
        'code': 'auth_code_from_callback',
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://yourdomain.com/callback'
    },
    headers={'Content-Type': 'application/json'}
)

tokens = response.json()['data']
access_token = tokens['access_token']
refresh_token = tokens['refresh_token']
expires_in = tokens['expires_in']
```

### Example 2: Video Post Initialization

```python
import requests

response = requests.post(
    'https://open.tiktokapis.com/v2/post/publish/video/init/',
    json={
        'post_info': {
            'title': 'My Video',
            'privacy_level': 'PRIVATE'
        },
        'source_info': {
            'source': 'FILE_UPLOAD',
            'video_size': 52428800,
            'chunk_size': 5242880,
            'total_chunk_count': 10
        }
    },
    headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8'
    }
)

publish_id = response.json()['data']['publish_id']
upload_url = response.json()['data']['upload_url']
```

### Example 3: Upload Video Chunk

```python
import requests

with open('video.mp4', 'rb') as f:
    chunk_data = f.read(5242880)  # 5 MB

response = requests.put(
    upload_url,
    data=chunk_data,
    headers={
        'Content-Type': 'video/mp4',
        'Content-Length': str(len(chunk_data)),
        'Content-Range': f'bytes 0-{len(chunk_data)-1}/52428800'
    }
)
```

### Example 4: Check Status

```python
import requests
import time

for i in range(60):  # Max 5 minutes
    response = requests.post(
        'https://open.tiktokapis.com/v2/post/publish/status/fetch/',
        json={'publish_id': publish_id},
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }
    )

    status = response.json()['data']['status']

    if status == 'POSTED':
        print("Video published!")
        break
    elif status == 'FAILED':
        print("Video publishing failed")
        break
    else:
        print(f"Status: {status}")
        time.sleep(5)
```

---

## Endpoint Categorization

### OAuth Endpoints (2)
- `GET https://www.tiktok.com/v2/auth/authorize/` - User redirect
- `POST https://open.tiktokapis.com/v2/oauth/token/` - Token exchange/refresh

### Publishing Endpoints (5)
- `POST /post/publish/video/init/` - Direct video
- `PUT {upload_url}` - Video file upload
- `POST /post/publish/content/init/` - Direct photo
- `POST /post/publish/inbox/video/init/` - Draft upload
- `POST /post/publish/status/fetch/` - Status check

### Query Endpoints (1)
- `GET /creator_info/query/` - Creator info

**Total: 8 Endpoints**

---

## Summary

- **2 OAuth endpoints** for authorization
- **5 publishing endpoints** for content
- **1 query endpoint** for creator info
- **6 requests/minute** rate limit per token
- **15 uploads/day** per account limit
- **Response format:** All endpoints use standard `{data, error}` envelope
- **Auth:** Bearer token in Authorization header
- **Content-Type:** Always `application/json; charset=UTF-8`

---

**Last Updated:** December 15, 2025
**Status:** Complete Reference
