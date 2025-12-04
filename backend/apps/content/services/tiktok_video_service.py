"""
TikTok video upload and publishing service
Handles video file upload and post publishing
"""
from typing import Dict, Any, BinaryIO, Optional
from pathlib import Path
import logging
import mimetypes
import requests

from config.tiktok_config import TikTokConfig
from core.utils.tiktok_api_client import TikTokAPIClient

logger = logging.getLogger(__name__)


class TikTokVideoUploadError(Exception):
    """Exception raised when video upload fails"""
    pass


class TikTokVideoService:
    """
    TikTok video upload and publishing service
    Manages video upload initialization, file upload, and publishing
    """

    def __init__(self, access_token: str):
        """
        Initialize service with access token

        Args:
            access_token: Decrypted OAuth access token
        """
        self.config = TikTokConfig()
        self.client = TikTokAPIClient(access_token)

    def _validate_video_file(self, video_path: str) -> tuple[bool, str]:
        """
        Validate video file meets TikTok requirements

        Args:
            video_path: Path to video file

        Returns:
            Tuple of (is_valid, error_message)
        """
        video_file = Path(video_path)

        # Check existence
        if not video_file.exists():
            return False, "File not found"

        # Check extension
        valid_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        if video_file.suffix.lower() not in valid_extensions:
            return False, f"Invalid format: {video_file.suffix}"

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(video_path))
        if mime_type and not mime_type.startswith('video/'):
            return False, f"Not a video file: {mime_type}"

        # Check size
        file_size_mb = video_file.stat().st_size / (1024 * 1024)
        max_size = getattr(self.config, 'MAX_VIDEO_SIZE_MB', 500)

        if file_size_mb > max_size:
            return False, f"File too large: {file_size_mb:.1f}MB (max {max_size}MB)"

        if file_size_mb < 0.001:  # Less than 1KB
            return False, "File too small or corrupt"

        return True, "Valid"

    def initiate_upload(
        self,
        source_type: str = 'FILE_UPLOAD',
        post_mode: str = 'DIRECT_POST',
        privacy_level: str = 'PUBLIC_TO_EVERYONE',
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False
    ) -> Dict[str, Any]:
        """
        Initialize video upload session

        Args:
            source_type: 'FILE_UPLOAD' or 'PULL_FROM_URL'
            post_mode: 'DIRECT_POST' or 'MEDIA_UPLOAD'
            privacy_level: Privacy setting
            disable_comment: Disable comments
            disable_duet: Disable duet
            disable_stitch: Disable stitch

        Returns:
            Dictionary with:
            - publish_id: Upload session ID
            - upload_url: URL for file upload

        Raises:
            requests.exceptions.RequestException: On API error
        """
        logger.info("Initializing video upload")

        url = f"{self.config.API_BASE_URL}post/publish/inbox/video/init/"

        data = {
            'post_info': {
                'title': '',  # Will be set during publish
                'privacy_level': privacy_level,
                'disable_duet': disable_duet,
                'disable_comment': disable_comment,
                'disable_stitch': disable_stitch,
                'video_cover_timestamp_ms': 1000,
            },
            'source_info': {
                'source': source_type,
                'post_mode': post_mode,
            }
        }

        try:
            response = self.client.post(url, json=data)
            upload_data = response.get('data', {})

            publish_id = upload_data.get('publish_id')
            upload_url = upload_data.get('upload_url')

            logger.info(f"Upload initialized with publish_id: {publish_id}")

            return upload_data

        except Exception as e:
            logger.error(f"Failed to initialize upload: {str(e)}")
            raise

    def upload_video_file(self, upload_url: str, video_path: str) -> bool:
        """
        Upload video file to TikTok using streaming to prevent memory overload

        Args:
            upload_url: Upload URL from initiate_upload
            video_path: Path to video file

        Returns:
            True if upload successful

        Raises:
            TikTokVideoUploadError: On upload error
            ValueError: On validation error
        """
        logger.info(f"Starting streaming upload: {video_path}")

        # Validate before upload
        is_valid, error_msg = self._validate_video_file(video_path)
        if not is_valid:
            raise ValueError(f"Video validation failed: {error_msg}")

        video_file = Path(video_path)
        file_size = video_file.stat().st_size

        try:
            # Stream file without loading into memory
            with open(video_path, 'rb') as video_file_obj:
                headers = {
                    'Content-Type': 'application/octet-stream',
                    'Content-Length': str(file_size)
                }

                response = self.client.session.put(
                    upload_url,
                    data=video_file_obj,  # Requests streams automatically
                    headers=headers,
                    timeout=self.config.UPLOAD_TIMEOUT
                )
                response.raise_for_status()

            logger.info(f"Upload successful: {video_path} ({file_size / 1024 / 1024:.1f}MB)")
            return True

        except requests.exceptions.Timeout:
            logger.error(f"Upload timeout for {video_path}")
            raise TikTokVideoUploadError("Upload timeout exceeded")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Upload failed with HTTP {e.response.status_code}")
            raise TikTokVideoUploadError(f"Upload failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected upload error: {str(e)}")
            raise TikTokVideoUploadError(f"Upload failed: {str(e)}")

    def check_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """
        Check video processing and publishing status

        Args:
            publish_id: Upload session ID

        Returns:
            Dictionary with:
            - status: Processing status
            - fail_reason: Reason if failed
            - publiclyAvailablePostId: Posted video ID if published

        Raises:
            requests.exceptions.RequestException: On API error
        """
        logger.info(f"Checking publish status for: {publish_id}")

        url = f"{self.config.API_BASE_URL}post/publish/status/fetch/"

        params = {'publish_id': publish_id}

        try:
            response = self.client.post(url, json=params)
            status_data = response.get('data', {})

            status = status_data.get('status', 'UNKNOWN')
            logger.info(f"Publish status for {publish_id}: {status}")

            return status_data

        except Exception as e:
            logger.error(f"Failed to check publish status: {str(e)}")
            raise

    def publish_video(
        self,
        video_path: str,
        caption: str = '',
        privacy_level: str = 'PUBLIC_TO_EVERYONE',
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False
    ) -> Dict[str, Any]:
        """
        Complete video upload and publishing flow

        Args:
            video_path: Path to video file
            caption: Video caption (max 2200 chars)
            privacy_level: Privacy setting
            disable_comment: Disable comments
            disable_duet: Disable duet
            disable_stitch: Disable stitch

        Returns:
            Dictionary with publish_id and status

        Raises:
            Various exceptions on failure
        """
        logger.info(f"Starting video publish flow: {video_path}")

        # Validate caption length
        if len(caption) > self.config.MAX_CAPTION_LENGTH:
            raise ValueError(
                f"Caption too long: {len(caption)} chars "
                f"(max {self.config.MAX_CAPTION_LENGTH})"
            )

        # Initialize upload
        upload_data = self.initiate_upload(
            privacy_level=privacy_level,
            disable_comment=disable_comment,
            disable_duet=disable_duet,
            disable_stitch=disable_stitch
        )

        publish_id = upload_data.get('publish_id')
        upload_url = upload_data.get('upload_url')

        if not publish_id or not upload_url:
            raise ValueError("Failed to get publish_id or upload_url")

        # Upload video file
        upload_success = self.upload_video_file(upload_url, video_path)

        if not upload_success:
            raise RuntimeError("Video upload failed")

        # Check status
        status_data = self.check_publish_status(publish_id)

        logger.info(f"Video publish flow completed for publish_id: {publish_id}")

        return {
            'publish_id': publish_id,
            'status': status_data.get('status'),
            'caption': caption
        }

    def close(self):
        """Close the API client"""
        self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
