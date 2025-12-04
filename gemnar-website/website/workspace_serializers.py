"""
Workspace serializers for Flow Generator
"""
from rest_framework import serializers
from .workspace_models import FlowWorkspace, WorkspaceMedia


class WorkspaceMediaSerializer(serializers.ModelSerializer):
    """Serializer for WorkspaceMedia model"""
    
    fileUrl = serializers.SerializerMethodField()
    thumbnailUrl = serializers.SerializerMethodField()
    mediaType = serializers.CharField(source='media_type')
    
    class Meta:
        model = WorkspaceMedia
        fields = ['id', 'mediaType', 'fileUrl', 'thumbnailUrl', 'title', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_fileUrl(self, obj):
        """Return full URL for media file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_thumbnailUrl(self, obj):
        """Return full URL for thumbnail"""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
    
    def to_representation(self, instance):
        """Convert datetime fields to ISO format"""
        data = super().to_representation(instance)
        data['createdAt'] = instance.created_at.isoformat()
        data.pop('created_at', None)
        return data


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for FlowWorkspace model"""
    
    userId = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    userName = serializers.SerializerMethodField()
    userProfilePicture = serializers.SerializerMethodField()
    isPublic = serializers.BooleanField(source='is_public', required=False)
    publishedAt = serializers.SerializerMethodField()
    viewCount = serializers.IntegerField(source='view_count', read_only=True)
    cloneCount = serializers.IntegerField(source='clone_count', read_only=True)
    media = WorkspaceMediaSerializer(many=True, read_only=True)
    
    class Meta:
        model = FlowWorkspace
        fields = [
            'id', 'slug', 'userId', 'userName', 'userProfilePicture', 'name', 'description', 
            'content', 'url', 'isPublic', 'publishedAt', 'viewCount', 
            'cloneCount', 'media', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'url', 'viewCount', 'cloneCount', 'created_at', 'updated_at']
    
    def get_userId(self, obj):
        """Return user ID as string to match frontend interface"""
        return str(obj.user.id)
    
    def get_userName(self, obj):
        """Return username for display"""
        return obj.user.username or obj.user.email
    
    def get_userProfilePicture(self, obj):
        """Return user's profile picture URL"""
        if obj.user.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile_image.url)
            return obj.user.profile_image.url
        return None
    
    def get_url(self, obj):
        """Return the public URL for this workspace"""
        return obj.get_absolute_url()
    
    def get_publishedAt(self, obj):
        """Return published date if workspace is public"""
        if obj.published_at:
            return obj.published_at.isoformat()
        return None
    
    def to_representation(self, instance):
        """Convert datetime fields to ISO format for JSON compatibility"""
        data = super().to_representation(instance)
        data['createdAt'] = instance.created_at.isoformat()
        data['updatedAt'] = instance.updated_at.isoformat()
        # Remove snake_case fields in favor of camelCase
        data.pop('created_at', None)
        data.pop('updated_at', None)
        return data


class PublicWorkspaceSerializer(WorkspaceSerializer):
    """Serializer for public workspace views (read-only, no edit permissions)"""
    
    class Meta(WorkspaceSerializer.Meta):
        read_only_fields = WorkspaceSerializer.Meta.fields  # All fields read-only
