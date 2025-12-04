"""
URL configuration for workspace API endpoints
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .workspace_views import WorkspaceViewSet, PublicWorkspaceViewSet

router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'public-workspaces', PublicWorkspaceViewSet, basename='public-workspace')

urlpatterns = router.urls
