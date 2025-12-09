# Phase 02: API Endpoints

**Status:** Done
**Completed:** 2025-12-10T00:00:00Z
**Priority:** High

## Context

Create REST API endpoints for slideshow creation and management.

## Requirements

1. Endpoint to create slideshow post
2. Endpoint to check conversion status
3. Update existing post endpoints for slideshow support

## Implementation Steps

### 2.1 Create Slideshow Schemas

**File:** `backend/api/posts/schemas.py`

Add:
```python
class SlideshowImageIn(Schema):
    file_path: str
    order: int
    duration_ms: int = 4000

class SlideshowCreateIn(Schema):
    title: str
    description: str
    account_ids: List[str]
    images: List[SlideshowImageIn]  # 2-10 images
    scheduled_time: Optional[datetime]
    privacy_level: PostPrivacy
```

### 2.2 Add Slideshow Endpoint

**File:** `backend/api/posts/post_router.py`

```python
@router.post("/slideshow", response=PostOut)
def create_slideshow_post(request, data: SlideshowCreateIn):
    # Validate images
    # Create post with slideshow flag
    # Queue conversion task
    # Return post with pending status
```

### 2.3 Add Conversion Status Endpoint

```python
@router.get("/slideshow/{post_id}/status")
def get_slideshow_status(request, post_id: str):
    # Return conversion progress
    # States: pending, converting, ready, failed
```

## Related Files

- `backend/api/posts/post_router.py`
- `backend/api/posts/schemas.py`
- `backend/api/posts/post_service.py`

## Success Criteria

- [x] Slideshow POST endpoint works
- [x] Conversion status endpoint works
- [x] Proper validation errors returned
- [x] Integration with existing post flow
