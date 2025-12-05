/**
 * Client-side API service for organization operations
 * Uses same auth pattern as workspace-api and user-api
 */

export interface Organization {
  id: number;
  name: string;
  is_admin: boolean;
  created_at: string;
  member_count?: number;
  owner?: {
    id: number;
    email: string;
  };
}

export interface OrganizationMember {
  id: number;
  user: {
    id: number;
    email: string;
    username: string;
  };
  role: 'admin' | 'member';
  joined_at: string;
}

export interface CreateOrganizationData {
  name: string;
}

export interface InviteUserData {
  email: string;
  role: 'admin' | 'member';
  message?: string;
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
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Token ${token}` }),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
}

class OrganizationsAPI {
  async getOrganizations(): Promise<Organization[]> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/`);

    if (!response.ok) {
      throw new Error('Failed to fetch organizations');
    }

    return response.json();
  }

  async getOrganization(id: number): Promise<Organization> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/${id}/`);

    if (!response.ok) {
      throw new Error('Failed to fetch organization');
    }

    return response.json();
  }

  async createOrganization(data: CreateOrganizationData): Promise<Organization> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/create/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to create organization');
    }

    return response.json();
  }

  async updateOrganization(organizationId: number, data: CreateOrganizationData): Promise<Organization> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/${organizationId}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to update organization');
    }

    return response.json();
  }

  async deleteOrganization(organizationId: number): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/${organizationId}/delete/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to delete organization');
    }
  }

  async getOrganizationMembers(orgId: number): Promise<OrganizationMember[]> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/${orgId}/members/`);

    if (!response.ok) {
      throw new Error('Failed to fetch organization members');
    }

    return response.json();
  }

  async getOrganizationBrands(orgId: number): Promise<any[]> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/${orgId}/brands/`);

    if (!response.ok) {
      throw new Error('Failed to fetch organization brands');
    }

    return response.json();
  }

  async inviteUser(orgId: number, data: InviteUserData): Promise<{ success: boolean; message: string }> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/${orgId}/invite/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to send invitation');
    }

    return response.json();
  }

  async removeMember(orgId: number, memberId: number): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/${orgId}/members/${memberId}/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to remove member');
    }
  }

  async updateMemberRole(orgId: number, memberId: number, role: 'admin' | 'member'): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/organizations/${orgId}/members/${memberId}/`, {
      method: 'PATCH',
      body: JSON.stringify({ role }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to update member role');
    }
  }
}

export const organizationsAPI = new OrganizationsAPI();