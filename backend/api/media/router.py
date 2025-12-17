"""
Media upload router for handling file uploads
"""
import tempfile
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ninja import Router, File, Form, UploadedFile
from django.shortcuts import get_object_or_404
from django.conf import settings

from api.auth.middleware import JWTAuth
from apps.content.models import PostMedia, ScheduledPost
from .schemas import (
    UploadInitIn, UploadInitOut,
    ChunkUploadOut, MediaOut,
    UploadProgressOut, SimpleUploadOut,
    MultiImageUploadIn, SupportedFormatsOut
)
from .upload_handler import ChunkedUploadHandler
from .processing_service import MediaProcessingService

logger = logging.getLogger(__name__)
router = Router()
auth = JWTAuth()


@router.post("/upload/init", response=UploadInitOut, auth=auth)
def init_upload(request, data: UploadInitIn):
    """
    Initialize chunked upload session for large files

    Use this endpoint for files > 50MB. For smaller files, use /upload/simple
    """
    handler = ChunkedUploadHandler()

    try:
        result = handler.init_upload(request.auth.id, data.dict())
        logger.info(f"User {request.auth.id} initialized upload: {data.file_name}")
        return result
    except Exception as e:
        logger.error(f"Failed to init upload: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": f"Upload initialization failed: {str(e)}"},
            status=500
        )


@router.post("/upload/chunk", response=ChunkUploadOut, auth=auth)
def upload_chunk(
    request,
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk: UploadedFile = File(...)
):
    """
    Upload individual chunk

    Chunks can be uploaded in any order and the upload is resumable.
    """
    handler = ChunkedUploadHandler()

    # Read chunk data
    chunk_data = chunk.read()

    try:
        result = handler.handle_chunk(upload_id, chunk_index, chunk_data)
        return result
    except ValueError as e:
        logger.error(f"Chunk upload failed: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": str(e)},
            status=400
        )
    except Exception as e:
        logger.error(f"Chunk upload error: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": "Chunk upload failed"},
            status=500
        )


@router.get("/upload/{upload_id}/status", response=UploadProgressOut, auth=auth)
def get_upload_status(request, upload_id: str):
    """
    Get upload progress status

    Poll this endpoint to track upload progress for chunked uploads.
    """
    handler = ChunkedUploadHandler()

    try:
        status = handler.get_upload_status(upload_id)
        return status
    except ValueError as e:
        return router.api.create_response(
            request,
            {"detail": str(e)},
            status=404
        )


@router.post("/upload/{upload_id}/finalize", response=MediaOut, auth=auth)
def finalize_upload(request, upload_id: str, post_id: Optional[str] = None):
    """
    Finalize chunked upload and create media record

    Call this after all chunks are uploaded (progress = 100%).
    """
    handler = ChunkedUploadHandler()
    processing_service = MediaProcessingService()

    try:
        # Get final file path
        final_path = handler.get_final_path(upload_id)
        if not final_path:
            return router.api.create_response(
                request,
                {"detail": "Upload not completed or not found"},
                status=400
            )

        # Get upload metadata
        status = handler.get_upload_status(upload_id)
        if status['progress'] < 100:
            return router.api.create_response(
                request,
                {"detail": "Upload not completed yet"},
                status=400
            )

        # Validate media type
        cache_key = f"upload:{upload_id}"
        from django.core.cache import cache
        upload_meta = cache.get(cache_key)

        if not upload_meta:
            return router.api.create_response(
                request,
                {"detail": "Upload session expired"},
                status=400
            )

        media_type = upload_meta['media_type']
        file_name = upload_meta['file_name']
        file_size = upload_meta['file_size']
        content_type = upload_meta['content_type']

        # Validate file
        is_valid = False
        metadata = {}

        if media_type == 'video':
            is_valid = processing_service.validate_video(str(final_path))
            if is_valid:
                metadata = processing_service.extract_video_metadata(str(final_path))

                # Generate thumbnail if ffmpeg available
                try:
                    thumb_path = final_path.with_suffix('.jpg')
                    processing_service.generate_thumbnail(str(final_path), str(thumb_path))
                    thumbnail_url = f"/media/uploads/temp/{upload_id}/{thumb_path.name}"
                except Exception as e:
                    logger.warning(f"Thumbnail generation failed: {str(e)}")
                    thumbnail_url = None
        else:
            is_valid = processing_service.validate_image(str(final_path))
            thumbnail_url = None

        if not is_valid:
            handler.cleanup_upload(upload_id)
            return router.api.create_response(
                request,
                {"detail": "Media validation failed"},
                status=400
            )

        # Create media record
        media = PostMedia.objects.create(
            post_id=post_id,
            file_path=str(final_path),
            file_size=file_size,
            file_mime_type=content_type,
            media_type=media_type,
            duration=metadata.get('duration'),
            thumbnail_path=thumbnail_url
        )

        logger.info(f"Finalized upload {upload_id} -> Media {media.id}")

        return media

    except Exception as e:
        logger.error(f"Upload finalization failed: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": f"Finalization failed: {str(e)}"},
            status=500
        )


@router.post("/upload/simple", response=SimpleUploadOut, auth=auth)
def simple_upload(
    request,
    file: UploadedFile = File(...),
    post_id: Optional[str] = None,
    media_type: str = Form("video")
):
    """
    Simple upload for small files (<50MB)

    For larger files, use chunked upload (/upload/init + /upload/chunk).
    """
    if file.size > 50 * 1024 * 1024:
        return router.api.create_response(
            request,
            {"detail": "File too large. Use chunked upload for files > 50MB."},
            status=413
        )

    processing_service = MediaProcessingService()

    # Create upload directory
    upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / str(request.auth.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save to temp file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_filename = f"{timestamp}_{file.name}"
    temp_path = upload_dir / temp_filename

    try:
        with open(temp_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

        # Validate file
        is_valid = False
        metadata = {}
        thumbnail_url = None

        if media_type == 'video':
            is_valid = processing_service.validate_video(str(temp_path))
            if is_valid:
                metadata = processing_service.extract_video_metadata(str(temp_path))

                # Generate thumbnail
                try:
                    thumb_path = temp_path.with_suffix('.jpg')
                    processing_service.generate_thumbnail(str(temp_path), str(thumb_path))
                    thumbnail_url = f"/media/uploads/{request.auth.id}/{thumb_path.name}"
                except Exception as e:
                    logger.warning(f"Thumbnail generation failed: {str(e)}")
        else:
            is_valid = processing_service.validate_image(str(temp_path))
            if is_valid:
                # Generate thumbnail for images
                try:
                    thumb_path = temp_path.with_name(f"thumb_{temp_path.name}")
                    processing_service.generate_image_thumbnail(str(temp_path), str(thumb_path))
                    thumbnail_url = f"/media/uploads/{request.auth.id}/{thumb_path.name}"
                except Exception as e:
                    logger.warning(f"Thumbnail generation failed: {str(e)}")

        if not is_valid:
            temp_path.unlink()
            return router.api.create_response(
                request,
                {"detail": "Media validation failed"},
                status=400
            )

        # Create media record
        media = PostMedia.objects.create(
            post_id=post_id,
            file_path=str(temp_path),
            file_size=file.size,
            file_mime_type=file.content_type,
            media_type=media_type,
            duration=metadata.get('duration'),
            thumbnail_path=thumbnail_url  # Store thumbnail path
        )

        logger.info(f"Simple upload completed: {file.name} -> Media {media.id}")

        return SimpleUploadOut(
            media_id=str(media.id),
            file_name=file.name,
            file_size=file.size,
            media_type=media_type,
            duration=metadata.get('duration'),
            thumbnail_url=thumbnail_url,
            file_path=str(temp_path),
            message="Upload successful"
        )

    except Exception as e:
        logger.error(f"Simple upload failed: {str(e)}")
        if temp_path.exists():
            temp_path.unlink()
        return router.api.create_response(
            request,
            {"detail": f"Upload failed: {str(e)}"},
            status=500
        )


@router.post("/upload/images", response=List[MediaOut], auth=auth)
def upload_multiple_images(
    request,
    images: List[UploadedFile] = File(...),
    post_id: Optional[str] = Form(None)
):
    """
    Upload multiple images at once

    Supports up to 10 images per request. Each image must be < 20MB.
    """
    if len(images) > 10:
        return router.api.create_response(
            request,
            {"detail": "Maximum 10 images per upload"},
            status=400
        )

    processing_service = MediaProcessingService()
    created_media = []

    # Create upload directory
    upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / str(request.auth.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    for idx, image in enumerate(images):
        if image.size > 20 * 1024 * 1024:
            logger.warning(f"Image {image.name} too large ({image.size} bytes), skipping")
            continue

        try:
            # Save image
            filename = f"{timestamp}_{idx}_{image.name}"
            image_path = upload_dir / filename

            with open(image_path, 'wb') as f:
                for chunk in image.chunks():
                    f.write(chunk)

            # Validate
            if not processing_service.validate_image(str(image_path)):
                logger.warning(f"Image {image.name} validation failed, skipping")
                image_path.unlink()
                continue

            # Generate thumbnail
            thumbnail_url = None
            try:
                thumb_path = image_path.with_name(f"thumb_{image_path.name}")
                processing_service.generate_image_thumbnail(str(image_path), str(thumb_path))
                thumbnail_url = f"/media/uploads/{request.auth.id}/{thumb_path.name}"
            except Exception as e:
                logger.warning(f"Thumbnail generation failed: {str(e)}")

            # Create media record
            media = PostMedia.objects.create(
                post_id=post_id,
                file_path=str(image_path),
                file_size=image.size,
                file_mime_type=image.content_type,
                media_type='image',
                thumbnail_path=thumbnail_url
            )

            created_media.append(media)

        except Exception as e:
            logger.error(f"Failed to upload image {image.name}: {str(e)}")
            continue

    if not created_media:
        return router.api.create_response(
            request,
            {"detail": "No images uploaded successfully"},
            status=400
        )

    logger.info(f"Uploaded {len(created_media)} images for user {request.auth.id}")
    return created_media


@router.delete("/{media_id}", auth=auth)
def delete_media(request, media_id: str):
    """
    Delete media file

    Removes both database record and file from local storage.
    """
    try:
        media = get_object_or_404(
            PostMedia,
            id=media_id,
            post__user=request.auth
        )

        processing_service = MediaProcessingService()

        # Delete files
        files_to_delete = [media.file_path]
        if media.thumbnail_url:
            # Extract file path from URL
            thumb_path = Path(settings.MEDIA_ROOT) / media.thumbnail_url.lstrip('/media/')
            files_to_delete.append(str(thumb_path))

        deleted_count = processing_service.cleanup_media_files(files_to_delete)

        # Delete database record
        media.delete()

        logger.info(f"Deleted media {media_id} ({deleted_count} files)")

        return {
            "success": True,
            "message": f"Media deleted ({deleted_count} files removed)"
        }

    except Exception as e:
        logger.error(f"Failed to delete media {media_id}: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": f"Deletion failed: {str(e)}"},
            status=500
        )


@router.get("/supported-formats", response=SupportedFormatsOut, auth=auth)
def get_supported_formats(request):
    """
    Get list of supported media formats and constraints
    """
    return SupportedFormatsOut(
        video=["mp4", "mov", "webm"],
        image=["jpg", "jpeg", "png"],
        max_file_size=500 * 1024 * 1024,  # 500MB
        max_duration=180,  # 3 minutes
        max_resolution="4096x4096",
        chunk_size_recommended=5 * 1024 * 1024  # 5MB
    )


@router.post("/cleanup/expired", auth=auth)
def cleanup_expired_uploads(request):
    """
    Clean up expired upload sessions (admin only)

    Removes temp files from uploads older than 2 hours.
    """
    # Check if user is admin/staff
    if not request.auth.is_staff:
        return router.api.create_response(
            request,
            {"detail": "Admin access required"},
            status=403
        )

    handler = ChunkedUploadHandler()
    cleanup_count = handler.cleanup_expired_uploads()

    return {
        "success": True,
        "cleaned_uploads": cleanup_count,
        "message": f"Cleaned up {cleanup_count} expired uploads"
    }
