"""
Integration tests for TikTok Accounts API
"""
import pytest
from django.test import Client
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.tiktok_accounts.models import TikTokAccount
from api.auth.jwt_handler import JWTHandler


@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create(
        email="test@example.com",
        username="testuser",
        password="testpassword123"
    )


@pytest.fixture
def auth_headers(user):
    """Generate JWT auth headers"""
    handler = JWTHandler()
    tokens = handler.generate_tokens(user.id)
    return {
        "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}"
    }


@pytest.fixture
def tiktok_account(user, db):
    """Create test TikTok account"""
    return TikTokAccount.objects.create(
        user=user,
        tiktok_user_id="test_tiktok_123",
        username="testtiktok",
        display_name="Test TikTok",
        avatar_url="https://example.com/avatar.jpg",
        status="active",
        access_token="encrypted_access_token",
        refresh_token="encrypted_refresh_token",
        token_expires_at=timezone.now() + timedelta(days=30),
        follower_count=1000,
        following_count=500,
        video_count=50
    )


@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.mark.django_db
class TestListAccounts:
    """Tests for list accounts endpoint"""

    def test_list_accounts_success(self, client, auth_headers, tiktok_account):
        """Test listing accounts returns success"""
        response = client.get('/api/v1/accounts/', **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert 'has_more' in data
        assert data['total'] == 1
        assert len(data['items']) == 1
        assert data['items'][0]['username'] == 'testtiktok'

    def test_list_accounts_unauthorized(self, client):
        """Test listing accounts without auth returns 401"""
        response = client.get('/api/v1/accounts/')
        assert response.status_code == 401

    def test_list_accounts_with_search(self, client, auth_headers, tiktok_account):
        """Test searching accounts by username"""
        response = client.get('/api/v1/accounts/?search=testtiktok', **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert data['items'][0]['username'] == 'testtiktok'

    def test_list_accounts_with_status_filter(self, client, auth_headers, tiktok_account):
        """Test filtering accounts by status"""
        response = client.get('/api/v1/accounts/?status=active', **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1

    def test_list_accounts_pagination(self, client, auth_headers, user):
        """Test pagination with limit"""
        # Create multiple accounts
        for i in range(5):
            TikTokAccount.objects.create(
                user=user,
                tiktok_user_id=f"test_tiktok_{i}",
                username=f"testtiktok{i}",
                display_name=f"Test TikTok {i}",
                status="active",
                access_token="encrypted_access_token",
                token_expires_at=timezone.now() + timedelta(days=30)
            )

        response = client.get('/api/v1/accounts/?limit=2', **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 2
        assert data['has_more'] is True
        assert data['cursor'] is not None


@pytest.mark.django_db
class TestGetAccount:
    """Tests for get single account endpoint"""

    def test_get_account_success(self, client, auth_headers, tiktok_account):
        """Test getting single account returns success"""
        response = client.get(f'/api/v1/accounts/{tiktok_account.id}', **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data['username'] == 'testtiktok'
        assert data['display_name'] == 'Test TikTok'
        assert data['follower_count'] == 1000
        assert 'tiktok_user_id' in data
        assert 'token_expires_at' in data

    def test_get_account_not_found(self, client, auth_headers):
        """Test getting non-existent account returns 404"""
        import uuid
        fake_id = uuid.uuid4()
        response = client.get(f'/api/v1/accounts/{fake_id}', **auth_headers)

        assert response.status_code == 404
        assert 'detail' in response.json()

    def test_get_account_unauthorized(self, client, tiktok_account):
        """Test getting account without auth returns 401"""
        response = client.get(f'/api/v1/accounts/{tiktok_account.id}')
        assert response.status_code == 401


@pytest.mark.django_db
class TestDeleteAccount:
    """Tests for delete account endpoint"""

    def test_delete_account_success(self, client, auth_headers, tiktok_account):
        """Test deleting account performs soft delete"""
        response = client.delete(f'/api/v1/accounts/{tiktok_account.id}', **auth_headers)

        assert response.status_code == 200
        assert response.json()['success'] is True

        # Verify soft delete
        tiktok_account.refresh_from_db()
        assert tiktok_account.is_deleted is True

    def test_delete_account_not_found(self, client, auth_headers):
        """Test deleting non-existent account returns 404"""
        import uuid
        fake_id = uuid.uuid4()
        response = client.delete(f'/api/v1/accounts/{fake_id}', **auth_headers)

        assert response.status_code == 404

    def test_delete_account_unauthorized(self, client, tiktok_account):
        """Test deleting account without auth returns 401"""
        response = client.delete(f'/api/v1/accounts/{tiktok_account.id}')
        assert response.status_code == 401


@pytest.mark.django_db
class TestSyncAccount:
    """Tests for sync account endpoint"""

    def test_sync_account_success(self, client, auth_headers, tiktok_account, mocker):
        """Test syncing account updates data"""
        # Mock TikTokAccountService
        mock_service = mocker.patch('api.accounts.router.TikTokAccountService')
        mock_service.return_value.get_user_info.return_value = {
            'display_name': 'Updated Name',
            'follower_count': 2000,
            'following_count': 600,
            'video_count': 60
        }

        response = client.post(f'/api/v1/accounts/{tiktok_account.id}/sync', **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['follower_count'] == 2000
        assert data['following_count'] == 600
        assert data['video_count'] == 60

    def test_sync_account_not_found(self, client, auth_headers):
        """Test syncing non-existent account returns 404"""
        import uuid
        fake_id = uuid.uuid4()
        response = client.post(f'/api/v1/accounts/{fake_id}/sync', **auth_headers)

        assert response.status_code == 404

    def test_sync_account_api_failure(self, client, auth_headers, tiktok_account, mocker):
        """Test sync handles API failures gracefully"""
        # Mock TikTokAccountService to raise exception
        mock_service = mocker.patch('api.accounts.router.TikTokAccountService')
        mock_service.return_value.get_user_info.side_effect = Exception("API Error")

        response = client.post(f'/api/v1/accounts/{tiktok_account.id}/sync', **auth_headers)

        assert response.status_code == 500
        assert 'detail' in response.json()


@pytest.mark.django_db
class TestAccountsSummary:
    """Tests for accounts summary endpoint"""

    def test_get_summary_success(self, client, auth_headers, user):
        """Test getting accounts summary"""
        # Create multiple accounts
        TikTokAccount.objects.create(
            user=user,
            tiktok_user_id="test_1",
            username="test1",
            display_name="Test 1",
            status="active",
            access_token="token",
            token_expires_at=timezone.now() + timedelta(days=30),
            follower_count=1000,
            video_count=10
        )
        TikTokAccount.objects.create(
            user=user,
            tiktok_user_id="test_2",
            username="test2",
            display_name="Test 2",
            status="active",
            access_token="token",
            token_expires_at=timezone.now() + timedelta(days=30),
            follower_count=2000,
            video_count=20
        )

        response = client.get('/api/v1/accounts/stats/summary', **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data['total_accounts'] == 2
        assert data['active_accounts'] == 2
        assert data['total_followers'] == 3000
        assert data['total_videos'] == 30

    def test_get_summary_empty(self, client, auth_headers):
        """Test summary with no accounts"""
        response = client.get('/api/v1/accounts/stats/summary', **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data['total_accounts'] == 0
        assert data['total_followers'] == 0


@pytest.mark.django_db
class TestBatchSync:
    """Tests for batch sync endpoint"""

    def test_batch_sync_success(self, client, auth_headers, user, mocker):
        """Test batch syncing multiple accounts"""
        # Create accounts
        account1 = TikTokAccount.objects.create(
            user=user,
            tiktok_user_id="test_1",
            username="test1",
            display_name="Test 1",
            status="active",
            access_token="token",
            token_expires_at=timezone.now() + timedelta(days=30)
        )
        account2 = TikTokAccount.objects.create(
            user=user,
            tiktok_user_id="test_2",
            username="test2",
            display_name="Test 2",
            status="active",
            access_token="token",
            token_expires_at=timezone.now() + timedelta(days=30)
        )

        # Mock service
        mock_service = mocker.patch('api.accounts.router.TikTokAccountService')
        mock_service.return_value.get_user_info.return_value = {
            'display_name': 'Updated',
            'follower_count': 1000,
            'following_count': 500,
            'video_count': 50
        }

        payload = {
            'account_ids': [str(account1.id), str(account2.id)]
        }
        response = client.post(
            '/api/v1/accounts/batch/sync',
            data=payload,
            content_type='application/json',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert len(data['success']) == 2
        assert len(data['failed']) == 0

    def test_batch_sync_partial_failure(self, client, auth_headers, user, mocker):
        """Test batch sync with some failures"""
        account1 = TikTokAccount.objects.create(
            user=user,
            tiktok_user_id="test_1",
            username="test1",
            display_name="Test 1",
            status="active",
            access_token="token",
            token_expires_at=timezone.now() + timedelta(days=30)
        )

        # Mock service to fail
        mock_service = mocker.patch('api.accounts.router.TikTokAccountService')
        mock_service.return_value.get_user_info.side_effect = Exception("API Error")

        payload = {
            'account_ids': [str(account1.id), 'invalid-id']
        }
        response = client.post(
            '/api/v1/accounts/batch/sync',
            data=payload,
            content_type='application/json',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert len(data['failed']) == 2
