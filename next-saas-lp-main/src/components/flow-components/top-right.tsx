'use client';

import Link from 'next/link';
import { Suspense } from 'react';
import { CreditCounter } from './credits-counter';
import { Menu } from './menu';
import { Button } from './ui/button';
import { PublishDialog } from './publish-dialog';
import { useProject } from '@/providers/project-provider';
import { useUser } from '@/hooks/use-user';
import type { Workspace } from '@/lib/workspace-api';

type TopRightProps = {
  onWorkspaceUpdate?: (workspace: Workspace) => void;
};

export const TopRight = ({ onWorkspaceUpdate }: TopRightProps) => {
  const { project, setProject } = useProject();
  const user = useUser();

  if (!user || !project) {
    return null;
  }

  const handlePublish = (updatedWorkspace: Workspace) => {
    // Update the project provider with the new workspace state
    setProject(updatedWorkspace);
    
    // Callback for parent component
    if (onWorkspaceUpdate) {
      onWorkspaceUpdate(updatedWorkspace);
    }
  };

  return (
    <div className="absolute top-16 right-0 left-0 z-[50] m-4 flex items-center gap-2 sm:top-0 sm:left-auto">
      {user.id && (
        <>
          <div className="flex items-center rounded-full border bg-card/90 px-2 py-1 drop-shadow-xs backdrop-blur-sm">
            <PublishDialog workspace={project as Workspace} onPublish={handlePublish} />
          </div>
          <div className="flex items-center rounded-full border bg-card/90 p-3 drop-shadow-xs backdrop-blur-sm">
            <Suspense
              fallback={
                <p className="text-muted-foreground text-sm">Loading...</p>
              }
            >
              <CreditCounter />
            </Suspense>
          </div>
        </>
      )}
      {!user.id && (
        <div className="flex items-center rounded-full border bg-card/90 p-0.5 drop-shadow-xs backdrop-blur-sm">
          <Button className="rounded-full" size="lg" asChild>
            <Link href="/pricing">Claim your free AI credits</Link>
          </Button>
        </div>
      )}
      <div className="flex items-center rounded-full border bg-card/90 p-1 drop-shadow-xs backdrop-blur-sm">
        <Menu />
      </div>
    </div>
  );
};
