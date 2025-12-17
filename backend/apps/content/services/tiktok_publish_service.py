"""
TikTok direct publishing service
Handles video posting with chunked upload support
"""
from typing import Dict, Any
from pathlib import Path
import logging
import math
import time
import requests

from config.tiktok_config import TikTokConfig
from core.utils.tiktok_api_client import TikTokAPIClient

logger = logging.getLogger(__name__)


class TikTokPublishError(Exception):
    """Exception raised when publishing fails"""
    pass


class TikTokPublishService:
    """
    TikTok publishing service with support for:
    - Direct Post API (requires video.publish scope + app review)
    - Creator Inbox API (only video.upload scope, sandbox-compatible)
    """

    # Chunk size constraints (TikTok requirements)
    MIN_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB minimum
    MAX_CHUNK_SIZE = 64 * 1024 * 1024  # 64MB maximum

    def __init__(self, access_token: str, use_inbox: bool = True):
        """
        Initialize service with access token

        Args:
            access_token: Decrypted OAuth access token
            use_inbox: If True, use Creator Inbox API (sandbox-compatible)
                       If False, use Direct Post API (requires app review)
        """
        self.config = TikTokConfig()
        self.client = TikTokAPIClient(access_token)
        self.use_inbox = use_inbox

    def _calculate_chunks(self, file_size: int) -> tuple:
        """
        Calculate chunk parameters for upload

        TikTok requirements:
        - For files < 5MB: chunk_size = file_size (single chunk)
        - For files >= 5MB: chunk_size between 5MB-64MB
        """
        if file_size < self.MIN_CHUNK_SIZE:
            # Small file: single chunk with exact file size
            return file_size, 1

        # Large file: use 5MB chunks
        chunk_size = self.MIN_CHUNK_SIZE
        total_chunks = math.ceil(file_size / chunk_size)
        return chunk_size, total_chunks

    def initiate_video_post(
        self,
        video_path: str,
        caption: str = '',
        privacy_level: str = 'public',
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False
    ) -> Dict[str, Any]:
        """
        Initialize video post session

        Args:
            video_path: Path to video file
            caption: Video caption (max 2200 chars)
            privacy_level: 'public', 'friends', or 'private'

        Uses Creator Inbox API (sandbox) or Direct Post API (production)
        based on use_inbox setting.
        """
        video_file = Path(video_path)
        if not video_file.exists():
            raise ValueError(f"Video file not found: {video_path}")

        file_size = video_file.stat().st_size
        chunk_size, total_chunks = self._calculate_chunks(file_size)

        api_privacy = self.config.get_api_privacy_level(privacy_level)

        # Choose endpoint based on mode
        if self.use_inbox:
            # Creator Inbox API - works in sandbox without app review
            url = f"{self.config.API_BASE_URL}post/publish/inbox/video/init/"
            logger.info(f"Initiating Creator Inbox upload: {file_size} bytes")

            data = {
                'source_info': {
                    'source': 'FILE_UPLOAD',
                    'video_size': file_size,
                    'chunk_size': chunk_size,
                    'total_chunk_count': total_chunks,
                }
            }
        else:
            # Direct Post API - requires video.publish scope + app review
            url = f"{self.config.API_BASE_URL}post/publish/video/init/"
            logger.info(f"Initiating Direct Post: {file_size} bytes, {total_chunks} chunks")

            data = {
                'post_info': {
                    'title': caption[:2200],
                    'privacy_level': api_privacy,
                    'disable_comment': disable_comment,
                    'disable_duet': disable_duet,
                    'disable_stitch': disable_stitch,
                },
                'source_info': {
                    'source': 'FILE_UPLOAD',
                    'video_size': file_size,
                    'chunk_size': chunk_size,
                    'total_chunk_count': total_chunks,
                }
            }

        try:
            response = self.client.post(url, json=data)
            result = response.get('data', {})

            publish_id = result.get('publish_id')
            upload_url = result.get('upload_url')

            if not publish_id or not upload_url:
                raise TikTokPublishError("Missing publish_id or upload_url")

            logger.info(f"Video post initiated: {publish_id} (inbox={self.use_inbox})")

            return {
                'publish_id': publish_id,
                'upload_url': upload_url,
                'file_size': file_size,
                'chunk_size': chunk_size,
                'total_chunks': total_chunks,
            }

        except Exception as e:
            logger.error(f"Failed to initiate video post: {e}")
            raise TikTokPublishError(f"Init failed: {e}")

    def upload_video_chunks(
        self,
        upload_url: str,
        video_path: str,
        chunk_size: int,
        total_chunks: int
    ) -> bool:
        """Upload video file in chunks"""
        video_file = Path(video_path)
        file_size = video_file.stat().st_size

        logger.info(f"Starting chunked upload: {total_chunks} chunks")

        try:
            with open(video_path, 'rb') as f:
                for chunk_index in range(total_chunks):
                    start_byte = chunk_index * chunk_size
                    end_byte = min(start_byte + chunk_size, file_size) - 1
                    current_chunk_size = end_byte - start_byte + 1

                    f.seek(start_byte)
                    chunk_data = f.read(current_chunk_size)

                    success = self._upload_single_chunk(
                        upload_url=upload_url,
                        chunk_data=chunk_data,
                        start_byte=start_byte,
                        end_byte=end_byte,
                        file_size=file_size,
                        chunk_index=chunk_index,
                        total_chunks=total_chunks
                    )

                    if not success:
                        raise TikTokPublishError(
                            f"Chunk {chunk_index + 1}/{total_chunks} failed"
                        )

                    logger.info(
                        f"Uploaded chunk {chunk_index + 1}/{total_chunks} "
                        f"({current_chunk_size} bytes)"
                    )

            logger.info("Chunked upload completed successfully")
            return True

        except IOError as e:
            logger.error(f"File read error: {e}")
            raise TikTokPublishError(f"File error: {e}")

    def _upload_single_chunk(
        self,
        upload_url: str,
        chunk_data: bytes,
        start_byte: int,
        end_byte: int,
        file_size: int,
        chunk_index: int,
        total_chunks: int,
        max_retries: int = 3
    ) -> bool:
        """Upload single chunk with retry logic"""
        headers = {
            'Content-Type': 'video/mp4',
            'Content-Length': str(len(chunk_data)),
            'Content-Range': f'bytes {start_byte}-{end_byte}/{file_size}',
        }

        for attempt in range(max_retries):
            try:
                response = requests.put(
                    upload_url,
                    data=chunk_data,
                    headers=headers,
                    timeout=self.config.UPLOAD_TIMEOUT
                )

                if response.status_code in [200, 201, 206]:
                    return True

                logger.warning(
                    f"Chunk upload returned {response.status_code}, "
                    f"attempt {attempt + 1}/{max_retries}"
                )

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Chunk upload error: {e}, "
                    f"attempt {attempt + 1}/{max_retries}"
                )

                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        return False

    def check_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """Check video processing and publishing status"""
        url = f"{self.config.API_BASE_URL}post/publish/status/fetch/"

        try:
            response = self.client.post(url, json={'publish_id': publish_id})
            status_data = response.get('data', {})

            status = status_data.get('status', 'UNKNOWN')
            logger.info(f"Publish status for {publish_id}: {status}")

            return {
                'status': status,
                'fail_reason': status_data.get('fail_reason'),
                'video_id': status_data.get('publiclyAvailablePostId'),
            }

        except Exception as e:
            logger.error(f"Failed to check status: {e}")
            raise

    def publish_video(
        self,
        video_path: str,
        caption: str = '',
        privacy_level: str = 'public',
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False,
        poll_interval: int = 5,
        max_poll_attempts: int = 60
    ) -> Dict[str, Any]:
        """Complete video publishing flow"""
        # Step 1: Initialize post
        init_result = self.initiate_video_post(
            video_path=video_path,
            caption=caption,
            privacy_level=privacy_level,
            disable_comment=disable_comment,
            disable_duet=disable_duet,
            disable_stitch=disable_stitch
        )

        publish_id = init_result['publish_id']
        upload_url = init_result['upload_url']

        # Step 2: Upload chunks
        self.upload_video_chunks(
            upload_url=upload_url,
            video_path=video_path,
            chunk_size=init_result['chunk_size'],
            total_chunks=init_result['total_chunks']
        )

        # Step 3: Poll for status
        for attempt in range(max_poll_attempts):
            status = self.check_publish_status(publish_id)
            current_status = status['status']

            # Success statuses
            # - PUBLISH_COMPLETE: Direct Post API success
            # - SEND_TO_USER_INBOX: Creator Inbox API success (video sent to user's inbox)
            if current_status == 'PUBLISH_COMPLETE':
                logger.info(f"Video published directly: {status.get('video_id')}")
                return {
                    'success': True,
                    'video_id': status.get('video_id'),
                    'publish_id': publish_id,
                }

            if current_status == 'SEND_TO_USER_INBOX':
                logger.info(f"Video sent to Creator Inbox: {publish_id}")
                return {
                    'success': True,
                    'video_id': publish_id,  # Inbox mode doesn't return video_id
                    'publish_id': publish_id,
                    'inbox_mode': True,
                }

            # Failure statuses
            if current_status in ['FAILED', 'PUBLISH_FAILED']:
                reason = status.get('fail_reason', 'Unknown')
                logger.error(f"Publish failed: {reason}")
                return {
                    'success': False,
                    'error': reason,
                    'publish_id': publish_id,
                }

            # Processing statuses - keep polling
            if current_status in ['PROCESSING_UPLOAD', 'PROCESSING', 'SENDING_TO_USER_INBOX']:
                logger.info(f"Processing... ({attempt + 1}/{max_poll_attempts})")
                time.sleep(poll_interval)
                continue

            # Unknown status - keep polling but log warning
            logger.warning(f"Unknown status: {current_status}, continuing to poll...")
            time.sleep(poll_interval)

        logger.error(f"Publish timeout after {max_poll_attempts * poll_interval}s")
        return {
            'success': False,
            'error': 'Processing timeout',
            'publish_id': publish_id,
        }

    def close(self):
        """Close API client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
