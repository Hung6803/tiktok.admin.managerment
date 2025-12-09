"""
Tests for Slideshow API endpoints
"""
import os
import tempfile
from unittest.mock import patch, MagicMock

from django.test import TestCase
from PIL import Image

from api.posts.schemas import (
    SlideshowImageIn, SlideshowCreateIn,
    SlideshowConversionStatus, SlideshowStatusOut
)


class SlideshowSchemaTests(TestCase):
    """Test cases for slideshow schemas"""

    def test_slideshow_image_in_valid(self):
        """Test valid SlideshowImageIn"""
        data = {
            'file_path': '/path/to/image.jpg',
            'order': 0,
            'duration_ms': 4000
        }
        schema = SlideshowImageIn(**data)
        self.assertEqual(schema.file_path, '/path/to/image.jpg')
        self.assertEqual(schema.order, 0)
        self.assertEqual(schema.duration_ms, 4000)

    def test_slideshow_image_in_default_values(self):
        """Test SlideshowImageIn default values"""
        data = {'file_path': '/path/to/image.jpg'}
        schema = SlideshowImageIn(**data)
        self.assertEqual(schema.order, 0)
        self.assertEqual(schema.duration_ms, 4000)

    def test_slideshow_image_in_invalid_duration_too_short(self):
        """Test validation rejects too short duration"""
        from pydantic import ValidationError
        data = {
            'file_path': '/path/to/image.jpg',
            'duration_ms': 500  # Too short
        }
        with self.assertRaises(ValidationError):
            SlideshowImageIn(**data)

    def test_slideshow_image_in_invalid_duration_too_long(self):
        """Test validation rejects too long duration"""
        from pydantic import ValidationError
        data = {
            'file_path': '/path/to/image.jpg',
            'duration_ms': 15000  # Too long
        }
        with self.assertRaises(ValidationError):
            SlideshowImageIn(**data)

    def test_slideshow_create_in_valid(self):
        """Test valid SlideshowCreateIn"""
        data = {
            'title': 'Test Slideshow',
            'description': 'A test slideshow',
            'account_ids': ['acc-1', 'acc-2'],
            'images': [
                {'file_path': '/path/img1.jpg', 'order': 0},
                {'file_path': '/path/img2.jpg', 'order': 1},
            ],
            'privacy_level': 'public'
        }
        schema = SlideshowCreateIn(**data)
        self.assertEqual(schema.title, 'Test Slideshow')
        self.assertEqual(len(schema.images), 2)

    def test_slideshow_create_in_too_few_images(self):
        """Test validation rejects less than 2 images"""
        from pydantic import ValidationError
        data = {
            'title': 'Test',
            'description': 'Test',
            'account_ids': ['acc-1'],
            'images': [{'file_path': '/path/img1.jpg', 'order': 0}],
        }
        with self.assertRaises(ValidationError):
            SlideshowCreateIn(**data)

    def test_slideshow_create_in_too_many_images(self):
        """Test validation rejects more than 10 images"""
        from pydantic import ValidationError
        data = {
            'title': 'Test',
            'description': 'Test',
            'account_ids': ['acc-1'],
            'images': [
                {'file_path': f'/path/img{i}.jpg', 'order': i}
                for i in range(15)  # 15 images, exceeds limit
            ],
        }
        with self.assertRaises(ValidationError):
            SlideshowCreateIn(**data)

    def test_slideshow_create_in_hashtags_validation(self):
        """Test hashtag validation strips # prefix"""
        data = {
            'title': 'Test',
            'description': 'Test',
            'account_ids': ['acc-1'],
            'images': [
                {'file_path': '/path/img1.jpg', 'order': 0},
                {'file_path': '/path/img2.jpg', 'order': 1},
            ],
            'hashtags': ['#travel', 'photography', '#sunset']
        }
        schema = SlideshowCreateIn(**data)
        self.assertEqual(schema.hashtags, ['travel', 'photography', 'sunset'])

    def test_slideshow_create_in_too_many_hashtags(self):
        """Test validation rejects more than 30 hashtags"""
        from pydantic import ValidationError
        data = {
            'title': 'Test',
            'description': 'Test',
            'account_ids': ['acc-1'],
            'images': [
                {'file_path': '/path/img1.jpg', 'order': 0},
                {'file_path': '/path/img2.jpg', 'order': 1},
            ],
            'hashtags': [f'tag{i}' for i in range(35)]  # 35 hashtags
        }
        with self.assertRaises(ValidationError):
            SlideshowCreateIn(**data)

    def test_slideshow_status_out(self):
        """Test SlideshowStatusOut schema"""
        data = {
            'post_id': 'post-123',
            'status': SlideshowConversionStatus.pending,
            'progress': 0,
            'video_ready': False,
            'image_count': 5,
            'estimated_duration_sec': 20.0
        }
        schema = SlideshowStatusOut(**data)
        self.assertEqual(schema.post_id, 'post-123')
        self.assertEqual(schema.status, SlideshowConversionStatus.pending)
        self.assertFalse(schema.video_ready)

    def test_slideshow_conversion_status_values(self):
        """Test SlideshowConversionStatus enum values"""
        self.assertEqual(SlideshowConversionStatus.pending.value, 'pending')
        self.assertEqual(SlideshowConversionStatus.converting.value, 'converting')
        self.assertEqual(SlideshowConversionStatus.ready.value, 'ready')
        self.assertEqual(SlideshowConversionStatus.failed.value, 'failed')


class PostServiceSlideshowTests(TestCase):
    """Test cases for PostService slideshow methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_images = []

    def tearDown(self):
        """Clean up test files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_test_image(self, name='test.jpg'):
        """Helper to create test image"""
        path = os.path.join(self.temp_dir, name)
        img = Image.new('RGB', (800, 600), color='blue')
        img.save(path, 'JPEG')
        self.test_images.append(path)
        return path

    @patch('api.posts.post_service.TikTokAccount')
    @patch('api.posts.post_service.ScheduledPost')
    @patch('api.posts.post_service.PostMedia')
    def test_create_slideshow_post(self, mock_media, mock_post_cls, mock_account):
        """Test slideshow post creation"""
        from api.posts.post_service import PostService

        # Create test images
        img1 = self.create_test_image('img1.jpg')
        img2 = self.create_test_image('img2.jpg')

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 'user-123'

        # Mock post instance
        mock_post = MagicMock()
        mock_post.id = 'post-123'
        mock_post.accounts = MagicMock()
        mock_post_cls.objects.create.return_value = mock_post

        # Mock account queryset
        mock_account.objects.filter.return_value = MagicMock()

        # Data
        data = {
            'title': 'Test Slideshow',
            'description': 'A test slideshow post',
            'account_ids': ['acc-1'],
            'images': [
                {'file_path': img1, 'order': 0, 'duration_ms': 4000},
                {'file_path': img2, 'order': 1, 'duration_ms': 4000},
            ],
            'privacy_level': 'public',
            'hashtags': [],
            'is_draft': True
        }

        service = PostService()

        # Patch the conversion queue
        with patch.object(service, '_queue_slideshow_conversion'):
            result = service.create_slideshow_post(mock_user, data)

        # Verify post was created
        mock_post_cls.objects.create.assert_called_once()
        self.assertEqual(result, mock_post)

        # Verify media was created for each image
        self.assertEqual(mock_media.objects.create.call_count, 2)

    @patch('api.posts.post_service.ScheduledPost')
    def test_queue_slideshow_conversion(self, mock_post_cls):
        """Test slideshow conversion queueing"""
        from api.posts.post_service import PostService

        mock_post = MagicMock()
        mock_post.id = 'post-123'

        service = PostService()

        # Patch at the import location in the service method
        with patch('apps.scheduler.tasks.convert_slideshow') as mock_task:
            mock_task.delay = MagicMock()
            service._queue_slideshow_conversion(mock_post)
            mock_task.delay.assert_called_once_with('post-123')

    @patch('api.posts.post_service.ScheduledPost')
    def test_queue_slideshow_conversion_import_error(self, mock_post_cls):
        """Test handling of missing convert_slideshow task"""
        from api.posts.post_service import PostService

        mock_post = MagicMock()
        mock_post.id = 'post-123'

        service = PostService()

        # This should not raise, just log warning
        with patch.dict('sys.modules', {'apps.scheduler.tasks': None}):
            # No exception should be raised
            service._queue_slideshow_conversion(mock_post)
