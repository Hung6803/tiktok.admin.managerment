"""
Media processing service for video validation, thumbnail generation, and TikTok upload
Includes automatic video transcoding for TikTok compatibility
"""
import subprocess
import json
import logging
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image

from django.conf import settings

logger = logging.getLogger(__name__)


# TikTok video requirements
TIKTOK_MIN_FPS = 23
TIKTOK_MAX_FPS = 60
TIKTOK_TARGET_FPS = 30
TIKTOK_CODEC = 'h264'
TIKTOK_OUTPUT_CODEC = 'libx264'
TIKTOK_MAX_BITRATE = '8M'
TIKTOK_PIXEL_FORMAT = 'yuv420p'


class MediaProcessingService:
    """Service for processing media files (validation, thumbnails, metadata)"""

    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is installed"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("ffmpeg not found - thumbnail generation will be disabled")
            return False

    def validate_video(self, video_path: str) -> bool:
        """
        Validate video file

        Args:
            video_path: Path to video file

        Returns:
            True if valid, False otherwise
        """
        try:
            metadata = self.extract_video_metadata(video_path)

            # Check video constraints
            if metadata['duration'] > 180:  # 3 minutes max
                logger.error(f"Video exceeds maximum duration: {metadata['duration']}s")
                return False

            if metadata['width'] > 4096 or metadata['height'] > 4096:
                logger.error(f"Video resolution too high: {metadata['width']}x{metadata['height']}")
                return False

            if metadata['duration'] < 1:
                logger.error("Video too short (< 1 second)")
                return False

            return True

        except Exception as e:
            logger.error(f"Video validation failed: {str(e)}")
            return False

    def validate_image(self, image_path: str) -> bool:
        """
        Validate image file

        Args:
            image_path: Path to image file

        Returns:
            True if valid, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size

                # Check image constraints
                if width > 4096 or height > 4096:
                    logger.error(f"Image resolution too high: {width}x{height}")
                    return False

                if width < 100 or height < 100:
                    logger.error(f"Image resolution too low: {width}x{height}")
                    return False

                # Check file size
                file_size = os.path.getsize(image_path)
                if file_size > 20 * 1024 * 1024:  # 20MB max
                    logger.error(f"Image file too large: {file_size} bytes")
                    return False

                return True

        except Exception as e:
            logger.error(f"Image validation failed: {str(e)}")
            return False

    def extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract video metadata using ffprobe

        Args:
            video_path: Path to video file

        Returns:
            Video metadata dictionary

        Raises:
            ValueError: If no video stream found or ffmpeg not available
        """
        if not self.ffmpeg_available:
            raise ValueError("ffmpeg not installed - cannot extract metadata")

        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        # Find video stream
        video_stream = next(
            (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
            None
        )

        if not video_stream:
            raise ValueError("No video stream found")

        # Calculate FPS
        fps_parts = video_stream.get('avg_frame_rate', '0/1').split('/')
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 0.0

        return {
            'duration': int(float(data['format'].get('duration', 0))),
            'width': video_stream.get('width', 0),
            'height': video_stream.get('height', 0),
            'fps': round(fps, 2),
            'codec': video_stream.get('codec_name', 'unknown'),
            'bitrate': int(data['format'].get('bit_rate', 0)),
            'has_audio': any(s['codec_type'] == 'audio' for s in data.get('streams', []))
        }

    def generate_thumbnail(
        self,
        video_path: str,
        output_path: str,
        time_offset: int = 1,
        width: int = 640
    ) -> str:
        """
        Generate thumbnail from video

        Args:
            video_path: Path to video file
            output_path: Path to save thumbnail
            time_offset: Time offset in seconds for thumbnail capture
            width: Thumbnail width (height auto-calculated)

        Returns:
            Path to generated thumbnail

        Raises:
            ValueError: If ffmpeg not available or generation fails
        """
        if not self.ffmpeg_available:
            raise ValueError("ffmpeg not installed - cannot generate thumbnail")

        cmd = [
            'ffmpeg',
            '-ss', str(time_offset),
            '-i', video_path,
            '-vframes', '1',
            '-vf', f'scale={width}:-1',
            '-q:v', '2',
            '-y',  # Overwrite output file
            output_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            logger.info(f"Generated thumbnail: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Thumbnail generation failed: {e.stderr.decode()}")
            raise ValueError(f"Failed to generate thumbnail: {e.stderr.decode()}")

    def generate_image_thumbnail(
        self,
        image_path: str,
        output_path: str,
        width: int = 640
    ) -> str:
        """
        Generate thumbnail from image

        Args:
            image_path: Path to image file
            output_path: Path to save thumbnail
            width: Thumbnail width

        Returns:
            Path to generated thumbnail
        """
        try:
            with Image.open(image_path) as img:
                # Calculate height maintaining aspect ratio
                aspect_ratio = img.height / img.width
                height = int(width * aspect_ratio)

                # Resize image
                img.thumbnail((width, height), Image.Resampling.LANCZOS)

                # Save thumbnail
                img.save(output_path, quality=85, optimize=True)

                logger.info(f"Generated image thumbnail: {output_path}")
                return output_path

        except Exception as e:
            logger.error(f"Image thumbnail generation failed: {str(e)}")
            raise ValueError(f"Failed to generate thumbnail: {str(e)}")

    def needs_transcoding(self, video_path: str) -> Tuple[bool, str]:
        """
        Check if video needs transcoding for TikTok compatibility

        Args:
            video_path: Path to video file

        Returns:
            Tuple of (needs_transcoding, reason)
        """
        try:
            metadata = self.extract_video_metadata(video_path)
            reasons = []

            # Check FPS
            fps = metadata.get('fps', 0)
            if fps < TIKTOK_MIN_FPS:
                reasons.append(f"FPS too low ({fps} < {TIKTOK_MIN_FPS})")
            elif fps > TIKTOK_MAX_FPS:
                reasons.append(f"FPS too high ({fps} > {TIKTOK_MAX_FPS})")

            # Check codec
            codec = metadata.get('codec', '').lower()
            if codec != TIKTOK_CODEC:
                reasons.append(f"Non-H.264 codec ({codec})")

            if reasons:
                return True, "; ".join(reasons)
            return False, "Video meets TikTok requirements"

        except Exception as e:
            logger.error(f"Failed to check transcoding needs: {e}")
            return True, f"Metadata extraction failed: {e}"

    def transcode_for_tiktok(
        self,
        video_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcode video for TikTok compatibility

        Ensures video meets TikTok requirements:
        - Frame rate: 23-60 FPS (targets 30 FPS)
        - Codec: H.264
        - Pixel format: yuv420p
        - Container: MP4

        Args:
            video_path: Path to input video
            output_path: Path for output (auto-generated if None)

        Returns:
            Dictionary with:
            - transcoded: bool (True if transcoded, False if original used)
            - path: str (path to output video)
            - original_metadata: dict
            - new_metadata: dict (if transcoded)

        Raises:
            ValueError: If FFmpeg not available or transcoding fails
        """
        if not self.ffmpeg_available:
            raise ValueError("FFmpeg not installed - cannot transcode video")

        video_file = Path(video_path)
        if not video_file.exists():
            raise ValueError(f"Video file not found: {video_path}")

        # Get original metadata
        original_metadata = self.extract_video_metadata(video_path)
        logger.info(
            f"Original video: {original_metadata['width']}x{original_metadata['height']}, "
            f"{original_metadata['fps']} FPS, {original_metadata['codec']}"
        )

        # Check if transcoding needed
        needs_transcode, reason = self.needs_transcoding(video_path)

        if not needs_transcode:
            logger.info(f"No transcoding needed for {video_path}")
            return {
                'transcoded': False,
                'path': video_path,
                'original_metadata': original_metadata,
                'reason': reason
            }

        logger.info(f"Transcoding required: {reason}")

        # Generate output path if not provided
        if output_path is None:
            # Create temp file with same name pattern
            temp_dir = tempfile.mkdtemp(prefix='tiktok_transcode_')
            output_filename = f"transcoded_{video_file.stem}.mp4"
            output_path = os.path.join(temp_dir, output_filename)

        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-i', video_path,
            '-c:v', TIKTOK_OUTPUT_CODEC,
            '-preset', 'medium',
            '-crf', '23',
            '-r', str(TIKTOK_TARGET_FPS),
            '-pix_fmt', TIKTOK_PIXEL_FORMAT,
            '-maxrate', TIKTOK_MAX_BITRATE,
            '-bufsize', '16M',
            '-movflags', '+faststart',  # Enable web streaming
            '-c:a', 'aac',  # Audio codec
            '-b:a', '128k',  # Audio bitrate
            output_path
        ]

        logger.info(f"Starting video transcoding: {video_path} -> {output_path}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for longer videos
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg transcoding failed: {result.stderr}")
                raise ValueError(f"Transcoding failed: {result.stderr}")

            # Verify output exists
            if not Path(output_path).exists():
                raise ValueError("Transcoded file not created")

            # Get new metadata
            new_metadata = self.extract_video_metadata(output_path)
            output_size = Path(output_path).stat().st_size

            logger.info(
                f"Transcoding complete: {new_metadata['width']}x{new_metadata['height']}, "
                f"{new_metadata['fps']} FPS, {output_size / 1024 / 1024:.1f}MB"
            )

            return {
                'transcoded': True,
                'path': output_path,
                'original_metadata': original_metadata,
                'new_metadata': new_metadata,
                'reason': reason,
                'output_size': output_size
            }

        except subprocess.TimeoutExpired:
            logger.error("Video transcoding timed out")
            raise ValueError("Transcoding timed out (10 min limit)")
        except Exception as e:
            logger.error(f"Transcoding error: {e}")
            # Cleanup failed output
            if output_path and Path(output_path).exists():
                Path(output_path).unlink()
            raise

    def get_content_type(self, file_path: str) -> str:
        """
        Determine content type from file extension

        Args:
            file_path: Path to file

        Returns:
            MIME content type
        """
        ext = Path(file_path).suffix.lower()
        content_types = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.webm': 'video/webm',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        return content_types.get(ext, 'application/octet-stream')

    def cleanup_file(self, file_path: str) -> bool:
        """
        Delete file from local storage

        Args:
            file_path: Path to file to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False

    def cleanup_media_files(self, file_paths: list) -> int:
        """
        Delete multiple files from local storage

        Args:
            file_paths: List of file paths to delete

        Returns:
            Number of files successfully deleted
        """
        deleted_count = 0
        for file_path in file_paths:
            if self.cleanup_file(file_path):
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count}/{len(file_paths)} media files")
        return deleted_count
