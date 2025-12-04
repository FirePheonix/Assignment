"use client";

import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { mockFetchMedia, mockUploadMedia, mockDeleteMedia, isDjangoBackendAvailable } from '@/lib/mock-media-api';

export interface MediaItem {
  id: number;
  url: string;
  thumbnail_url?: string;
  original_filename: string;
  format: string;
  width?: number;
  height?: number;
  file_size: number;
  purpose: string;
  usage_count: number;
  created_at: string;
  storage_type: 'cloudinary' | 'local';
  public_id?: string;
}

export interface MediaQuota {
  cloudinary_used: number;
  cloudinary_limit: number;
  local_used: number;
  local_limit: number;
  total_files: number;
  max_files: number;
  usage_percentage: number;
}

export interface MediaResponse {
  success: boolean;
  local_uploads: MediaItem[];
  cloudinary_uploads: MediaItem[];
  quota?: MediaQuota;
  total_local: number;
  total_cloudinary: number;
}

const API_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  const token = localStorage.getItem('auth_token');
  return token;
}

// Remove CSRF function - using token auth only

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getAuthToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Token ${token}` }),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  return response;
}

async function fetchMultipartWithAuth(url: string, options: RequestInit = {}) {
  const token = getAuthToken();
  
  const headers: HeadersInit = {
    ...(token && { 'Authorization': `Token ${token}` }),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  return response;
}

export function useMediaGallery() {
  const [allMedia, setAllMedia] = useState<MediaItem[]>([]);
  const [filteredMedia, setFilteredMedia] = useState<MediaItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [quota, setQuota] = useState<MediaQuota | null>(null);
  const [totalCount, setTotalCount] = useState({ local: 0, cloudinary: 0 });
  const [useMockData, setUseMockData] = useState(false);
  
  // Filter states
  const [storageFilter, setStorageFilter] = useState<'all' | 'local' | 'cloudinary'>('all');
  const [formatFilter, setFormatFilter] = useState<'all' | 'images' | 'videos' | 'audio'>('all');
  const [purposeFilter, setPurposeFilter] = useState<'all' | string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Check if backend is available on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const isAvailable = await isDjangoBackendAvailable();
        console.log('Django backend available:', isAvailable);
        setUseMockData(!isAvailable);
        
        if (!isAvailable) {
          console.log('Using mock data - Django backend not available');
          // Use mock data
          const data = await mockFetchMedia('all', 100, 0);
          const combinedMedia: MediaItem[] = [
            ...data.cloudinary_uploads.map(item => ({ ...item, storage_type: 'cloudinary' as const })),
            ...data.local_uploads.map(item => ({ ...item, storage_type: 'local' as const }))
          ];
          combinedMedia.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
          setAllMedia(combinedMedia);
          setQuota(data.quota || null);
          setTotalCount({ local: data.total_local, cloudinary: data.total_cloudinary });
          setIsLoading(false);
          toast.info('Using demo data - Django backend not available');
        } else {
          console.log('Django backend is available, attempting to fetch real data...');
          // Backend is available, try to fetch real data
          setIsLoading(false); // Let fetchMedia handle loading state
        }
      } catch (error) {
        console.log('Backend check failed, using mock data:', error);
        setUseMockData(true);
        // Load mock data immediately
        const data = await mockFetchMedia('all', 100, 0);
        const combinedMedia: MediaItem[] = [
          ...data.cloudinary_uploads.map(item => ({ ...item, storage_type: 'cloudinary' as const })),
          ...data.local_uploads.map(item => ({ ...item, storage_type: 'local' as const }))
        ];
        combinedMedia.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setAllMedia(combinedMedia);
        setQuota(data.quota || null);
        setTotalCount({ local: data.total_local, cloudinary: data.total_cloudinary });
        setIsLoading(false);
        toast.info('Using demo data - Django backend not available');
      }
    };
    checkBackend();
  }, []);

  const fetchMedia = useCallback(async (
    storageType: 'all' | 'local' | 'cloudinary' = 'all',
    limit: number = 100,
    offset: number = 0
  ) => {
    try {
      setIsLoading(true);

      let data: MediaResponse;

      if (useMockData) {
        // Use mock data when Django backend is not available
        data = await mockFetchMedia(storageType, limit, offset);
      } else {
        // Use real API
        const params = new URLSearchParams({
          type: storageType,
          limit: limit.toString(),
          offset: offset.toString(),
          format: 'detailed'
        });

        const response = await fetchWithAuth(`${API_URL}/api/users/my-uploads/?${params}`);

        if (!response.ok) {
          if (response.status === 401 || response.status === 403) {
            // Authentication issue - user needs to login
            toast.error('Please login to view your media library');
            throw new Error('Authentication required');
          }
          if (response.status === 404) {
            // Endpoint not found - might be server issue
            toast.error('Media API endpoint not found. Using demo data instead.');
            throw new Error('API endpoint not found');
          }
          throw new Error(`Failed to fetch media: ${response.status} ${response.statusText}`);
        }

        data = await response.json();
      }
      
      // Combine local and cloudinary uploads into a single array
      const combinedMedia: MediaItem[] = [
        ...data.cloudinary_uploads.map(item => ({ ...item, storage_type: 'cloudinary' as const })),
        ...data.local_uploads.map(item => ({ ...item, storage_type: 'local' as const }))
      ];

      // Sort by creation date (newest first)
      combinedMedia.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

      setAllMedia(combinedMedia);
      setQuota(data.quota || null);
      setTotalCount({
        local: data.total_local,
        cloudinary: data.total_cloudinary
      });

      return combinedMedia;
    } catch (error: any) {
      console.error('Failed to fetch media:', error);
      
      // Fallback to mock data if real API fails
      if (!useMockData) {
        console.log('Falling back to mock data due to API error...');
        setUseMockData(true);
        const mockData = await mockFetchMedia(storageType, limit, offset);
        
        const combinedMedia: MediaItem[] = [
          ...mockData.cloudinary_uploads.map(item => ({ ...item, storage_type: 'cloudinary' as const })),
          ...mockData.local_uploads.map(item => ({ ...item, storage_type: 'local' as const }))
        ];

        combinedMedia.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

        setAllMedia(combinedMedia);
        setQuota(mockData.quota || null);
        setTotalCount({
          local: mockData.total_local,
          cloudinary: mockData.total_cloudinary
        });

        if (error.message.includes('Authentication required')) {
          toast.info('Please login to view your real media. Showing demo data for now.');
        } else {
          toast.info('Using demo data - API temporarily unavailable');
        }
        return combinedMedia;
      }
      
      // Only show error toast if we're already using mock data
      if (!error.message.includes('Authentication required')) {
        toast.error(error.message || 'Failed to fetch media');
      }
      setAllMedia([]);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [useMockData]);

  // Apply filters when media or filter values change
  useEffect(() => {
    let filtered = [...allMedia];

    // Storage filter
    if (storageFilter !== 'all') {
      filtered = filtered.filter(item => item.storage_type === storageFilter);
    }

    // Format filter
    if (formatFilter !== 'all') {
      switch (formatFilter) {
        case 'images':
          filtered = filtered.filter(item => 
            ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(item.format.toLowerCase())
          );
          break;
        case 'videos':
          filtered = filtered.filter(item => 
            ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(item.format.toLowerCase())
          );
          break;
        case 'audio':
          filtered = filtered.filter(item => 
            ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(item.format.toLowerCase())
          );
          break;
      }
    }

    // Purpose filter
    if (purposeFilter !== 'all') {
      filtered = filtered.filter(item => item.purpose === purposeFilter);
    }

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(item =>
        item.original_filename.toLowerCase().includes(term) ||
        item.purpose.toLowerCase().includes(term)
      );
    }

    setFilteredMedia(filtered);
  }, [allMedia, storageFilter, formatFilter, purposeFilter, searchTerm]);

  const uploadMedia = useCallback(async (file: File, purpose: string = 'other') => {
    try {
      if (useMockData) {
        // Use mock upload when Django backend is not available
        const result = await mockUploadMedia(file, purpose);
        
        // Refresh the media list
        await fetchMedia();
        
        toast.success('Media uploaded successfully (demo mode)');
        return result;
      } else {
        // Use real API
        const formData = new FormData();
        formData.append('image', file);
        formData.append('purpose', purpose);

        const response = await fetchMultipartWithAuth(`${API_URL}/api/users/upload-image/`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to upload media');
        }

        const result = await response.json();
        
        // Refresh the media list
        await fetchMedia();
        
        toast.success('Media uploaded successfully');
        return result;
      }
    } catch (error: any) {
      console.error('Failed to upload media:', error);
      toast.error(error.message || 'Failed to upload media');
      throw error;
    }
  }, [fetchMedia, useMockData]);

  const deleteMedia = useCallback(async (mediaId: number, storageType: 'local' | 'cloudinary') => {
    try {
      if (useMockData) {
        // Use mock delete when Django backend is not available
        await mockDeleteMedia(mediaId);
        
        // Remove from local state immediately
        setAllMedia(prev => prev.filter(item => item.id !== mediaId));
        toast.success('Media deleted successfully (demo mode)');
      } else {
        // Use real API
        const params = new URLSearchParams({
          storage_type: storageType
        });

        const response = await fetchWithAuth(`${API_URL}/api/users/my-uploads/${mediaId}/?${params}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          throw new Error('Failed to delete media');
        }

        // Remove from local state immediately
        setAllMedia(prev => prev.filter(item => item.id !== mediaId));
        toast.success('Media deleted successfully');
      }
    } catch (error: any) {
      console.error('Failed to delete media:', error);
      toast.error(error.message || 'Failed to delete media');
    }
  }, [useMockData]);

  const getUniqueFormats = useCallback(() => {
    const formats = new Set(allMedia.map(item => item.format.toLowerCase()));
    return Array.from(formats).sort();
  }, [allMedia]);

  const getUniquePurposes = useCallback(() => {
    const purposes = new Set(allMedia.map(item => item.purpose));
    return Array.from(purposes).sort();
  }, [allMedia]);

  const getMediaStats = useCallback(() => {
    const stats = {
      total: allMedia.length,
      images: 0,
      videos: 0,
      audio: 0,
      local: 0,
      cloudinary: 0
    };

    allMedia.forEach(item => {
      const format = item.format.toLowerCase();
      
      if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(format)) {
        stats.images++;
      } else if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(format)) {
        stats.videos++;
      } else if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'].includes(format)) {
        stats.audio++;
      }

      if (item.storage_type === 'local') {
        stats.local++;
      } else {
        stats.cloudinary++;
      }
    });

    return stats;
  }, [allMedia]);

  // Load media on mount only if backend is available and data not already loaded
  useEffect(() => {
    // Only fetch if we're not using mock data and data hasn't been loaded yet
    if (!useMockData && allMedia.length === 0) {
      console.log('Fetching real media data from Django backend...');
      fetchMedia();
    }
  }, [useMockData, fetchMedia]); // Include fetchMedia but it's wrapped in useCallback so should be stable

  return {
    // Data
    allMedia: filteredMedia,
    isLoading,
    quota,
    totalCount,
    useMockData,
    
    // Filters
    storageFilter,
    setStorageFilter,
    formatFilter,
    setFormatFilter,
    purposeFilter,
    setPurposeFilter,
    searchTerm,
    setSearchTerm,
    
    // Actions
    uploadMedia,
    deleteMedia,
    refetch: () => fetchMedia(),
    
    // Utilities
    getUniqueFormats,
    getUniquePurposes,
    getMediaStats,
  };
}