# Performance & Architecture Fixes Research

## Issue 4: Rate Limiter Atomicity
### Key Findings
- Django `cache.incr()` not inherently atomic across all backends
- Race conditions possible between key existence check and increment
- Redis INCR differs from Django cache.incr() behavior

### Mitigation Strategies
1. Use distributed locking with `cache.lock()`
2. Utilize `ignore_key_check` flag in django-redis
3. Leverage raw Redis client for advanced atomic operations
4. Implement explicit transaction-like checks before incrementing

## Issue 5: Token Refresh + Celery
### Configuration Insights
- Django-Celery-Beat stores schedules in database
- Requires both worker and beat services running simultaneously
- Namespace configurations prevent setting conflicts
- Admin interface allows runtime task management

### Token Refresh Implementation
- Create shared task for clearing expired tokens
- Schedule periodic refresh using intervals/crontabs
- Ensure single scheduler per task to prevent duplication
- Implement error handling for failed refresh attempts

### Windows-Specific Considerations
- Use single command for worker+beat in development:
  ```bash
  celery -A [project-name] worker --beat --scheduler django --loglevel=info
  ```

## Issue 6: Video Streaming Upload
### Memory-Efficient Upload Patterns
- Stream files in chunks without full memory load
- Use file-like objects for efficient data transfer
- Leverage requests_toolbelt for advanced streaming

### Recommended Approach
1. Use MultipartEncoder from requests_toolbelt
2. Implement chunk-based file reading
3. Use generators for memory-efficient streaming
4. Utilize file.seek() and file.read() for controlled chunk uploads

## Implementation Recommendations
- Use django-redis for atomic cache operations
- Configure Celery with database-backed beat scheduler
- Implement streaming upload with requests_toolbelt
- Add comprehensive error handling and logging

## Unresolved Questions
1. Specific Windows-specific Celery configuration nuances
2. Performance benchmarks for different streaming chunk sizes
3. Detailed race condition testing strategies for rate limiter

**Research Completed:** 2025-12-04
**Researcher:** Claude Code