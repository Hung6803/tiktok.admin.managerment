from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from apps.content.models.post_media_model import PostMedia
from apps.content.models.scheduled_post_model import ScheduledPost
from apps.tiktok_accounts.models.tiktok_account_model import TikTokAccount

User = get_user_model()

class PostMediaModelTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # Create a TikTok account
        self.tiktok_account = TikTokAccount.objects.create(
            user=self.user,
            tiktok_user_id='12345',
            username='testtiktokuser',
            display_name='Test TikTok User',
            access_token='encrypted_token_value',
            token_expires_at=timezone.now() + timedelta(hours=2)
        )

        # Create a scheduled post
        self.scheduled_post = ScheduledPost.objects.create(
            tiktok_account=self.tiktok_account,
            caption='Test post',
            scheduled_time=timezone.now() + timedelta(days=1)
        )

        # Create a post media
        self.post_media = PostMedia.objects.create(
            scheduled_post=self.scheduled_post,
            media_type='video',
            file_path='/path/to/video.mp4',
            file_size=1024 * 1024 * 10,  # 10MB
            file_mime_type='video/mp4',
            duration=30,
            width=1920,
            height=1080,
            is_processed=False,
            thumbnail_path='/path/to/thumbnail.jpg'
        )

    def test_media_creation(self):
        """Test media file creation with all fields"""
        self.assertEqual(self.post_media.scheduled_post, self.scheduled_post)
        self.assertEqual(self.post_media.media_type, 'video')
        self.assertEqual(self.post_media.file_path, '/path/to/video.mp4')
        self.assertEqual(self.post_media.file_size, 1024 * 1024 * 10)
        self.assertFalse(self.post_media.is_processed)

    def test_media_type_choices(self):
        """Test valid media type choices"""
        valid_media_types = ['video', 'image', 'thumbnail']
        for media_type in valid_media_types:
            self.post_media.media_type = media_type
            self.post_media.save()
            self.assertEqual(self.post_media.media_type, media_type)

    def test_optional_fields(self):
        """Test optional fields"""
        # Test video metadata fields
        self.assertEqual(self.post_media.duration, 30)
        self.assertEqual(self.post_media.width, 1920)
        self.assertEqual(self.post_media.height, 1080)

        # Test thumbnail path
        self.assertEqual(self.post_media.thumbnail_path, '/path/to/thumbnail.jpg')

    def test_file_size_calculation(self):
        """Test get_file_size_mb method"""
        # 10MB file
        expected_size = round(10, 2)
        self.assertEqual(self.post_media.get_file_size_mb(), expected_size)

        # Test with a different file size
        self.post_media.file_size = 1024 * 1024 * 5  # 5MB
        expected_size = round(5, 2)
        self.assertEqual(self.post_media.get_file_size_mb(), expected_size)

    def test_string_representation(self):
        """Test string representation of the model"""
        expected_str = f"{self.post_media.media_type} for {self.scheduled_post.id}"
        self.assertEqual(str(self.post_media), expected_str)