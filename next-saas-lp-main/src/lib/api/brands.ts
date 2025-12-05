/**
 * Client-side API service for brand operations
 * Uses same auth pattern as workspace-api and user-api
 */

export interface Brand {
  id: number;
  name: string;
  slug: string;
  description?: string;
  logo?: string;
  url?: string;
  is_default: boolean;
  instagram_username?: string;
  has_instagram_config: boolean;
  instagram_connected: boolean; // Added for compatibility with Instagram queue page
  twitter_username?: string;
  has_twitter_config: boolean;
  organization_id?: number | null;
  organization_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateBrandData {
  name: string;
  description?: string;
  url: string;
  organization_id?: number | null;
}

const API_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';

// Helper to get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
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
    credentials: 'include', // Important: include cookies
  });

  return response;
}

class BrandsAPI {

  async getBrands(): Promise<Brand[]> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/`);

    if (!response.ok) {
      throw new Error('Failed to fetch brands');
    }

    return response.json();
  }

  async createBrand(data: CreateBrandData): Promise<Brand> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/create/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to create brand');
    }

    return response.json();
  }

  async updateBrand(brandId: number, data: Partial<CreateBrandData>): Promise<Brand> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/${brandId}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to update brand');
    }

    return response.json();
  }

  async setDefaultBrand(brandId: number): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/${brandId}/set-default/`, {
      method: 'POST',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to set default brand');
    }
  }

  async deleteBrand(brandId: number): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/${brandId}/delete/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to delete brand');
    }
  }
}

export const brandsAPI = new BrandsAPI();