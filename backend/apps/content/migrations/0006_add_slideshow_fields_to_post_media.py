# Generated migration for slideshow fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0005_add_scheduling_fields'),
    ]

    operations = [
        # Add carousel_order field
        migrations.AddField(
            model_name='postmedia',
            name='carousel_order',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text='Order position in slideshow (0-indexed)'
            ),
        ),
        # Add image_duration_ms field
        migrations.AddField(
            model_name='postmedia',
            name='image_duration_ms',
            field=models.IntegerField(
                blank=True,
                default=4000,
                null=True,
                help_text='Display duration per image in milliseconds'
            ),
        ),
        # Add is_slideshow_source field
        migrations.AddField(
            model_name='postmedia',
            name='is_slideshow_source',
            field=models.BooleanField(
                default=False,
                help_text='Whether this is a source image for slideshow'
            ),
        ),
        # Add slideshow_video foreign key
        migrations.AddField(
            model_name='postmedia',
            name='slideshow_video',
            field=models.ForeignKey(
                blank=True,
                help_text='Generated slideshow video (for source images)',
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='source_images',
                to='content.postmedia'
            ),
        ),
        # Update media_type choices (handled by model)
        migrations.AlterField(
            model_name='postmedia',
            name='media_type',
            field=models.CharField(
                choices=[
                    ('video', 'Video'),
                    ('image', 'Image'),
                    ('thumbnail', 'Thumbnail'),
                    ('slideshow_source', 'Slideshow Source Image'),
                    ('slideshow_video', 'Slideshow Generated Video'),
                ],
                help_text='Type of media file',
                max_length=20
            ),
        ),
        # Add index for slideshow source queries
        migrations.AddIndex(
            model_name='postmedia',
            index=models.Index(
                fields=['post', 'is_slideshow_source'],
                name='post_media_post_id_slideshow_idx'
            ),
        ),
        # Update ordering
        migrations.AlterModelOptions(
            name='postmedia',
            options={
                'ordering': ['carousel_order', '-created_at'],
                'verbose_name': 'Post Media',
                'verbose_name_plural': 'Post Media'
            },
        ),
    ]
