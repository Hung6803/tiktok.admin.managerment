"""
Integration tests for Posts API endpoints
"""
import pytest
from django.test import Client
from django.utils import timezone
from datetime import timedelta
import json

from apps.accounts.models import User
from apps.tiktok_accounts.models import TikTokAccount
from apps.content.models import ScheduledPost, PostMedia
from api.auth.jwt_handler import JWTHandler


@pytest.mark.django_db
class TestPostsAPI:
    """Test Posts API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return Client()

    @pytest.fixture
    def user(self):
        """Create test user"""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def auth_headers(self, user):
        """Create auth headers with JWT token"""
        token = JWTHandler.create_token(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    @pytest.fixture
    def tiktok_account(self, user):
        """Create test TikTok account"""
        return TikTokAccount.objects.create(
            user=user,
            username='test_tiktok',
            display_name='Test TikTok',
            access_token='test_token'
        )

    def test_create_post(self, client, user, auth_headers, tiktok_account):
        """Test creating a new post"""
        data = {
            'title': 'Test Post',
            'description': 'Test Description',
            'account_ids': [str(tiktok_account.id)],
            'privacy_level': 'public',
            'hashtags': ['test'],
            'is_draft': True
        }

        response = client.post(
            '/api/v1/posts/',
            data=json.dumps(data),
            content_type='application/json',
            **auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result['title'] == 'Test Post'
        assert result['status'] == 'draft'

    def test_create_scheduled_post(self, client, user, auth_headers, tiktok_account):
        """Test creating a scheduled post"""
        future_time = (timezone.now() + timedelta(hours=2)).isoformat()
        data = {
            'title': 'Scheduled Post',
            'description': 'Test',
            'account_ids': [str(tiktok_account.id)],
            'scheduled_time': future_time,
            'is_draft': False,
            'privacy_level': 'public'
        }

        response = client.post(
            '/api/v1/posts/',
            data=json.dumps(data),
            content_type='application/json',
            **auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'scheduled'

    def test_list_posts(self, client, user, auth_headers):
        """Test listing posts"""
        # Create test posts
        for i in range(3):
            ScheduledPost.objects.create(
                user=user,
                title=f'Post {i}',
                description='Description',
                status='draft',
                privacy_level='public'
            )

        response = client.get('/api/v1/posts/', **auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result['total'] == 3
        assert len(result['items']) == 3

    def test_list_posts_with_pagination(self, client, user, auth_headers):
        """Test listing posts with pagination"""
        # Create 25 posts
        for i in range(25):
            ScheduledPost.objects.create(
                user=user,
                title=f'Post {i}',
                description='Description',
                status='draft',
                privacy_level='public'
            )

        response = client.get('/api/v1/posts/?page=1&limit=10', **auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result['total'] == 25
        assert len(result['items']) == 10
        assert result['has_next'] is True

    def test_list_posts_filter_by_status(self, client, user, auth_headers):
        """Test filtering posts by status"""
        ScheduledPost.objects.create(
            user=user,
            title='Draft Post',
            description='Description',
            status='draft',
            privacy_level='public'
        )
        ScheduledPost.objects.create(
            user=user,
            title='Published Post',
            description='Description',
            status='published',
            privacy_level='public'
        )

        response = client.get('/api/v1/posts/?status=draft', **auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result['total'] == 1
        assert result['items'][0]['status'] == 'draft'

    def test_get_post_detail(self, client, user, auth_headers, tiktok_account):
        """Test getting post details"""
        post = ScheduledPost.objects.create(
            user=user,
            title='Test Post',
            description='Description',
            status='draft',
            privacy_level='public'
        )
        post.accounts.add(tiktok_account)

        response = client.get(f'/api/v1/posts/{post.id}', **auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result['id'] == str(post.id)
        assert result['title'] == 'Test Post'
        assert len(result['accounts']) == 1

    def test_update_post(self, client, user, auth_headers):
        """Test updating a post"""
        post = ScheduledPost.objects.create(
            user=user,
            title='Original Title',
            description='Description',
            status='draft',
            privacy_level='public'
        )

        data = {
            'title': 'Updated Title'
        }

        response = client.put(
            f'/api/v1/posts/{post.id}',
            data=json.dumps(data),
            content_type='application/json',
            **auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result['title'] == 'Updated Title'

    def test_delete_post(self, client, user, auth_headers):
        """Test deleting a post"""
        post = ScheduledPost.objects.create(
            user=user,
            title='Test Post',
            description='Description',
            status='draft',
            privacy_level='public'
        )

        response = client.delete(f'/api/v1/posts/{post.id}', **auth_headers)

        assert response.status_code == 200
        post.refresh_from_db()
        assert post.is_deleted is True

    def test_cannot_delete_published_post(self, client, user, auth_headers):
        """Test that published posts cannot be deleted"""
        post = ScheduledPost.objects.create(
            user=user,
            title='Test Post',
            description='Description',
            status='published',
            privacy_level='public'
        )

        response = client.delete(f'/api/v1/posts/{post.id}', **auth_headers)

        assert response.status_code == 400

    def test_list_drafts(self, client, user, auth_headers):
        """Test listing draft posts"""
        ScheduledPost.objects.create(
            user=user,
            title='Draft 1',
            description='Description',
            status='draft',
            privacy_level='public'
        )
        ScheduledPost.objects.create(
            user=user,
            title='Published',
            description='Description',
            status='published',
            privacy_level='public'
        )

        response = client.get('/api/v1/posts/drafts/list', **auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result['total'] == 1

    def test_upcoming_posts(self, client, user, auth_headers):
        """Test getting upcoming scheduled posts"""
        future_time = timezone.now() + timedelta(days=3)
        ScheduledPost.objects.create(
            user=user,
            title='Upcoming Post',
            description='Description',
            status='scheduled',
            scheduled_time=future_time,
            privacy_level='public'
        )

        response = client.get('/api/v1/posts/upcoming/list', **auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result['count'] == 1

    def test_bulk_schedule(self, client, user, auth_headers):
        """Test bulk scheduling posts"""
        post1 = ScheduledPost.objects.create(
            user=user,
            title='Post 1',
            description='Description',
            status='draft',
            privacy_level='public'
        )
        post2 = ScheduledPost.objects.create(
            user=user,
            title='Post 2',
            description='Description',
            status='draft',
            privacy_level='public'
        )

        future_time = (timezone.now() + timedelta(hours=2)).isoformat()
        data = {
            'post_ids': [str(post1.id), str(post2.id)],
            'scheduled_time': future_time
        }

        response = client.post(
            '/api/v1/posts/bulk/schedule',
            data=json.dumps(data),
            content_type='application/json',
            **auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result['updated_count'] == 2

    def test_unauthorized_access(self, client):
        """Test that unauthorized access is blocked"""
        response = client.get('/api/v1/posts/')
        assert response.status_code == 401
