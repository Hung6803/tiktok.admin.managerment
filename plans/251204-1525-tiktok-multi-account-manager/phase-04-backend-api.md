# Phase 04: Backend API Development

**Priority:** High
**Status:** Ready After Phase 03
**Estimated Time:** 6-8 hours

## Context Links

- [Main Plan](./plan.md)
- [Phase 02: Database Schema](./phase-02-database-schema.md)
- [Phase 03: TikTok API Integration](./phase-03-tiktok-api-integration.md)

## Overview

Build RESTful API using Django Ninja for account management, content scheduling, media uploads, and publishing queue operations.

## Key Insights

- Django Ninja provides FastAPI-like syntax for Django
- Use Pydantic schemas for request/response validation
- Implement JWT authentication for API access
- Paginate list endpoints
- Use background tasks for heavy operations
- Implement proper error responses with status codes

## Requirements

### Functional Requirements
- User authentication (JWT)
- TikTok account CRUD operations
- OAuth callback handling
- Scheduled post management
- Media file upload
- Publishing queue operations
- Analytics data retrieval

### Non-Functional Requirements
- API response time < 200ms (excluding uploads)
- Proper HTTP status codes
- Comprehensive error messages
- Request validation
- API documentation (auto-generated)
- Rate limiting per user

## Architecture

```
API Endpoints Structure:

/api/v1/
├── /auth
│   ├── POST /register
│   ├── POST /login
│   ├── POST /logout
│   └── POST /refresh
├── /tiktok
│   ├── GET  /auth/url
│   ├── GET  /callback
│   ├── GET  /accounts
│   ├── GET  /accounts/{id}
│   ├── DELETE /accounts/{id}
│   └── POST /accounts/{id}/sync
├── /posts
│   ├── GET  /
│   ├── POST /
│   ├── GET  /{id}
│   ├── PUT  /{id}
│   ├── DELETE /{id}
│   └── POST /{id}/publish-now
├── /media
│   ├── POST /upload
│   └── GET  /{id}
└── /analytics
    ├── GET /accounts/{id}/stats
    └── GET /accounts/{id}/history
```

## Related Code Files

### Files to Create
- `backend/api/v1/__init__.py`
- `backend/api/v1/auth-router.py`
- `backend/api/v1/tiktok-accounts-router.py`
- `backend/api/v1/posts-router.py`
- `backend/api/v1/media-router.py`
- `backend/api/v1/analytics-router.py`
- `backend/api/schemas/auth-schemas.py`
- `backend/api/schemas/tiktok-account-schemas.py`
- `backend/api/schemas/post-schemas.py`
- `backend/api/schemas/media-schemas.py`
- `backend/core/auth/jwt-handler.py`
- `backend/core/middleware/auth-middleware.py`
- `backend/core/middleware/rate-limit-middleware.py`

## Implementation Steps

### 1. Setup Django Ninja

```python
# backend/config/urls.py
from django.urls import path
from ninja import NinjaAPI
from api.v1 import auth_router, tiktok_router, posts_router, media_router, analytics_router

api = NinjaAPI(
    title="TikTok Manager API",
    version="1.0.0",
    description="Multi-account TikTok management and scheduling API"
)

# Register routers
api.add_router("/auth/", auth_router.router, tags=["Authentication"])
api.add_router("/tiktok/", tiktok_router.router, tags=["TikTok Accounts"])
api.add_router("/posts/", posts_router.router, tags=["Scheduled Posts"])
api.add_router("/media/", media_router.router, tags=["Media"])
api.add_router("/analytics/", analytics_router.router, tags=["Analytics"])

urlpatterns = [
    path("api/v1/", api.urls),
]
```

### 2. Create Pydantic Schemas

```python
# backend/api/schemas/auth-schemas.py
from pydantic import BaseModel, EmailStr, Field

class UserRegisterSchema(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    timezone: str = Field(default="UTC")

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserSchema(BaseModel):
    id: str
    email: str
    username: str
    timezone: str
    created_at: str
```

```python
# backend/api/schemas/tiktok-account-schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TikTokAccountSchema(BaseModel):
    id: str
    tiktok_user_id: str
    username: str
    display_name: str
    avatar_url: Optional[str]
    status: str
    follower_count: int
    following_count: int
    video_count: int
    last_synced_at: Optional[datetime]
    created_at: datetime

class TikTokAccountListSchema(BaseModel):
    accounts: list[TikTokAccountSchema]
    total: int
    page: int
    per_page: int
```

```python
# backend/api/schemas/post-schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ScheduledPostCreateSchema(BaseModel):
    tiktok_account_id: str
    caption: str = Field(..., max_length=2200)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    privacy_level: str = Field(default="public")
    scheduled_time: datetime
    timezone: str = Field(default="UTC")

class ScheduledPostUpdateSchema(BaseModel):
    caption: Optional[str] = Field(None, max_length=2200)
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    privacy_level: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    timezone: Optional[str] = None

class ScheduledPostSchema(BaseModel):
    id: str
    tiktok_account_id: str
    status: str
    caption: str
    hashtags: List[str]
    mentions: List[str]
    privacy_level: str
    scheduled_time: datetime
    timezone: str
    published_at: Optional[datetime]
    tiktok_video_id: Optional[str]
    video_url: Optional[str]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime

class ScheduledPostListSchema(BaseModel):
    posts: List[ScheduledPostSchema]
    total: int
    page: int
    per_page: int
```

### 3. Create JWT Authentication

```python
# backend/core/auth/jwt-handler.py
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from django.conf import settings
from apps.accounts.models.user-model import User

class JWTHandler:
    """Handle JWT token creation and validation"""

    @staticmethod
    def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create access token"""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)

        payload = {
            'user_id': str(user_id),
            'exp': datetime.utcnow() + expires_delta,
            'iat': datetime.utcnow(),
            'type': 'access'
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create refresh token"""
        payload = {
            'user_id': str(user_id),
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def decode_token(token: str) -> Dict:
        """Decode and validate token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")

    @staticmethod
    def get_user_from_token(token: str) -> Optional[User]:
        """Get user from token"""
        try:
            payload = JWTHandler.decode_token(token)
            user_id = payload.get('user_id')
            return User.objects.filter(id=user_id, is_deleted=False).first()
        except Exception:
            return None
```

### 4. Create Authentication Router

```python
# backend/api/v1/auth-router.py
from ninja import Router
from django.contrib.auth.hashers import make_password, check_password
from api.schemas.auth-schemas import (
    UserRegisterSchema, UserLoginSchema, TokenSchema, UserSchema
)
from apps.accounts.models.user-model import User
from core.auth.jwt-handler import JWTHandler

router = Router()

@router.post("/register", response=TokenSchema)
def register(request, data: UserRegisterSchema):
    """Register new user"""
    # Check if email exists
    if User.objects.filter(email=data.email, is_deleted=False).exists():
        return 400, {"message": "Email already registered"}

    # Create user
    user = User.objects.create(
        email=data.email,
        username=data.username,
        password=make_password(data.password),
        timezone=data.timezone
    )

    # Generate tokens
    access_token = JWTHandler.create_access_token(user.id)
    refresh_token = JWTHandler.create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/login", response=TokenSchema)
def login(request, data: UserLoginSchema):
    """Login user"""
    user = User.objects.filter(email=data.email, is_deleted=False).first()

    if not user or not check_password(data.password, user.password):
        return 401, {"message": "Invalid credentials"}

    # Generate tokens
    access_token = JWTHandler.create_access_token(user.id)
    refresh_token = JWTHandler.create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response=TokenSchema)
def refresh(request, refresh_token: str):
    """Refresh access token"""
    try:
        payload = JWTHandler.decode_token(refresh_token)

        if payload.get('type') != 'refresh':
            return 401, {"message": "Invalid token type"}

        user_id = payload.get('user_id')
        new_access_token = JWTHandler.create_access_token(user_id)

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        return 401, {"message": str(e)}
```

### 5. Create TikTok Accounts Router

```python
# backend/api/v1/tiktok-accounts-router.py
from ninja import Router
from typing import List
from ninja.security import HttpBearer
from api.schemas.tiktok-account-schemas import TikTokAccountSchema, TikTokAccountListSchema
from apps.tiktok_accounts.models.tiktok-account-model import TikTokAccount
from apps.tiktok_accounts.services.tiktok-oauth-service import TikTokOAuthService
from apps.tiktok_accounts.services.tiktok-account-service import TikTokAccountService
from core.auth.jwt-handler import JWTHandler

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        user = JWTHandler.get_user_from_token(token)
        if user:
            return user
        return None

router = Router(auth=AuthBearer())

@router.get("/auth/url")
def get_auth_url(request):
    """Get TikTok OAuth authorization URL"""
    oauth_service = TikTokOAuthService()
    auth_url = oauth_service.get_authorization_url()
    return {"auth_url": auth_url}

@router.get("/callback")
def oauth_callback(request, code: str, state: str):
    """Handle OAuth callback"""
    oauth_service = TikTokOAuthService()

    # Exchange code for token
    token_data = oauth_service.exchange_code_for_token(code)

    # Get user info
    account_service = TikTokAccountService(token_data['access_token'])
    user_info = account_service.get_user_info()

    # Create or update TikTok account
    account, created = TikTokAccount.objects.update_or_create(
        tiktok_user_id=user_info['open_id'],
        defaults={
            'user': request.auth,
            'username': user_info.get('username', ''),
            'display_name': user_info.get('display_name', ''),
            'avatar_url': user_info.get('avatar_url'),
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'token_expires_at': token_data['token_expires_at'],
            'status': 'active',
        }
    )

    return {"success": True, "account_id": str(account.id)}

@router.get("/accounts", response=TikTokAccountListSchema)
def list_accounts(request, page: int = 1, per_page: int = 20):
    """List user's TikTok accounts"""
    accounts = TikTokAccount.objects.filter(
        user=request.auth,
        is_deleted=False
    ).order_by('-created_at')

    total = accounts.count()
    offset = (page - 1) * per_page
    paginated = accounts[offset:offset + per_page]

    return {
        "accounts": list(paginated),
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.get("/accounts/{account_id}", response=TikTokAccountSchema)
def get_account(request, account_id: str):
    """Get TikTok account details"""
    account = TikTokAccount.objects.filter(
        id=account_id,
        user=request.auth,
        is_deleted=False
    ).first()

    if not account:
        return 404, {"message": "Account not found"}

    return account

@router.delete("/accounts/{account_id}")
def delete_account(request, account_id: str):
    """Delete TikTok account"""
    account = TikTokAccount.objects.filter(
        id=account_id,
        user=request.auth,
        is_deleted=False
    ).first()

    if not account:
        return 404, {"message": "Account not found"}

    # Soft delete
    account.is_deleted = True
    account.save()

    return {"success": True}

@router.post("/accounts/{account_id}/sync")
def sync_account(request, account_id: str):
    """Sync account data from TikTok"""
    account = TikTokAccount.objects.filter(
        id=account_id,
        user=request.auth,
        is_deleted=False
    ).first()

    if not account:
        return 404, {"message": "Account not found"}

    account_service = TikTokAccountService(account.access_token)
    user_info = account_service.get_user_info()

    # Update account data
    account.username = user_info.get('username', account.username)
    account.display_name = user_info.get('display_name', account.display_name)
    account.avatar_url = user_info.get('avatar_url', account.avatar_url)
    account.last_synced_at = datetime.now()
    account.save()

    return {"success": True}
```

### 6. Create Posts Router

```python
# backend/api/v1/posts-router.py
from ninja import Router
from ninja.security import HttpBearer
from datetime import datetime
from api.schemas.post-schemas import (
    ScheduledPostCreateSchema, ScheduledPostUpdateSchema,
    ScheduledPostSchema, ScheduledPostListSchema
)
from apps.content.models.scheduled-post-model import ScheduledPost
from apps.tiktok_accounts.models.tiktok-account-model import TikTokAccount
from core.auth.jwt-handler import JWTHandler

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        user = JWTHandler.get_user_from_token(token)
        return user if user else None

router = Router(auth=AuthBearer())

@router.post("/", response=ScheduledPostSchema)
def create_post(request, data: ScheduledPostCreateSchema):
    """Create scheduled post"""
    # Verify account ownership
    account = TikTokAccount.objects.filter(
        id=data.tiktok_account_id,
        user=request.auth,
        is_deleted=False
    ).first()

    if not account:
        return 404, {"message": "TikTok account not found"}

    post = ScheduledPost.objects.create(
        tiktok_account=account,
        caption=data.caption,
        hashtags=data.hashtags,
        mentions=data.mentions,
        privacy_level=data.privacy_level,
        scheduled_time=data.scheduled_time,
        timezone=data.timezone,
        status='scheduled'
    )

    return post

@router.get("/", response=ScheduledPostListSchema)
def list_posts(request, status: str = None, page: int = 1, per_page: int = 20):
    """List scheduled posts"""
    posts = ScheduledPost.objects.filter(
        tiktok_account__user=request.auth,
        is_deleted=False
    )

    if status:
        posts = posts.filter(status=status)

    total = posts.count()
    offset = (page - 1) * per_page
    paginated = posts.order_by('-scheduled_time')[offset:offset + per_page]

    return {
        "posts": list(paginated),
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.get("/{post_id}", response=ScheduledPostSchema)
def get_post(request, post_id: str):
    """Get scheduled post"""
    post = ScheduledPost.objects.filter(
        id=post_id,
        tiktok_account__user=request.auth,
        is_deleted=False
    ).first()

    if not post:
        return 404, {"message": "Post not found"}

    return post

@router.put("/{post_id}", response=ScheduledPostSchema)
def update_post(request, post_id: str, data: ScheduledPostUpdateSchema):
    """Update scheduled post"""
    post = ScheduledPost.objects.filter(
        id=post_id,
        tiktok_account__user=request.auth,
        is_deleted=False,
        status__in=['draft', 'scheduled']
    ).first()

    if not post:
        return 404, {"message": "Post not found or cannot be edited"}

    # Update fields
    if data.caption is not None:
        post.caption = data.caption
    if data.hashtags is not None:
        post.hashtags = data.hashtags
    if data.mentions is not None:
        post.mentions = data.mentions
    if data.privacy_level is not None:
        post.privacy_level = data.privacy_level
    if data.scheduled_time is not None:
        post.scheduled_time = data.scheduled_time
    if data.timezone is not None:
        post.timezone = data.timezone

    post.save()
    return post

@router.delete("/{post_id}")
def delete_post(request, post_id: str):
    """Delete scheduled post"""
    post = ScheduledPost.objects.filter(
        id=post_id,
        tiktok_account__user=request.auth,
        is_deleted=False
    ).first()

    if not post:
        return 404, {"message": "Post not found"}

    post.is_deleted = True
    post.save()

    return {"success": True}

@router.post("/{post_id}/publish-now")
def publish_now(request, post_id: str):
    """Publish post immediately"""
    post = ScheduledPost.objects.filter(
        id=post_id,
        tiktok_account__user=request.auth,
        is_deleted=False,
        status__in=['draft', 'scheduled']
    ).first()

    if not post:
        return 404, {"message": "Post not found or cannot be published"}

    # Queue for immediate publishing
    post.status = 'queued'
    post.scheduled_time = datetime.now()
    post.save()

    # Trigger async task (will implement in Phase 05)
    # publish_post_task.delay(post.id)

    return {"success": True, "message": "Post queued for publishing"}
```

## Todo List

- [ ] Install Django Ninja
- [ ] Create API structure
- [ ] Implement Pydantic schemas
- [ ] Create JWT authentication handler
- [ ] Implement auth middleware
- [ ] Create authentication router
- [ ] Create TikTok accounts router
- [ ] Create posts router
- [ ] Create media router
- [ ] Create analytics router
- [ ] Add input validation
- [ ] Implement error handling
- [ ] Add rate limiting
- [ ] Test all endpoints
- [ ] Generate API documentation
- [ ] Write integration tests

## Success Criteria

- ✅ All endpoints respond correctly
- ✅ JWT authentication works
- ✅ Request validation catches errors
- ✅ Proper error responses
- ✅ API documentation auto-generated
- ✅ Response time < 200ms
- ✅ Pagination works correctly
- ✅ Rate limiting prevents abuse

## Risk Assessment

**Risk:** Authentication bypass vulnerabilities
**Mitigation:** Implement comprehensive auth tests, use established JWT library

**Risk:** SQL injection through query parameters
**Mitigation:** Use Django ORM exclusively, validate all inputs

**Risk:** Excessive data exposure in responses
**Mitigation:** Use Pydantic schemas to control response fields

## Security Considerations

- Validate all user inputs
- Never expose sensitive data (tokens, passwords)
- Implement CSRF protection
- Use HTTPS only in production
- Rate limit by IP and user
- Log failed authentication attempts
- Implement request timeouts
- Sanitize error messages

## Next Steps

After Phase 04 completion:
1. Proceed to Phase 05: Scheduling System
2. Implement Celery workers
3. Create publishing queue processor
4. Add retry logic for failed publishes
