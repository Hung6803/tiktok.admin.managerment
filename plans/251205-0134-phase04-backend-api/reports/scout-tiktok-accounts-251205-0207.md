# TikTok Accounts Implementation Scout Report

## Key Files
- `backend/apps/tiktok_accounts/models/tiktok_account_model.py`
- `backend/apps/tiktok_accounts/services/tiktok_account_service.py`
- `backend/apps/tiktok_accounts/services/tiktok_oauth_service.py`

## TikTokAccount Model Details
### Fields
- `user`: Foreign key to User model (CASCADE)
- `tiktok_user_id`: Unique TikTok user identifier
- `username`, `display_name`: User profile details
- `avatar_url`: Profile picture URL
- `status`: Account connection status (active/expired/revoked/error)
- `access_token`, `refresh_token`: Encrypted OAuth tokens
- `token_expires_at`: Token expiration timestamp
- Metadata: `follower_count`, `following_count`, `video_count`
- `last_synced_at`, `last_refreshed`, `last_error`

### Key Methods
- `is_token_expired()`: Check token expiration
- `needs_refresh()`: Identify tokens expiring within 1 hour

## TikTokAccountService Capabilities
### User Information
- `get_user_info()`: Fetch TikTok user profile
  - Returns: open_id, union_id, avatar_url, display_name, username

### Video Retrieval
- `get_user_videos()`: Fetch user's video list
  - Supports pagination via cursor
  - Returns max 20 videos per request
  - Fields: video ID, title, description, create time, cover image, share URL

## TikTokOAuthService Workflow
### Authorization Flow
- `get_authorization_url()`: Generate OAuth authorization URL
- `exchange_code_for_token()`: Convert authorization code to access token
- `refresh_access_token()`: Renew expired access tokens
- `validate_state()`: CSRF protection for OAuth callbacks

## Implementation Notes
- Uses encrypted token storage
- Supports token lifecycle management
- Implements soft delete via `is_deleted` flag
- Detailed logging for OAuth and API interactions

## Unresolved Questions
- Rate limits for TikTok API methods
- Error handling for token refresh failures
- Detailed sync strategy for user metadata
