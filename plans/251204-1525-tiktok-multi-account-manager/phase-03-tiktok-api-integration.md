# Phase 03: TikTok API Integration

**Priority:** High
**Status:** ✅ COMPLETE (with 6 critical issues to address before Phase 04)
**Estimated Time:** 4-6 hours
**Actual Time:** ~5 hours
**Code Review Date:** 2025-12-04
**Completion Date:** 2025-12-04 21:51

## Context Links

- [Main Plan](./plan.md)
- [Phase 02: Database Schema](./phase-02-database-schema.md)
- [TikTok API Research Report](./research/tiktok-api-research.md) - In Progress

## Overview

Implement TikTok API integration for OAuth authentication, account management, and video publishing using TikTok Business API or Content Posting API.

## Key Insights

- TikTok uses OAuth 2.0 for authentication
- Tokens expire and require refresh mechanism
- Rate limiting is strict - need retry logic with exponential backoff
- Video upload may require chunked upload for large files
- API scopes determine available permissions
- Webhook support for real-time updates (if available)

## Requirements

### Functional Requirements
- OAuth 2.0 authorization flow
- Token storage and automatic refresh
- Account information retrieval
- Video upload to TikTok
- Post creation with captions/hashtags
- Publishing status tracking
- Error handling and retry logic

### Non-Functional Requirements
- Secure token storage (encrypted)
- Rate limit compliance
- Request timeout handling
- Comprehensive logging
- Idempotent operations
- Circuit breaker pattern for API failures

## Architecture

```
┌─────────────────┐
│  Django App     │
│                 │
│  ┌───────────┐  │      ┌──────────────┐
│  │ OAuth     │  │──────▶│ TikTok OAuth │
│  │ Service   │  │◀──────│ Server       │
│  └───────────┘  │      └──────────────┘
│                 │
│  ┌───────────┐  │      ┌──────────────┐
│  │ Video     │  │──────▶│ TikTok API   │
│  │ Upload    │  │◀──────│ (Content)    │
│  │ Service   │  │      └──────────────┘
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │ Token     │  │
│  │ Refresh   │  │
│  │ Service   │  │
│  └───────────┘  │
└─────────────────┘
```

### Service Components

1. **TikTokOAuthService** - Handle OAuth flow
2. **TikTokAccountService** - Account management
3. **TikTokVideoService** - Video upload and publishing
4. **TikTokTokenService** - Token refresh and validation
5. **TikTokWebhookService** - Handle webhooks (if supported)

## Related Code Files

### Files to Create
- `backend/apps/tiktok_accounts/services/tiktok-oauth-service.py`
- `backend/apps/tiktok_accounts/services/tiktok-account-service.py`
- `backend/apps/tiktok_accounts/services/tiktok-token-service.py`
- `backend/apps/content/services/tiktok-video-service.py`
- `backend/apps/content/services/tiktok-publish-service.py`
- `backend/core/utils/tiktok-api-client.py`
- `backend/core/utils/token-encryption.py`
- `backend/core/utils/rate-limiter.py`
- `backend/config/tiktok-config.py`

### Configuration Files
- `backend/.env` - Add TikTok API credentials
- `backend/config/settings.py` - TikTok API settings

## Implementation Steps

### 1. Create TikTok API Configuration

```python
# backend/config/tiktok-config.py
from decouple import config

class TikTokConfig:
    """TikTok API configuration"""

    # OAuth credentials
    CLIENT_KEY = config('TIKTOK_CLIENT_KEY')
    CLIENT_SECRET = config('TIKTOK_CLIENT_SECRET')
    REDIRECT_URI = config('TIKTOK_REDIRECT_URI', default='http://localhost:8000/api/tiktok/callback')

    # API endpoints
    OAUTH_URL = 'https://www.tiktok.com/v2/auth/authorize/'
    TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/'
    API_BASE_URL = 'https://open.tiktokapis.com/v2/'

    # API scopes
    SCOPES = [
        'user.info.basic',
        'video.upload',
        'video.publish',
        'video.list',
    ]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 100
    RATE_LIMIT_PER_DAY = 10000

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
```

### 2. Create TikTok API Client

```python
# backend/core/utils/tiktok-api-client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TikTokAPIClient:
    """HTTP client for TikTok API with retry logic"""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token"""
        headers = {
            'Content-Type': 'application/json',
        }
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def get(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute GET request"""
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed: {url}, Error: {str(e)}")
            raise

    def post(self, url: str, data: Optional[Dict] = None,
            json: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute POST request"""
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                data=data,
                json=json,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed: {url}, Error: {str(e)}")
            raise
```

### 3. Create Token Encryption Utility

```python
# backend/core/utils/token-encryption.py
from cryptography.fernet import Fernet
from django.conf import settings
import base64

class TokenEncryption:
    """Encrypt/decrypt OAuth tokens"""

    def __init__(self):
        # Use Django SECRET_KEY as basis for encryption key
        key = base64.urlsafe_b64encode(
            settings.SECRET_KEY[:32].encode().ljust(32)[:32]
        )
        self.cipher = Fernet(key)

    def encrypt(self, token: str) -> str:
        """Encrypt token"""
        if not token:
            return ""
        encrypted = self.cipher.encrypt(token.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt token"""
        if not encrypted_token:
            return ""
        decrypted = self.cipher.decrypt(encrypted_token.encode())
        return decrypted.decode()
```

### 4. Create OAuth Service

```python
# backend/apps/tiktok_accounts/services/tiktok-oauth-service.py
from urllib.parse import urlencode
from typing import Dict, Any
from datetime import datetime, timedelta
from config.tiktok-config import TikTokConfig
from core.utils.tiktok-api-client import TikTokAPIClient
from core.utils.token-encryption import TokenEncryption
import secrets

class TikTokOAuthService:
    """Handle TikTok OAuth authentication flow"""

    def __init__(self):
        self.config = TikTokConfig()
        self.client = TikTokAPIClient()
        self.encryptor = TokenEncryption()

    def get_authorization_url(self, state: str = None) -> str:
        """Generate OAuth authorization URL"""
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            'client_key': self.config.CLIENT_KEY,
            'scope': ','.join(self.config.SCOPES),
            'response_type': 'code',
            'redirect_uri': self.config.REDIRECT_URI,
            'state': state,
        }

        return f"{self.config.OAUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            'client_key': self.config.CLIENT_KEY,
            'client_secret': self.config.CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.config.REDIRECT_URI,
        }

        response = self.client.post(self.config.TOKEN_URL, data=data)

        return {
            'access_token': self.encryptor.encrypt(response['access_token']),
            'refresh_token': self.encryptor.encrypt(response.get('refresh_token', '')),
            'expires_in': response['expires_in'],
            'token_expires_at': datetime.now() + timedelta(seconds=response['expires_in']),
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        decrypted_token = self.encryptor.decrypt(refresh_token)

        data = {
            'client_key': self.config.CLIENT_KEY,
            'client_secret': self.config.CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': decrypted_token,
        }

        response = self.client.post(self.config.TOKEN_URL, data=data)

        return {
            'access_token': self.encryptor.encrypt(response['access_token']),
            'refresh_token': self.encryptor.encrypt(response.get('refresh_token', '')),
            'expires_in': response['expires_in'],
            'token_expires_at': datetime.now() + timedelta(seconds=response['expires_in']),
        }
```

### 5. Create Account Service

```python
# backend/apps/tiktok_accounts/services/tiktok-account-service.py
from typing import Dict, Any
from config.tiktok-config import TikTokConfig
from core.utils.tiktok-api-client import TikTokAPIClient
from core.utils.token-encryption import TokenEncryption

class TikTokAccountService:
    """Manage TikTok account operations"""

    def __init__(self, access_token: str):
        self.config = TikTokConfig()
        self.encryptor = TokenEncryption()
        decrypted_token = self.encryptor.decrypt(access_token)
        self.client = TikTokAPIClient(decrypted_token)

    def get_user_info(self) -> Dict[str, Any]:
        """Fetch TikTok user information"""
        url = f"{self.config.API_BASE_URL}user/info/"
        params = {'fields': 'open_id,union_id,avatar_url,display_name,username'}

        response = self.client.get(url, params=params)
        return response.get('data', {}).get('user', {})

    def get_user_videos(self, cursor: int = 0, max_count: int = 20) -> Dict[str, Any]:
        """Fetch user's video list"""
        url = f"{self.config.API_BASE_URL}video/list/"
        params = {
            'fields': 'id,title,video_description,create_time,cover_image_url',
            'cursor': cursor,
            'max_count': max_count,
        }

        response = self.client.get(url, params=params)
        return response.get('data', {})
```

### 6. Create Video Upload Service

```python
# backend/apps/content/services/tiktok-video-service.py
from typing import Dict, Any, BinaryIO
from config.tiktok-config import TikTokConfig
from core.utils.tiktok-api-client import TikTokAPIClient
from core.utils.token-encryption import TokenEncryption
import logging

logger = logging.getLogger(__name__)

class TikTokVideoService:
    """Handle TikTok video upload and publishing"""

    def __init__(self, access_token: str):
        self.config = TikTokConfig()
        self.encryptor = TokenEncryption()
        decrypted_token = self.encryptor.decrypt(access_token)
        self.client = TikTokAPIClient(decrypted_token)

    def initiate_upload(self) -> Dict[str, Any]:
        """Initialize video upload session"""
        url = f"{self.config.API_BASE_URL}post/publish/video/init/"

        data = {
            'post_info': {
                'title': '',
                'privacy_level': 'SELF_ONLY',  # Will be updated later
                'disable_duet': False,
                'disable_comment': False,
                'disable_stitch': False,
                'video_cover_timestamp_ms': 1000,
            },
            'source_info': {
                'source': 'FILE_UPLOAD',
                'post_mode': 'DIRECT_POST',
            }
        }

        response = self.client.post(url, json=data)
        return response.get('data', {})

    def upload_video_chunk(self, upload_url: str, video_file: BinaryIO,
                          chunk_size: int = 10485760) -> bool:
        """Upload video file in chunks (10MB default)"""
        try:
            # For simplicity, upload entire file
            # In production, implement chunked upload for large files
            files = {'video': video_file}
            response = self.client.session.put(upload_url, files=files)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Video upload failed: {str(e)}")
            return False

    def publish_video(self, publish_id: str, caption: str,
                     privacy_level: str = 'PUBLIC_TO_EVERYONE',
                     disable_comment: bool = False) -> Dict[str, Any]:
        """Publish uploaded video"""
        url = f"{self.config.API_BASE_URL}post/publish/status/fetch/"

        params = {'publish_id': publish_id}
        response = self.client.post(url, json=params)

        return response.get('data', {})
```

### 7. Create Rate Limiter

```python
# backend/core/utils/rate-limiter.py
from django.core.cache import cache
from datetime import datetime
import time

class RateLimiter:
    """Rate limiting for API calls"""

    def __init__(self, key_prefix: str, max_calls: int, time_window: int):
        """
        Args:
            key_prefix: Cache key prefix
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.key_prefix = key_prefix
        self.max_calls = max_calls
        self.time_window = time_window

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        cache_key = f"{self.key_prefix}:{identifier}"
        current_calls = cache.get(cache_key, 0)

        if current_calls >= self.max_calls:
            return False

        cache.set(cache_key, current_calls + 1, self.time_window)
        return True

    def wait_if_needed(self, identifier: str) -> None:
        """Wait if rate limit exceeded"""
        while not self.is_allowed(identifier):
            time.sleep(1)
```

## Todo List

### Completed (13/17)
- [x] Install required packages (requests, cryptography)
- [x] Create TikTok API configuration
- [x] Implement API client with retry logic
- [x] Create token encryption utility (Phase 02 EncryptedTextField)
- [x] Implement OAuth service
- [x] Create account service
- [x] Implement video upload service
- [x] Create rate limiter
- [x] Add TikTok credentials to .env
- [x] Create API endpoints for OAuth flow
- [x] Implement error handling
- [x] Add comprehensive logging
- [x] Write unit tests for services

### Pending Manual Testing (4/17)
- [ ] Test OAuth authorization flow (requires TikTok Dev Account)
- [ ] Test token refresh mechanism (requires live tokens)
- [ ] Test account info retrieval (requires live API)
- [ ] Test video upload (requires live API + video file)

### Critical Issues Found (Code Review 2025-12-04)
See: `reports/code-reviewer-251204-phase03-tiktok-api-integration.md`

**BLOCKERS:**
- [ ] 🔴 Fix token logging audit (security)
- [ ] 🔴 Add CRYPTOGRAPHY_KEY validation (security)
- [ ] 🔴 Fix rate limiter race condition (performance)
- [ ] 🟠 Implement automatic token refresh service (architecture)
- [ ] 🟠 Add custom exception hierarchy (error handling)
- [ ] 🟠 Fix video upload memory issue (performance)

## Success Criteria

### Implementation Status
- ✅ OAuth flow completes successfully (code complete, needs live testing)
- ✅ Tokens stored encrypted in database (EncryptedTextField working)
- ⚠️ Token refresh works automatically (service missing - needs implementation)
- ✅ Account info retrieval successful (code complete, needs live testing)
- ✅ Video upload completes (code complete, needs live testing)
- ⚠️ Rate limiting prevents API throttling (race condition found - needs fix)
- ⚠️ Error handling catches all API errors (insufficient granularity - needs improvement)
- ✅ Retry logic works for transient failures (exponential backoff implemented)

### Overall Phase Status
**Status:** ⚠️ **Implementation Complete with Critical Issues**

**Blockers before Phase 04:**
1. Security: Token logging audit + key validation
2. Performance: Rate limiter atomicity fix
3. Architecture: Token refresh automation service
4. Testing: Manual testing with live TikTok API

**See detailed review:** `reports/code-reviewer-251204-phase03-tiktok-api-integration.md`

## Risk Assessment

**Risk:** TikTok API changes or deprecation
**Mitigation:** Abstract API calls behind service layer, monitor TikTok developer portal

**Risk:** Rate limit exceeded causing delays
**Mitigation:** Implement queuing system, circuit breaker pattern

**Risk:** Token encryption key compromise
**Mitigation:** Use environment-specific keys, rotate regularly, consider using KMS

**Risk:** Large video upload failures
**Mitigation:** Implement chunked upload, resume capability, timeout handling

## Security Considerations

- Never log access tokens or refresh tokens
- Encrypt tokens at rest in database
- Use HTTPS for all OAuth redirects
- Validate OAuth state parameter to prevent CSRF
- Implement token rotation on refresh
- Store client secret in environment variables only
- Use secure random state generation
- Implement request signing if supported by API

## Next Steps

After Phase 03 completion:
1. Proceed to Phase 04: Backend API Development
2. Create REST endpoints for account management
3. Build scheduling queue system
4. Integrate video upload with scheduled posts
