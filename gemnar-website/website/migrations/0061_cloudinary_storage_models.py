# Generated manually to add Cloudinary storage models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('website', '0060_flowworkspace'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserStorageQuota',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cloudinary_used', models.BigIntegerField(default=0)),
                ('cloudinary_limit', models.BigIntegerField(default=1073741824, help_text='Storage limit in bytes')),
                ('local_used', models.BigIntegerField(default=0)),
                ('local_limit', models.BigIntegerField(default=5368709120, help_text='Local storage limit in bytes')),
                ('total_files', models.IntegerField(default=0)),
                ('max_files', models.IntegerField(default=10000)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='storage_quota', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User storage quotas',
            },
        ),
        migrations.CreateModel(
            name='CloudinaryUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.CharField(help_text='Cloudinary public ID (unique identifier)', max_length=500, unique=True)),
                ('secure_url', models.URLField(help_text='HTTPS URL to access the image', max_length=1000)),
                ('url', models.URLField(help_text='HTTP URL to access the image', max_length=1000)),
                ('folder', models.CharField(help_text='Cloudinary folder path (e.g., user_5/kling_references)', max_length=255)),
                ('original_filename', models.CharField(max_length=255)),
                ('format', models.CharField(help_text='File format (jpg, png, gif, etc.)', max_length=10)),
                ('width', models.IntegerField(blank=True, null=True)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('file_size', models.BigIntegerField(help_text='File size in bytes')),
                ('purpose', models.CharField(choices=[('kling_reference', 'Kling AI Reference'), ('video_generation', 'Video Generation'), ('image_generation', 'Image Generation'), ('flow_generator_image', 'Flow Generator Image'), ('flow_generator_video', 'Flow Generator Video'), ('flow_generator_audio', 'Flow Generator Audio'), ('profile_avatar', 'Profile Avatar'), ('reference', 'Reference Upload'), ('other', 'Other')], default='other', max_length=50)),
                ('usage_count', models.IntegerField(default=0, help_text='Number of times this file has been used')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_accessed', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cloudinary_uploads', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='cloudinaryupload',
            index=models.Index(fields=['user', '-created_at'], name='website_clo_user_id_4b1ecb_idx'),
        ),
        migrations.AddIndex(
            model_name='cloudinaryupload',
            index=models.Index(fields=['public_id'], name='website_clo_public__a09abb_idx'),
        ),
        migrations.AddIndex(
            model_name='cloudinaryupload',
            index=models.Index(fields=['user', 'purpose'], name='website_clo_user_id_60f30f_idx'),
        ),
    ]
