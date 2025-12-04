'use server';

import { cookies } from 'next/headers';

export interface Workspace {
  id: string;
  userId: string;
  name: string;
  content: {
    nodes: any[];
    edges: any[];
  };
  createdAt: Date;
  updatedAt: Date;
}

const API_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';

// Helper to get auth headers with cookies
async function getAuthHeaders() {
  const cookieStore = await cookies();
  const sessionid = cookieStore.get('sessionid')?.value;
  const csrftoken = cookieStore.get('csrftoken')?.value;
  
  return {
    'Content-Type': 'application/json',
    ...(sessionid && { Cookie: `sessionid=${sessionid}` }),
    ...(csrftoken && { 'X-CSRFToken': csrftoken }),
  };
}

export const saveWorkspaceAction = async (
  workspaceId: string,
  content: { nodes: any[]; edges: any[] }
): Promise<
  | {
      success: true;
      workspace: Workspace;
    }
  | {
      error: string;
    }
> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/workspaces/${workspaceId}/`, {
      method: 'PATCH',
      headers,
      credentials: 'include',
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save workspace');
    }

    const data = await response.json();
    
    return { 
      success: true, 
      workspace: {
        ...data.workspace,
        createdAt: new Date(data.workspace.createdAt),
        updatedAt: new Date(data.workspace.updatedAt),
      }
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const createWorkspaceAction = async (
  name: string,
  userId?: string
): Promise<
  | {
      success: true;
      workspace: Workspace;
    }
  | {
      error: string;
    }
> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/workspaces/`, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify({ name, content: { nodes: [], edges: [] } }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create workspace');
    }

    const data = await response.json();
    
    return { 
      success: true, 
      workspace: {
        ...data.workspace,
        createdAt: new Date(data.workspace.createdAt),
        updatedAt: new Date(data.workspace.updatedAt),
      }
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const deleteWorkspaceAction = async (
  workspaceId: string
): Promise<
  | {
      success: true;
    }
  | {
      error: string;
    }
> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/workspaces/${workspaceId}/`, {
      method: 'DELETE',
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete workspace');
    }

    return { success: true };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const getWorkspaceAction = async (
  workspaceId: string
): Promise<
  | {
      success: true;
      workspace: Workspace;
    }
  | {
      error: string;
    }
> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/workspaces/${workspaceId}/`, {
      method: 'GET',
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get workspace');
    }

    const data = await response.json();
    
    return { 
      success: true, 
      workspace: {
        ...data.workspace,
        createdAt: new Date(data.workspace.createdAt),
        updatedAt: new Date(data.workspace.updatedAt),
      }
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const listWorkspacesAction = async (
  userId?: string
): Promise<
  | {
      success: true;
      workspaces: Workspace[];
    }
  | {
      error: string;
    }
> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/workspaces/`, {
      method: 'GET',
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list workspaces');
    }

    const data = await response.json();
    const workspaces = data.workspaces.map((ws: any) => ({
      ...ws,
      createdAt: new Date(ws.createdAt),
      updatedAt: new Date(ws.updatedAt),
    }));
    
    return { success: true, workspaces };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const renameWorkspaceAction = async (
  workspaceId: string,
  name: string
): Promise<
  | {
      success: true;
      workspace: Workspace;
    }
  | {
      error: string;
    }
> => {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/workspaces/${workspaceId}/`, {
      method: 'PATCH',
      headers,
      credentials: 'include',
      body: JSON.stringify({ name }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to rename workspace');
    }

    const data = await response.json();
    
    return { 
      success: true, 
      workspace: {
        ...data.workspace,
        createdAt: new Date(data.workspace.createdAt),
        updatedAt: new Date(data.workspace.updatedAt),
      }
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};
