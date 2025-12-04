"""
Models for tracking cloud-stored files (Cloudinary, S3, etc.)
Separate from Image model which is for local file storage
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class CloudinaryUpload(models.Model):
    """Track images uploaded to Cloudinary with full metadata"""
    
    UPLOAD_PURPOSES = [
        ('kling_reference', 'Kling AI Reference'),
        ('video_generation', 'Video Generation'),
        ('image_generation', 'Image Generation'),
        ('flow_generator_image', 'Flow Generator Image'),
        ('flow_generator_video', 'Flow Generator Video'),
        ('flow_generator_audio', 'Flow Generator Audio'),
        ('profile_avatar', 'Profile Avatar'),
        ('reference', 'Reference Upload'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="cloudinary_uploads",
        null=True,
        blank=True,
        help_text="User who uploaded the file (null for anonymous uploads)"
    )
    
    # Cloudinary-specific fields
    public_id = models.CharField(
        max_length=500,
        unique=True,
        help_text="Cloudinary public ID (unique identifier)"
    )
    secure_url = models.URLField(
        max_length=1000,
        help_text="HTTPS URL to access the image"
    )
    url = models.URLField(
        max_length=1000,
        help_text="HTTP URL to access the image"
    )
    folder = models.CharField(
        max_length=255,
        help_text="Cloudinary folder path (e.g., user_5/kling_references)"
    )
    
    # File metadata
    original_filename = models.CharField(max_length=255)
    format = models.CharField(
        max_length=10,
        help_text="File format (jpg, png, gif, etc.)"
    )
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    file_size = models.BigIntegerField(
        help_text="File size in bytes"
    )
    
    # Usage tracking
    purpose = models.CharField(
        max_length=50,
        choices=UPLOAD_PURPOSES,
        default='other'
    )
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times this file has been used"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Soft delete (don't actually delete from Cloudinary immediately)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['public_id']),
            models.Index(fields=['user', 'purpose']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.original_filename} ({self.purpose})"
    
    def increment_usage(self):
        """Track when this file is used"""
        self.usage_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['usage_count', 'last_accessed'])
    
    def soft_delete(self):
        """Mark as deleted without removing from Cloudinary"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def get_thumbnail_url(self, width=200, height=200):
        """Generate thumbnail URL using Cloudinary transformations"""
        # Insert transformation parameters into the URL
        # https://res.cloudinary.com/demo/image/upload/w_200,h_200,c_fill/sample.jpg
        parts = self.secure_url.split('/upload/')
        if len(parts) == 2:
            return f"{parts[0]}/upload/w_{width},h_{height},c_fill/{parts[1]}"
        return self.secure_url


class UserStorageQuota(models.Model):
    """Track storage usage per user"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="storage_quota"
    )
    
    # Cloudinary storage (in bytes)
    cloudinary_used = models.BigIntegerField(default=0)
    cloudinary_limit = models.BigIntegerField(
        default=1024 * 1024 * 1024,  # 1GB default
        help_text="Storage limit in bytes"
    )
    
    # Local storage (in bytes)
    local_used = models.BigIntegerField(default=0)
    local_limit = models.BigIntegerField(
        default=5 * 1024 * 1024 * 1024,  # 5GB default
        help_text="Local storage limit in bytes"
    )
    
    # File count limits
    total_files = models.IntegerField(default=0)
    max_files = models.IntegerField(default=10000)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "User storage quotas"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_usage_percentage()}% used"
    
    def get_usage_percentage(self):
        """Calculate total storage usage percentage"""
        total_used = self.cloudinary_used + self.local_used
        total_limit = self.cloudinary_limit + self.local_limit
        return round((total_used / total_limit) * 100, 1) if total_limit > 0 else 0
    
    def has_space_for(self, file_size):
        """Check if user has enough quota for a file"""
        total_used = self.cloudinary_used + self.local_used
        total_limit = self.cloudinary_limit + self.local_limit
        return (total_used + file_size) <= total_limit
    
    def add_cloudinary_usage(self, file_size):
        """Add to Cloudinary usage"""
        self.cloudinary_used += file_size
        self.total_files += 1
        self.save(update_fields=['cloudinary_used', 'total_files', 'updated_at'])
    
    def remove_cloudinary_usage(self, file_size):
        """Remove from Cloudinary usage"""
        self.cloudinary_used = max(0, self.cloudinary_used - file_size)
        self.total_files = max(0, self.total_files - 1)
        self.save(update_fields=['cloudinary_used', 'total_files', 'updated_at'])
