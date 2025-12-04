# Phase 04: Token Refresh Service + Celery Implementation

## Context Links
- Code Review: `../251204-1525-tiktok-multi-account-manager/reports/code-reviewer-251204-phase03-tiktok-api-integration.md:214-301`
- Research: `research/researcher-02-performance-fixes.md:15-31`
- Main Plan: `plan.md`

## Parallelization Info
**Group**: B (Sequential)
**Depends On**: Phase 01, 02, 03 completion
**Blocks**: None (final phase)
**File Conflicts**: None (all new files)

## Overview
**Date**: 2025-12-04
**Priority**: COMPLEX
**Status**: PLANNED
**Complexity**: VERY HIGH (new service + infrastructure)

## Key Insights
- Tokens expire in 24 hours causing service interruptions
- Refresh method exists but no automatic caller
- Celery Beat needed for periodic task scheduling
- Windows requires special Celery configuration

## Requirements
1. Create token refresh service for automatic renewal
2. Implement Celery task for periodic execution
3. Configure Celery Beat scheduler
4. Handle refresh failures gracefully
5. Support Windows development environment

## Architecture

### Token Refresh Service
```python
# backend/apps/tiktok_accounts/services/tiktok_token_refresh_service.py
from django.utils import timezone
from datetime import timedelta
from typing import Optional, List
import logging

from apps.tiktok_accounts.models import TikTokAccount
from apps.tiktok_accounts.services.tiktok_oauth_service import TikTokOAuthService

logger = logging.getLogger(__name__)


class TikTokTokenRefreshService:
    """Service for automatic TikTok token refresh management"""

    def __init__(self, hours_before_expiry: int = 1):
        """
        Initialize token refresh service

        Args:
            hours_before_expiry: Hours before expiry to trigger refresh
        """
        self.hours_before_expiry = hours_before_expiry
        self.oauth_service = TikTokOAuthService()

    def refresh_expiring_tokens(self, dry_run: bool = False) -> dict:
        """
        Refresh all tokens expiring soon

        Args:
            dry_run: If True, only report what would be refreshed

        Returns:
            Summary of refresh operations
        """
        expiring_threshold = timezone.now() + timedelta(hours=self.hours_before_expiry)

        accounts = self.get_expiring_accounts(expiring_threshold)
        logger.info(f"Found {len(accounts)} accounts with expiring tokens")

        results = {
            'total': len(accounts),
            'refreshed': 0,
            'failed': 0,
            'errors': []
        }

        for account in accounts:
            try:
                if not dry_run:
                    self.refresh_account_token(account)
                    results['refreshed'] += 1
                    logger.info(f"Token refreshed for account {account.id}")
                else:
                    logger.info(f"[DRY RUN] Would refresh token for account {account.id}")
                    results['refreshed'] += 1

            except Exception as e:
                results['failed'] += 1
                error_msg = f"Token refresh failed for account {account.id}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

                if not dry_run:
                    self._handle_refresh_failure(account, str(e))

        logger.info(
            f"Token refresh completed: {results['refreshed']} refreshed, "
            f"{results['failed']} failed"
        )
        return results

    def get_expiring_accounts(self, threshold: timezone.datetime) -> List[TikTokAccount]:
        """Get accounts with tokens expiring before threshold"""
        return TikTokAccount.objects.filter(
            token_expires_at__lte=threshold,
            status='active',
            is_deleted=False
        ).select_for_update()  # Lock rows to prevent concurrent refresh

    def refresh_account_token(self, account: TikTokAccount) -> bool:
        """
        Refresh single account token

        Args:
            account: TikTokAccount instance to refresh

        Returns:
            True if successful, raises exception otherwise
        """
        logger.info(f"Refreshing token for account {account.tiktok_username}")

        # Get decrypted refresh token (auto-decrypted by field)
        refresh_token = account.refresh_token
        if not refresh_token:
            raise ValueError("No refresh token available")

        # Call OAuth service to refresh
        token_data = self.oauth_service.refresh_access_token(refresh_token)

        # Update account with new tokens (auto-encrypted on save)
        account.access_token = token_data['access_token']
        account.refresh_token = token_data.get('refresh_token', refresh_token)
        account.token_expires_at = token_data['token_expires_at']
        account.status = 'active'
        account.last_refreshed = timezone.now()
        account.save(update_fields=[
            'access_token', 'refresh_token', 'token_expires_at',
            'status', 'last_refreshed'
        ])

        logger.info(
            f"Token refreshed successfully for {account.tiktok_username}, "
            f"expires at {account.token_expires_at}"
        )
        return True

    def _handle_refresh_failure(self, account: TikTokAccount, error: str):
        """Handle token refresh failure"""
        account.status = 'expired'
        account.last_error = f"Token refresh failed: {error}"
        account.save(update_fields=['status', 'last_error'])

        # TODO: Send notification to user about expired account
        logger.warning(f"Account {account.id} marked as expired due to refresh failure")

    def refresh_specific_account(self, account_id: int) -> bool:
        """
        Refresh token for specific account

        Args:
            account_id: ID of account to refresh

        Returns:
            True if successful
        """
        try:
            account = TikTokAccount.objects.get(id=account_id)
            return self.refresh_account_token(account)
        except TikTokAccount.DoesNotExist:
            logger.error(f"Account {account_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to refresh account {account_id}: {str(e)}")
            raise
```

### Celery Tasks
```python
# backend/apps/tiktok_accounts/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from typing import Optional

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def refresh_expiring_tokens(self, dry_run: bool = False):
    """
    Periodic task to refresh expiring TikTok tokens

    Args:
        dry_run: If True, only report what would be refreshed
    """
    from apps.tiktok_accounts.services.tiktok_token_refresh_service import (
        TikTokTokenRefreshService
    )

    # Prevent concurrent execution
    lock_key = 'tiktok_token_refresh_lock'
    lock_timeout = 300  # 5 minutes

    if not cache.add(lock_key, 'locked', lock_timeout):
        logger.info("Token refresh already running, skipping")
        return {'status': 'skipped', 'reason': 'already_running'}

    try:
        logger.info("Starting token refresh task")
        service = TikTokTokenRefreshService()
        results = service.refresh_expiring_tokens(dry_run=dry_run)

        # Retry if failures occurred
        if results['failed'] > 0 and not dry_run:
            logger.warning(f"Retrying due to {results['failed']} failures")
            raise self.retry(
                exc=Exception(f"{results['failed']} tokens failed to refresh")
            )

        return {'status': 'success', 'results': results}

    except Exception as e:
        logger.error(f"Token refresh task failed: {str(e)}")
        raise self.retry(exc=e)
    finally:
        cache.delete(lock_key)


@shared_task
def refresh_single_account_token(account_id: int):
    """
    Refresh token for a specific account

    Args:
        account_id: ID of TikTok account to refresh
    """
    from apps.tiktok_accounts.services.tiktok_token_refresh_service import (
        TikTokTokenRefreshService
    )

    logger.info(f"Refreshing token for account {account_id}")

    try:
        service = TikTokTokenRefreshService()
        success = service.refresh_specific_account(account_id)
        return {'status': 'success', 'account_id': account_id}
    except Exception as e:
        logger.error(f"Failed to refresh account {account_id}: {str(e)}")
        return {'status': 'failed', 'account_id': account_id, 'error': str(e)}


@shared_task
def cleanup_expired_tokens():
    """
    Clean up expired tokens and mark accounts as inactive
    """
    from django.utils import timezone
    from apps.tiktok_accounts.models import TikTokAccount

    expired_accounts = TikTokAccount.objects.filter(
        token_expires_at__lt=timezone.now(),
        status='active'
    ).update(status='expired')

    logger.info(f"Marked {expired_accounts} accounts as expired")
    return {'expired_accounts': expired_accounts}
```

### Celery Configuration
```python
# backend/config/celery.py
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('tiktok_manager')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Beat schedule configuration
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
}

# Windows-specific configuration
if os.name == 'nt':  # Windows
    app.conf.update(
        task_always_eager=False,
        task_eager_propagates=False,
        broker_connection_retry_on_startup=True,
        worker_pool='solo',  # Use solo pool on Windows
    )

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
    return 'pong'
```

### Django Settings Update
```python
# backend/config/settings.py (additions)

# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Celery Beat
CELERY_BEAT_SCHEDULE = {
    'refresh-expiring-tokens': {
        'task': 'apps.tiktok_accounts.tasks.refresh_expiring_tokens',
        'schedule': 1800.0,  # 30 minutes in seconds
    },
}
```

### Management Commands
```python
# backend/apps/tiktok_accounts/management/commands/refresh_tokens.py
from django.core.management.base import BaseCommand
from apps.tiktok_accounts.tasks import refresh_expiring_tokens


class Command(BaseCommand):
    help = 'Manually trigger token refresh'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform dry run without actual refresh',
        )
        parser.add_argument(
            '--account-id',
            type=int,
            help='Refresh specific account by ID',
        )

    def handle(self, *args, **options):
        if options['account_id']:
            from apps.tiktok_accounts.tasks import refresh_single_account_token
            result = refresh_single_account_token(options['account_id'])
            self.stdout.write(f"Result: {result}")
        else:
            result = refresh_expiring_tokens(dry_run=options['dry_run'])
            self.stdout.write(f"Refresh completed: {result}")
```

## File Ownership
**Exclusive to Phase 04** (all new files):
- `backend/apps/tiktok_accounts/services/tiktok_token_refresh_service.py`
- `backend/apps/tiktok_accounts/tasks.py`
- `backend/config/celery.py`
- `backend/apps/tiktok_accounts/management/commands/refresh_tokens.py`
- `backend/apps/tiktok_accounts/tests/test_token_refresh.py`

## Implementation Steps

### Step 1: Install Celery Dependencies
```bash
pip install celery==5.3.4
pip install django-celery-beat==2.5.0
pip install redis==5.0.1
pip freeze > requirements.txt
```

### Step 2: Create Token Refresh Service
1. Create `tiktok_token_refresh_service.py`
2. Implement service class with methods
3. Add error handling and logging
4. Test service methods independently

### Step 3: Create Celery Tasks
1. Create `tasks.py` in tiktok_accounts app
2. Implement refresh tasks
3. Add distributed lock for concurrency
4. Configure retries and error handling

### Step 4: Configure Celery
1. Create `config/celery.py`
2. Update `config/settings.py` with Celery settings
3. Add beat schedule configuration
4. Configure for Windows if needed

### Step 5: Create Management Command
1. Create management command structure
2. Implement refresh_tokens command
3. Add dry-run and specific account options

### Step 6: Database Migrations
```bash
python manage.py migrate django_celery_beat
```

### Step 7: Testing
```python
# test_token_refresh.py
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta


class TestTokenRefreshService:
    def test_get_expiring_accounts(self):
        """Test fetching accounts with expiring tokens"""
        # Create test accounts
        expiring = TikTokAccount.objects.create(
            token_expires_at=timezone.now() + timedelta(minutes=30)
        )
        not_expiring = TikTokAccount.objects.create(
            token_expires_at=timezone.now() + timedelta(hours=24)
        )

        service = TikTokTokenRefreshService()
        accounts = service.get_expiring_accounts(
            timezone.now() + timedelta(hours=1)
        )

        assert expiring in accounts
        assert not_expiring not in accounts

    @patch('apps.tiktok_accounts.services.TikTokOAuthService.refresh_access_token')
    def test_refresh_account_token(self, mock_refresh):
        """Test single account token refresh"""
        mock_refresh.return_value = {
            'access_token': 'new_token',
            'refresh_token': 'new_refresh',
            'token_expires_at': timezone.now() + timedelta(hours=24)
        }

        account = TikTokAccount.objects.create(
            refresh_token='old_refresh',
            status='active'
        )

        service = TikTokTokenRefreshService()
        success = service.refresh_account_token(account)

        assert success
        account.refresh_from_db()
        assert account.access_token == 'new_token'
        assert account.status == 'active'
```

## Todo List
- [ ] Install Celery and dependencies
- [ ] Create tiktok_token_refresh_service.py
- [ ] Implement refresh service methods
- [ ] Create tasks.py with Celery tasks
- [ ] Add distributed lock mechanism
- [ ] Create config/celery.py
- [ ] Update settings.py with Celery config
- [ ] Run django_celery_beat migrations
- [ ] Create refresh_tokens management command
- [ ] Write comprehensive tests
- [ ] Test on Windows with solo pool
- [ ] Verify Beat schedule works
- [ ] Document Celery startup commands

## Success Criteria
- Tokens refresh automatically before expiry
- No duplicate refresh attempts (distributed lock)
- Failed refreshes retry with backoff
- Expired accounts marked appropriately
- Management command works for manual refresh
- All tests pass including async tasks

## Conflict Prevention
- All files are new (no conflicts possible)
- Depends on Phase 1-3 completion
- Independent service layer addition
- No modification of existing files

## Risk Assessment
- **High Risk**: Incorrect token refresh could break all accounts
- **Medium Risk**: Celery configuration issues on Windows
- **Medium Risk**: Redis dependency adds complexity
- **Mitigation**: Dry-run mode, comprehensive tests, gradual rollout

## Security Considerations
- Never log token values
- Use distributed locks to prevent race conditions
- Encrypt tokens at rest (already implemented)
- Monitor for suspicious refresh patterns

## Next Steps
After Phase 04 completion:
1. Monitor token refresh success rate
2. Tune refresh timing based on usage
3. Add alerting for refresh failures
4. Consider implementing token rotation
5. Add metrics dashboard for token status
6. Document Celery deployment for production