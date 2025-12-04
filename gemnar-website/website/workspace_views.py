"""
Workspace API views for Flow Generator
"""
import uuid
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .workspace_models import FlowWorkspace, WorkspaceMedia
from .workspace_serializers import WorkspaceSerializer, PublicWorkspaceSerializer, WorkspaceMediaSerializer


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Flow Generator workspaces
    
    list: GET /api/workspaces/ - List all user workspaces
    create: POST /api/workspaces/ - Create a new workspace
    retrieve: GET /api/workspaces/{id_or_slug}/ - Get a specific workspace by ID or slug
    update: PUT /api/workspaces/{id_or_slug}/ - Update entire workspace
    partial_update: PATCH /api/workspaces/{id_or_slug}/ - Update workspace content (for saving)
    destroy: DELETE /api/workspaces/{id_or_slug}/ - Delete a workspace
    by_slug: GET /api/workspaces/slug/{slug}/ - Get workspace by slug
    duplicate: POST /api/workspaces/{id_or_slug}/duplicate/ - Duplicate a workspace
    """
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        """Return workspaces for the current user only"""
        return FlowWorkspace.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Support lookup by both UUID and slug"""
        lookup_value = self.kwargs.get(self.lookup_field)
        queryset = self.get_queryset()
        
        # Try UUID first
        try:
            return queryset.get(id=lookup_value)
        except (FlowWorkspace.DoesNotExist, ValueError):
            pass
        
        # Try slug
        try:
            return queryset.get(slug=lookup_value)
        except FlowWorkspace.DoesNotExist:
            pass
        
        # If neither works, raise 404
        from rest_framework.exceptions import NotFound
        raise NotFound('Workspace not found')

    def perform_create(self, serializer):
        """Create workspace with auto-generated UUID and current user"""
        workspace_id = uuid.uuid4()
        serializer.save(
            id=workspace_id,
            user=self.request.user
        )

    def create(self, request, *args, **kwargs):
        """Create a new workspace"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'workspace': serializer.data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """List all workspaces for the current user"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'workspaces': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Get a specific workspace"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'workspace': serializer.data
        })

    def update(self, request, *args, **kwargs):
        """Update a workspace (PUT)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'success': True,
            'workspace': serializer.data
        })

    def partial_update(self, request, *args, **kwargs):
        """Update workspace content (PATCH) - used for saving"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a workspace"""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return Response({
            'success': True
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def rename(self, request, pk=None):
        """Rename a workspace"""
        workspace = self.get_object()
        name = request.data.get('name')
        
        if not name:
            return Response({
                'error': 'Name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        workspace.name = name
        workspace.save()
        
        serializer = self.get_serializer(workspace)
        return Response({
            'success': True,
            'workspace': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a workspace"""
        workspace = self.get_object()
        new_name = request.data.get('name', f"{workspace.name} (Copy)")
        
        new_workspace = workspace.duplicate(new_name=new_name)
        
        serializer = self.get_serializer(new_workspace)
        return Response({
            'success': True,
            'workspace': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def by_slug(self, request, slug=None):
        """Get workspace by slug"""
        try:
            workspace = self.get_queryset().get(slug=slug)
        except FlowWorkspace.DoesNotExist:
            return Response({
                'error': 'Workspace not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(workspace)
        return Response({
            'success': True,
            'workspace': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a workspace to make it publicly accessible"""
        workspace = self.get_object()
        
        workspace.is_public = True
        if not workspace.published_at:
            workspace.published_at = timezone.now()
        
        # Update description if provided
        description = request.data.get('description')
        if description:
            workspace.description = description
        
        workspace.save()
        
        serializer = self.get_serializer(workspace)
        return Response({
            'success': True,
            'workspace': serializer.data,
            'message': 'Workspace published successfully'
        })
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish a workspace to make it private"""
        workspace = self.get_object()
        
        workspace.is_public = False
        workspace.save()
        
        serializer = self.get_serializer(workspace)
        return Response({
            'success': True,
            'workspace': serializer.data,
            'message': 'Workspace unpublished successfully'
        })
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_media(self, request, pk=None):
        """Upload media (image/video) to a workspace"""
        workspace = self.get_object()
        
        media_type = request.data.get('mediaType', 'image')
        title = request.data.get('title', '')
        file = request.FILES.get('file')
        thumbnail = request.FILES.get('thumbnail')  # Optional for videos
        
        if not file:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the current max order
        max_order = WorkspaceMedia.objects.filter(workspace=workspace).count()
        
        media = WorkspaceMedia.objects.create(
            workspace=workspace,
            media_type=media_type,
            file=file,
            thumbnail=thumbnail,
            title=title,
            order=max_order
        )
        
        serializer = WorkspaceMediaSerializer(media, context={'request': request})
        return Response({
            'success': True,
            'media': serializer.data,
            'message': 'Media uploaded successfully'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='media/(?P<media_id>[^/.]+)')
    def delete_media(self, request, pk=None, media_id=None):
        """Delete media from a workspace"""
        workspace = self.get_object()
        
        try:
            media = WorkspaceMedia.objects.get(id=media_id, workspace=workspace)
            media.delete()
            
            return Response({
                'success': True,
                'message': 'Media deleted successfully'
            })
        except WorkspaceMedia.DoesNotExist:
            return Response({
                'error': 'Media not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def import_workspace(self, request, pk=None):
        """Import/clone a public workspace to current user's account"""
        try:
            # Get the public workspace (don't use get_object as it filters by user)
            workspace = FlowWorkspace.objects.get(pk=pk, is_public=True)
        except FlowWorkspace.DoesNotExist:
            return Response({
                'error': 'Public workspace not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        new_name = request.data.get('name', f"{workspace.name} (Imported)")
        
        # Clone to current user
        new_workspace = workspace.clone_from_public(
            new_user=request.user,
            new_name=new_name
        )
        
        serializer = self.get_serializer(new_workspace)
        return Response({
            'success': True,
            'workspace': serializer.data,
            'message': 'Workspace imported successfully'
        }, status=status.HTTP_201_CREATED)


class PublicWorkspaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only workspace views
    
    list: GET /api/public-workspaces/ - List all public workspaces (feed)
    retrieve: GET /api/public-workspaces/{slug}/ - Get a public workspace by slug
    """
    serializer_class = PublicWorkspaceSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Return only public workspaces"""
        return FlowWorkspace.objects.filter(is_public=True).select_related('user').prefetch_related('media')
    
    def list(self, request, *args, **kwargs):
        """List all public workspaces (feed)"""
        queryset = self.get_queryset()
        
        # Support sorting
        sort_by = request.query_params.get('sort', 'recent')  # recent, popular, most_cloned
        
        if sort_by == 'popular':
            queryset = queryset.order_by('-view_count', '-published_at')
        elif sort_by == 'most_cloned':
            queryset = queryset.order_by('-clone_count', '-published_at')
        else:  # recent
            queryset = queryset.order_by('-published_at')
        
        # Filter by search query
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(description__icontains=search)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'workspaces': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get a public workspace by slug"""
        workspace = self.get_object()
        
        # Increment view count
        workspace.view_count += 1
        workspace.save(update_fields=['view_count'])
        
        serializer = self.get_serializer(workspace)
        
        return Response({
            'success': True,
            'workspace': serializer.data
        })
