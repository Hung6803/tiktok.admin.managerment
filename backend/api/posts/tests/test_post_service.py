"""
Unit tests for post service
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from unittest.mock import Mock, patch

from api.posts.post_service import PostService
from apps.content.models import ScheduledPost, PostMedia, PublishHistory
from apps.tiktok_accounts.models import TikTokAccount
from apps.accounts.models import User


@pytest.mark.django_db
class TestPostService:
    """Test PostService class"""

    @pytest.fixture
    def user(self):
        """Create test user"""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def tiktok_account(self, user):
        """Create test TikTok account"""
        return TikTokAccount.objects.create(
            user=user,
            username='test_tiktok',
            display_name='Test TikTok',
            access_token='test_token'
        )

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return PostService()

    def test_create_draft_post(self, service, user, tiktok_account):
        """Test creating a draft post"""
        data = {
            'title': 'Test Draft',
            'description': 'Test Description',
            'account_ids': [str(tiktok_account.id)],
            'hashtags': ['test', 'draft'],
            'is_draft': True,
            'privacy_level': 'public',
            'allow_comments': True,
            'allow_duet': True,
            'allow_stitch': True
        }

        post = service.create_post(user, data)

        assert post.status == 'draft'
        assert post.title == 'Test Draft'
        assert post.accounts.count() == 1
        assert post.hashtags == ['test', 'draft']

    def test_create_scheduled_post(self, service, user, tiktok_account):
        """Test creating a scheduled post"""
        future_time = timezone.now() + timedelta(hours=2)
        data = {
            'title': 'Test Scheduled',
            'description': 'Test Description',
            'account_ids': [str(tiktok_account.id)],
            'scheduled_time': future_time,
            'is_draft': False,
            'privacy_level': 'public',
            'allow_comments': True,
            'allow_duet': True,
            'allow_stitch': True
        }

        with patch.object(service, '_schedule_post'):
            post = service.create_post(user, data)

        assert post.status == 'scheduled'
        assert post.scheduled_time == future_time

    def test_create_pending_post(self, service, user, tiktok_account):
        """Test creating a pending post (immediate publish)"""
        data = {
            'title': 'Test Pending',
            'description': 'Test Description',
            'account_ids': [str(tiktok_account.id)],
            'is_draft': False,
            'privacy_level': 'public',
            'allow_comments': True,
            'allow_duet': True,
            'allow_stitch': True
        }

        post = service.create_post(user, data)

        assert post.status == 'pending'
        assert post.scheduled_time is None

    def test_create_post_with_media(self, service, user, tiktok_account):
        """Test creating post with media"""
        data = {
            'title': 'Test With Media',
            'description': 'Test Description',
            'account_ids': [str(tiktok_account.id)],
            'media': [
                {
                    'file_path': '/path/to/video.mp4',
                    'file_size': 10000000,
                    'file_mime_type': 'video/mp4',
                    'media_type': 'video',
                    'duration': 30
                }
            ],
            'is_draft': True,
            'privacy_level': 'public',
            'allow_comments': True,
            'allow_duet': True,
            'allow_stitch': True
        }

        post = service.create_post(user, data)

        assert post.media.count() == 1
        media = post.media.first()
        assert media.file_path == '/path/to/video.mp4'

    @patch('api.posts.post_service.TikTokVideoService')
    def test_publish_now_success(self, mock_video_service, service, user, tiktok_account):
        """Test successful immediate publishing"""
        # Create post with media
        post = ScheduledPost.objects.create(
            user=user,
            title='Test Post',
            description='Test Description',
            status='pending',
            privacy_level='public'
        )
        post.accounts.add(tiktok_account)
        PostMedia.objects.create(
            post=post,
            file_path='/path/to/video.mp4',
            file_size=10000000,
            file_mime_type='video/mp4',
            media_type='video'
        )

        # Mock video service
        mock_service_instance = Mock()
        mock_service_instance.upload_video.return_value = {
            'video_id': 'tiktok123'
        }
        mock_video_service.return_value = mock_service_instance

        # Publish
        results = service.publish_now(post)

        assert len(results['success']) == 1
        assert len(results['failed']) == 0
        assert post.status == 'published'
        assert post.published_at is not None

    @patch('api.posts.post_service.TikTokVideoService')
    def test_publish_now_failure(self, mock_video_service, service, user, tiktok_account):
        """Test failed publishing"""
        # Create post with media
        post = ScheduledPost.objects.create(
            user=user,
            title='Test Post',
            description='Test Description',
            status='pending',
            privacy_level='public'
        )
        post.accounts.add(tiktok_account)
        PostMedia.objects.create(
            post=post,
            file_path='/path/to/video.mp4',
            file_size=10000000,
            file_mime_type='video/mp4',
            media_type='video'
        )

        # Mock video service to raise exception
        mock_service_instance = Mock()
        mock_service_instance.upload_video.side_effect = Exception("Upload failed")
        mock_video_service.return_value = mock_service_instance

        # Publish
        results = service.publish_now(post)

        assert len(results['success']) == 0
        assert len(results['failed']) == 1
        assert post.status == 'failed'

    def test_update_post(self, service, user, tiktok_account):
        """Test updating post"""
        post = ScheduledPost.objects.create(
            user=user,
            title='Original Title',
            description='Original Description',
            status='draft',
            privacy_level='public'
        )

        update_data = {
            'title': 'Updated Title',
            'description': 'Updated Description'
        }

        updated_post = service.update_post(post, update_data)

        assert updated_post.title == 'Updated Title'
        assert updated_post.description == 'Updated Description'

    def test_cannot_update_published_post(self, service, user):
        """Test that published posts cannot be updated"""
        post = ScheduledPost.objects.create(
            user=user,
            title='Published Post',
            description='Description',
            status='published',
            privacy_level='public'
        )

        with pytest.raises(ValueError, match="Cannot update published post"):
            service.update_post(post, {'title': 'New Title'})
