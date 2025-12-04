'use client';

import { ProjectSelector } from './project-selector';
import { ProjectSettings } from './project-settings';
import { useProject } from '@/providers/project-provider';

type TopLeftProps = {
  projects?: any[];
};

export const TopLeft = ({ projects: allProjects = [] }: TopLeftProps) => {
  const { project: currentProject } = useProject();

  if (!currentProject || !allProjects.length) {
    return null;
  }

  return (
    <div className="absolute top-16 right-0 left-0 z-[50] m-4 flex items-center gap-2 sm:top-0 sm:right-auto">
      <div className="flex flex-1 items-center rounded-full border bg-card/90 p-1 drop-shadow-xs backdrop-blur-sm">
        <ProjectSelector
          projects={allProjects}
          currentProject={currentProject.id}
        />
      </div>
      <div className="flex shrink-0 items-center rounded-full border bg-card/90 p-1 drop-shadow-xs backdrop-blur-sm">
        <ProjectSettings data={currentProject} />
      </div>
    </div>
  );
};
