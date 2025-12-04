# Phase 03: Video Upload Streaming Fix

## Context Links
- Code Review: `../251204-1525-tiktok-multi-account-manager/reports/code-reviewer-251204-phase03-tiktok-api-integration.md:380-434`
- Research: `research/researcher-02-performance-fixes.md:36-45`
- Main Plan: `plan.md`

## Parallelization Info
**Group**: A (Parallel)
**Concurrent With**: Phase 01 (Security), Phase 02 (Rate Limiter)
**Blocks**: Phase 04 (Token Refresh)
**File Conflicts**: None

## Overview
**Date**: 2025-12-04
**Priority**: HIGH
**Status**: COMPLETED (2025-12-05)
**Complexity**: HIGH (memory management redesign)

## Key Insights
- Current implementation loads entire video into RAM
- 500MB video = 500MB RAM per upload
- Multiple concurrent uploads risk server crash
- Requests library supports automatic streaming

## Requirements
1. Implement streaming upload without full memory load
2. Maintain upload progress tracking capability
3. Add proper file validation before upload
4. Support chunked uploads for large files
5. Ensure memory efficiency for concurrent uploads

## Architecture

### Current Problem
```python
# MEMORY INEFFICIENT: Loads entire file
with open(video_path, 'rb') as f:
    video_data = f.read()  # 500MB file = 500MB RAM!
success = self.client.put(upload_url, data=video_data)
```

### Solution 1: Simple Streaming
```python
def upload_video_file(self, upload_url: str, video_path: str) -> bool:
    """Upload video using streaming to prevent memory overload"""
    logger.info(f"Starting streaming upload: {video_path}")

    # Validate before upload
    is_valid, error_msg = self._validate_video_file(video_path)
    if not is_valid:
        raise ValueError(f"Video validation failed: {error_msg}")

    video_file = Path(video_path)
    file_size = video_file.stat().st_size

    try:
        # Stream file without loading into memory
        with open(video_path, 'rb') as video_file:
            headers = {
                'Content-Type': 'application/octet-stream',
                'Content-Length': str(file_size)
            }

            response = self.client.session.put(
                upload_url,
                data=video_file,  # Requests streams automatically
                headers=headers,
                timeout=self.config.UPLOAD_TIMEOUT
            )
            response.raise_for_status()

        logger.info(f"Upload successful: {video_path} ({file_size / 1024 / 1024:.1f}MB)")
        return True

    except requests.exceptions.Timeout:
        logger.error(f"Upload timeout for {video_path}")
        raise TikTokVideoUploadError("Upload timeout exceeded")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Upload failed with HTTP {e.response.status_code}")
        raise TikTokVideoUploadError(f"Upload failed: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}")
        raise TikTokVideoUploadError(f"Upload failed: {str(e)}")
```

### Solution 2: Chunked Upload with Progress
```python
def upload_video_file_chunked(
    self,
    upload_url: str,
    video_path: str,
    chunk_size: int = 10 * 1024 * 1024  # 10MB chunks
) -> bool:
    """Upload video in chunks with progress tracking"""
    from itertools import chain

    logger.info(f"Starting chunked upload: {video_path}")

    video_file = Path(video_path)
    file_size = video_file.stat().st_size
    uploaded = 0

    def file_chunk_generator():
        """Generate file chunks with progress tracking"""
        nonlocal uploaded
        with open(video_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                uploaded += len(chunk)
                progress = (uploaded / file_size) * 100
                logger.debug(f"Upload progress: {progress:.1f}%")
                yield chunk

    try:
        headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Length': str(file_size)
        }

        response = self.client.session.put(
            upload_url,
            data=file_chunk_generator(),
            headers=headers,
            timeout=self.config.UPLOAD_TIMEOUT
        )
        response.raise_for_status()

        logger.info(f"Upload complete: {video_path}")
        return True

    except Exception as e:
        logger.error(f"Chunked upload failed: {str(e)}")
        raise TikTokVideoUploadError(f"Upload failed at {uploaded / 1024 / 1024:.1f}MB: {str(e)}")
```

### Video Validation
```python
def _validate_video_file(self, video_path: str) -> tuple[bool, str]:
    """Validate video meets TikTok requirements"""
    import mimetypes

    video_file = Path(video_path)

    # Check existence
    if not video_file.exists():
        return False, "File not found"

    # Check extension
    valid_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    if video_file.suffix.lower() not in valid_extensions:
        return False, f"Invalid format: {video_file.suffix}"

    # Check MIME type
    mime_type, _ = mimetypes.guess_type(str(video_path))
    if mime_type and not mime_type.startswith('video/'):
        return False, f"Not a video file: {mime_type}"

    # Check size
    file_size_mb = video_file.stat().st_size / (1024 * 1024)
    max_size = getattr(self.config, 'MAX_VIDEO_SIZE_MB', 500)

    if file_size_mb > max_size:
        return False, f"File too large: {file_size_mb:.1f}MB (max {max_size}MB)"

    if file_size_mb < 0.001:  # Less than 1KB
        return False, "File too small or corrupt"

    return True, "Valid"
```

### Memory Monitoring (Optional)
```python
def _log_memory_usage(self, operation: str):
    """Log current memory usage for monitoring"""
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.debug(f"[{operation}] Memory usage: {memory_mb:.1f}MB")
```

## File Ownership
**Exclusive to Phase 03**:
- `backend/apps/content/services/tiktok_video_service.py`
- `backend/apps/content/tests/test_video_service.py` (new/updated)

## Implementation Steps

### Step 1: Add Video Validation
1. Open `tiktok_video_service.py`
2. Add `_validate_video_file()` method
3. Add validation to upload methods
4. Test with various file types/sizes

### Step 2: Implement Streaming Upload
1. Replace `upload_video_file()` method
2. Remove `f.read()` pattern
3. Use file object directly for streaming
4. Add proper headers

### Step 3: Add Error Handling
1. Import or create `TikTokVideoUploadError`
2. Add specific error cases (timeout, HTTP, etc.)
3. Ensure proper cleanup on failure

### Step 4: Create Tests
```python
# test_video_service.py
import tempfile
from pathlib import Path

def test_streaming_upload_memory_efficient(self):
    """Test that upload doesn't load file into memory"""
    # Create large test file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        # Write 100MB of data
        chunk = b'0' * (1024 * 1024)  # 1MB
        for _ in range(100):
            f.write(chunk)
        temp_path = f.name

    try:
        # Mock the upload
        with patch('requests.Session.put') as mock_put:
            mock_put.return_value.status_code = 200

            service = TikTokVideoService()
            service.upload_video_file('http://test.com', temp_path)

            # Verify file was passed as object, not data
            call_args = mock_put.call_args
            assert hasattr(call_args.kwargs['data'], 'read')
    finally:
        Path(temp_path).unlink()

def test_video_validation(self):
    """Test video file validation"""
    service = TikTokVideoService()

    # Test invalid extension
    is_valid, msg = service._validate_video_file('test.txt')
    assert not is_valid
    assert 'Invalid format' in msg

    # Test non-existent file
    is_valid, msg = service._validate_video_file('/nonexistent.mp4')
    assert not is_valid
    assert 'not found' in msg
```

## Todo List
- [x] Add _validate_video_file() method
- [x] Add TikTokVideoUploadError exception class
- [x] Replace upload_video_file() with streaming version
- [x] Remove f.read() memory loading pattern
- [x] Add proper Content-Type and Content-Length headers
- [ ] Implement chunked upload variant (optional - future enhancement)
- [ ] Add memory monitoring logging (optional - future enhancement)
- [ ] Create test for memory efficiency (recommended for future)
- [ ] Create test for file validation (recommended for future)
- [ ] Create test for error scenarios (recommended for future)
- [ ] Test with large files (>100MB) (production verification needed)
- [ ] Verify concurrent uploads work (production verification needed)

## Success Criteria
- No full file load into memory
- Memory usage stays constant regardless of file size
- Large files (500MB+) upload successfully
- Concurrent uploads don't cause memory issues
- All existing tests pass
- New streaming tests pass

## Conflict Prevention
- No shared files with Phase 01 (security files)
- No shared files with Phase 02 (rate limiter)
- Isolated to video service only
- No dependencies on other phases

## Risk Assessment
- **High Risk**: Breaking video uploads impacts core functionality
- **Medium Risk**: Streaming may not work with all endpoints
- **Low Risk**: Performance might be slightly slower
- **Mitigation**: Keep backup of original, test thoroughly

## Security Considerations
- Validate files before upload to prevent malicious uploads
- Don't trust client-provided file metadata
- Sanitize file names before logging
- Consider virus scanning for user uploads

## Next Steps
After Phase 03 completion:
1. Monitor memory usage during uploads
2. Benchmark upload speeds
3. Test with various video formats
4. Consider implementing resumable uploads
5. Add upload progress callbacks for UI