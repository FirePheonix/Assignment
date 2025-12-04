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
  Music,
  File,
  Cloud,
  HardDrive,
  X,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Eye,
  Calendar,
  Database,
  MoreHorizontal
} from 'lucide-react';
import { useMediaGallery, type MediaItem } from '@/hooks/use-media-gallery';
import { toast } from 'sonner';

interface MediaGalleryProps {
  onMediaSelect?: (media: MediaItem) => void;
  selectedMedia?: MediaItem | null;
  className?: string;
  showUpload?: boolean;
  maxSelection?: number;
}

export function MediaGallery({ 
  onMediaSelect, 
  selectedMedia, 
  className = "",
  showUpload = true,
  maxSelection = 1 
}: MediaGalleryProps) {
  const {
    allMedia,
    isLoading,
    quota,
    storageFilter,
    setStorageFilter,
    formatFilter,
    setFormatFilter,
    purposeFilter,
    setPurposeFilter,
    searchTerm,
    setSearchTerm,
    uploadMedia,
    deleteMedia,
    refetch,
    getUniqueFormats,
    getUniquePurposes,
    getMediaStats
  } = useMediaGallery();

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewMedia, setPreviewMedia] = useState<MediaItem | null>(null);

  const stats = getMediaStats();
  const uniqueFormats = getUniqueFormats();
  const uniquePurposes = getUniquePurposes();

  const handleFileUpload = async (files: FileList) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    const file = files[0];

    // Validate file size (100MB limit)
    if (file.size > 100 * 1024 * 1024) {
      toast.error('File size must be less than 100MB');
      setUploading(false);
      return;
    }

    try {
      await uploadMedia(file, 'user_upload');
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    handleFileUpload(files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      handleFileUpload(files);
    }
  };

  const handleMediaSelect = (media: MediaItem) => {
    if (onMediaSelect) {
      onMediaSelect(media);
    }
  };

  const handleDelete = async (media: MediaItem, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (confirm(`Are you sure you want to delete "${media.original_filename}"?`)) {
      await deleteMedia(media.id, media.storage_type);
    }
  };

  const downloadMedia = async (media: MediaItem, e: React.MouseEvent) => {
    e.stopPropagation();
    
    try {
      const response = await fetch(media.url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = media.original_filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      toast.error('Failed to download media');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getMediaIcon = (format: string, className?: string) => {
    const ext = format.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) {
      return <ImageIcon className={className} />;
    } else if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(ext)) {
      return <Video className={className} />;
    } else if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(ext)) {
      return <Music className={className} />;
    }
    return <File className={className} />;
  };

  const isVideoFile = (format: string) => {
    return ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(format.toLowerCase());
  };

  const isAudioFile = (format: string) => {
    return ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(format.toLowerCase());
  };

  const isImageFile = (format: string) => {
    return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(format.toLowerCase());
  };

  if (isLoading) {
    return (
      <div className={`bg-[#1a1a1a] border border-white/10 rounded-lg p-8 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          <span className="ml-3 text-gray-400">Loading media library...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-[#1a1a1a] border border-white/10 rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Media Library</h2>
            <p className="text-gray-400 text-sm mt-1">
              Manage your images, videos, and audio files
            </p>
          </div>
          <button
            onClick={refetch}
            className="text-purple-400 hover:text-purple-300 text-sm px-4 py-2 border border-white/10 rounded-lg"
          >
            Refresh
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
          <div className="bg-white/5 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-purple-400" />
              <span className="text-xs text-gray-400">Total</span>
            </div>
            <div className="text-lg font-bold text-white">{stats.total}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-green-400" />
              <span className="text-xs text-gray-400">Images</span>
            </div>
            <div className="text-lg font-bold text-white">{stats.images}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <Video className="w-4 h-4 text-blue-400" />
              <span className="text-xs text-gray-400">Videos</span>
            </div>
            <div className="text-lg font-bold text-white">{stats.videos}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <Music className="w-4 h-4 text-orange-400" />
              <span className="text-xs text-gray-400">Audio</span>
            </div>
            <div className="text-lg font-bold text-white">{stats.audio}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <Cloud className="w-4 h-4 text-cyan-400" />
              <span className="text-xs text-gray-400">Cloudinary</span>
            </div>
            <div className="text-lg font-bold text-white">{stats.cloudinary}</div>
          </div>
        </div>

        {/* Search and Controls */}
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search media files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          {/* View Mode */}
          <div className="flex bg-white/5 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded transition ${
                viewMode === 'grid' 
                  ? 'bg-purple-500 text-white' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Grid3x3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded transition ${
                viewMode === 'list' 
                  ? 'bg-purple-500 text-white' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Filters */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm hover:bg-white/10 transition"
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-4 p-4 bg-white/5 rounded-lg border border-white/10">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Storage Filter */}
              <div>
                <label className="block text-xs text-gray-400 mb-2">Storage</label>
                <select
                  value={storageFilter}
                  onChange={(e) => setStorageFilter(e.target.value as any)}
                  className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-sm"
                >
                  <option value="all">All Storage</option>
                  <option value="cloudinary">Cloudinary</option>
                  <option value="local">Local</option>
                </select>
              </div>

              {/* Format Filter */}
              <div>
                <label className="block text-xs text-gray-400 mb-2">Type</label>
                <select
                  value={formatFilter}
                  onChange={(e) => setFormatFilter(e.target.value as any)}
                  className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-sm"
                >
                  <option value="all">All Types</option>
                  <option value="images">Images</option>
                  <option value="videos">Videos</option>
                  <option value="audio">Audio</option>
                </select>
              </div>

              {/* Purpose Filter */}
              <div>
                <label className="block text-xs text-gray-400 mb-2">Purpose</label>
                <select
                  value={purposeFilter}
                  onChange={(e) => setPurposeFilter(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-sm"
                >
                  <option value="all">All Purposes</option>
                  {uniquePurposes.map(purpose => (
                    <option key={purpose} value={purpose}>
                      {purpose.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Upload Section */}
      {showUpload && (
        <div className="p-6 border-b border-white/10">
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center transition ${
              isDragOver 
                ? 'border-purple-500 bg-purple-500/10' 
                : 'border-white/20 hover:border-purple-500/50'
            }`}
            onDrop={handleDrop}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
          >
            {uploading ? (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mb-3"></div>
                <p className="text-sm text-gray-400">Uploading media...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <Upload className="w-8 h-8 text-gray-400 mb-3" />
                <p className="text-sm text-gray-400 mb-2">
                  Drag & drop media files here, or click to upload
                </p>
                <p className="text-xs text-gray-500">
                  Images, Videos, Audio files up to 100MB
                </p>
                <input
                  type="file"
                  accept="image/*,video/*,audio/*"
                  onChange={handleFileInput}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Storage Quota */}
      {quota && (
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Storage Usage</span>
            <span className="text-sm text-white">{quota.usage_percentage}%</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition ${
                quota.usage_percentage > 90 
                  ? 'bg-red-500' 
                  : quota.usage_percentage > 75 
                    ? 'bg-yellow-500' 
                    : 'bg-gradient-to-r from-purple-500 to-pink-500'
              }`}
              style={{ width: `${Math.min(quota.usage_percentage, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>{formatFileSize(quota.cloudinary_used + quota.local_used)} used</span>
            <span>{formatFileSize(quota.cloudinary_limit + quota.local_limit)} total</span>
          </div>
        </div>
      )}

      {/* Media Content */}
      <div className="p-6">
        {allMedia.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-400 mb-2">No media files found</h4>
            <p className="text-sm text-gray-500">
              {searchTerm || storageFilter !== 'all' || formatFilter !== 'all' || purposeFilter !== 'all'
                ? 'Try adjusting your filters or search term'
                : showUpload
                ? 'Upload your first media file to get started'
                : 'No media files in your library'
              }
            </p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {allMedia.map((media) => (
              <MediaGridItem
                key={`${media.storage_type}-${media.id}`}
                media={media}
                isSelected={selectedMedia?.id === media.id && selectedMedia?.storage_type === media.storage_type}
                onSelect={() => handleMediaSelect(media)}
                onDelete={(e) => handleDelete(media, e)}
                onDownload={(e) => downloadMedia(media, e)}
                onPreview={() => setPreviewMedia(media)}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {allMedia.map((media) => (
              <MediaListItem
                key={`${media.storage_type}-${media.id}`}
                media={media}
                isSelected={selectedMedia?.id === media.id && selectedMedia?.storage_type === media.storage_type}
                onSelect={() => handleMediaSelect(media)}
                onDelete={(e) => handleDelete(media, e)}
                onDownload={(e) => downloadMedia(media, e)}
                onPreview={() => setPreviewMedia(media)}
                formatFileSize={formatFileSize}
                getMediaIcon={getMediaIcon}
              />
            ))}
          </div>
        )}
      </div>

      {/* Media Preview Modal */}
      {previewMedia && (
        <MediaPreviewModal
          media={previewMedia}
          onClose={() => setPreviewMedia(null)}
          onDownload={(e) => downloadMedia(previewMedia, e)}
          formatFileSize={formatFileSize}
          isImageFile={isImageFile}
          isVideoFile={isVideoFile}
          isAudioFile={isAudioFile}
        />
      )}
    </div>
  );
}

// Grid Item Component
interface MediaGridItemProps {
  media: MediaItem;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onDownload: (e: React.MouseEvent) => void;
  onPreview: () => void;
}

function MediaGridItem({ media, isSelected, onSelect, onDelete, onDownload, onPreview }: MediaGridItemProps) {
  const isVideo = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(media.format.toLowerCase());
  const isAudio = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(media.format.toLowerCase());
  const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(media.format.toLowerCase());

  return (
    <div
      className={`relative group aspect-square rounded-lg overflow-hidden cursor-pointer border-2 transition ${
        isSelected
          ? 'border-purple-500 ring-2 ring-purple-500/50'
          : 'border-white/10 hover:border-white/30'
      }`}
      onClick={onSelect}
    >
      {/* Media Preview */}
      <div className="w-full h-full bg-gray-900 flex items-center justify-center">
        {isImage ? (
          <img
            src={media.thumbnail_url || media.url}
            alt={media.original_filename}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
              (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
            }}
          />
        ) : isVideo ? (
          <div className="relative w-full h-full bg-gray-800 flex items-center justify-center">
            <Video className="w-8 h-8 text-blue-400" />
            <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-1 rounded">
              {media.format.toUpperCase()}
            </div>
          </div>
        ) : isAudio ? (
          <div className="relative w-full h-full bg-gray-800 flex items-center justify-center">
            <Music className="w-8 h-8 text-orange-400" />
            <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-1 rounded">
              {media.format.toUpperCase()}
            </div>
          </div>
        ) : (
          <div className="relative w-full h-full bg-gray-800 flex items-center justify-center">
            <File className="w-8 h-8 text-gray-400" />
            <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-1 rounded">
              {media.format.toUpperCase()}
            </div>
          </div>
        )}
      </div>

      {/* Overlay */}
      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
        <div className="flex gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onPreview();
            }}
            className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition"
            title="Preview"
          >
            <Eye className="w-4 h-4 text-white" />
          </button>
          <button
            onClick={onDownload}
            className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition"
            title="Download"
          >
            <Download className="w-4 h-4 text-white" />
          </button>
          <button
            onClick={onDelete}
            className="p-2 bg-red-500/20 rounded-full hover:bg-red-500/30 transition"
            title="Delete"
          >
            <Trash2 className="w-4 h-4 text-red-400" />
          </button>
        </div>
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )}

      {/* Storage indicator */}
      <div className="absolute top-2 left-2">
        {media.storage_type === 'cloudinary' ? (
          <Cloud className="w-4 h-4 text-cyan-400" />
        ) : (
          <HardDrive className="w-4 h-4 text-green-400" />
        )}
      </div>

      {/* File info */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2">
        <div className="text-white text-xs font-medium truncate">
          {media.original_filename}
        </div>
        <div className="text-gray-300 text-xs">
          {new Date(media.created_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}

// List Item Component
interface MediaListItemProps {
  media: MediaItem;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onDownload: (e: React.MouseEvent) => void;
  onPreview: () => void;
  formatFileSize: (bytes: number) => string;
  getMediaIcon: (format: string, className?: string) => React.ReactNode;
}

function MediaListItem({ 
  media, 
  isSelected, 
  onSelect, 
  onDelete, 
  onDownload, 
  onPreview,
  formatFileSize,
  getMediaIcon
}: MediaListItemProps) {
  return (
    <div
      className={`flex items-center p-3 rounded-lg cursor-pointer transition ${
        isSelected
          ? 'bg-purple-500/20 border border-purple-500/50'
          : 'bg-white/5 hover:bg-white/10 border border-transparent'
      }`}
      onClick={onSelect}
    >
      {/* Icon/Thumbnail */}
      <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gray-800 flex items-center justify-center mr-4">
        {getMediaIcon(media.format, "w-6 h-6 text-gray-400")}
      </div>

      {/* File Info */}
      <div className="flex-1 min-w-0">
        <div className="font-medium text-white truncate">
          {media.original_filename}
        </div>
        <div className="text-sm text-gray-400">
          {formatFileSize(media.file_size)} • {media.format.toUpperCase()} • {new Date(media.created_at).toLocaleDateString()}
        </div>
        <div className="text-xs text-gray-500">
          {media.purpose.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} • {media.storage_type === 'cloudinary' ? 'Cloudinary' : 'Local'}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 ml-4">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onPreview();
          }}
          className="p-2 text-gray-400 hover:text-white transition"
          title="Preview"
        >
          <Eye className="w-4 h-4" />
        </button>
        <button
          onClick={onDownload}
          className="p-2 text-gray-400 hover:text-white transition"
          title="Download"
        >
          <Download className="w-4 h-4" />
        </button>
        <button
          onClick={onDelete}
          className="p-2 text-gray-400 hover:text-red-400 transition"
          title="Delete"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// Preview Modal Component
interface MediaPreviewModalProps {
  media: MediaItem;
  onClose: () => void;
  onDownload: (e: React.MouseEvent) => void;
  formatFileSize: (bytes: number) => string;
  isImageFile: (format: string) => boolean;
  isVideoFile: (format: string) => boolean;
  isAudioFile: (format: string) => boolean;
}

function MediaPreviewModal({ 
  media, 
  onClose, 
  onDownload, 
  formatFileSize,
  isImageFile,
  isVideoFile,
  isAudioFile
}: MediaPreviewModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
      <div className="bg-[#1a1a1a] rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gray-800 rounded flex items-center justify-center">
              {media.storage_type === 'cloudinary' ? (
                <Cloud className="w-4 h-4 text-cyan-400" />
              ) : (
                <HardDrive className="w-4 h-4 text-green-400" />
              )}
            </div>
            <div>
              <h3 className="font-medium text-white truncate">{media.original_filename}</h3>
              <p className="text-sm text-gray-400">
                {formatFileSize(media.file_size)} • {media.format.toUpperCase()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onDownload}
              className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition"
              title="Download"
            >
              <Download className="w-4 h-4 text-white" />
            </button>
            <button
              onClick={onClose}
              className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition"
              title="Close"
            >
              <X className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>

        {/* Media Content */}
        <div className="p-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Media Display */}
            <div className="flex-1">
              {isImageFile(media.format) ? (
                <img
                  src={media.url}
                  alt={media.original_filename}
                  className="w-full h-auto max-h-96 object-contain rounded-lg bg-gray-900"
                />
              ) : isVideoFile(media.format) ? (
                <video
                  src={media.url}
                  controls
                  className="w-full h-auto max-h-96 rounded-lg bg-gray-900"
                >
                  Your browser does not support video playback.
                </video>
              ) : isAudioFile(media.format) ? (
                <div className="bg-gray-900 rounded-lg p-8 flex flex-col items-center">
                  <Music className="w-16 h-16 text-orange-400 mb-4" />
                  <audio
                    src={media.url}
                    controls
                    className="w-full max-w-md"
                  >
                    Your browser does not support audio playback.
                  </audio>
                </div>
              ) : (
                <div className="bg-gray-900 rounded-lg p-8 flex flex-col items-center text-center">
                  <File className="w-16 h-16 text-gray-400 mb-4" />
                  <p className="text-white font-medium mb-2">{media.original_filename}</p>
                  <p className="text-gray-400">Preview not available for this file type</p>
                </div>
              )}
            </div>

            {/* Media Details */}
            <div className="lg:w-80 space-y-4">
              <div className="bg-white/5 rounded-lg p-4">
                <h4 className="font-medium text-white mb-3">File Details</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Format:</span>
                    <span className="text-white">{media.format.toUpperCase()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Size:</span>
                    <span className="text-white">{formatFileSize(media.file_size)}</span>
                  </div>
                  {media.width && media.height && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Dimensions:</span>
                      <span className="text-white">{media.width} × {media.height}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-400">Storage:</span>
                    <span className="text-white capitalize">{media.storage_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Purpose:</span>
                    <span className="text-white">
                      {media.purpose.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Usage Count:</span>
                    <span className="text-white">{media.usage_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Created:</span>
                    <span className="text-white">{new Date(media.created_at).toLocaleDateString()}</span>
                  </div>
                  {media.public_id && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Public ID:</span>
                      <span className="text-white text-xs truncate">{media.public_id}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}