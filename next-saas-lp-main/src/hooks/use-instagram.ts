"use client";

import { useState, useEffect, useCallback } from 'react';
import { instagramAPI, InstagramPost, InstagramAccount, CreatePostData } from '@/lib/api/instagram';
import { toast } from 'sonner';

export function useInstagramAuth(brandId?: number) {
  const [account, setAccount] = useState<InstagramAccount | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);

  const fetchStatus = useCallback(async (retryCount = 0) => {
    if (!brandId) {
      setIsLoading(false);
      return;
    }
    
    try {
      setIsLoading(true);
      console.log(`Fetching Instagram status for brand ${brandId}, attempt ${retryCount + 1}`);
      
      const status = await instagramAPI.getOAuthStatus(brandId);
      console.log('Instagram status response:', status);
      setAccount(status);
    } catch (error: any) {
      console.error('Failed to get Instagram status:', error);
      
      // If it's an auth error, don't retry
      if (error.message.includes('Authentication required') || error.message.includes('Not authorized')) {
        toast.error('Please login again to access Instagram features');
        setAccount(null);
        return;
      }
      
      // If it's a brand not found error, don't retry
      if (error.message.includes('Brand not found')) {
        console.error(`Brand ${brandId} not found`);
        setAccount(null);
        return;
      }
      
      // Retry once after OAuth callback for other errors
      if (retryCount === 0) {
        console.log('Retrying Instagram status fetch in 2 seconds...');
        setTimeout(() => {
          fetchStatus(1);
        }, 2000);
        return;
      }
      
      setAccount(null);
    } finally {
      setIsLoading(false);
    }
  }, [brandId]);

  const connect = useCallback(async () => {
    if (!brandId) {
      toast.error('Brand ID is required to connect Instagram');
      return;
    }

    try {
      setIsConnecting(true);
      
      // Store brand info for callback page
      localStorage.setItem('instagram_connecting_brand_id', brandId.toString());
      
      // Get the OAuth URL from our API (just constructs the URL, no API call)
      const { oauth_url } = await instagramAPI.startOAuth(brandId);
      
      // Open OAuth in a new tab instead of same tab
      const popup = window.open(oauth_url, 'instagram_oauth', 'width=600,height=700,scrollbars=yes,resizable=yes');
      
      if (!popup) {
        toast.error('Please allow popups to connect Instagram');
        setIsConnecting(false);
        return;
      }
      
      // Listen for the popup to close or send a message
      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          setIsConnecting(false);
          
          // Wait a moment then check the connection status
          setTimeout(() => {
            fetchStatus();
          }, 1000);
        }
      }, 1000);
      
      // Also listen for postMessage from the callback page
      const handleMessage = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) {
          return;
        }
        
        if (event.data.type === 'INSTAGRAM_OAUTH_SUCCESS') {
          clearInterval(checkClosed);
          popup.close();
          setIsConnecting(false);
          toast.success('Instagram connected successfully!');
          fetchStatus();
          window.removeEventListener('message', handleMessage);
        } else if (event.data.type === 'INSTAGRAM_OAUTH_ERROR') {
          clearInterval(checkClosed);
          popup.close();
          setIsConnecting(false);
          toast.error(event.data.error || 'Instagram connection failed');
          window.removeEventListener('message', handleMessage);
        }
      };
      
      window.addEventListener('message', handleMessage);
      
      // Cleanup after 5 minutes
      setTimeout(() => {
        if (!popup.closed) {
          popup.close();
        }
        clearInterval(checkClosed);
        setIsConnecting(false);
        window.removeEventListener('message', handleMessage);
      }, 5 * 60 * 1000);
      
    } catch (error: any) {
      console.error('Failed to start Instagram OAuth:', error);
      
      if (error.message.includes('Setup Required')) {
        toast.error('Instagram OAuth setup required. Please configure your Facebook App credentials.');
      } else {
        toast.error(error.message || 'Failed to start Instagram authentication');
      }
      
      setIsConnecting(false);
    }
  }, [brandId, fetchStatus]);

  const disconnect = useCallback(async () => {
    if (!brandId) {
      toast.error('Brand ID is required to disconnect Instagram');
      return;
    }

    try {
      await instagramAPI.disconnect(brandId);
      toast.success('Instagram account disconnected');
      setAccount(null);
    } catch (error: any) {
      console.error('Failed to disconnect Instagram:', error);
      toast.error(error.message || 'Failed to disconnect Instagram account');
    }
  }, [brandId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    account,
    isLoading,
    isConnecting,
    connect,
    disconnect,
    refetch: fetchStatus,
  };
}

export function useInstagramPosts(brandId?: number) {
  const [posts, setPosts] = useState<InstagramPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  const fetchPosts = useCallback(async (pageNum = 1) => {
    try {
      setIsLoading(true);
      const data = await instagramAPI.getPosts(brandId, pageNum, pageSize);
      setPosts(data.posts);
      setTotal(data.total);
      setPage(data.page);
    } catch (error) {
      console.error('Failed to fetch Instagram posts:', error);
      toast.error('Failed to fetch Instagram posts');
    } finally {
      setIsLoading(false);
    }
  }, [brandId, pageSize]);

  const createPost = useCallback(async (data: CreatePostData) => {
    try {
      const newPost = await instagramAPI.createPost(data);
      setPosts(prev => [newPost, ...prev]);
      toast.success('Instagram post created successfully');
      return newPost;
    } catch (error: any) {
      console.error('Failed to create Instagram post:', error);
      toast.error(error.message || 'Failed to create Instagram post');
      throw error;
    }
  }, []);

  const updatePost = useCallback(async (postId: number, data: Partial<CreatePostData>) => {
    try {
      const updatedPost = await instagramAPI.updatePost(postId, data);
      setPosts(prev => prev.map(post => post.id === postId ? updatedPost : post));
      toast.success('Instagram post updated successfully');
      return updatedPost;
    } catch (error: any) {
      console.error('Failed to update Instagram post:', error);
      toast.error(error.message || 'Failed to update Instagram post');
      throw error;
    }
  }, []);

  const deletePost = useCallback(async (postId: number) => {
    try {
      await instagramAPI.deletePost(postId);
      setPosts(prev => prev.filter(post => post.id !== postId));
      toast.success('Instagram post deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete Instagram post:', error);
      toast.error(error.message || 'Failed to delete Instagram post');
    }
  }, []);

  const postNow = useCallback(async (postId: number) => {
    try {
      await instagramAPI.postNow(postId);
      // Refresh posts to get updated status
      await fetchPosts(page);
      toast.success('Instagram post published successfully');
    } catch (error: any) {
      console.error('Failed to post to Instagram:', error);
      toast.error(error.message || 'Failed to post to Instagram');
    }
  }, [fetchPosts, page]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  return {
    posts,
    isLoading,
    total,
    page,
    pageSize,
    createPost,
    updatePost,
    deletePost,
    postNow,
    refetch: () => fetchPosts(page),
    fetchPage: fetchPosts,
  };
}

export function useInstagramImageUpload() {
  const [uploads, setUploads] = useState<Array<{
    id: number;
    image_url: string;
    public_id: string;
    created_at: string;
  }>>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUploads = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await instagramAPI.getUserUploads();
      // Ensure data is an array before setting it
      if (Array.isArray(data)) {
        setUploads(data);
      } else {
        console.error('Expected array from getUserUploads, got:', data);
        setUploads([]);
      }
    } catch (error) {
      console.error('Failed to fetch user uploads:', error);
      setUploads([]); // Ensure uploads is always an array on error
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadImage = useCallback(async (file: File) => {
    try {
      const result = await instagramAPI.uploadImage(file);
      await fetchUploads(); // Refresh the list
      toast.success('Image uploaded successfully');
      return result;
    } catch (error: any) {
      console.error('Failed to upload image:', error);
      toast.error(error.message || 'Failed to upload image');
      throw error;
    }
  }, [fetchUploads]);

  const deleteUpload = useCallback(async (imageId: number) => {
    try {
      await instagramAPI.deleteUserUpload(imageId);
      setUploads(prev => prev.filter(upload => upload.id !== imageId));
      toast.success('Image deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete image:', error);
      toast.error(error.message || 'Failed to delete image');
    }
  }, []);

  useEffect(() => {
    fetchUploads();
  }, [fetchUploads]);

  return {
    uploads,
    isLoading,
    uploadImage,
    deleteUpload,
    refetch: fetchUploads,
  };
}