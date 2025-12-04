'use client';

import { workspaceApi } from '@/lib/workspace-api';
import type { Workspace } from '@/lib/workspace-api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/flow-components/ui/dialog';
import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
  ComboboxSeparator,
  ComboboxTrigger,
} from '@/components/flow-components/ui/kibo-ui/combobox';
import { useUser } from '@/hooks/use-user';
import { handleError } from '@/lib/error/handle';
import { cn } from '@/lib/utils';
import Fuse from 'fuse.js';
import { CheckIcon, PlusIcon, PencilIcon, TrashIcon } from 'lucide-react';
import { useRouter } from 'next/navigation';
import {
  type FormEventHandler,
  Fragment,
  useCallback,
  useMemo,
  useState,
} from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';

type WorkspaceSelectorProps = {
  workspaces: Workspace[];
  currentWorkspace: string;
  onWorkspaceChange?: (workspaceId: string) => void;
};

export const WorkspaceSelector = ({
  workspaces,
  currentWorkspace,
  onWorkspaceChange,
}: WorkspaceSelectorProps) => {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(currentWorkspace);
  const [name, setName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [renameOpen, setRenameOpen] = useState(false);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const router = useRouter();
  const user = useUser();

  const fuse = useMemo(
    () =>
      new Fuse(workspaces, {
        keys: ['name'],
        minMatchCharLength: 1,
        threshold: 0.3,
      }),
    [workspaces]
  );

  const handleCreateWorkspace = useCallback<FormEventHandler<HTMLFormElement>>(
    async (event) => {
      event.preventDefault();

      if (isCreating) {
        return;
      }

      setIsCreating(true);

      try {
        const newWorkspace = await workspaceApi.create(name.trim());

        setOpen(false);
        setCreateOpen(false);
        setName('');
        toast.success('Workspace created successfully!');
        
        if (onWorkspaceChange) {
          onWorkspaceChange(newWorkspace.id);
        }
      } catch (error) {
        handleError('Error creating workspace', error);
        toast.error('Failed to create workspace');
      } finally {
        setIsCreating(false);
      }
    },
    [isCreating, name, user, onWorkspaceChange]
  );

  const handleRenameWorkspace = useCallback<FormEventHandler<HTMLFormElement>>(
    async (event) => {
      event.preventDefault();

      if (!renamingId || isCreating) {
        return;
      }

      setIsCreating(true);

      try {
        await workspaceApi.rename(renamingId, name.trim());

        setRenameOpen(false);
        setRenamingId(null);
        setName('');
        toast.success('Workspace renamed successfully!');
        
        // Refresh the page to update the workspace list
        router.refresh();
      } catch (error) {
        handleError('Error renaming workspace', error);
        toast.error('Failed to rename workspace');
      } finally {
        setIsCreating(false);
      }
    },
    [renamingId, name, isCreating, router]
  );

  const handleDeleteWorkspace = useCallback(
    async (workspaceId: string) => {
      if (!confirm('Are you sure you want to delete this workspace?')) {
        return;
      }

      try {
        await workspaceApi.delete(workspaceId);

        toast.success('Workspace deleted successfully!');
        
        // If we deleted the current workspace, switch to the first available one
        if (workspaceId === currentWorkspace && workspaces.length > 1) {
          const nextWorkspace = workspaces.find((w) => w.id !== workspaceId);
          if (nextWorkspace && onWorkspaceChange) {
            onWorkspaceChange(nextWorkspace.id);
          }
        }
        
        router.refresh();
      } catch (error: any) {
        // If workspace already deleted (404), just refresh UI
        if (error.message?.includes('not found') || error.message?.includes('404')) {
          toast.info('Workspace already deleted');
          router.refresh();
        } else {
          handleError('Error deleting workspace', error);
          toast.error('Failed to delete workspace');
        }
      }
    },
    [currentWorkspace, workspaces, onWorkspaceChange, router]
  );

  const handleSelect = useCallback(
    (workspaceId: string) => {
      if (workspaceId === 'new') {
        setCreateOpen(true);
        return;
      }

      if (workspaceId.startsWith('rename-')) {
        const id = workspaceId.replace('rename-', '');
        const workspace = workspaces.find((w) => w.id === id);
        if (workspace) {
          setRenamingId(id);
          setName(workspace.name);
          setRenameOpen(true);
        }
        return;
      }

      if (workspaceId.startsWith('delete-')) {
        const id = workspaceId.replace('delete-', '');
        handleDeleteWorkspace(id);
        return;
      }

      setValue(workspaceId);
      setOpen(false);
      
      if (onWorkspaceChange) {
        onWorkspaceChange(workspaceId);
      }
    },
    [workspaces, onWorkspaceChange, handleDeleteWorkspace]
  );

  const workspaceGroups = useMemo(() => {
    if (!user) {
      return [];
    }

    return [
      {
        label: 'My Workspaces',
        data: workspaces.filter((workspace) => workspace.userId === user.id),
      },
      {
        label: 'Other Workspaces',
        data: workspaces.filter((workspace) => workspace.userId !== user.id),
      },
    ];
  }, [workspaces, user]);

  const filterByFuse = useCallback(
    (currentValue: string, search: string) => {
      return fuse
        .search(search)
        .find((result) => result.item.id === currentValue)
        ? 1
        : 0;
    },
    [fuse]
  );

  const currentWorkspaceName = workspaces.find((w) => w.id === value)?.name || 'Select workspace';

  return (
    <>
      <Combobox
        open={open}
        onOpenChange={setOpen}
        data={workspaces.map((workspace) => ({
          label: workspace.name,
          value: workspace.id,
        }))}
        type="workspace"
        value={value}
        onValueChange={handleSelect}
      >
        <ComboboxTrigger className="w-[280px] rounded-full border-none bg-transparent shadow-none">
          {currentWorkspaceName}
        </ComboboxTrigger>
        <ComboboxContent
          filter={filterByFuse}
          className="p-0 w-[320px]"
          popoverOptions={{
            sideOffset: 8,
          }}
        >
          <ComboboxInput placeholder="Search workspaces..." />
          <ComboboxList>
            <ComboboxEmpty />
            {workspaceGroups
              .filter((group) => group.data.length > 0)
              .map((group) => (
                <Fragment key={group.label}>
                  <ComboboxGroup heading={group.label}>
                    {group.data.map((workspace) => (
                      <ComboboxItem 
                        key={workspace.id} 
                        value={workspace.id}
                        className="group flex items-center justify-between pr-2"
                      >
                        <span className="flex items-center flex-1 min-w-0">
                          {workspace.name}
                          <CheckIcon
                            className={cn(
                              'ml-2 flex-shrink-0',
                              value === workspace.id ? 'opacity-100' : 'opacity-0'
                            )}
                          />
                        </span>
                        <div className="flex items-center gap-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setRenamingId(workspace.id);
                              setName(workspace.name);
                              setRenameOpen(true);
                              setOpen(false);
                            }}
                            className="p-1 hover:bg-accent rounded"
                            title="Rename workspace"
                          >
                            <PencilIcon size={14} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteWorkspace(workspace.id);
                              setOpen(false);
                            }}
                            className="p-1 hover:bg-destructive/10 hover:text-destructive rounded"
                            title="Delete workspace"
                          >
                            <TrashIcon size={14} />
                          </button>
                        </div>
                      </ComboboxItem>
                    ))}
                  </ComboboxGroup>
                  <ComboboxSeparator />
                </Fragment>
              ))}
            <ComboboxGroup>
              <ComboboxItem value="new">
                <PlusIcon size={16} />
                Create new workspace
              </ComboboxItem>
            </ComboboxGroup>
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
      
      <Dialog open={createOpen} onOpenChange={setCreateOpen} modal={false}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create new workspace</DialogTitle>
            <DialogDescription>
              What would you like to call your new workspace?
            </DialogDescription>
            <form
              onSubmit={handleCreateWorkspace}
              className="mt-2 flex items-center gap-2"
              aria-disabled={isCreating}
            >
              <Input
                placeholder="My new workspace"
                value={name}
                onChange={({ target }) => setName(target.value)}
                autoFocus
              />
              <Button type="submit" disabled={isCreating || !name.trim()}>
                Create
              </Button>
            </form>
          </DialogHeader>
        </DialogContent>
      </Dialog>

      <Dialog open={renameOpen} onOpenChange={setRenameOpen} modal={false}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename workspace</DialogTitle>
            <DialogDescription>
              Enter a new name for this workspace
            </DialogDescription>
            <form
              onSubmit={handleRenameWorkspace}
              className="mt-2 flex items-center gap-2"
              aria-disabled={isCreating}
            >
              <Input
                placeholder="Workspace name"
                value={name}
                onChange={({ target }) => setName(target.value)}
                autoFocus
              />
              <Button type="submit" disabled={isCreating || !name.trim()}>
                Rename
              </Button>
            </form>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </>
  );
};
