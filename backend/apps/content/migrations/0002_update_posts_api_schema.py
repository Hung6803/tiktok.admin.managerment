# Generated migration for Posts API schema updates

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
        ('tiktok_accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ScheduledPost changes
        migrations.RenameField(
            model_name='scheduledpost',
            old_name='caption',
            new_name='description',
        ),
        migrations.AddField(
            model_name='scheduledpost',
            name='title',
            field=models.CharField(default='', help_text='Post title (max 150 chars)', max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scheduledpost',
            name='user',
            field=models.ForeignKey(
                default=1,
                help_text='User who created the post',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posts',
                to=settings.AUTH_USER_MODEL
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scheduledpost',
            name='allow_comments',
            field=models.BooleanField(default=True, help_text='Allow comments on post'),
        ),
        migrations.AddField(
            model_name='scheduledpost',
            name='allow_duet',
            field=models.BooleanField(default=True, help_text='Allow duet with this video'),
        ),
        migrations.AddField(
            model_name='scheduledpost',
            name='allow_stitch',
            field=models.BooleanField(default=True, help_text='Allow stitch with this video'),
        ),
        migrations.RemoveField(
            model_name='scheduledpost',
            name='tiktok_account',
        ),
        migrations.AddField(
            model_name='scheduledpost',
            name='accounts',
            field=models.ManyToManyField(
                help_text='TikTok accounts to publish to',
                related_name='scheduled_posts',
                to='tiktok_accounts.tiktokaccount'
            ),
        ),
        migrations.RemoveField(
            model_name='scheduledpost',
            name='mentions',
        ),
        migrations.RemoveField(
            model_name='scheduledpost',
            name='timezone',
        ),
        migrations.RemoveField(
            model_name='scheduledpost',
            name='tiktok_video_id',
        ),
        migrations.RemoveField(
            model_name='scheduledpost',
            name='video_url',
        ),
        migrations.RemoveField(
            model_name='scheduledpost',
            name='retry_count',
        ),
        migrations.RemoveField(
            model_name='scheduledpost',
            name='max_retries',
        ),
        migrations.AlterField(
            model_name='scheduledpost',
            name='scheduled_time',
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text='When to publish the post',
                null=True
            ),
        ),
        migrations.AlterField(
            model_name='scheduledpost',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('scheduled', 'Scheduled'),
                    ('pending', 'Pending'),
                    ('publishing', 'Publishing'),
                    ('published', 'Published'),
                    ('failed', 'Failed')
                ],
                db_index=True,
                default='draft',
                help_text='Current status of the post',
                max_length=20
            ),
        ),
        migrations.AlterModelOptions(
            name='scheduledpost',
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Scheduled Post',
                'verbose_name_plural': 'Scheduled Posts'
            },
        ),

        # PostMedia changes
        migrations.RenameField(
            model_name='postmedia',
            old_name='scheduled_post',
            new_name='post',
        ),

        # PublishHistory changes
        migrations.RenameField(
            model_name='publishhistory',
            old_name='scheduled_post',
            new_name='post',
        ),
        migrations.AddField(
            model_name='publishhistory',
            name='account',
            field=models.ForeignKey(
                default=1,
                help_text='Account used for publishing',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='publish_history',
                to='tiktok_accounts.tiktokaccount'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='publishhistory',
            name='status',
            field=models.CharField(
                choices=[('success', 'Success'), ('failed', 'Failed')],
                default='failed',
                help_text='Status of publish attempt',
                max_length=20
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='publishhistory',
            name='tiktok_video_id',
            field=models.CharField(
                blank=True,
                help_text="TikTok's video ID if successful",
                max_length=100,
                null=True
            ),
        ),
        migrations.RemoveField(
            model_name='publishhistory',
            name='started_at',
        ),
        migrations.AddField(
            model_name='publishhistory',
            name='published_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When successfully published',
                null=True
            ),
        ),
        migrations.RemoveField(
            model_name='publishhistory',
            name='attempt_number',
        ),
        migrations.RemoveField(
            model_name='publishhistory',
            name='completed_at',
        ),
        migrations.RemoveField(
            model_name='publishhistory',
            name='success',
        ),
        migrations.RemoveField(
            model_name='publishhistory',
            name='error_code',
        ),
        migrations.RemoveField(
            model_name='publishhistory',
            name='api_response',
        ),
        migrations.RemoveField(
            model_name='publishhistory',
            name='http_status',
        ),
        migrations.AlterModelOptions(
            name='publishhistory',
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Publish History',
                'verbose_name_plural': 'Publish Histories'
            },
        ),

        # Update indexes
        migrations.AlterIndexTogether(
            name='scheduledpost',
            index_together={('user', 'status'), ('status', 'scheduled_time')},
        ),
        migrations.AlterIndexTogether(
            name='publishhistory',
            index_together={('post', 'account')},
        ),
    ]
