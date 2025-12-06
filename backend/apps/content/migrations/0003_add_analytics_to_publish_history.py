"""
Add analytics metrics fields to PublishHistory model
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_update_posts_api_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishhistory',
            name='views',
            field=models.BigIntegerField(
                blank=True,
                null=True,
                help_text="Total views for this video"
            ),
        ),
        migrations.AddField(
            model_name='publishhistory',
            name='likes',
            field=models.BigIntegerField(
                blank=True,
                null=True,
                help_text="Total likes for this video"
            ),
        ),
        migrations.AddField(
            model_name='publishhistory',
            name='comments',
            field=models.BigIntegerField(
                blank=True,
                null=True,
                help_text="Total comments for this video"
            ),
        ),
        migrations.AddField(
            model_name='publishhistory',
            name='shares',
            field=models.BigIntegerField(
                blank=True,
                null=True,
                help_text="Total shares for this video"
            ),
        ),
    ]
