# Phase 01: Schema Validation Fixes

## Context
- **Parent Plan**: [Fix Phase 03 Critical Issues](./plan.md)
- **Dependencies**: None - Can run in parallel with Phase 02 & 03
- **Related Docs**: `docs/code-standards.md`, `docs/system-architecture.md`

## Parallelization Info
- **Parallel Group**: 1 (can run with Phase 02, Phase 03)
- **File Ownership**: Exclusive access to `backend/api/posts/schemas.py`
- **No Conflicts**: Other phases modify different files
- **Execution Order**: Any (independent)

## Overview
**Date**: 2025-12-05
**Priority**: P0 (Critical)
**Status**: ✅ COMPLETED
**Estimated Time**: 10 minutes
**Actual Time**: 5 minutes

Fix 2 critical validation issues in post schemas:
1. Timezone validation using wrong method (allows past scheduling)
2. Missing required fields in MediaIn schema

## Key Insights
- `datetime.now()` is timezone-naive, use `timezone.now()` from Django
- MediaIn schema must match PostMedia model requirements
- Pydantic validation happens before database insert
- Type validation prevents SQL injection at schema level

## Requirements

### Functional
- Prevent scheduling posts in the past
- Validate all required media fields before database insert
- Maintain backward compatibility with existing API contracts

### Non-Functional
- No performance impact
- Clear error messages for validation failures
- Type-safe validation

## Architecture

```
API Request → Pydantic Schema Validation → Service Layer → Database
                     ↑
              FIX HERE (schemas.py)
```

## Related Code Files

**Exclusive to this phase:**
- `backend/api/posts/schemas.py` (lines 1-133)

**Read-only references:**
- `backend/apps/content/models/post_media_model.py` (for field requirements)

## File Ownership

**Modified Files**:
- ✅ `backend/api/posts/schemas.py` - Full ownership, no other phase touches this

**Dependencies** :
- Django 5.0 (`django.utils.timezone`)
- Pydantic (`pydantic.field_validator`)

## Implementation Steps

### 1. Fix Timezone Validation (Issue #1)

**Location**: `backend/api/posts/schemas.py:60-66`

```python
# CURRENT (BROKEN):
from datetime import datetime

@field_validator('scheduled_time')
@classmethod
def validate_scheduled_time(cls, v):
    """Validate scheduled time is in future"""
    if v and v <= datetime.now():  # ❌ WRONG: timezone-naive
        raise ValueError('Scheduled time must be in the future')
    return v

# FIX TO:
from datetime import datetime
from django.utils import timezone  # ADD THIS IMPORT

@field_validator('scheduled_time')
@classmethod
def validate_scheduled_time(cls, v):
    """Validate scheduled time is in future"""
    if v and v <= timezone.now():  # ✅ CORRECT: timezone-aware
        raise ValueError('Scheduled time must be in the future')
    return v
```

**Changes**:
1. Add import: `from django.utils import timezone`
2. Replace `datetime.now()` with `timezone.now()` on line 64

### 2. Add Missing MediaIn Fields (Issue #4)

**Location**: `backend/api/posts/schemas.py:28-33`

```python
# CURRENT (INCOMPLETE):
class MediaIn(Schema):
    """Media input schema"""
    file_path: str
    media_type: str = "video"
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None

# FIX TO:
class MediaIn(Schema):
    """Media input schema"""
    file_path: str
    file_size: int  # ✅ ADD: Required by PostMedia model
    file_mime_type: str  # ✅ ADD: Required by PostMedia model
    media_type: str = "video"
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
```

**Changes**:
1. Add `file_size: int` field (required)
2. Add `file_mime_type: str` field (required)

### 3. Update Documentation

Add docstring details:
```python
class MediaIn(Schema):
    """
    Media input schema for post attachments

    Required fields match PostMedia model:
    - file_size: File size in bytes
    - file_mime_type: MIME type (e.g., 'video/mp4')
    """
```

## Todo List
- [x] Import `timezone` from `django.utils`
- [x] Replace `datetime.now()` with `timezone.now()` in validator
- [x] Add `file_size: int` to MediaIn schema
- [x] Add `file_mime_type: str` to MediaIn schema
- [x] Update MediaIn docstring
- [x] Verify no syntax errors
- [x] Run local validation tests

## Success Criteria
- [x] Timezone validation uses `timezone.now()`
- [x] MediaIn has all required fields (`file_size`, `file_mime_type`)
- [x] Schema validation rejects past dates
- [x] Schema validation rejects media without size/mime type
- [x] No breaking changes to API contract
- [x] Code passes linting

## Conflict Prevention
- **File Locking**: This phase has exclusive write access to `schemas.py`
- **No Dependencies**: Doesn't depend on other phases
- **Clean Boundaries**: Only modifies validation logic, not business logic

## Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking API contract | Low | High | Only add required fields, maintain defaults |
| Timezone conversion issues | Low | Medium | Django handles TZ conversion automatically |
| Validation too strict | Very Low | Low | Only reject truly invalid data |

## Security Considerations
- ✅ Prevents scheduling attacks (past-date exploitation)
- ✅ Ensures media metadata integrity
- ✅ Type-safe validation prevents injection

## Next Steps
After implementation:
1. Sync with Phase 02 & 03 completion
2. Run integration tests
3. Code review
