# Celery Explained - Task Scheduling System

## What is Celery?

Celery is a distributed task queue system for Python that allows you to run tasks asynchronously (in the background).

## Components

### 1. Celery Worker
**What it does:** Executes tasks
**Analogy:** The worker bee that does the actual work

Example:
```python
# Task: Publish video to TikTok
@task
def publish_video(post_id):
    # Upload video
    # Create TikTok post
    # Update database
```

**Run it:**
```bash
celery -A core worker -l info
```

### 2. Celery Beat
**What it does:** Schedules when tasks should run
**Analogy:** An alarm clock that tells workers when to start working

Example:
```python
# Check every 60 seconds if any posts need publishing
app.conf.beat_schedule = {
    'check-posts-every-minute': {
        'task': 'check_scheduled_posts',
        'schedule': 60.0,  # Every 60 seconds
    },
}
```

**Run it:**
```bash
celery -A core beat -l info
```

### 3. Message Broker (Redis)
**What it does:** Queue that holds tasks
**Analogy:** A to-do list where Beat writes tasks and Worker reads from

## How They Work Together

```
┌─────────────┐
│ Celery Beat │  "It's 3:00 PM, time to publish!"
│ (Scheduler) │
└──────┬──────┘
       │
       │ Creates task
       ▼
┌──────────────┐
│ Redis Queue  │  [Task: publish_video(123)]
│ (To-do list) │
└──────┬───────┘
       │
       │ Worker picks up task
       ▼
┌───────────────┐
│ Celery Worker │  Executes: publish_video(123)
│ (Does work)   │  - Uploads video to TikTok
└───────────────┘  - Marks as published
```

## Real Example: Scheduled Post Publishing

**Scenario:** User schedules post for 3:00 PM

1. **User Action (3:00 PM scheduled)**
   - User uploads video
   - Sets schedule: "December 5, 2025 at 3:00 PM"
   - Saved to database

2. **Celery Beat (Checks every minute)**
   ```python
   # Runs every 60 seconds
   @periodic_task(schedule=60.0)
   def check_scheduled_posts():
       now = datetime.now()
       posts = ScheduledPost.objects.filter(
           scheduled_time__lte=now,
           status='scheduled'
       )
       for post in posts:
           publish_video.delay(post.id)  # Send to worker
   ```

3. **Celery Worker (Publishes)**
   ```python
   @task
   def publish_video(post_id):
       post = ScheduledPost.objects.get(id=post_id)
       # Upload to TikTok
       tiktok_api.upload_video(post.video_file)
       # Update status
       post.status = 'published'
       post.save()
   ```

## When You Need Celery

### Phase 01-04: **NOT NEEDED**
- Building basic structure
- Creating models
- Building API endpoints
- ✅ Can skip Celery for now

### Phase 05: **NEEDED**
- Implementing scheduled post publishing
- Automatic account syncing
- Background video processing
- ✅ Install and configure Celery

## Development Workflow

### Initial Development (Phase 01-04)
```bash
# Terminal 1: PostgreSQL
docker-compose up -d

# Terminal 2: Django Backend
cd backend
python manage.py runserver

# Terminal 3: Next.js Frontend
cd frontend
npm run dev
```

### With Scheduling (Phase 05+)
```bash
# Terminal 1: PostgreSQL
docker-compose up -d

# Terminal 2: Django Backend
cd backend
python manage.py runserver

# Terminal 3: Celery Worker
cd backend
celery -A core worker -l info

# Terminal 4: Celery Beat
cd backend
celery -A core beat -l info

# Terminal 5: Next.js Frontend
cd frontend
npm run dev
```

## Summary

**For Now (Phase 01-04):**
- ✅ Use Docker for PostgreSQL only
- ✅ Run Django and Next.js locally
- ❌ Skip Celery (not needed yet)

**Later (Phase 05):**
- ✅ Add Celery Worker (executes tasks)
- ✅ Add Celery Beat (schedules tasks)
- ✅ Use Redis as message broker

## Key Takeaways

1. **Celery Worker** = Does background work
2. **Celery Beat** = Schedules when work should happen
3. **Redis** = Holds the queue of tasks
4. You don't need Celery until Phase 05 (Scheduling System)
5. For Phase 01-04, just focus on Django + PostgreSQL + Next.js
