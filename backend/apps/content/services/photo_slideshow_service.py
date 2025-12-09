"""
Photo slideshow service for converting images to video
Converts multiple images into MP4 video slideshow for TikTok upload
"""
import subprocess
import tempfile
import shutil
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

from django.conf import settings
from config.tiktok_config import TikTokConfig

logger = logging.getLogger(__name__)


class SlideshowConversionError(Exception):
    """Exception raised when slideshow conversion fails"""
    pass


class PhotoSlideshowService:
    """
    Service for converting images to video slideshow
    Uses FFmpeg to create MP4 video from image sequence
    """

    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}

    # TikTok video specifications
    OUTPUT_WIDTH = 1080
    OUTPUT_HEIGHT = 1920
    OUTPUT_FPS = 30
    OUTPUT_CODEC = 'libx264'
    OUTPUT_FORMAT = 'mp4'

    def __init__(self):
        """Initialize service and verify FFmpeg availability"""
        self.config = TikTokConfig()
        self.ffmpeg_available = self._check_ffmpeg()

        # Get slideshow settings from config
        self.default_duration_ms = getattr(
            self.config, 'SLIDESHOW_IMAGE_DURATION_MS', 4000
        )
        self.min_images = getattr(self.config, 'SLIDESHOW_MIN_IMAGES', 2)
        self.max_images = getattr(self.config, 'SLIDESHOW_MAX_IMAGES', 10)

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is installed and available"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("FFmpeg not found - slideshow creation disabled")
            return False

    def _sanitize_path(self, path: str) -> str:
        """
        Sanitize file path to prevent path traversal and injection attacks

        Args:
            path: File path to sanitize

        Returns:
            Sanitized absolute path

        Raises:
            ValueError: If path contains dangerous patterns
        """
        # Check for null bytes (path traversal attack)
        if '\x00' in path:
            raise ValueError("Invalid path: contains null bytes")

        # Resolve to absolute path and normalize
        abs_path = os.path.abspath(os.path.normpath(path))

        # Check for path traversal attempts
        if '..' in path:
            # Verify the resolved path doesn't escape expected directories
            logger.warning(f"Path contains '..': {path} -> {abs_path}")

        return abs_path

    def _validate_prepared_path(self, path: str, temp_dir: str) -> bool:
        """
        Validate that a prepared image path is within the expected temp directory

        Args:
            path: Path to validate
            temp_dir: Expected parent directory

        Returns:
            True if path is valid
        """
        abs_path = os.path.abspath(path)
        abs_temp = os.path.abspath(temp_dir)
        return abs_path.startswith(abs_temp)

    def validate_images(
        self,
        image_paths: List[str]
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Validate list of images for slideshow creation

        Args:
            image_paths: List of paths to image files

        Returns:
            Tuple of (is_valid, error_message, image_info_list)
        """
        if not image_paths:
            return False, "No images provided", []

        count = len(image_paths)
        if count < self.min_images:
            return False, f"Minimum {self.min_images} images required, got {count}", []

        if count > self.max_images:
            return False, f"Maximum {self.max_images} images allowed, got {count}", []

        image_info = []
        for idx, path in enumerate(image_paths):
            # Sanitize path to prevent injection attacks
            try:
                sanitized_path = self._sanitize_path(path)
            except ValueError as e:
                return False, f"Invalid path: {str(e)}", []

            file_path = Path(sanitized_path)

            # Check existence
            if not file_path.exists():
                return False, f"Image not found: {path}", []

            # Check extension
            if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
                return False, f"Unsupported format: {file_path.suffix}", []

            # Validate and get dimensions
            try:
                with Image.open(sanitized_path) as img:
                    width, height = img.size
                    file_size = file_path.stat().st_size

                    # Check minimum dimensions
                    if width < 100 or height < 100:
                        return False, f"Image too small: {width}x{height}", []

                    # Check maximum dimensions
                    if width > 4096 or height > 4096:
                        return False, f"Image too large: {width}x{height}", []

                    # Check file size (max 20MB per image)
                    if file_size > 20 * 1024 * 1024:
                        return False, f"Image file too large: {file_size} bytes", []

                    image_info.append({
                        'path': sanitized_path,
                        'order': idx,
                        'width': width,
                        'height': height,
                        'size': file_size,
                        'format': img.format
                    })

            except Exception as e:
                return False, f"Failed to read image {path}: {str(e)}", []

        return True, "Valid", image_info

    def prepare_image(
        self,
        image_path: str,
        output_path: str,
        target_width: int = OUTPUT_WIDTH,
        target_height: int = OUTPUT_HEIGHT
    ) -> str:
        """
        Prepare single image for slideshow (resize and pad to target dimensions)

        Args:
            image_path: Source image path
            output_path: Output image path
            target_width: Target width (default 1080)
            target_height: Target height (default 1920)

        Returns:
            Path to prepared image
        """
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (e.g., PNG with alpha)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            orig_width, orig_height = img.size

            # Calculate scaling to fit within target while maintaining aspect ratio
            width_ratio = target_width / orig_width
            height_ratio = target_height / orig_height
            scale_ratio = min(width_ratio, height_ratio)

            new_width = int(orig_width * scale_ratio)
            new_height = int(orig_height * scale_ratio)

            # Resize image
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Create black background canvas
            canvas = Image.new('RGB', (target_width, target_height), (0, 0, 0))

            # Center image on canvas
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            canvas.paste(resized, (x_offset, y_offset))

            # Save as high-quality JPEG
            canvas.save(output_path, 'JPEG', quality=95)

            logger.debug(f"Prepared image: {image_path} -> {output_path}")
            return output_path

    def prepare_images(
        self,
        image_paths: List[str],
        temp_dir: str
    ) -> List[str]:
        """
        Prepare all images for slideshow conversion

        Args:
            image_paths: List of source image paths
            temp_dir: Temporary directory for prepared images

        Returns:
            List of prepared image paths (ordered)
        """
        prepared_paths = []

        for idx, path in enumerate(image_paths):
            # Use sequential naming for FFmpeg concat
            output_filename = f"img_{idx:04d}.jpg"
            output_path = os.path.join(temp_dir, output_filename)

            self.prepare_image(path, output_path)
            prepared_paths.append(output_path)

        logger.info(f"Prepared {len(prepared_paths)} images for slideshow")
        return prepared_paths

    def create_slideshow(
        self,
        image_paths: List[str],
        output_path: str,
        duration_per_image_ms: int = None,
        transition: str = 'none'
    ) -> Dict[str, Any]:
        """
        Create video slideshow from images using FFmpeg

        Args:
            image_paths: List of image file paths (in order)
            output_path: Path to save output video
            duration_per_image_ms: Display time per image in milliseconds
            transition: Transition type ('none', 'fade') - future enhancement

        Returns:
            Dictionary with video info (path, duration, size)

        Raises:
            SlideshowConversionError: If conversion fails
            ValueError: If FFmpeg not available or validation fails
        """
        if not self.ffmpeg_available:
            raise ValueError("FFmpeg not installed - cannot create slideshow")

        # Set duration
        duration_ms = duration_per_image_ms or self.default_duration_ms
        duration_sec = duration_ms / 1000.0

        # Validate images
        is_valid, error_msg, _ = self.validate_images(image_paths)
        if not is_valid:
            raise ValueError(f"Image validation failed: {error_msg}")

        # Create temp directory for processing
        temp_dir = tempfile.mkdtemp(prefix='slideshow_')

        try:
            # Prepare images (resize/pad to 1080x1920)
            prepared_images = self.prepare_images(image_paths, temp_dir)

            # Create concat file for FFmpeg
            concat_file = os.path.join(temp_dir, 'concat.txt')
            with open(concat_file, 'w') as f:
                for img_path in prepared_images:
                    # Escape path for FFmpeg
                    escaped_path = img_path.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
                    f.write(f"duration {duration_sec}\n")
                # Add last image again (FFmpeg concat quirk)
                escaped_last = prepared_images[-1].replace("'", "'\\''")
                f.write(f"file '{escaped_last}'\n")

            # Calculate total duration
            total_duration = len(image_paths) * duration_sec

            # Build FFmpeg command
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-vsync', 'vfr',
                '-pix_fmt', 'yuv420p',
                '-c:v', self.OUTPUT_CODEC,
                '-preset', 'medium',
                '-crf', '23',
                '-r', str(self.OUTPUT_FPS),
                '-movflags', '+faststart',  # Enable streaming
                output_path
            ]

            logger.info(f"Starting FFmpeg conversion: {len(image_paths)} images")

            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise SlideshowConversionError(
                    f"FFmpeg conversion failed: {result.stderr}"
                )

            # Verify output exists
            output_file = Path(output_path)
            if not output_file.exists():
                raise SlideshowConversionError("Output video file not created")

            file_size = output_file.stat().st_size
            logger.info(
                f"Slideshow created: {output_path} "
                f"({file_size / 1024 / 1024:.1f}MB, {total_duration:.1f}s)"
            )

            return {
                'path': output_path,
                'duration': total_duration,
                'duration_ms': int(total_duration * 1000),
                'size': file_size,
                'width': self.OUTPUT_WIDTH,
                'height': self.OUTPUT_HEIGHT,
                'fps': self.OUTPUT_FPS,
                'codec': self.OUTPUT_CODEC,
                'image_count': len(image_paths),
                'duration_per_image_ms': duration_ms
            }

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg conversion timed out")
            raise SlideshowConversionError("Conversion timed out (5 min limit)")

        except Exception as e:
            logger.error(f"Slideshow creation failed: {str(e)}")
            raise

        finally:
            # Cleanup temp directory
            self.cleanup(temp_dir)

    def cleanup(self, temp_dir: str) -> bool:
        """
        Remove temporary directory and files

        Args:
            temp_dir: Path to temporary directory

        Returns:
            True if cleanup successful
        """
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temp directory: {temp_dir}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {temp_dir}: {str(e)}")
            return False

    def get_slideshow_settings(self) -> Dict[str, Any]:
        """
        Get current slideshow configuration

        Returns:
            Dictionary with slideshow settings
        """
        return {
            'min_images': self.min_images,
            'max_images': self.max_images,
            'default_duration_ms': self.default_duration_ms,
            'output_width': self.OUTPUT_WIDTH,
            'output_height': self.OUTPUT_HEIGHT,
            'output_fps': self.OUTPUT_FPS,
            'supported_formats': list(self.SUPPORTED_FORMATS),
            'ffmpeg_available': self.ffmpeg_available
        }
