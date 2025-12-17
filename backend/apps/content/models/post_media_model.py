"""
Post media model for tracking media files attached to scheduled posts
"""
from django.db import models
from core.models import BaseModel


class PostMedia(BaseModel):
    """
    Media files (videos, images, thumbnails) associated with scheduled posts
    """

    MEDIA_TYPE_CHOICES = [
        ('video', 'Video'),
        ('image', 'Image'),
        ('thumbnail', 'Thumbnail'),
        ('slideshow_source', 'Slideshow Source Image'),
        ('slideshow_video', 'Slideshow Generated Video'),
    ]

    post = models.ForeignKey(
        'content.ScheduledPost',
        on_delete=models.CASCADE,
        related_name='media',
        null=True,
        blank=True,
        help_text="Post this media belongs to (optional for standalone uploads)"
    )
    media_type = models.CharField(
        max_length=20,
        choices=MEDIA_TYPE_CHOICES,
        help_text="Type of media file"
    )

    # File storage
    file_path = models.CharField(
        max_length=500,
        help_text="Path to the media file"
    )
    file_size = models.BigIntegerField(
        help_text="File size in bytes"
    )
    file_mime_type = models.CharField(
        max_length=100,
        help_text="MIME type of the file"
    )

    # Video metadata
    duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Video duration in seconds"
    )
    width = models.IntegerField(
        null=True,
        blank=True,
        help_text="Video/image width in pixels"
    )
    height = models.IntegerField(
        null=True,
        blank=True,
        help_text="Video/image height in pixels"
    )

    # Processing
    is_processed = models.BooleanField(
        default=False,
        help_text="Whether media has been processed"
    )
    thumbnail_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Path to generated thumbnail"
    )

    # Slideshow specific fields
    carousel_order = models.IntegerField(
        null=True,
        blank=True,
        help_text="Order position in slideshow (0-indexed)"
    )
    image_duration_ms = models.IntegerField(
        null=True,
        blank=True,
        default=4000,
        help_text="Display duration per image in milliseconds"
    )
    is_slideshow_source = models.BooleanField(
        default=False,
        help_text="Whether this is a source image for slideshow"
    )
    slideshow_video = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_images',
        help_text="Generated slideshow video (for source images)"
    )

    class Meta:
        db_table = 'post_media'
        ordering = ['carousel_order', '-created_at']
        indexes = [
            models.Index(fields=['post', 'media_type']),
            models.Index(fields=['post', 'is_slideshow_source']),
        ]
        verbose_name = "Post Media"
        verbose_name_plural = "Post Media"
        app_label = 'content'

    def __str__(self):
        return f"{self.media_type} for {self.post.id}"

    def get_file_size_mb(self):
        """Get file size in megabytes"""
        return round(self.file_size / (1024 * 1024), 2)
