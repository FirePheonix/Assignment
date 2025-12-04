"use client";

import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  Grid3x3, 
  List, 
  Download, 
  Trash2, 
  Upload,
  Image as ImageIcon,
  Video,
  File,
  X,
  Play,
  Eye,
  Calendar,
  Database,
  MoreHorizontal,
  Folder
} from 'lucide-react';
import { useWorkspaceMedia, type WorkspaceMediaItem } from '@/hooks/use-workspace-media';
import { MediaViewer } from '@/components/MediaViewer';
import { toast } from 'sonner';

interface WorkspaceMediaGalleryProps {
  onMediaSelect?: (media: WorkspaceMediaItem) => void;
  selectedMedia?: WorkspaceMediaItem | null;
  className?: string;
  showUpload?: boolean;
  maxSelection?: number;
}

export function WorkspaceMediaGallery({ 
  onMediaSelect, 
  selectedMedia, 
  className = "",
  showUpload = true,
  maxSelection = 1 
}: WorkspaceMediaGalleryProps) {
  const {
    allMedia,
    isLoading,
    workspaces,
    formatFilter,
    setFormatFilter,
    workspaceFilter,
    setWorkspaceFilter,
    searchTerm,
    setSearchTerm,
    refetch,
    getMediaStats,
    getUniqueWorkspaces,
  } = useWorkspaceMedia();

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [viewerMedia, setViewerMedia] = useState<WorkspaceMediaItem | null>(null);
  const [viewerIndex, setViewerIndex] = useState(0);

  const stats = getMediaStats();
  const workspaceOptions = getUniqueWorkspaces();

  const handleMediaClick = (media: WorkspaceMediaItem, isForSelection: boolean = false) => {
    if (isForSelection) {
      // Handle selection logic
      if (maxSelection === 1) {
        // Single selection mode with handler
        onMediaSelect?.(media);
      } else {
        // Multi-selection mode
        const newSelection = new Set(selectedItems);
        if (newSelection.has(media.id)) {
          newSelection.delete(media.id);
        } else if (newSelection.size < maxSelection) {
          newSelection.add(media.id);
        } else {
          toast.error(`Maximum ${maxSelection} items can be selected`);
          return;
        }
        setSelectedItems(newSelection);
        onMediaSelect?.(media);
      }
    } else {
      // Default behavior: open media viewer
      const index = allMedia.findIndex(m => m.id === media.id);
      setViewerIndex(index);
      setViewerMedia(media);
    }
  };

  const handleViewerNavigate = (index: number) => {
    if (index >= 0 && index < allMedia.length) {
      setViewerIndex(index);
      setViewerMedia(allMedia[index]);
    }
  };

  const getFileIcon = (format: string, mediaType: 'image' | 'video') => {
    if (mediaType === 'image') return ImageIcon;
    if (mediaType === 'video') return Video;
    return File;
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Unknown date';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
        <span className="ml-3 text-gray-400">Loading your workspace media...</span>
      </div>
    );
  }

  return (
    <div className={`h-full flex flex-col ${className}`}>
      {/* Header */}
      <div className="flex flex-col space-y-4 p-4 border-b border-white/10">
        {/* Title and Stats */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Workspace Media</h2>
            <p className="text-sm text-gray-400">
              {stats.total} items from {stats.workspaces} workspaces • {stats.images} images • {stats.videos} videos
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
              title={`Switch to ${viewMode === 'grid' ? 'list' : 'grid'} view`}
            >
              {viewMode === 'grid' ? <List className="w-4 h-4" /> : <Grid3x3 className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 rounded-lg transition-colors ${
                showFilters ? 'bg-purple-500 text-white' : 'bg-white/10 hover:bg-white/20'
              }`}
              title="Toggle filters"
            >
              <Filter className="w-4 h-4" />
            </button>
            <button
              onClick={refetch}
              className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
              title="Refresh media"
            >
              <Database className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by filename, title, or workspace..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-400"
          />
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-white/5 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Media Type</label>
              <select
                value={formatFilter}
                onChange={(e) => setFormatFilter(e.target.value as any)}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-400"
              >
                <option value="all">All Types</option>
                <option value="images">Images</option>
                <option value="videos">Videos</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Workspace</label>
              <select
                value={workspaceFilter}
                onChange={(e) => setWorkspaceFilter(e.target.value)}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-400"
              >
                <option value="all">All Workspaces</option>
                {workspaceOptions.map(workspace => (
                  <option key={workspace.id} value={workspace.id}>
                    {workspace.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Media Grid/List */}
      <div className="flex-1 overflow-auto p-4">
        {allMedia.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <Folder className="w-12 h-12 mb-4" />
            <h3 className="text-lg font-medium mb-2">No media found</h3>
            <p className="text-sm text-center">
              {searchTerm || formatFilter !== 'all' || workspaceFilter !== 'all'
                ? 'Try adjusting your filters or search terms'
                : 'No media files found in your workspaces'
              }
            </p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {allMedia.map((media) => (
              <MediaGridItem
                key={media.id}
                media={media}
                isSelected={selectedItems.has(media.id) || selectedMedia?.id === media.id}
                onClick={() => handleMediaClick(media)}
                onSelect={() => handleMediaClick(media, true)}
                showSelection={!!onMediaSelect}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {allMedia.map((media) => (
              <MediaListItem
                key={media.id}
                media={media}
                isSelected={selectedItems.has(media.id) || selectedMedia?.id === media.id}
                onClick={() => handleMediaClick(media)}
                onSelect={() => handleMediaClick(media, true)}
                showSelection={!!onMediaSelect}
              />
            ))}
          </div>
        )}
      </div>
      
      {/* Media Viewer */}
      <MediaViewer
        media={viewerMedia}
        onClose={() => setViewerMedia(null)}
        allMedia={allMedia}
        currentIndex={viewerIndex}
        onNavigate={handleViewerNavigate}
      />
    </div>
  );
}

// Grid Item Component
function MediaGridItem({ 
  media, 
  isSelected, 
  onClick,
  onSelect,
  showSelection = false
}: { 
  media: WorkspaceMediaItem; 
  isSelected: boolean; 
  onClick: () => void;
  onSelect?: () => void;
  showSelection?: boolean;
}) {
  const [imageError, setImageError] = useState(false);
  const FileIcon = getFileIcon(media.format, media.mediaType);

  return (
    <div
      onClick={onClick}
      className={`group relative bg-white/5 rounded-lg overflow-hidden cursor-pointer border-2 transition-all hover:bg-white/10 ${
        isSelected ? 'border-purple-400 bg-white/15' : 'border-transparent'
      }`}
    >
      {/* Media Preview */}
      <div className="aspect-square relative overflow-hidden bg-gray-800">
        {media.mediaType === 'image' && !imageError ? (
          <img
            src={media.thumbnail_url || media.url}
            alt={media.title}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : media.mediaType === 'video' ? (
          <div className="w-full h-full bg-gray-800 flex items-center justify-center relative">
            <Play className="w-8 h-8 text-white/60" />
            {media.thumbnail_url && (
              <img
                src={media.thumbnail_url}
                alt={media.title}
                className="absolute inset-0 w-full h-full object-cover"
                onError={() => setImageError(true)}
              />
            )}
          </div>
        ) : (
          <div className="w-full h-full bg-gray-800 flex items-center justify-center">
            <FileIcon className="w-8 h-8 text-gray-400" />
          </div>
        )}

        {/* Overlay */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
          <Eye className="w-6 h-6 text-white" />
        </div>

        {/* Selection indicator - only show if showSelection is enabled */}
        {showSelection && isSelected && (
          <div className="absolute top-2 right-2 w-5 h-5 bg-purple-400 rounded-full flex items-center justify-center">
            <div className="w-2 h-2 bg-white rounded-full"></div>
          </div>
        )}
        
        {/* Selection button for interactive selection - only show if showSelection is enabled */}
        {showSelection && !isSelected && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelect?.();
            }}
            className="absolute top-2 right-2 w-5 h-5 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100"
          >
            <div className="w-2 h-2 border border-white rounded-full"></div>
          </button>
        )}

        {/* Media type indicator */}
        <div className="absolute top-2 left-2 px-2 py-1 bg-black/60 rounded text-xs text-white font-medium">
          {media.mediaType.toUpperCase()}
        </div>
      </div>

      {/* Info */}
      <div className="p-3">
        <h4 className="text-sm font-medium text-white truncate" title={media.title}>
          {media.title}
        </h4>
        <p className="text-xs text-gray-400 truncate mt-1" title={media.workspace_name}>
          {media.workspace_name}
        </p>
        <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
          <span className="uppercase">{media.format}</span>
          <span>{formatDate(media.created_at).split(',')[0]}</span>
        </div>
      </div>
    </div>
  );
}

// List Item Component
function MediaListItem({ 
  media, 
  isSelected, 
  onClick,
  onSelect,
  showSelection = false
}: { 
  media: WorkspaceMediaItem; 
  isSelected: boolean; 
  onClick: () => void;
  onSelect?: () => void;
  showSelection?: boolean;
}) {
  const [imageError, setImageError] = useState(false);
  const FileIcon = getFileIcon(media.format, media.mediaType);

  return (
    <div
      onClick={onClick}
      className={`group flex items-center p-3 rounded-lg cursor-pointer border transition-colors hover:bg-white/5 ${
        isSelected ? 'border-purple-400 bg-white/10' : 'border-white/10'
      }`}
    >
      {/* Thumbnail */}
      <div className="w-12 h-12 rounded overflow-hidden bg-gray-800 flex-shrink-0">
        {media.mediaType === 'image' && !imageError ? (
          <img
            src={media.thumbnail_url || media.url}
            alt={media.title}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : media.mediaType === 'video' ? (
          <div className="w-full h-full bg-gray-800 flex items-center justify-center relative">
            <Play className="w-4 h-4 text-white/60" />
            {media.thumbnail_url && (
              <img
                src={media.thumbnail_url}
                alt={media.title}
                className="absolute inset-0 w-full h-full object-cover"
                onError={() => setImageError(true)}
              />
            )}
          </div>
        ) : (
          <div className="w-full h-full bg-gray-800 flex items-center justify-center">
            <FileIcon className="w-4 h-4 text-gray-400" />
          </div>
        )}
      </div>

      {/* Info */}
      <div className="ml-3 flex-1 min-w-0">
        <h4 className="text-sm font-medium text-white truncate" title={media.title}>
          {media.title}
        </h4>
        <div className="flex items-center space-x-3 text-xs text-gray-400 mt-1">
          <span>{media.workspace_name}</span>
          <span>•</span>
          <span className="uppercase">{media.format}</span>
          <span>•</span>
          <span>{media.mediaType}</span>
        </div>
      </div>

      {/* Date and Actions */}
      <div className="flex items-center space-x-3 text-sm text-gray-400">
        <span className="hidden sm:block">{formatDate(media.created_at)}</span>
        
        {/* Selection controls - only show if showSelection is enabled */}
        {showSelection && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelect?.();
            }}
            className={`p-2 rounded transition-all ${
              isSelected 
                ? 'bg-purple-500 text-white' 
                : 'bg-white/10 text-gray-400 hover:bg-white/20 opacity-0 group-hover:opacity-100'
            }`}
          >
            {isSelected ? '✓' : '+'}
          </button>
        )}
        
        <button className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/10 rounded transition-all">
          <MoreHorizontal className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// Helper functions
function getFileIcon(format: string, mediaType: 'image' | 'video') {
  if (mediaType === 'image') return ImageIcon;
  if (mediaType === 'video') return Video;
  return File;
}

function formatDate(dateString: string) {
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return 'Unknown date';
  }
}