# Fix Phase 03 Posts API Critical Issues

**Created**: 2025-12-05 16:51
**Status**: Ready for Implementation
**Priority**: P0 (Critical Bugs)
**Type**: Bug Fixes - Parallel Execution

## Overview

Fix 5 critical issues identified in Phase 03 Posts API code review. All issues block production deployment and compromise security, performance, or functionality.

## Execution Strategy

**Parallel Execution**: All 3 phases can run simultaneously (no dependencies)

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Phase 01   │   │  Phase 02   │   │  Phase 03   │
│  Schemas    │   │  Router     │   │  Service    │
│  (Issues    │   │  (Issues    │   │  (Issue 5)  │
│   1 & 4)    │   │   2 & 3)    │   │             │
└─────────────┘   └─────────────┘   └─────────────┘
       ↓                  ↓                  ↓
       └──────────────────┴──────────────────┘
                          ↓
                   Testing & Review
```

## File Ownership Matrix

| Phase | Files Owned | Issues Fixed |
|-------|-------------|--------------|
| Phase 01 | `backend/api/posts/schemas.py` | #1 Timezone, #4 MediaIn validation |
| Phase 02 | `backend/api/posts/post_router.py` | #2 N+1 queries, #3 SQL injection |
| Phase 03 | `backend/api/posts/post_service.py` | #5 Service signature |

**No file conflicts** - Each phase modifies different files exclusively.

## Implementation Phases

### Phase 01: Fix Schema Validation Issues ⚡ PARALLEL
**File**: [phase-01-schema-validation-fixes.md](./phase-01-schema-validation-fixes.md)
**Status**: Ready
**Parallel Group**: 1
**Dependencies**: None
**Estimated Time**: 10 min

Fixes:
- Issue #1: Timezone validation (use `timezone.now()` instead of `datetime.now()`)
- Issue #4: Add missing MediaIn fields (`file_size`, `file_mime_type`)

### Phase 02: Fix Router Performance & Security ⚡ PARALLEL
**File**: [phase-02-router-optimization-fixes.md](./phase-02-router-optimization-fixes.md)
**Status**: Ready
**Parallel Group**: 1
**Dependencies**: None
**Estimated Time**: 15 min

Fixes:
- Issue #2: N+1 query problem (add `prefetch_related`, `annotate`)
- Issue #3: SQL injection risk (change date params to `datetime` type)

### Phase 03: Fix Service Integration ⚡ PARALLEL
**File**: [phase-03-service-signature-fix.md](./phase-03-service-signature-fix.md)
**Status**: Ready
**Parallel Group**: 1
**Dependencies**: None
**Estimated Time**: 5 min

Fixes:
- Issue #5: TikTokVideoService signature (pass `access_token` instead of `account` object)

## Success Criteria

- [ ] All 5 critical issues resolved
- [ ] No new issues introduced
- [ ] All tests pass
- [ ] Query count reduced from 41+ to ~3 for list_posts
- [ ] Timezone validation works correctly
- [ ] SQL injection prevented
- [ ] MediaIn validation enforced
- [ ] Publishing functionality works

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes | Low | High | Comprehensive tests, backward compatible |
| New bugs | Low | Medium | Code review, test coverage |
| Performance regression | Very Low | Low | Query optimization reduces queries |

## Next Steps

1. Execute all 3 phases in parallel using `fullstack-developer` agents
2. Run comprehensive test suite
3. Code review all changes
4. Update documentation
5. Deploy fixes
