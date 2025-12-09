"""
Tests for PhotoSlideshowService
"""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.test import TestCase
from PIL import Image

from apps.content.services.photo_slideshow_service import (
    PhotoSlideshowService,
    SlideshowConversionError
)


class PhotoSlideshowServiceTestCase(TestCase):
    """Test cases for PhotoSlideshowService"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = PhotoSlideshowService()
        self.temp_dir = tempfile.mkdtemp(prefix='test_slideshow_')
        self.test_images = []

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_test_image(self, width=800, height=600, format='JPEG', name=None):
        """Helper to create test image files"""
        if name is None:
            name = f'test_image_{len(self.test_images)}.jpg'
        path = os.path.join(self.temp_dir, name)

        img = Image.new('RGB', (width, height), color='red')
        img.save(path, format)
        self.test_images.append(path)
        return path

    def test_validate_images_success(self):
        """Test successful image validation"""
        # Create 3 valid test images
        paths = [self.create_test_image() for _ in range(3)]

        is_valid, error_msg, info = self.service.validate_images(paths)

        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "Valid")
        self.assertEqual(len(info), 3)

    def test_validate_images_empty_list(self):
        """Test validation fails with empty list"""
        is_valid, error_msg, info = self.service.validate_images([])

        self.assertFalse(is_valid)
        self.assertIn("No images", error_msg)

    def test_validate_images_too_few(self):
        """Test validation fails with less than minimum images"""
        paths = [self.create_test_image()]  # Only 1 image

        is_valid, error_msg, info = self.service.validate_images(paths)

        self.assertFalse(is_valid)
        self.assertIn("Minimum", error_msg)

    def test_validate_images_too_many(self):
        """Test validation fails with more than maximum images"""
        paths = [self.create_test_image() for _ in range(15)]  # 15 images

        is_valid, error_msg, info = self.service.validate_images(paths)

        self.assertFalse(is_valid)
        self.assertIn("Maximum", error_msg)

    def test_validate_images_nonexistent_file(self):
        """Test validation fails with nonexistent file"""
        # Need at least min_images to pass count check first
        paths = [
            self.create_test_image(),
            '/nonexistent/path/image.jpg'
        ]

        is_valid, error_msg, info = self.service.validate_images(paths)

        self.assertFalse(is_valid)
        self.assertIn("not found", error_msg)

    def test_validate_images_unsupported_format(self):
        """Test validation fails with unsupported format"""
        # Create a file with unsupported extension
        bad_path = os.path.join(self.temp_dir, 'test.gif')
        with open(bad_path, 'wb') as f:
            f.write(b'fake gif content')

        paths = [bad_path, self.create_test_image()]

        is_valid, error_msg, info = self.service.validate_images(paths)

        self.assertFalse(is_valid)
        self.assertIn("Unsupported format", error_msg)

    def test_validate_images_too_small(self):
        """Test validation fails with too small image"""
        small_path = self.create_test_image(width=50, height=50, name='small.jpg')
        paths = [small_path, self.create_test_image()]

        is_valid, error_msg, info = self.service.validate_images(paths)

        self.assertFalse(is_valid)
        self.assertIn("too small", error_msg)

    def test_prepare_image_resize_landscape(self):
        """Test image preparation resizes landscape image correctly"""
        # Create landscape image
        source_path = self.create_test_image(width=1920, height=1080)
        output_path = os.path.join(self.temp_dir, 'prepared.jpg')

        result = self.service.prepare_image(source_path, output_path)

        self.assertEqual(result, output_path)
        self.assertTrue(os.path.exists(output_path))

        # Verify output dimensions
        with Image.open(output_path) as img:
            self.assertEqual(img.size, (1080, 1920))

    def test_prepare_image_resize_portrait(self):
        """Test image preparation handles portrait image correctly"""
        # Create portrait image
        source_path = self.create_test_image(width=1080, height=1920)
        output_path = os.path.join(self.temp_dir, 'prepared_portrait.jpg')

        result = self.service.prepare_image(source_path, output_path)

        self.assertTrue(os.path.exists(output_path))
        with Image.open(output_path) as img:
            self.assertEqual(img.size, (1080, 1920))

    def test_prepare_image_rgba_conversion(self):
        """Test image preparation converts RGBA to RGB"""
        # Create RGBA image (PNG with alpha)
        png_path = os.path.join(self.temp_dir, 'test_rgba.png')
        img = Image.new('RGBA', (800, 600), color=(255, 0, 0, 128))
        img.save(png_path, 'PNG')
        self.test_images.append(png_path)

        output_path = os.path.join(self.temp_dir, 'prepared_rgba.jpg')
        result = self.service.prepare_image(png_path, output_path)

        self.assertTrue(os.path.exists(output_path))
        with Image.open(output_path) as img:
            self.assertEqual(img.mode, 'RGB')

    def test_prepare_images_batch(self):
        """Test batch image preparation"""
        paths = [self.create_test_image() for _ in range(3)]
        output_dir = os.path.join(self.temp_dir, 'prepared')
        os.makedirs(output_dir)

        prepared = self.service.prepare_images(paths, output_dir)

        self.assertEqual(len(prepared), 3)
        for i, path in enumerate(prepared):
            self.assertTrue(os.path.exists(path))
            self.assertIn(f'img_{i:04d}.jpg', path)

    @patch('subprocess.run')
    def test_create_slideshow_ffmpeg_not_available(self, mock_run):
        """Test slideshow creation fails when FFmpeg not available"""
        # Make FFmpeg check fail
        self.service.ffmpeg_available = False

        paths = [self.create_test_image() for _ in range(3)]
        output_path = os.path.join(self.temp_dir, 'output.mp4')

        with self.assertRaises(ValueError) as context:
            self.service.create_slideshow(paths, output_path)

        self.assertIn("FFmpeg not installed", str(context.exception))

    @patch('subprocess.run')
    def test_create_slideshow_success(self, mock_run):
        """Test successful slideshow creation with mocked FFmpeg"""
        # Mock FFmpeg success
        mock_run.return_value = MagicMock(returncode=0, stderr='')
        self.service.ffmpeg_available = True

        paths = [self.create_test_image() for _ in range(3)]
        output_path = os.path.join(self.temp_dir, 'output.mp4')

        # Create fake output file (simulating FFmpeg output)
        with open(output_path, 'wb') as f:
            f.write(b'fake mp4 content')

        result = self.service.create_slideshow(paths, output_path)

        self.assertEqual(result['path'], output_path)
        self.assertEqual(result['image_count'], 3)
        self.assertIn('duration', result)
        self.assertIn('size', result)

    @patch('subprocess.run')
    def test_create_slideshow_ffmpeg_failure(self, mock_run):
        """Test slideshow creation handles FFmpeg failure"""
        # Mock FFmpeg failure
        mock_run.return_value = MagicMock(returncode=1, stderr='FFmpeg error')
        self.service.ffmpeg_available = True

        paths = [self.create_test_image() for _ in range(3)]
        output_path = os.path.join(self.temp_dir, 'output.mp4')

        with self.assertRaises(SlideshowConversionError):
            self.service.create_slideshow(paths, output_path)

    def test_cleanup_temp_directory(self):
        """Test temp directory cleanup"""
        temp_path = tempfile.mkdtemp(prefix='cleanup_test_')

        # Create some files
        for i in range(3):
            with open(os.path.join(temp_path, f'file_{i}.txt'), 'w') as f:
                f.write('test')

        result = self.service.cleanup(temp_path)

        self.assertTrue(result)
        self.assertFalse(os.path.exists(temp_path))

    def test_cleanup_nonexistent_directory(self):
        """Test cleanup handles nonexistent directory"""
        result = self.service.cleanup('/nonexistent/path')
        self.assertTrue(result)

    def test_get_slideshow_settings(self):
        """Test getting slideshow settings"""
        settings = self.service.get_slideshow_settings()

        self.assertIn('min_images', settings)
        self.assertIn('max_images', settings)
        self.assertIn('default_duration_ms', settings)
        self.assertIn('output_width', settings)
        self.assertIn('output_height', settings)
        self.assertIn('supported_formats', settings)
        self.assertEqual(settings['output_width'], 1080)
        self.assertEqual(settings['output_height'], 1920)

    def test_supported_formats(self):
        """Test supported image formats"""
        supported = self.service.SUPPORTED_FORMATS

        self.assertIn('.jpg', supported)
        self.assertIn('.jpeg', supported)
        self.assertIn('.png', supported)
        self.assertIn('.webp', supported)
