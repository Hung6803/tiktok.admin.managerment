# TikTok API OAuth 2.0 Authentication Research

## Developer Access Requirements (2024)

### Registration Process
- Register at: https://developers.tiktok.com/
- Provide:
  - Terms of Service URL (https)
  - Privacy Policy URL (https)
  - Redirect URI(s) (1-10 URIs)
- Approval time: 1-3 days

### OAuth 2.0 Flow Components
- Authorization Endpoint: `https://www.tiktok.com/v2/auth/authorize/`
- Token Endpoint: `https://open.tiktokapis.com/v2/oauth/token/`

### Authentication Parameters
- `client_key`
- `client_secret`
- `code` (authorization code)
- `grant_type` (authorization_code)
- `redirect_uri`

## API Endpoints & Limitations

### Video Upload Endpoint
- Base URL: `https://open.tiktokapis.com/v2/post/publish/inbox/video/init/`

### Rate Limits
- 6 requests/minute per user access token
- 15 video uploads/24 hours
- 600 requests/minute per endpoint

### Required Scopes
- `video.upload`: For video publishing
- `user.info.basic`: For basic user information

## Error Handling Best Practices

### Retry Strategy
- Exponential backoff
- Start: 1-second delay
- Maximum: 300 seconds
- Add random jitter to prevent synchronized retries

### Webhook Retry
- TikTok will retry delivery for 72 hours
- Exponential backoff mechanism

## Security Considerations
- Prevent request forgery using state parameter
- Secure token management
- Use Bearer token in Authorization header

## Unresolved Questions
1. Exact pricing for higher API tiers
2. Comprehensive list of all available scopes
3. Detailed process for API client audit

## Documentation Links
- OAuth v2 Guide: https://developers.tiktok.com/doc/oauth-user-access-token-management
- Content Posting API: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
- Rate Limits: https://developers.tiktok.com/doc/tiktok-api-v2-rate-limit

**Note:** Always refer to the most recent TikTok Developer documentation for the latest updates.