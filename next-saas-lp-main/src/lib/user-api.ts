/**
 * Client-side API service for user profile operations
 */

export interface UserProfile {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  age?: number;
  instagram_handle?: string;
  bio?: string;
  profile_picture?: string | null;
  banner_image?: string | null;
  additional_image1?: string | null;
  additional_image2?: string | null;
  story_price?: string | null;
  post_price?: string | null;
  reel_price?: string | null;
  impressions_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface UserProfileUpdate {
  first_name?: string;
  last_name?: string;
  age?: number;
  instagram_handle?: string;
  bio?: string;
  profile_picture_url?: string;
  banner_image_url?: string;
  additional_image1_url?: string;
  additional_image2_url?: string;
  story_price?: string;
  post_price?: string;
  reel_price?: string;
}

const API_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';

// Helper to get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}



// Helper to make authenticated requests
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getAuthToken();
  
  console.log('[fetchWithAuth] Token:', token ? 'present' : 'missing');
  console.log('[fetchWithAuth] URL:', url);
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Token ${token}` }),
    ...options.headers,
  };

  console.log('[fetchWithAuth] Headers:', headers);

  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
}

export const userApi = {
  async getCurrentProfile(): Promise<UserProfile> {
    const response = await fetchWithAuth(`${API_URL}/api/users/profile/`);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to get profile' }));
      throw new Error(error.detail || 'Failed to get profile');
    }

    return await response.json();
  },

  async getProfile(userId: number): Promise<UserProfile> {
    const response = await fetch(`${API_URL}/api/users/${userId}/profile/`);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'User not found' }));
      throw new Error(error.detail || 'User not found');
    }

    return await response.json();
  },

  async updateProfile(data: UserProfileUpdate): Promise<UserProfile> {
    const response = await fetchWithAuth(`${API_URL}/api/users/profile/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to update profile' }));
      throw new Error(error.detail || 'Failed to update profile');
    }

    return await response.json();
  },

  async uploadProfilePicture(file: File): Promise<{ url: string }> {
    const token = getAuthToken();
    
    const formData = new FormData();
    formData.append('image', file);
    formData.append('purpose', 'other');

    const response = await fetch(`${API_URL}/api/users/upload-image/`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Token ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to upload image' }));
      throw new Error(error.error || 'Failed to upload image');
    }

    const data = await response.json();
    return { url: data.url };
  },
};
