"""
Chunked upload handler with local file storage
"""
import os
import shutil
import uuid
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)


class ChunkedUploadHandler:
    """Handle chunked file uploads with local storage"""

    def __init__(self):
        # Use MEDIA_ROOT/uploads for temporary upload storage
        self.upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'temp'
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Final storage location
        self.storage = FileSystemStorage(location=settings.MEDIA_ROOT / 'uploads')

    def init_upload(self, user_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize chunked upload session

        Args:
            user_id: User ID creating the upload
            file_data: File metadata (file_name, file_size, chunk_size, content_type)

        Returns:
            Upload session metadata
        """
        upload_id = str(uuid.uuid4())
        total_chunks = (file_data['file_size'] + file_data['chunk_size'] - 1) // file_data['chunk_size']

        # Store upload metadata in cache
        cache_key = f"upload:{upload_id}"
        upload_meta = {
            'user_id': str(user_id),
            'file_name': file_data['file_name'],
            'file_size': file_data['file_size'],
            'chunk_size': file_data['chunk_size'],
            'total_chunks': total_chunks,
            'received_chunks': [],
            'content_type': file_data['content_type'],
            'media_type': file_data.get('media_type', 'video'),
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }

        # 1 hour expiry
        cache.set(cache_key, upload_meta, 3600)

        # Create temp directory for chunks
        chunk_dir = self.upload_dir / upload_id
        chunk_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized upload {upload_id} for user {user_id} - "
                   f"{file_data['file_name']} ({file_data['file_size']} bytes, {total_chunks} chunks)")

        return {
            'upload_id': upload_id,
            'chunk_size': file_data['chunk_size'],
            'total_chunks': total_chunks,
            'upload_url': f'/api/v1/media/upload/chunk',
            'expires_at': datetime.now() + timedelta(hours=1)
        }

    def handle_chunk(self, upload_id: str, chunk_index: int, chunk_data: bytes) -> Dict[str, Any]:
        """
        Handle individual chunk upload

        Args:
            upload_id: Upload session ID
            chunk_index: Chunk index (0-based)
            chunk_data: Chunk binary data

        Returns:
            Chunk upload status
        """
        cache_key = f"upload:{upload_id}"
        upload_meta = cache.get(cache_key)

        if not upload_meta:
            raise ValueError("Upload session not found or expired")

        # Save chunk to temp file
        chunk_dir = self.upload_dir / upload_id
        chunk_path = chunk_dir / f"chunk_{chunk_index:04d}"

        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)

        # Update metadata
        if chunk_index not in upload_meta['received_chunks']:
            upload_meta['received_chunks'].append(chunk_index)
            upload_meta['received_chunks'].sort()

        upload_meta['status'] = 'uploading'
        cache.set(cache_key, upload_meta, 3600)

        # Calculate progress
        progress = int(len(upload_meta['received_chunks']) / upload_meta['total_chunks'] * 100)

        logger.debug(f"Upload {upload_id}: Received chunk {chunk_index}/{upload_meta['total_chunks']} "
                    f"({len(chunk_data)} bytes, {progress}% complete)")

        # Check if all chunks received
        if len(upload_meta['received_chunks']) == upload_meta['total_chunks']:
            logger.info(f"Upload {upload_id}: All chunks received, assembling file...")
            self._assemble_chunks(upload_id)

        return {
            'upload_id': upload_id,
            'chunk_index': chunk_index,
            'received_bytes': len(chunk_data),
            'status': 'received',
            'progress': progress,
            'next_chunk': self._get_next_missing_chunk(upload_meta)
        }

    def _assemble_chunks(self, upload_id: str) -> None:
        """
        Assemble chunks into final file

        Args:
            upload_id: Upload session ID
        """
        cache_key = f"upload:{upload_id}"
        upload_meta = cache.get(cache_key)

        if not upload_meta:
            raise ValueError("Upload session not found")

        chunk_dir = self.upload_dir / upload_id

        # Create final file
        final_filename = f"{upload_id}_{upload_meta['file_name']}"
        final_path = chunk_dir / final_filename

        try:
            with open(final_path, 'wb') as final_file:
                for i in range(upload_meta['total_chunks']):
                    chunk_path = chunk_dir / f"chunk_{i:04d}"

                    if not chunk_path.exists():
                        raise FileNotFoundError(f"Missing chunk {i}")

                    with open(chunk_path, 'rb') as chunk_file:
                        final_file.write(chunk_file.read())

                    # Clean up chunk
                    chunk_path.unlink()

            # Update status
            upload_meta['status'] = 'completed'
            upload_meta['final_path'] = str(final_path)
            cache.set(cache_key, upload_meta, 3600)

            logger.info(f"Upload {upload_id}: File assembled successfully - {final_path}")

        except Exception as e:
            logger.error(f"Upload {upload_id}: Assembly failed - {str(e)}")
            upload_meta['status'] = 'failed'
            upload_meta['error'] = str(e)
            cache.set(cache_key, upload_meta, 3600)
            raise

    def get_upload_status(self, upload_id: str) -> Dict[str, Any]:
        """
        Get current upload status

        Args:
            upload_id: Upload session ID

        Returns:
            Upload progress information
        """
        cache_key = f"upload:{upload_id}"
        upload_meta = cache.get(cache_key)

        if not upload_meta:
            raise ValueError("Upload not found")

        progress = int(len(upload_meta['received_chunks']) / upload_meta['total_chunks'] * 100)
        uploaded_bytes = len(upload_meta['received_chunks']) * upload_meta['chunk_size']

        # Estimate time remaining
        eta_seconds = None
        if progress > 0 and progress < 100:
            created_at = datetime.fromisoformat(upload_meta['created_at'])
            elapsed = (datetime.now() - created_at).total_seconds()
            if elapsed > 0:
                eta_seconds = int((elapsed / progress) * (100 - progress))

        return {
            'upload_id': upload_id,
            'progress': progress,
            'uploaded_bytes': uploaded_bytes,
            'total_bytes': upload_meta['file_size'],
            'status': upload_meta['status'],
            'eta_seconds': eta_seconds,
            'message': f"{len(upload_meta['received_chunks'])}/{upload_meta['total_chunks']} chunks uploaded"
        }

    def _get_next_missing_chunk(self, upload_meta: Dict[str, Any]) -> Optional[int]:
        """
        Find next missing chunk for resumable upload

        Args:
            upload_meta: Upload metadata

        Returns:
            Next missing chunk index or None if complete
        """
        received = set(upload_meta['received_chunks'])
        total = upload_meta['total_chunks']

        for i in range(total):
            if i not in received:
                return i
        return None

    def get_final_path(self, upload_id: str) -> Optional[Path]:
        """
        Get final assembled file path

        Args:
            upload_id: Upload session ID

        Returns:
            Path to assembled file or None if not completed
        """
        cache_key = f"upload:{upload_id}"
        upload_meta = cache.get(cache_key)

        if not upload_meta or upload_meta['status'] != 'completed':
            return None

        return Path(upload_meta['final_path'])

    def cleanup_upload(self, upload_id: str) -> None:
        """
        Clean up upload session and temp files

        Args:
            upload_id: Upload session ID
        """
        # Remove cache entry
        cache_key = f"upload:{upload_id}"
        cache.delete(cache_key)

        # Remove temp directory
        chunk_dir = self.upload_dir / upload_id
        if chunk_dir.exists():
            shutil.rmtree(chunk_dir)
            logger.info(f"Cleaned up upload {upload_id}")

    def cleanup_expired_uploads(self) -> int:
        """
        Clean up expired upload sessions (older than 2 hours)

        Returns:
            Number of uploads cleaned up
        """
        cleanup_count = 0
        cutoff_time = datetime.now() - timedelta(hours=2)

        for upload_dir in self.upload_dir.iterdir():
            if not upload_dir.is_dir():
                continue

            # Check directory modification time
            mtime = datetime.fromtimestamp(upload_dir.stat().st_mtime)
            if mtime < cutoff_time:
                try:
                    shutil.rmtree(upload_dir)
                    cleanup_count += 1
                    logger.info(f"Cleaned up expired upload: {upload_dir.name}")
                except Exception as e:
                    logger.error(f"Failed to cleanup {upload_dir.name}: {str(e)}")

        return cleanup_count
