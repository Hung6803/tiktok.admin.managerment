# Phase 07: Testing & Quality Assurance

**Priority:** Medium
**Status:** Ready After Phase 06
**Estimated Time:** 4-6 hours

## Context Links

- [Main Plan](./plan.md)

## Overview

Comprehensive testing strategy covering unit tests, integration tests, API tests, and end-to-end testing to ensure system reliability and quality.

## Requirements

### Test Coverage
- Unit tests: 80%+ coverage
- Integration tests for critical flows
- API endpoint tests
- End-to-end user flows
- Performance testing
- Security testing

## Related Code Files

### Files to Create
- `backend/tests/test_models.py`
- `backend/tests/test_services.py`
- `backend/tests/test_api_endpoints.py`
- `backend/tests/test_celery_tasks.py`
- `frontend/tests/components/*.test.tsx`
- `frontend/tests/integration/*.test.tsx`
- `tests/e2e/*.spec.ts` (Playwright)

## Implementation Steps

### 1. Backend Unit Tests (pytest)

```python
# backend/tests/test_models.py
import pytest
from apps.tiktok_accounts.models.tiktok-account-model import TikTokAccount
from apps.content.models.scheduled-post-model import ScheduledPost

@pytest.mark.django_db
def test_create_tiktok_account(user):
    account = TikTokAccount.objects.create(
        user=user,
        tiktok_user_id='test123',
        username='testuser',
        display_name='Test User',
        access_token='encrypted_token',
        refresh_token='encrypted_refresh',
        token_expires_at=timezone.now() + timedelta(days=30)
    )
    assert account.status == 'active'
    assert str(account.id) != ''

@pytest.mark.django_db
def test_scheduled_post_creation(tiktok_account):
    post = ScheduledPost.objects.create(
        tiktok_account=tiktok_account,
        caption='Test caption',
        scheduled_time=timezone.now() + timedelta(days=1),
        status='scheduled'
    )
    assert post.retry_count == 0
    assert post.status == 'scheduled'
```

### 2. API Integration Tests

```python
# backend/tests/test_api_endpoints.py
import pytest
from django.test import Client

@pytest.fixture
def auth_client(user):
    from core.auth.jwt-handler import JWTHandler
    token = JWTHandler.create_access_token(user.id)
    client = Client()
    client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    return client

def test_list_tiktok_accounts(auth_client, tiktok_account):
    response = auth_client.get('/api/v1/tiktok/accounts')
    assert response.status_code == 200
    data = response.json()
    assert 'accounts' in data
    assert len(data['accounts']) > 0

def test_create_scheduled_post(auth_client, tiktok_account):
    post_data = {
        'tiktok_account_id': str(tiktok_account.id),
        'caption': 'Test post',
        'hashtags': ['test', 'demo'],
        'scheduled_time': '2025-12-10T15:00:00Z',
        'privacy_level': 'public'
    }
    response = auth_client.post('/api/v1/posts/', post_data, content_type='application/json')
    assert response.status_code == 201
```

### 3. Celery Task Tests

```python
# backend/tests/test_celery_tasks.py
import pytest
from apps.scheduler.tasks.publish-post-task import publish_post

@pytest.mark.django_db
@pytest.mark.celery
def test_publish_post_task(scheduled_post, mocker):
    # Mock TikTok API
    mocker.patch('apps.content.services.tiktok-publish-service.TikTokPublishService.publish_video',
                return_value={'success': True, 'video_id': 'test123', 'video_url': 'https://test.com'})

    result = publish_post(str(scheduled_post.id))
    assert result['status'] == 'success'

    scheduled_post.refresh_from_db()
    assert scheduled_post.status == 'published'
```

### 4. Frontend Component Tests (Jest + React Testing Library)

```typescript
// frontend/tests/components/account-card.test.tsx
import { render, screen } from '@testing-library/react';
import { AccountCard } from '@/components/accounts/account-card';

describe('AccountCard', () => {
  const mockAccount = {
    id: '123',
    username: 'testuser',
    display_name: 'Test User',
    follower_count: 1000,
    status: 'active',
  };

  it('renders account information', () => {
    render(<AccountCard account={mockAccount} />);
    expect(screen.getByText('testuser')).toBeInTheDocument();
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('1000')).toBeInTheDocument();
  });

  it('shows active status badge', () => {
    render(<AccountCard account={mockAccount} />);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });
});
```

### 5. E2E Tests (Playwright)

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can login successfully', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/accounts');
    await expect(page.locator('h1')).toContainText('TikTok Accounts');
  });

  test('user can connect TikTok account', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Connect account
    await page.click('button:has-text("Connect Account")');
    // Handle OAuth flow (mock or actual)
    await expect(page).toHaveURL(/tiktok\.com/);
  });
});
```

## Todo List

- [ ] Setup pytest for backend
- [ ] Write model unit tests
- [ ] Write service unit tests
- [ ] Write API endpoint tests
- [ ] Write Celery task tests
- [ ] Setup Jest for frontend
- [ ] Write component tests
- [ ] Write hook tests
- [ ] Setup Playwright for E2E
- [ ] Write authentication E2E tests
- [ ] Write scheduling flow E2E tests
- [ ] Run load tests (Locust/K6)
- [ ] Perform security audit (OWASP)
- [ ] Test cross-browser compatibility
- [ ] Test mobile responsiveness
- [ ] Generate coverage reports

## Success Criteria

- ✅ 80%+ unit test coverage
- ✅ All critical flows tested
- ✅ E2E tests pass consistently
- ✅ No critical security vulnerabilities
- ✅ Performance meets requirements
- ✅ All browsers supported

## Next Steps

After Phase 07 completion:
1. Proceed to Phase 08: Deployment
2. Setup CI/CD pipeline
3. Deploy to production
