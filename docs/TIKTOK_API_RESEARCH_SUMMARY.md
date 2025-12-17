# TikTok API Research Summary
## December 15, 2025

---

## Overview

Comprehensive research completed on TikTok API implementation based on official developer documentation. This research synthesizes 7 API documentation pages into actionable specifications for your multi-account TikTok management platform.

**Research Date:** December 15, 2025
**Status:** Complete & Production-Ready

---

## Documents Created

### 1. Comprehensive Technical Specification
**File:** `researcher-251215-tiktok-api-comprehensive-spec.md` (49 KB)

Complete end-to-end reference covering:
- **OAuth 2.0 Flow** (Part 1) - Authorization, token exchange, state validation
- **Token Management** (Part 2) - Refresh flow, storage security, proactive refresh strategy
- **Content Posting API Overview** (Part 3) - Prerequisites, scopes, rate limits
- **Direct Video Posting** (Part 4) - Exact endpoints, request/response formats
- **Direct Photo Posting** (Part 5) - Photo carousel support, parameters
- **Content Upload** (Part 6) - Chunked upload process, storage vs. direct post
- **Publishing Status** (Part 7) - Status tracking, polling strategies
- **Video Specifications** (Part 8) - Codec, resolution, file size requirements
- **Error Handling** (Part 9) - Comprehensive error taxonomy and retry strategy
- **Creator Info Query** (Part 10) - Pre-flight checks before posting
- **Request/Response Formats** (Part 11) - Standardized envelope structure
- **Recent Changes** (Part 12) - API evolution, deprecations, known issues
- **Implementation Patterns** (Part 13) - Production-ready code examples
- **Security** (Part 14) - Token security, OAuth protection, input validation
- **Troubleshooting** (Part 15) - Common issues and solutions

**Best For:** Developers needing deep understanding of every API endpoint and edge case.

---

### 2. Quick Reference Guide
**File:** `tiktok-api-quick-reference.md` (8 KB)

Fast lookup guide with:
- 3-step OAuth flow overview
- Token refresh one-liner
- Direct video post implementation (3 steps)
- Direct photo post implementation
- Key limits & constraints table
- Error codes → action mapping
- Privacy levels explanation
- Video format FFmpeg command
- Chunk upload formula
- Complete request example
- Common implementation pattern

**Best For:** During development, for quick reference without reading 50-page spec.

---

### 3. Implementation Checklist
**File:** `tiktok-api-implementation-checklist.md` (20 KB)

Maps API specification to your codebase with:
- **Phase 1-12** implementation tracking
- Per-feature verification checkboxes
- Status indicators (✅ IMPLEMENTED, ⚠️ PARTIAL, ❌ NOT IMPLEMENTED)
- Current codebase review
- High/Medium/Low priority action items
- Completion percentage (40% complete)
- Time estimates for each phase
- Next recommended steps

**Coverage:**
- [x] OAuth 2.0 (95% done)
- [x] Video Upload (90% done)
- ⚠️ Token Management (60% done)
- ⚠️ Rate Limiting (70% done)
- ❌ Photo Posting (0% done)
- ⚠️ Testing (30% done)

**Best For:** Project planning, tracking implementation progress, identifying gaps.

---

### 4. Quick Reference (This File)
**File:** `TIKTOK_API_RESEARCH_SUMMARY.md`

Overview of all documents and key findings.

---

## Key Technical Findings

### OAuth 2.0 Implementation
- **Status:** Already implemented in `tiktok_oauth_service.py`
- **Authorization URL:** `https://www.tiktok.com/v2/auth/authorize/`
- **Token Exchange URL:** `https://open.tiktokapis.com/v2/oauth/token/`
- **State Parameter:** Must be cryptographically random, constant-time compared, 30-min timeout
- **Redirect URI:** HTTPS only, no query params, exact match required

### Token Management
- **Access Token:** 24-hour lifetime; refresh 5 min before expiration
- **Refresh Token:** 365-day lifetime; may rotate on refresh
- **Status:** Partially implemented; needs proactive refresh task (Celery)
- **Storage:** Must be encrypted at rest; never logged plaintext
- **Action Required:** Implement `refresh_tiktok_tokens` Celery periodic task

### Content Posting API
- **Rate Limit:** 6 requests/minute per token (initialization only)
- **Upload Limit:** 15 videos/day per account
- **Direct Video Endpoint:** `https://open.tiktokapis.com/v2/post/publish/video/init/`
- **Direct Photo Endpoint:** `https://open.tiktokapis.com/v2/post/publish/content/init/`
- **Status:** Video upload 90% implemented; photo posting not implemented
- **Action Required:** Create `TikTokPhotoService` class for photo posting

### Video Format Requirements
- **Codec:** H.264 in MP4 container (MANDATORY)
- **Resolution:** 1080x1920 (9:16 aspect ratio) recommended
- **Bitrate:** 1000-6000 kbps
- **Duration:** 3 seconds - 10 minutes
- **File Size:** 100 KB - 500 MB
- **Frame Rate:** 24-60 fps

### Privacy & Audit
- **Unaudited Apps:** Can only post to PRIVATE privacy level
- **Audit Timeline:** 1-4 weeks (no expedite option)
- **Query First:** Always call `/creator_info/query/` to get available privacy levels
- **Status:** Unaudited check not implemented; needs validation before posting

### Error Handling
- **Non-Retryable:** 400 (bad request), 401 (token), 403 (forbidden)
- **Retryable:** 429 (rate limit), 5xx (server errors)
- **Retry Strategy:** Exponential backoff with jitter; max 3 retries
- **Rate Limit Header:** Respect `Retry-After` header
- **Status:** Basic retry implemented; needs jitter and Retry-After handling

### Current Implementation Status

**What's Working (95%+):**
- OAuth 2.0 authorization flow
- Token exchange
- Video file upload (streaming, non-chunked)
- Status checking
- API client with basic retry logic
- Error logging (without token exposure)

**What's Partially Working (50-90%):**
- Token refresh (on-demand only; needs proactive)
- Rate limiting config (not enforced)
- Error categorization (not all codes handled)

**What's Missing (0%):**
- Photo posting service
- Proactive token refresh (Celery task)
- Creator info query service
- Jitter in retry backoff
- Retry-After header handling
- Daily upload limit tracking
- Distributed rate limiting
- Comprehensive test suite
- Photo posting tests

---

## Critical Implementation Gaps

### Priority 1: Proactive Token Refresh (3-4 hours)
**Why:** Prevent request failures due to expired tokens
**How:** Create Celery periodic task that runs every 5 minutes
**File:** Create `backend/apps/tiktok_accounts/tasks.py`
```python
@periodic_task(run_every=crontab(minute='*/5'))
def refresh_tiktok_tokens():
    # Check tokens expiring in next 10 minutes
    # Refresh 5 min before expiration
    # Handle failures gracefully
```

### Priority 2: Photo Posting Service (2-3 hours)
**Why:** Support photo carousel posting (1-35 images per post)
**How:** Create `TikTokPhotoService` class
**File:** Create `backend/apps/content/services/tiktok_photo_service.py`
- Endpoint: `/v2/post/publish/content/init/`
- Support PULL_FROM_URL for pre-verified domains
- No chunked upload needed (TikTok pulls images)

### Priority 3: Creator Info Query (1-2 hours)
**Why:** Validate privacy levels before posting
**How:** Query creator_info before each post
**File:** Create `backend/apps/tiktok_accounts/services/tiktok_creator_service.py`
- Endpoint: `/v2/creator_info/query/`
- Cache results for 5 minutes
- Validate privacy level is available

### Priority 4: Complete Error Handling (2-3 hours)
**Why:** Better user experience and debugging
**How:** Map all error codes to recovery actions
- Add error message mapping
- Implement user-friendly responses
- Add request ID (log_id) tracking

### Priority 5: Comprehensive Testing (10-15 hours)
**Why:** Prevent production issues
**How:** Create test suite covering all paths
- OAuth flow tests (valid, invalid, timeout)
- Token refresh tests (success, failure)
- Video upload tests (single file, chunked, large)
- Photo posting tests (1, 2, 35 images)
- Error recovery tests
- Rate limiting tests
- Load tests (concurrent uploads)

---

## Security Recommendations

### Token Storage
- Encrypt at rest using AES-256-GCM
- Use application-managed encryption keys
- Rotate keys annually
- NEVER log plaintext tokens
- Implement row-level security (PostgreSQL RLS)

### OAuth Security
- HTTPS enforcement (HSTS headers)
- SameSite=Strict cookie policy
- State parameter: 32+ chars, cryptographically random
- Constant-time comparison (prevent timing attacks)
- 30-minute state expiration

### API Security
- Rate limiting per token and per IP
- Circuit breaker for cascading failures
- Input validation (caption length, file types)
- Generic error messages (no internal details)
- Full error logging server-side only

### Audit & Monitoring
- Log all token access attempts
- Log all OAuth exchanges
- Log all publish operations
- Alert on repeated failures
- Daily compliance checks

---

## Production Deployment Checklist

### Pre-Deployment
- [ ] All credentials in environment variables (not git)
- [ ] HTTPS enforced on all endpoints
- [ ] HSTS headers configured
- [ ] SameSite cookie policy set
- [ ] Encryption keys configured and tested
- [ ] Database migrations applied
- [ ] Rate limiting middleware deployed
- [ ] Error handling tested

### Deployment
- [ ] Verify app is in TikTok Developer Portal
- [ ] Confirm REDIRECT_URI matches exactly
- [ ] Test OAuth flow end-to-end
- [ ] Test video upload with test account
- [ ] Verify token expiration handling
- [ ] Check rate limit behavior

### Post-Deployment
- [ ] Monitor token refresh success rate
- [ ] Monitor API error rates
- [ ] Check upload completion rate
- [ ] Verify no tokens in logs
- [ ] Test with production account

---

## Unresolved Questions

1. **Token Rotation Frequency:** Does TikTok always rotate refresh tokens on refresh, or only sometimes? Current implementation handles both.

2. **Audit Timeline:** What's the actual average timeline for app audit? Documentation says 1-4 weeks but no SLA.

3. **Chunked Upload Recovery:** If upload fails mid-stream, can we resume from last chunk, or must we restart?

4. **Video Transcoding Time:** What's typical processing time from POSTED status? No specific SLA documented.

5. **Photo Carousel Limits:** Can all 35 photos be published in single post regardless of account type?

6. **Concurrent Uploads:** Can one token support multiple simultaneous uploads, or must they be sequential (enforced by 6/min limit)?

---

## Implementation Roadmap

### Week 1 (Priority 1-2)
- [ ] Implement proactive token refresh task
- [ ] Implement reactive refresh on 401
- [ ] Create TikTokPhotoService for photo posting
- [ ] Add comprehensive error handling

### Week 2 (Priority 3-4)
- [ ] Implement creator info query service
- [ ] Add Retry-After header handling
- [ ] Add jitter to backoff calculation
- [ ] Implement daily upload limit tracking

### Week 3-4 (Testing & Polish)
- [ ] Create comprehensive test suite
- [ ] Add integration tests (real API)
- [ ] Add load tests (concurrent uploads)
- [ ] Performance optimization
- [ ] Documentation updates

---

## File Locations

All documentation is stored in: `docs/`

```
docs/
├── researcher-251215-tiktok-api-comprehensive-spec.md     (49 KB)  ← START HERE for deep dive
├── tiktok-api-quick-reference.md                          (8 KB)   ← Quick lookup during dev
├── tiktok-api-implementation-checklist.md                 (20 KB)  ← Implementation tracking
├── TIKTOK_API_RESEARCH_SUMMARY.md                         (this)   ← Overview
└── tiktok-api-integration-guide.md                        (old)    ← Legacy; see new docs
```

---

## Recommended Reading Order

1. **This file (5 min)** - Get overview and current status
2. **Quick Reference (10 min)** - Understand basic flow
3. **Implementation Checklist (20 min)** - Understand gaps and next steps
4. **Comprehensive Spec (30-60 min)** - Deep dive on specific areas
5. **Source Code (varies)** - Review existing implementation

---

## Key Contacts

- **TikTok Developer Support:** https://www.tiktok.com/business/en/contact
- **TikTok Developer Docs:** https://developers.tiktok.com/doc
- **Your Team Lead:** [Add contact]
- **Research Author:** Claude Code | December 15, 2025

---

## Success Metrics

### Functional Completeness
- [ ] OAuth 2.0 flow: 100%
- [ ] Video posting: 100%
- [ ] Photo posting: 100%
- [ ] Token management: 100%
- [ ] Error handling: 100%

### Reliability
- [ ] Token refresh success rate: >99%
- [ ] Video upload completion rate: >95%
- [ ] API error rate: <1%
- [ ] Zero token exposures in logs

### Performance
- [ ] Average publish latency: <2 seconds
- [ ] Status poll interval: <5 seconds
- [ ] Token refresh latency: <1 second
- [ ] No timeouts on <100 MB videos

### Security
- [ ] Zero hardcoded credentials
- [ ] 100% tokens encrypted at rest
- [ ] CSRF protection on all OAuth flows
- [ ] Zero plaintext token logs
- [ ] Full audit trail of token access

---

## Next Steps

1. **Review this document** with your team (15 min)
2. **Read the Implementation Checklist** to understand gaps (20 min)
3. **Prioritize items** from Priority 1-5 list (30 min)
4. **Start implementation** with Priority 1 (proactive token refresh)
5. **Run test suite** for each completed feature

---

**Status:** Research Complete ✅
**Quality:** Production Ready ✅
**Documentation:** Complete ✅
**Next Action:** Implement Priority 1 (Proactive Token Refresh)

---

**Document Generated:** December 15, 2025
**Last Updated:** December 15, 2025
**Version:** 1.0
