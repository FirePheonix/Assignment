'use client';

import type { ReactNode } from 'react';
import { createContext, useContext, useState, useCallback, useEffect } from 'react';

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

type ProjectContextType = {
  project: Project | null;
  updateProject: (updates: Partial<Project>) => void;
  setProject: (project: Project) => void;
};

export const ProjectContext = createContext<ProjectContextType>({
  project: null,
  updateProject: () => {},
  setProject: () => {},
});

export const useProject = () => {
  const context = useContext(ProjectContext);

  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }

  return context;
};

export const ProjectProvider = ({
  children,
  data,
}: {
  children: ReactNode;
  data: Project;
}) => {
  const [project, setProjectState] = useState<Project>(data);

  // Sync state when data prop changes (workspace switch)
  useEffect(() => {
    setProjectState(data);
  }, [data]);

  const updateProject = useCallback((updates: Partial<Project>) => {
    setProjectState((prev) => ({
      ...prev,
      ...updates,
      updatedAt: new Date(),
    }));
  }, []);

  const setProject = useCallback((newProject: Project) => {
    setProjectState(newProject);
  }, []);

  return (
    <ProjectContext.Provider value={{ project, updateProject, setProject }}>
      {children}
    </ProjectContext.Provider>
  );
};
