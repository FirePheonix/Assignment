/**
 * Client-side API service for workspace operations
 * Makes direct fetch calls to Django API with proper cookie handling
 */

export interface WorkspaceMedia {
  id: string;
  mediaType: 'image' | 'video';
  fileUrl: string;
  thumbnailUrl?: string;
  title: string;
  order: number;
  createdAt: Date;
}

export interface Workspace {
  id: string;
  slug: string;
  userId: string;
  userName?: string;
  userProfilePicture?: string | null;
  name: string;
  description?: string;
  content: {
    nodes: any[];
    edges: any[];
  };
  url: string;
  isPublic: boolean;
  publishedAt?: Date;
  viewCount: number;
  cloneCount: number;
  media: WorkspaceMedia[];
  createdAt: Date;
  updatedAt: Date;
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

export const workspaceApi = {
  async list(): Promise<Workspace[]> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/`);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to list workspaces' }));
      throw new Error(error.detail || 'Failed to list workspaces');
    }

    const data = await response.json();
    return data.workspaces.map((ws: any) => ({
      ...ws,
      createdAt: new Date(ws.createdAt),
      updatedAt: new Date(ws.updatedAt),
    }));
  },

  async get(id: string): Promise<Workspace> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/${id}/`);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to get workspace' }));
      throw new Error(error.detail || 'Failed to get workspace');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
    };
  },

  async create(name: string): Promise<Workspace> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/`, {
      method: 'POST',
      body: JSON.stringify({ 
        name, 
        content: { nodes: [], edges: [] } 
      }),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to create workspace' }));
      throw new Error(error.detail || 'Failed to create workspace');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
    };
  },

  async save(id: string, content: { nodes: any[]; edges: any[] }): Promise<Workspace> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ content }),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to save workspace' }));
      throw new Error(error.detail || 'Failed to save workspace');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
    };
  },

  async rename(id: string, name: string): Promise<Workspace> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ name }),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to rename workspace' }));
      throw new Error(error.detail || 'Failed to rename workspace');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
    };
  },

  async delete(id: string): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/${id}/`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to delete workspace' }));
      throw new Error(error.detail || 'Failed to delete workspace');
    }
  },

  async duplicate(id: string, newName?: string): Promise<Workspace> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/${id}/duplicate/`, {
      method: 'POST',
      body: JSON.stringify({ name: newName }),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to duplicate workspace' }));
      throw new Error(error.detail || 'Failed to duplicate workspace');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
    };
  },

  async getBySlug(slug: string): Promise<Workspace> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/slug/${slug}/`);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Workspace not found' }));
      throw new Error(error.detail || error.error || 'Workspace not found');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
      publishedAt: data.workspace.publishedAt ? new Date(data.workspace.publishedAt) : undefined,
      media: (data.workspace.media || []).map((m: any) => ({
        ...m,
        createdAt: new Date(m.createdAt),
      })),
    };
  },

  async publish(id: string, description?: string): Promise<Workspace> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/${id}/publish/`, {
      method: 'POST',
      body: JSON.stringify({ description }),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to publish workspace' }));
      throw new Error(error.detail || 'Failed to publish workspace');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
      publishedAt: data.workspace.publishedAt ? new Date(data.workspace.publishedAt) : undefined,
      media: (data.workspace.media || []).map((m: any) => ({
        ...m,
        createdAt: new Date(m.createdAt),
      })),
    };
  },

  async unpublish(id: string): Promise<Workspace> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/${id}/unpublish/`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to unpublish workspace' }));
      throw new Error(error.detail || 'Failed to unpublish workspace');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
      publishedAt: data.workspace.publishedAt ? new Date(data.workspace.publishedAt) : undefined,
      media: (data.workspace.media || []).map((m: any) => ({
        ...m,
        createdAt: new Date(m.createdAt),
      })),
    };
  },

  async uploadMedia(id: string, file: File, mediaType: 'image' | 'video', title?: string, thumbnail?: File): Promise<WorkspaceMedia> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mediaType', mediaType);
    if (title) formData.append('title', title);
    if (thumbnail) formData.append('thumbnail', thumbnail);

    const token = getAuthToken();

    const response = await fetch(`${API_URL}/api/workspaces/${id}/upload_media/`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Token ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to upload media' }));
      throw new Error(error.detail || 'Failed to upload media');
    }

    const data = await response.json();
    return {
      ...data.media,
      createdAt: new Date(data.media.createdAt),
    };
  },

  async deleteMedia(workspaceId: string, mediaId: string): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/${workspaceId}/media/${mediaId}/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to delete media' }));
      throw new Error(error.detail || 'Failed to delete media');
    }
  },

  async importWorkspace(id: string, newName?: string): Promise<Workspace> {
    const response = await fetchWithAuth(`${API_URL}/api/workspaces/${id}/import_workspace/`, {
      method: 'POST',
      body: JSON.stringify({ name: newName }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to import workspace' }));
      throw new Error(error.detail || 'Failed to import workspace');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
      publishedAt: data.workspace.publishedAt ? new Date(data.workspace.publishedAt) : undefined,
      media: (data.workspace.media || []).map((m: any) => ({
        ...m,
        createdAt: new Date(m.createdAt),
      })),
    };
  },
};

// Public workspace API (no auth required)
export const publicWorkspaceApi = {
  async list(sort: 'recent' | 'popular' | 'most_cloned' = 'recent', search?: string): Promise<Workspace[]> {
    const params = new URLSearchParams({ sort });
    if (search) params.append('search', search);

    const response = await fetch(`${API_URL}/api/public-workspaces/?${params}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to load feed' }));
      throw new Error(error.detail || 'Failed to load feed');
    }

    const data = await response.json();
    return data.workspaces.map((ws: any) => ({
      ...ws,
      createdAt: new Date(ws.createdAt),
      updatedAt: new Date(ws.updatedAt),
      publishedAt: ws.publishedAt ? new Date(ws.publishedAt) : undefined,
      media: (ws.media || []).map((m: any) => ({
        ...m,
        createdAt: new Date(m.createdAt),
      })),
    }));
  },

  async getBySlug(slug: string): Promise<Workspace> {
    const response = await fetch(`${API_URL}/api/public-workspaces/${slug}/`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Workspace not found' }));
      throw new Error(error.detail || 'Workspace not found');
    }

    const data = await response.json();
    return {
      ...data.workspace,
      createdAt: new Date(data.workspace.createdAt),
      updatedAt: new Date(data.workspace.updatedAt),
      publishedAt: data.workspace.publishedAt ? new Date(data.workspace.publishedAt) : undefined,
      media: (data.workspace.media || []).map((m: any) => ({
        ...m,
        createdAt: new Date(m.createdAt),
      })),
    };
  },
};
