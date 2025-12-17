# Phase 06: Testing and Documentation

**Duration:** 1-2 hours
**Priority:** HIGH
**Dependencies:** All previous phases

## Objective

Ensure all new services work correctly with unit tests and integration tests.

## Test Files to Create

### 1. TikTokPublishService Tests

**File:** `backend/apps/content/tests/test_tiktok_publish_service.py`

```python
"""Tests for TikTokPublishService"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from apps.content.services.tiktok_publish_service import (
    TikTokPublishService,
    TikTokPublishError
)


class TestTikTokPublishService:
    """Test suite for TikTokPublishService"""

    @pytest.fixture
    def service(self):
        """Create service instance with mock token"""
        with patch('apps.content.services.tiktok_publish_service.TikTokAPIClient'):
            return TikTokPublishService('mock_access_token')

    @pytest.fixture
    def temp_video(self):
        """Create temporary video file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            # Write 10MB of dummy data
            f.write(b'0' * (10 * 1024 * 1024))
            yield f.name
        os.unlink(f.name)

    def test_calculate_chunks_small_file(self, service):
        """Test chunk calculation for small file"""
        chunk_size, total_chunks = service._calculate_chunks(5 * 1024 * 1024)
        assert chunk_size == 5 * 1024 * 1024
        assert total_chunks == 1

    def test_calculate_chunks_large_file(self, service):
        """Test chunk calculation for large file"""
        chunk_size, total_chunks = service._calculate_chunks(52 * 1024 * 1024)
        assert chunk_size == 5 * 1024 * 1024
        assert total_chunks == 11

    @patch('apps.content.services.tiktok_publish_service.TikTokAPIClient')
    def test_initiate_video_post_success(self, mock_client_class, temp_video):
        """Test successful video post initialization"""
        mock_client = Mock()
        mock_client.post.return_value = {
            'data': {
                'publish_id': 'v_pub_123',
                'upload_url': 'https://upload.tiktok.com/...'
            }
        }
        mock_client_class.return_value = mock_client

        service = TikTokPublishService('mock_token')
        result = service.initiate_video_post(
            video_path=temp_video,
            caption='Test caption'
        )

        assert result['publish_id'] == 'v_pub_123'
        assert result['upload_url'] == 'https://upload.tiktok.com/...'
        assert result['total_chunks'] == 2  # 10MB file / 5MB chunks

    def test_initiate_video_post_file_not_found(self, service):
        """Test error when video file doesn't exist"""
        with pytest.raises(ValueError, match="not found"):
            service.initiate_video_post('/nonexistent/video.mp4')

    @patch('apps.content.services.tiktok_publish_service.TikTokAPIClient')
    def test_check_publish_status(self, mock_client_class):
        """Test publish status check"""
        mock_client = Mock()
        mock_client.post.return_value = {
            'data': {
                'status': 'PUBLISH_COMPLETE',
                'publiclyAvailablePostId': '7123456789'
            }
        }
        mock_client_class.return_value = mock_client

        service = TikTokPublishService('mock_token')
        status = service.check_publish_status('v_pub_123')

        assert status['status'] == 'PUBLISH_COMPLETE'
        assert status['video_id'] == '7123456789'


class TestChunkedUpload:
    """Test chunked upload functionality"""

    @pytest.fixture
    def service_with_mock(self):
        """Create service with mocked client"""
        with patch('apps.content.services.tiktok_publish_service.TikTokAPIClient'):
            service = TikTokPublishService('mock_token')
            return service

    @patch('requests.put')
    def test_upload_single_chunk_success(self, mock_put, service_with_mock):
        """Test successful single chunk upload"""
        mock_put.return_value = Mock(status_code=200)

        result = service_with_mock._upload_single_chunk(
            upload_url='https://upload.tiktok.com/...',
            chunk_data=b'test_data',
            start_byte=0,
            end_byte=8,
            file_size=9,
            chunk_index=0,
            total_chunks=1
        )

        assert result is True
        mock_put.assert_called_once()

    @patch('requests.put')
    def test_upload_single_chunk_retry(self, mock_put, service_with_mock):
        """Test chunk upload retry on failure"""
        mock_put.side_effect = [
            Mock(status_code=500),
            Mock(status_code=500),
            Mock(status_code=200),
        ]

        result = service_with_mock._upload_single_chunk(
            upload_url='https://upload.tiktok.com/...',
            chunk_data=b'test_data',
            start_byte=0,
            end_byte=8,
            file_size=9,
            chunk_index=0,
            total_chunks=1
        )

        assert result is True
        assert mock_put.call_count == 3
```

### 2. TikTokPhotoService Tests

**File:** `backend/apps/content/tests/test_tiktok_photo_service.py`

```python
"""Tests for TikTokPhotoService"""
import pytest
from unittest.mock import Mock, patch

from apps.content.services.tiktok_photo_service import (
    TikTokPhotoService,
    TikTokPhotoError
)


class TestTikTokPhotoService:
    """Test suite for TikTokPhotoService"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        with patch('apps.content.services.tiktok_photo_service.TikTokAPIClient'):
            return TikTokPhotoService('mock_token')

    def test_validate_image_urls_valid(self, service):
        """Test URL validation with valid URLs"""
        urls = [
            'https://example.com/photo1.jpg',
            'https://example.com/photo2.png',
        ]
        is_valid, error = service.validate_image_urls(urls)
        assert is_valid is True

    def test_validate_image_urls_too_few(self, service):
        """Test validation fails with less than 2 images"""
        urls = ['https://example.com/photo1.jpg']
        is_valid, error = service.validate_image_urls(urls)
        assert is_valid is False
        assert 'Minimum 2' in error

    def test_validate_image_urls_too_many(self, service):
        """Test validation fails with more than 35 images"""
        urls = [f'https://example.com/photo{i}.jpg' for i in range(36)]
        is_valid, error = service.validate_image_urls(urls)
        assert is_valid is False
        assert 'Maximum 35' in error

    def test_validate_image_urls_invalid_format(self, service):
        """Test validation fails with invalid image format"""
        urls = [
            'https://example.com/photo1.jpg',
            'https://example.com/document.pdf',
        ]
        is_valid, error = service.validate_image_urls(urls)
        assert is_valid is False
        assert 'JPG, PNG, or WebP' in error

    @patch('apps.content.services.tiktok_photo_service.TikTokAPIClient')
    def test_publish_photos_success(self, mock_client_class):
        """Test successful photo publish"""
        mock_client = Mock()
        mock_client.post.side_effect = [
            {'data': {'publish_id': 'p_123'}},
            {'data': {'status': 'PUBLISH_COMPLETE', 'post_id': '789'}},
        ]
        mock_client_class.return_value = mock_client

        service = TikTokPhotoService('mock_token')
        result = service.publish_photos(
            image_urls=[
                'https://example.com/photo1.jpg',
                'https://example.com/photo2.jpg',
            ],
            caption='Test caption',
            poll_interval=0.1,
            max_poll_attempts=1
        )

        assert result['success'] is True
        assert result['post_id'] == '789'
```

### 3. Integration Test

**File:** `backend/apps/scheduler/tests/test_publish_post_integration.py`

```python
"""Integration tests for publish_post task"""
import pytest
from unittest.mock import Mock, patch
from django.utils import timezone

from apps.scheduler.tasks.publish_post_task import publish_post


@pytest.mark.django_db
class TestPublishPostIntegration:
    """Integration tests for publish task"""

    @pytest.fixture
    def mock_tiktok_services(self):
        """Mock TikTok services for testing"""
        with patch('apps.scheduler.tasks.publish_post_task.TikTokPublishService') as mock_publish, \
             patch('apps.scheduler.tasks.publish_post_task.TikTokPhotoService') as mock_photo:

            # Configure publish service mock
            mock_publish_instance = Mock()
            mock_publish_instance.publish_video.return_value = {
                'success': True,
                'video_id': '123456789',
            }
            mock_publish.return_value.__enter__ = Mock(return_value=mock_publish_instance)
            mock_publish.return_value.__exit__ = Mock(return_value=False)

            # Configure photo service mock
            mock_photo_instance = Mock()
            mock_photo_instance.publish_photos.return_value = {
                'success': True,
                'post_id': '987654321',
            }
            mock_photo.return_value.__enter__ = Mock(return_value=mock_photo_instance)
            mock_photo.return_value.__exit__ = Mock(return_value=False)

            yield mock_publish_instance, mock_photo_instance

    def test_publish_video_post_success(
        self,
        mock_tiktok_services,
        scheduled_post_with_video,
        tiktok_account
    ):
        """Test successful video post publishing"""
        mock_publish, _ = mock_tiktok_services

        scheduled_post_with_video.accounts.add(tiktok_account)
        result = publish_post(str(scheduled_post_with_video.id))

        assert result['status'] == 'success'
        mock_publish.publish_video.assert_called_once()

    def test_publish_photo_post_success(
        self,
        mock_tiktok_services,
        scheduled_post_with_photos,
        tiktok_account
    ):
        """Test successful photo carousel publishing"""
        _, mock_photo = mock_tiktok_services

        scheduled_post_with_photos.accounts.add(tiktok_account)
        result = publish_post(str(scheduled_post_with_photos.id))

        assert result['status'] == 'success'
        mock_photo.publish_photos.assert_called_once()
```

## Running Tests

```bash
cd backend

# Run all new tests
pytest apps/content/tests/test_tiktok_publish_service.py -v
pytest apps/content/tests/test_tiktok_photo_service.py -v
pytest apps/scheduler/tests/test_publish_post_integration.py -v

# Run with coverage
pytest --cov=apps/content/services --cov=apps/scheduler/tasks -v
```

## Manual Testing Checklist

### Pre-requisites
- [ ] TikTok Developer account with app approved
- [ ] `video.publish` scope enabled in app
- [ ] Test TikTok account connected with new scopes
- [ ] Test video file (< 500MB, MP4 format)
- [ ] Test images (2-35, publicly accessible URLs)

### Video Publishing Tests
- [ ] Publish small video (< 5MB) - single chunk
- [ ] Publish large video (> 5MB) - multiple chunks
- [ ] Verify video appears on TikTok profile
- [ ] Verify caption, privacy settings applied
- [ ] Test with comments disabled
- [ ] Test error handling (invalid file, network error)

### Photo Publishing Tests
- [ ] Publish 2-image carousel
- [ ] Publish 10-image carousel
- [ ] Verify photos appear on TikTok
- [ ] Test cover image selection
- [ ] Test with invalid image URLs
- [ ] Test with inaccessible URLs

### Celery Integration Tests
- [ ] Schedule post for future time
- [ ] Verify Celery Beat triggers task
- [ ] Verify publish history recorded
- [ ] Test retry on failure
- [ ] Test max retry limit

## Documentation Updates

### Update README.md

Add to Features section:
```markdown
- Video publishing via TikTok API (chunked upload)
- Photo carousel posting (2-35 images)
- Real-time publish status tracking
```

### Update System Architecture

Add to TikTok API Integration section:
```markdown
### Publishing Services (Phase XX)
- `TikTokPublishService`: Direct video posting with chunked upload
- `TikTokPhotoService`: Photo carousel posting via URL pulling
- Endpoints: `post/publish/video/init/`, `post/publish/content/init/`
- Required scope: `video.publish`
```

### API Documentation

Document new internal APIs in code docstrings (already included in service files).
