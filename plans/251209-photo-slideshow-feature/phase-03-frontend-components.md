# Phase 03: Frontend Components

**Status:** Pending
**Priority:** High

## Context

Create frontend UI for uploading images and creating slideshow posts.

## Requirements

1. Image upload component (multi-select, drag-drop)
2. Image reordering UI
3. Preview slideshow before posting
4. Integration with post form

## Implementation Steps

### 3.1 Create Slideshow Upload Component

**File:** `frontend/src/components/posts/slideshow-upload.tsx`

Features:
- Drag-and-drop image upload
- Multi-file selection (2-10 images)
- Image preview grid
- Drag-to-reorder functionality
- Remove individual images
- Per-image duration setting

### 3.2 Create Slideshow Preview

**File:** `frontend/src/components/posts/slideshow-preview.tsx`

Features:
- Animated preview of slideshow
- Play/pause controls
- Duration indicator
- Aspect ratio preview (9:16)

### 3.3 Update Post Form

**File:** `frontend/src/components/posts/post-form.tsx`

Changes:
- Add toggle: Video vs Slideshow
- Show slideshow upload when selected
- Update validation for image count
- Submit to slideshow endpoint

### 3.4 Add Slideshow Hooks

**File:** `frontend/src/hooks/use-slideshow.ts`

```typescript
export function useCreateSlideshow() {
  // Mutation for creating slideshow post
}

export function useSlideshowStatus(postId: string) {
  // Query for conversion status polling
}
```

### 3.5 Update Types

**File:** `frontend/src/types/index.ts`

Add:
```typescript
interface SlideshowImage {
  file: File
  preview: string
  order: number
  duration_ms: number
}

interface SlideshowCreateRequest {
  title: string
  description: string
  account_ids: string[]
  images: SlideshowImage[]
  scheduled_time?: string
  privacy_level: PostVisibility
}
```

## Related Files

- `frontend/src/components/posts/post-form.tsx`
- `frontend/src/hooks/use-posts.ts`
- `frontend/src/types/index.ts`

## Success Criteria

- [ ] Multi-image upload works
- [ ] Drag-to-reorder works
- [ ] Preview displays correctly
- [ ] Post form integrates slideshow
- [ ] Conversion status polling works
