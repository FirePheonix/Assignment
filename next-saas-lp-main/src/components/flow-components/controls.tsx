'use client';

import { Controls as FlowControls } from '@xyflow/react';
import { memo, useCallback, useState, createContext, useContext } from 'react';
import { ThemeSwitcher } from './theme-switcher';
import { Button } from './ui/button';
import { SaveIcon, CheckIcon, Loader2Icon, MousePointer2, Hand } from 'lucide-react';
import { useProject } from '@/providers/project-provider';
import { workspaceApi } from '@/lib/workspace-api';
import { useReactFlow } from '@xyflow/react';
import { toast } from 'sonner';

// Mouse Mode Context
type MouseMode = 'select' | 'pan';

interface MouseModeContextType {
  mouseMode: MouseMode;
  setMouseMode: (mode: MouseMode) => void;
}

const MouseModeContext = createContext<MouseModeContextType | null>(null);

export const MouseModeProvider = ({ children }: { children: React.ReactNode }) => {
  const [mouseMode, setMouseMode] = useState<MouseMode>('select');

  return (
    <MouseModeContext.Provider value={{ mouseMode, setMouseMode }}>
      {children}
    </MouseModeContext.Provider>
  );
};

export const useMouseMode = () => {
  const context = useContext(MouseModeContext);
  if (!context) {
    throw new Error('useMouseMode must be used within MouseModeProvider');
  }
  return context;
};

export const ControlsInner = () => {
  const { project } = useProject();
  const { toObject } = useReactFlow();
  const [isSaving, setIsSaving] = useState(false);
  const [justSaved, setJustSaved] = useState(false);

  const handleSave = useCallback(async () => {
    if (!project?.id || isSaving) {
      return;
    }

    setIsSaving(true);
    try {
      const content = toObject();
      await workspaceApi.save(project.id, content as any);

      setJustSaved(true);
      toast.success('Workspace saved successfully!');
      
      setTimeout(() => {
        setJustSaved(false);
      }, 2000);
    } catch (error) {
      console.error('Error saving workspace', error);
      toast.error('Failed to save workspace');
    } finally {
      setIsSaving(false);
    }
  }, [project, toObject, isSaving]);

  return (
    <FlowControls
      orientation="horizontal"
      className="flex-col! rounded-lg border border-gray-700/50 bg-gray-900/95 p-1 shadow-lg backdrop-blur-sm sm:flex-row! [&_button]:!bg-gray-800/80 [&_button]:!text-white [&_button]:!border-gray-600/50 [&_button]:hover:!bg-gray-700/90 [&_button]:rounded-md [&_button]:m-0.5 [&_svg]:!text-white"
      showInteractive={false}
    >
      {/* Save Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={handleSave}
        disabled={isSaving}
        className="h-8 w-8 rounded-md"
        title="Save workspace"
      >
        {isSaving ? (
          <Loader2Icon className="h-4 w-4 animate-spin" />
        ) : justSaved ? (
          <CheckIcon className="h-4 w-4 text-green-500" />
        ) : (
          <SaveIcon className="h-4 w-4" />
        )}
      </Button>
    </FlowControls>
  );
};

export const Controls = memo(ControlsInner);
