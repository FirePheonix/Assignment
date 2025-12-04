"""
Flow Workspace models for Flow Generator
"""
from django.db import models
from django.contrib.auth import get_user_model
import uuid
import os

User = get_user_model()


class FlowWorkspace(models.Model):
    """
    Flow Workspace model for storing flow generator workspaces
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.CharField(
        max_length=12, 
        unique=True, 
        db_index=True, 
        editable=False,
        help_text='Unique slug for workspace URL (auto-generated from UUID)'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flow_workspaces')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='', help_text='Description shown on published workspace')
    content = models.JSONField(default=dict, blank=True)  # Stores {nodes: [], edges: []}
    is_public = models.BooleanField(default=False, help_text='Whether workspace is publicly accessible')
    published_at = models.DateTimeField(null=True, blank=True, help_text='When workspace was published')
    view_count = models.IntegerField(default=0, help_text='Number of views for public workspace')
    clone_count = models.IntegerField(default=0, help_text='Number of times workspace was cloned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from UUID on first save"""
        # Generate slug before first save if not present
        if not self.slug and self.id:
            # Use first 12 characters of UUID (without dashes) for slug
            self.slug = str(self.id).replace('-', '')[:12]
        
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_public', '-published_at']),
            models.Index(fields=['is_public', '-view_count']),
        ]
        db_table = 'website_flow_workspace'
        verbose_name = 'Flow Workspace'
        verbose_name_plural = 'Flow Workspaces'

    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
    def get_absolute_url(self):
        """Return the URL for this workspace"""
        return f"/flow-generator/{self.slug}"
    
    def duplicate(self, new_name=None):
        """Create a copy of this workspace with a new slug"""
        new_workspace = FlowWorkspace.objects.create(
            user=self.user,
            name=new_name or f"{self.name} (Copy)",
            content=self.content.copy() if self.content else {},
        )
        return new_workspace
    
    def clone_from_public(self, new_user, new_name=None):
        """Clone a public workspace to another user's account"""
        if not self.is_public:
            raise ValueError("Can only clone public workspaces")
        
        # Increment clone count
        self.clone_count += 1
        self.save(update_fields=['clone_count'])
        
        # Create new workspace for the user (not public)
        new_workspace = FlowWorkspace.objects.create(
            user=new_user,
            name=new_name or f"{self.name} (Imported)",
            description=self.description,
            content=self.content.copy() if self.content else {},
            is_public=False,
        )
        return new_workspace


def workspace_media_path(instance, filename):
    """Generate upload path for workspace media"""
    ext = os.path.splitext(filename)[1]
    return f'workspace_media/{instance.workspace.slug}/{uuid.uuid4()}{ext}'


class WorkspaceMedia(models.Model):
    """
    Media attachments for published workspaces (images/videos from AI generation)
    """
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(FlowWorkspace, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(upload_to=workspace_media_path)
    thumbnail = models.ImageField(upload_to=workspace_media_path, null=True, blank=True, help_text='Thumbnail for videos')
    title = models.CharField(max_length=255, blank=True, default='')
    order = models.IntegerField(default=0, help_text='Display order')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        db_table = 'website_workspace_media'
        verbose_name = 'Workspace Media'
        verbose_name_plural = 'Workspace Media'
    
    def __str__(self):
        return f"{self.get_media_type_display()} for {self.workspace.name}"
