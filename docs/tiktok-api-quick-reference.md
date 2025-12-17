# TikTok API Quick Reference Guide

## OAuth 2.0 Flow - 3 Steps

### 1. Authorization URL
```
https://www.tiktok.com/v2/auth/authorize/?client_key={CLIENT_KEY}&scope=user.info.basic,video.publish&response_type=code&redirect_uri={REDIRECT_URI}&state={RANDOM_STATE}
```

### 2. Callback (TikTok Redirects Back)
```
https://yourdomain.com/callback?code={CODE}&scopes=...&state={STATE}
```

### 3. Exchange Code for Token
```
POST https://open.tiktokapis.com/v2/oauth/token/
Content-Type: application/json

{
  "client_key": "YOUR_CLIENT_KEY",
  "client_secret": "YOUR_CLIENT_SECRET",
  "code": "CODE_FROM_STEP_2",
  "grant_type": "authorization_code",
  "redirect_uri": "https://yourdomain.com/callback"
}

Response:
{
  "data": {
    "access_token": "v.XXXXXX",
    "refresh_token": "v.XXXXXX",
    "expires_in": 86400,
    "open_id": "1234567890"
  }
}
```

---

## Token Refresh

```
POST https://open.tiktokapis.com/v2/oauth/token/
Content-Type: application/json

{
  "client_key": "YOUR_CLIENT_KEY",
  "client_secret": "YOUR_CLIENT_SECRET",
  "grant_type": "refresh_token",
  "refresh_token": "REFRESH_TOKEN"
}
```

**Strategy:** Refresh 5 minutes BEFORE expiration (proactive).

---

## Direct Video Post (Quickest)

### 1. Initialize Upload
```
POST https://open.tiktokapis.com/v2/post/publish/video/init/
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json

{
  "post_info": {
    "title": "My Video",
    "privacy_level": "PRIVATE",
    "disable_comment": false,
    "disable_duet": false,
    "disable_stitch": false,
    "video_cover_timestamp_ms": 1000
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
    "publish_id": "p_pub_url~v2.XXXXX",
    "upload_url": "https://upload.tiktokapis.com/..."
  }
}
```

### 2. Upload Video (Chunked)
```
PUT {upload_url}?part_number=1
Content-Type: video/mp4
Content-Length: 5242880
Content-Range: bytes 0-5242879/52428800

[BINARY VIDEO DATA]
```

### 3. Check Status
```
POST https://open.tiktokapis.com/v2/post/publish/status/fetch/
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json

{
  "publish_id": "p_pub_url~v2.XXXXX"
}

Response:
{
  "data": {
    "status": "POSTED",
    "publiclyAvailablePostId": "7284629384759284729"
  }
}
```

---

## Direct Photo Post

```
POST https://open.tiktokapis.com/v2/post/publish/content/init/
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json

{
  "media_type": "PHOTO",
  "post_mode": "DIRECT_POST",
  "post_info": {
    "title": "My Photos",
    "privacy_level": "PRIVATE"
  },
  "source_info": {
    "source": "PULL_FROM_URL",
    "photo_images": [
      "https://mysite.com/photo1.jpg",
      "https://mysite.com/photo2.jpg"
    ],
    "photo_cover_index": 0
  }
}

Response:
{
  "data": {
    "publish_id": "p_pub_url~v2.XXXXX"
  }
}
```

---

## Key Limits & Constraints

| Item | Limit |
|------|-------|
| API requests | 6/minute per token |
| Video uploads | 15/day per account |
| File size | 100 KB - 500 MB |
| Duration | 3 sec - 10 min |
| Caption length | 2200 UTF-16 runes |
| Photos per post | 1-35 |
| Video codec | H.264 (MP4) |
| Aspect ratio | 9:16 (1080x1920) |
| Access token expiry | 24 hours |
| Refresh token expiry | 365 days |
| Upload URL expiry | 1 hour |
| Rate limit window | Per minute |

---

## Error Codes

| Status | Code | Action |
|--------|------|--------|
| 400 | invalid_request | Fix parameters |
| 401 | unauthorized | Refresh token / re-auth |
| 403 | forbidden | Check audit status / privacy level |
| 429 | too_many_requests | Wait 60s; retry |
| 5xx | internal_server_error | Retry with backoff |

---

## Privacy Levels

- `PRIVATE` - Only user sees (safe for unaudited apps)
- `FRIENDS_ONLY` - Only friends see
- `PUBLIC_TO_EVERYONE` - Public (requires app audit)

**Note:** Unaudited apps can only post to PRIVATE.

---

## Video Format (FFmpeg)

```bash
ffmpeg -i input.mov \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
  -vcodec libx264 -preset medium -b:v 2500k -r 30 \
  -acodec aac -b:a 128k -ar 48000 \
  output.mp4
```

---

## Required Scopes

```
user.info.basic      # Basic user info
user.info.profile    # Profile info
video.publish        # Post videos/photos
video.upload         # Upload as draft
video.list           # List videos
```

---

## Chunk Upload Formula

```
START = (chunk_number - 1) * chunk_size
END = START + chunk_size - 1
Content-Range: bytes {START}-{END}/{TOTAL_SIZE}

Example (5MB chunks, 52MB file):
Chunk 1: bytes 0-5242879/52428800
Chunk 2: bytes 5242880-10485759/52428800
Chunk 3: bytes 10485760-15728639/52428800
```

---

## Status Values

| Status | Meaning |
|--------|---------|
| PROCESSING | Encoding; poll every 5s |
| POSTED | Success |
| FAILED | Permanent failure |
| UPLOAD_FAILED | Upload error; retry |
| SUBMITTED | Normal; keep polling |

---

## State Parameter (CSRF Protection)

```python
import secrets

# Generate
state = secrets.token_urlsafe(32)  # 43 chars

# Store (with 30-min expiration)
cache.set(f'oauth_state:{state}', created_at, 1800)

# Validate (constant-time comparison)
if not secrets.compare_digest(received_state, stored_state):
    raise ValueError("CSRF: State mismatch")
```

---

## Retry Strategy

- 400, 401, 403: Don't retry (non-retryable)
- 429, 5xx: Retry with exponential backoff
- Backoff formula: `wait = base * (2 ** attempt) + jitter`
- Max retries: 3
- Base delay: 1 second

---

## Complete Request Example

```python
import requests

token = "v.c0e1234567890abcdef"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json; charset=UTF-8"
}

# Initialize video post
response = requests.post(
    "https://open.tiktokapis.com/v2/post/publish/video/init/",
    headers=headers,
    json={
        "post_info": {
            "title": "My Video",
            "privacy_level": "PRIVATE"
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": 52428800,
            "chunk_size": 5242880,
            "total_chunk_count": 10
        }
    }
)

publish_id = response.json()['data']['publish_id']
upload_url = response.json()['data']['upload_url']

# Upload video chunks
with open('video.mp4', 'rb') as f:
    chunk_size = 5242880
    chunk_num = 1
    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            break

        start = (chunk_num - 1) * chunk_size
        end = start + len(chunk) - 1
        total = 52428800

        headers['Content-Range'] = f'bytes {start}-{end}/{total}'
        headers['Content-Length'] = str(len(chunk))

        requests.put(upload_url, data=chunk, headers=headers)
        chunk_num += 1
```

---

## Unaudited vs Audited Apps

| Feature | Unaudited | Audited |
|---------|-----------|---------|
| Max privacy | PRIVATE only | PUBLIC_TO_EVERYONE |
| Time to approve | N/A | 1-4 weeks |
| Testing | Use PRIVATE privacy | Use PUBLIC for testing |
| Production | Must post PRIVATE | Can post PUBLIC |

---

## Common Implementation Pattern

```python
def publish_video(video_path, caption, account):
    # Get token
    token = decrypt_token(account.access_token)

    # Init upload
    init_resp = requests.post(
        f"{BASE_URL}post/publish/video/init/",
        headers={"Authorization": f"Bearer {token}"},
        json={"post_info": {"title": caption}, "source_info": {...}}
    )
    publish_id = init_resp.json()['data']['publish_id']
    upload_url = init_resp.json()['data']['upload_url']

    # Upload video
    with open(video_path, 'rb') as f:
        requests.put(upload_url, data=f)

    # Poll status
    while True:
        status_resp = requests.post(
            f"{BASE_URL}post/publish/status/fetch/",
            json={"publish_id": publish_id}
        )
        status = status_resp.json()['data']['status']
        if status in ['POSTED', 'FAILED']:
            return status
        time.sleep(5)
```

---

**Last Updated:** December 15, 2025
