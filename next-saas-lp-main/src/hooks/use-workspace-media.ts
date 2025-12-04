"use client";

import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { workspaceApi, type Workspace, type WorkspaceMedia } from '@/lib/workspace-api';

export interface WorkspaceMediaItem {
  id: string;
  url: string;
  thumbnail_url?: string;
  original_filename: string;
  format: string;
  width?: number;
  height?: number;
  file_size?: number;
  purpose: string;
  usage_count: number;
  created_at: string;
  storage_type: 'workspace';
  public_id?: string;
  workspace_name?: string;
  workspace_id?: string;
  mediaType: 'image' | 'video';
  title: string;
}

export function useWorkspaceMedia() {
  const [allMedia, setAllMedia] = useState<WorkspaceMediaItem[]>([]);
  const [filteredMedia, setFilteredMedia] = useState<WorkspaceMediaItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  
  // Filter states
  const [storageFilter, setStorageFilter] = useState<'all' | 'workspace'>('all');
  const [formatFilter, setFormatFilter] = useState<'all' | 'images' | 'videos'>('all');
  const [workspaceFilter, setWorkspaceFilter] = useState<'all' | string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchWorkspaceMedia = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // Fetch all workspaces (list might not include media)
      const workspaceList = await workspaceApi.list();
      console.log('Loaded workspaces:', workspaceList);
      setWorkspaces(workspaceList);
      
      // Extract media from all workspaces
      const allMediaItems: WorkspaceMediaItem[] = [];
      
      // Fetch detailed data for each workspace to get media
      for (const workspace of workspaceList) {
        console.log(`Processing workspace: ${workspace.name}`);
        try {
          // Get detailed workspace data which should include media
          const detailedWorkspace = await workspaceApi.get(workspace.id);
          console.log(`Detailed workspace ${workspace.name}:`, detailedWorkspace.media);
          
          // Extract media from workspace.media array
          if (detailedWorkspace.media && detailedWorkspace.media.length > 0) {
            detailedWorkspace.media.forEach((media: WorkspaceMedia) => {
              console.log('Processing media:', media);
              try {
                // Convert WorkspaceMedia to WorkspaceMediaItem format
                const mediaItem: WorkspaceMediaItem = {
                  id: `${workspace.id}-${media.id}`,
                  url: media.fileUrl,
                  thumbnail_url: media.thumbnailUrl || media.fileUrl,
                  original_filename: media.title || `media_${media.id}`,
                  format: getFileExtension(media.fileUrl) || (media.mediaType === 'image' ? 'jpg' : 'mp4'),
                  width: undefined, // Not available in workspace media
                  height: undefined, // Not available in workspace media  
                  file_size: undefined, // Not available in workspace media
                  purpose: 'workspace_content',
                  usage_count: 1, // Default value
                  created_at: media.createdAt instanceof Date ? media.createdAt.toISOString() : 
                             typeof media.createdAt === 'string' ? media.createdAt : new Date().toISOString(),
                  storage_type: 'workspace',
                  public_id: media.id,
                  workspace_name: workspace.name,
                  workspace_id: workspace.id,
                  mediaType: media.mediaType,
                  title: media.title
                };
                
                allMediaItems.push(mediaItem);
              } catch (error) {
                console.error('Error processing media item:', media, error);
              }
            });
          }
          
          // Also extract media URLs from workspace content (nodes)
          if (detailedWorkspace.content && detailedWorkspace.content.nodes) {
            console.log(`Checking nodes in ${workspace.name}:`, detailedWorkspace.content.nodes);
            detailedWorkspace.content.nodes.forEach((node: any, index: number) => {
              try {
                // Look for media URLs in node data
                const nodeData = node.data || {};
                let mediaUrls: string[] = [];
                
                // Check various possible locations for media URLs
                if (nodeData.imageUrl) mediaUrls.push(nodeData.imageUrl);
                if (nodeData.videoUrl) mediaUrls.push(nodeData.videoUrl);
                if (nodeData.audioUrl) mediaUrls.push(nodeData.audioUrl);
                if (nodeData.mediaUrl) mediaUrls.push(nodeData.mediaUrl);
                if (nodeData.url && isMediaUrl(nodeData.url)) mediaUrls.push(nodeData.url);
                if (nodeData.src && isMediaUrl(nodeData.src)) mediaUrls.push(nodeData.src);
                if (nodeData.fileUrl && isMediaUrl(nodeData.fileUrl)) mediaUrls.push(nodeData.fileUrl);
                
                // Check if node data itself contains media URLs (recursive search)
                const foundUrls = findMediaUrlsInObject(nodeData);
                mediaUrls = mediaUrls.concat(foundUrls);
                
                // Remove duplicates
                mediaUrls = [...new Set(mediaUrls)];
                
                mediaUrls.forEach((url, urlIndex) => {
                  if (url && isMediaUrl(url)) {
                    console.log(`Found media URL in node: ${url}`);
                    const mediaType = getMediaTypeFromUrl(url);
                    const filename = getFilenameFromUrl(url);
                    
                    const mediaItem: WorkspaceMediaItem = {
                      id: `${workspace.id}-node-${index}-${urlIndex}`,
                      url: url,
                      thumbnail_url: mediaType === 'image' ? url : undefined,
                      original_filename: filename,
                      format: getFileExtension(url) || 'unknown',
                      width: undefined,
                      height: undefined,  
                      file_size: undefined,
                      purpose: 'node_content',
                      usage_count: 1,
                      created_at: detailedWorkspace.createdAt.toISOString(),
                      storage_type: 'workspace',
                      public_id: `node-${index}-${urlIndex}`,
                      workspace_name: workspace.name,
                      workspace_id: workspace.id,
                      mediaType: mediaType,
                      title: nodeData.label || nodeData.title || filename || 'Untitled Media'
                    };
                    
                    allMediaItems.push(mediaItem);
                  }
                });
              } catch (error) {
                console.error('Error processing node:', node, error);
              }
            });
          }
        } catch (error) {
          console.error(`Error fetching detailed workspace ${workspace.name}:`, error);
          // Continue with other workspaces even if one fails
        }
      }
      
      // Sort by creation date (newest first)
      allMediaItems.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      
      setAllMedia(allMediaItems);
      
      if (allMediaItems.length > 0) {
        toast.success(`Found ${allMediaItems.length} media items from ${workspaceList.length} workspaces`);
      } else {
        toast.info('No media found in your workspaces');
      }
      
      return allMediaItems;
    } catch (error: any) {
      console.error('Failed to fetch workspace media:', error);
      toast.error('Failed to load workspace media: ' + (error.message || 'Unknown error'));
      setAllMedia([]);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Apply filters when media or filter values change
  useEffect(() => {
    let filtered = [...allMedia];

    // Format filter
    if (formatFilter !== 'all') {
      switch (formatFilter) {
        case 'images':
          filtered = filtered.filter(item => item.mediaType === 'image');
          break;
        case 'videos':
          filtered = filtered.filter(item => item.mediaType === 'video');
          break;
      }
    }

    // Workspace filter
    if (workspaceFilter !== 'all') {
      filtered = filtered.filter(item => item.workspace_id === workspaceFilter);
    }

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(item =>
        item.original_filename.toLowerCase().includes(term) ||
        item.title.toLowerCase().includes(term) ||
        (item.workspace_name && item.workspace_name.toLowerCase().includes(term))
      );
    }

    setFilteredMedia(filtered);
  }, [allMedia, formatFilter, workspaceFilter, searchTerm]);

  const uploadMedia = useCallback(async (file: File, workspaceId: string, title?: string) => {
    try {
      const mediaType = file.type.startsWith('image/') ? 'image' : 'video';
      await workspaceApi.uploadMedia(workspaceId, file, mediaType, title);
      
      // Refresh the media list
      await fetchWorkspaceMedia();
      
      toast.success('Media uploaded successfully');
    } catch (error: any) {
      console.error('Failed to upload media:', error);
      toast.error(error.message || 'Failed to upload media');
      throw error;
    }
  }, [fetchWorkspaceMedia]);

  const deleteMedia = useCallback(async (mediaId: string, workspaceId: string) => {
    try {
      const actualMediaId = mediaId.split('-').pop() || mediaId; // Extract actual media ID
      await workspaceApi.deleteMedia(workspaceId, actualMediaId);
      
      // Remove from local state immediately
      setAllMedia(prev => prev.filter(item => item.id !== mediaId));
      toast.success('Media deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete media:', error);
      toast.error(error.message || 'Failed to delete media');
    }
  }, []);

  const getUniqueFormats = useCallback(() => {
    const formats = new Set(allMedia.map(item => item.format.toLowerCase()));
    return Array.from(formats).sort();
  }, [allMedia]);

  const getUniqueWorkspaces = useCallback(() => {
    return workspaces.map(ws => ({ id: ws.id, name: ws.name }));
  }, [workspaces]);

  const getMediaStats = useCallback(() => {
    const stats = {
      total: allMedia.length,
      images: 0,
      videos: 0,
      workspaces: workspaces.length
    };

    allMedia.forEach(item => {
      if (item.mediaType === 'image') {
        stats.images++;
      } else if (item.mediaType === 'video') {
        stats.videos++;
      }
    });

    return stats;
  }, [allMedia, workspaces]);

  // Load media on mount
  useEffect(() => {
    fetchWorkspaceMedia();
  }, [fetchWorkspaceMedia]);

  return {
    // Data
    allMedia: filteredMedia,
    isLoading,
    workspaces,
    useMockData: false, // Always real data from workspaces
    
    // Filters
    formatFilter,
    setFormatFilter,
    workspaceFilter,
    setWorkspaceFilter,
    searchTerm,
    setSearchTerm,
    
    // Actions
    uploadMedia,
    deleteMedia,
    refetch: fetchWorkspaceMedia,
    
    // Utilities
    getUniqueFormats,
    getUniqueWorkspaces,
    getMediaStats,
  };
}

// Helper function to extract file extension from URL
function getFileExtension(url: string): string | null {
  try {
    const pathname = new URL(url).pathname;
    const extension = pathname.split('.').pop()?.toLowerCase();
    return extension || null;
  } catch {
    // If URL parsing fails, try simple string method
    const parts = url.split('.');
    return parts.length > 1 ? parts.pop()?.toLowerCase() || null : null;
  }
}

// Helper function to check if URL is a media URL
function isMediaUrl(url: string): boolean {
  if (!url || typeof url !== 'string') return false;
  
  const mediaExtensions = [
    // Images
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'tiff', 'ico',
    // Videos  
    'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp',
    // Audio
    'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'
  ];
  
  const extension = getFileExtension(url);
  return extension ? mediaExtensions.includes(extension) : false;
}

// Helper function to determine media type from URL
function getMediaTypeFromUrl(url: string): 'image' | 'video' {
  const extension = getFileExtension(url)?.toLowerCase();
  
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'tiff', 'ico'];
  const videoExtensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp'];
  
  if (extension && imageExtensions.includes(extension)) return 'image';
  if (extension && videoExtensions.includes(extension)) return 'video';
  
  // Default to image if unknown
  return 'image';
}

// Helper function to get filename from URL
function getFilenameFromUrl(url: string): string {
  try {
    const pathname = new URL(url).pathname;
    return pathname.split('/').pop() || 'unknown_file';
  } catch {
    return url.split('/').pop() || 'unknown_file';
  }
}

// Recursively find media URLs in an object
function findMediaUrlsInObject(obj: any, visited = new Set()): string[] {
  if (!obj || typeof obj !== 'object' || visited.has(obj)) return [];
  
  visited.add(obj);
  const urls: string[] = [];
  
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'string' && isMediaUrl(value)) {
      urls.push(value);
    } else if (typeof value === 'object' && value !== null) {
      urls.push(...findMediaUrlsInObject(value, visited));
    }
  }
  
  return urls;
}