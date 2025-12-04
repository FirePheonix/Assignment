'use server';

import { cookies } from 'next/headers';

export interface Project {
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

// Mock storage - Replace with your Django API calls
const projectsStore = new Map<string, Project>();

// Initialize with demo project
projectsStore.set('demo-project', {
  id: 'demo-project',
  userId: 'demo-user',
  name: 'My AI Workflow',
  content: {
    nodes: [],
    edges: [],
  },
  createdAt: new Date(),
  updatedAt: new Date(),
});

export const updateProjectAction = async (
  projectId: string,
  data: Partial<Project>
): Promise<
  | {
      success: true;
    }
  | {
      error: string;
    }
> => {
  try {
    // TODO: Replace with Django API call
    // const response = await fetch(`${process.env.DJANGO_API_URL}/api/projects/${projectId}/`, {
    //   method: 'PATCH',
    //   headers: {
    //     'Content-Type': 'application/json',
    //     'Authorization': `Bearer ${await getAuthToken()}`,
    //   },
    //   body: JSON.stringify(data),
    // });

    const project = projectsStore.get(projectId);
    if (!project) {
      throw new Error('Project not found');
    }

    const updated = {
      ...project,
      ...data,
      updatedAt: new Date(),
    };

    projectsStore.set(projectId, updated);

    return { success: true };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const createProjectAction = async (
  data: Omit<Project, 'id' | 'createdAt' | 'updatedAt'>
): Promise<
  | {
      success: true;
      project: Project;
    }
  | {
      error: string;
    }
> => {
  try {
    // TODO: Replace with Django API call
    const project: Project = {
      id: Math.random().toString(36).substring(7),
      ...data,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    projectsStore.set(project.id, project);

    return { success: true, project };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const deleteProjectAction = async (
  projectId: string
): Promise<
  | {
      success: true;
    }
  | {
      error: string;
    }
> => {
  try {
    // TODO: Replace with Django API call
    projectsStore.delete(projectId);
    return { success: true };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const getProjectAction = async (
  projectId: string
): Promise<
  | {
      success: true;
      project: Project;
    }
  | {
      error: string;
    }
> => {
  try {
    // TODO: Replace with Django API call
    const project = projectsStore.get(projectId);
    if (!project) {
      throw new Error('Project not found');
    }
    return { success: true, project };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};
