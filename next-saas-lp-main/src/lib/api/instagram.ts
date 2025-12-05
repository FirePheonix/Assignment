/**
 * Client-side API service for Instagram operations
 * Uses same auth pattern as workspace-api and user-api
 */

export interface InstagramPost {
  id: number;
  content: string; // Backend uses 'content' for caption
  caption?: string; // Keep for backward compatibility
  image: string;
  video?: string;
  scheduled_for?: string; // Backend uses 'scheduled_for'
  scheduled_time?: string; // Keep for backward compatibility
  status: 'draft' | 'approved' | 'posted' | 'failed';
  instagram_id?: string;
  instagram_url?: string;
  created_at: string;
  posted_at?: string;
  brand: {
    id: number;
    name: string;
  };
}

export interface InstagramStats {
  total_posts: number;
  posted: number;
  scheduled: number;
  followers: number;
}

export interface InstagramAccount {
  instagram_username: string;
  instagram_user_id: string;
  connected: boolean;
  connected_at?: string;
}

export interface CreatePostData {
  caption: string;
  image?: File;
  imageUrl?: string;
  scheduled_time?: string;
  brand_id: number;
}

const API_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';

// Helper to get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  const token = localStorage.getItem('auth_token');
  console.log('Auth token available:', !!token);
  return token;
}

// Helper to get CSRF token from cookies
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(name + '=')) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  
  return null;
}

// Helper to make authenticated requests
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const csrfToken = getCsrfToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Token ${token}` }),
    ...(csrfToken && { 'X-CSRFToken': csrfToken }),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
}

// Helper to make authenticated multipart requests
async function fetchMultipartWithAuth(url: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const csrfToken = getCsrfToken();
  
  const headers: HeadersInit = {
    ...(token && { 'Authorization': `Token ${token}` }),
    ...(csrfToken && { 'X-CSRFToken': csrfToken }),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
}

class InstagramAPI {
  async getOAuthStatus(brandId?: number): Promise<InstagramAccount> {
    if (!brandId) {
      throw new Error('Brand ID is required');
    }
    
    const params = `?brand_id=${brandId}`;
    console.log(`Making request to: ${API_URL}/api/instagram/oauth-status/${params}`);
    
    const response = await fetchWithAuth(`${API_URL}/api/instagram/oauth-status/${params}`);

    console.log(`Instagram OAuth status response: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      let errorMessage = 'Failed to get Instagram OAuth status';
      
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorMessage;
        console.error('Instagram OAuth status error:', errorData);
      } catch (parseError) {
        console.error('Failed to parse error response:', parseError);
      }
      
      if (response.status === 401) {
        throw new Error('Authentication required. Please login again.');
      } else if (response.status === 403) {
        throw new Error('Not authorized to access this brand.');
      } else if (response.status === 404) {
        throw new Error('Brand not found.');
      }
      
      throw new Error(errorMessage);
    }

    const data = await response.json();
    console.log('Instagram OAuth status data:', data);
    return data;
  }

  async startOAuth(brandId: number): Promise<{ oauth_url: string }> {
    // Construct the OAuth URL directly without making any API calls
    // This avoids CORS issues when opening in a popup
    const params = new URLSearchParams({
      brand_id: brandId.toString(),
    });
    
    const oauth_url = `${API_URL}/api/instagram/oauth-start/?${params}`;
    return { oauth_url };
  }

  async disconnect(brandId: number): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/instagram/oauth-disconnect/`, {
      method: 'POST',
      body: JSON.stringify({ brand_id: brandId }),
    });

    if (!response.ok) {
      throw new Error('Failed to disconnect Instagram');
    }
  }

  async getPosts(brandId?: number, page = 1, pageSize = 20): Promise<{
    posts: InstagramPost[];
    total: number;
    page: number;
    page_size: number;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    if (brandId) {
      params.append('brand_id', brandId.toString());
    }

    const response = await fetchWithAuth(`${API_URL}/api/instagram/brand-posts/?${params}`);

    if (!response.ok) {
      throw new Error('Failed to get Instagram posts');
    }

    return response.json();
  }

  async createPost(data: CreatePostData): Promise<InstagramPost> {
    const formData = new FormData();
    formData.append('content', data.caption); // Backend expects 'content' not 'caption'
    formData.append('brand_id', data.brand_id.toString());

    if (data.image) {
      formData.append('image', data.image);
    } else if (data.imageUrl) {
      // Download the image and upload it as a file
      formData.append('image_url', data.imageUrl);
    }

    if (data.scheduled_time) {
      formData.append('scheduled_for', data.scheduled_time); // Backend expects 'scheduled_for'
      formData.append('status', 'approved'); // Set status to approved when scheduled
    }

    const response = await fetchMultipartWithAuth(`${API_URL}/api/instagram/brand-posts/`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to create Instagram post');
    }

    return response.json();
  }

  async updatePost(postId: number, data: Partial<CreatePostData>): Promise<InstagramPost> {
    const formData = new FormData();

    if (data.caption) formData.append('content', data.caption); // Backend expects 'content'
    if (data.image) formData.append('image', data.image);
    if (data.imageUrl) formData.append('image_url', data.imageUrl);
    if (data.scheduled_time) {
      formData.append('scheduled_for', data.scheduled_time); // Backend expects 'scheduled_for'
      formData.append('status', 'approved'); // Set status to approved when scheduled
    }

    const response = await fetchMultipartWithAuth(`${API_URL}/api/instagram/brand-posts/${postId}/`, {
      method: 'PUT',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to update Instagram post');
    }

    return response.json();
  }

  async deletePost(postId: number): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/instagram/brand-posts/${postId}/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete Instagram post');
    }
  }

  async postNow(postId: number): Promise<{ success: boolean; message: string }> {
    const response = await fetchWithAuth(`${API_URL}/api/instagram/brand-posts/${postId}/post-now/`, {
      method: 'POST',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to post Instagram content');
    }

    return response.json();
  }

  async generateContent(prompt: string, brandId: number): Promise<{ content: string }> {
    const response = await fetchWithAuth(`${API_URL}/api/instagram/generate-content/`, {
      method: 'POST',
      body: JSON.stringify({
        prompt,
        brand_id: brandId,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to generate Instagram content');
    }

    return response.json();
  }

  async uploadImage(file: File): Promise<{ url: string; public_id: string }> {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetchMultipartWithAuth(`${API_URL}/api/users/upload-instagram-image/`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload image');
    }

    return response.json();
  }

  async getUserUploads(): Promise<Array<{
    id: number;
    image_url: string;
    public_id: string;
    created_at: string;
  }>> {
    // Call through Next.js API route which proxies to Django with fallback
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    }
    
    const response = await fetch('/api/users/my-uploads?format=instagram', {
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to get user uploads');
    }

    return response.json();
  }

  async deleteUserUpload(imageId: number): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/users/my-uploads/${imageId}/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete image');
    }
  }
}

export const instagramAPI = new InstagramAPI();