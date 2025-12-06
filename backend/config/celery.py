"""
Celery configuration for TikTok Manager project
Handles task queue setup and beat schedule configuration
"""
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('tiktok_manager')

# Configure Celery using Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Beat schedule configuration for periodic tasks
app.conf.beat_schedule = {
    'refresh-tiktok-tokens': {
        'task': 'apps.tiktok_accounts.tasks.refresh_expiring_tokens',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {
            'expires': 1800,  # Task expires after 30 minutes
        }
    },
    'cleanup-expired-tokens': {
        'task': 'apps.tiktok_accounts.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'check-scheduled-posts-every-minute': {
        'task': 'apps.scheduler.tasks.check_scheduled_posts_task.check_scheduled_posts',
        'schedule': 60.0,  # Every 60 seconds
        'options': {
            'expires': 55,  # Task expires after 55 seconds (before next run)
        }
    },
    'sync-accounts-daily': {
        'task': 'apps.scheduler.tasks.sync_accounts_task.sync_all_accounts',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'options': {
            'expires': 3600,  # Task expires after 1 hour
        }
    },
}

# Windows-specific configuration for compatibility
if os.name == 'nt':  # Windows platform
    app.conf.update(
        task_always_eager=False,
        task_eager_propagates=False,
        broker_connection_retry_on_startup=True,
        worker_pool='solo',  # Use solo pool on Windows (gevent not supported)
    )


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
    return 'pong'
