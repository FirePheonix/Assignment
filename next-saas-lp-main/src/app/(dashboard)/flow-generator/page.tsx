"use client";

import { Canvas } from "@/components/flow-components/canvas";
import { ProjectProvider } from "@/providers/project-provider";
import { GatewayProviderClient } from "@/providers/gateway-provider";
import { ReactFlowProvider } from "@xyflow/react";
import { Controls, MouseModeProvider } from "@/components/flow-components/controls";
import { Toolbar } from "@/components/flow-components/toolbar";
import { TopLeft } from "@/components/flow-components/top-left";
import { TopRight } from "@/components/flow-components/top-right";
import { WorkspaceSelector } from "@/components/flow-components/workspace-selector";
import "@xyflow/react/dist/style.css";
import { useState, useEffect } from "react";
import { workspaceApi } from "@/lib/workspace-api";
import type { Workspace } from "@/lib/workspace-api";

// Mock text models for Gateway
const mockTextModels = {
  "gpt-4o": {
    id: "gpt-4o",
    label: "GPT-4o",
    provider: "openai",
    priceIndicator: "high" as const,
  },
  "gpt-4o-mini": {
    id: "gpt-4o-mini",
    label: "GPT-4o Mini",
    provider: "openai",
    priceIndicator: "lowest" as const,
  },
  "claude-3-5-sonnet": {
    id: "claude-3-5-sonnet",
    label: "Claude 3.5 Sonnet",
    provider: "anthropic",
    priceIndicator: "high" as const,
  },
};

interface PageProps {
  params?: Promise<Record<string, string>>;
  searchParams?: Promise<Record<string, string | string[]>>;
}

export default function FlowGeneratorPage(_props: PageProps) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadWorkspaces = async () => {
      try {
        const workspaceList = await workspaceApi.list();
        
        if (workspaceList.length > 0) {
          setWorkspaces(workspaceList);
          setCurrentWorkspace(workspaceList[0]);
        } else {
          // Create a default workspace if none exist
          const newWorkspace = await workspaceApi.create('My First Workspace');
          setWorkspaces([newWorkspace]);
          setCurrentWorkspace(newWorkspace);
        }
      } catch (error) {
        console.error('Error loading workspaces:', error);
        // If we can't load from API, show error but don't crash
      } finally {
        setIsLoading(false);
      }
    };

    loadWorkspaces();
  }, []);

  const handleWorkspaceChange = async (workspaceId: string) => {
    try {
      const workspace = await workspaceApi.get(workspaceId);
      setCurrentWorkspace(workspace);
      
      // Navigate to slug URL
      if (typeof window !== 'undefined') {
        window.history.pushState(null, '', `/flow-generator/${workspace.slug}`);
      }
      
      // Refresh the workspaces list
      const workspaceList = await workspaceApi.list();
      setWorkspaces(workspaceList);
    } catch (error) {
      console.error('Error changing workspace:', error);
    }
  };

  const handleWorkspaceUpdate = (updatedWorkspace: Workspace) => {
    setCurrentWorkspace(updatedWorkspace);
    
    // Update in the workspaces list
    setWorkspaces(prev => 
      prev.map(ws => ws.id === updatedWorkspace.id ? updatedWorkspace : ws)
    );
  };

  if (isLoading || !currentWorkspace) {
    return (
      <div className="h-[calc(100vh-6rem)] w-full rounded-2xl overflow-hidden border border-white/10 bg-black flex items-center justify-center">
        <p className="text-muted-foreground">Loading workspace...</p>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-6rem)] w-full overflow-hidden bg-black rounded-2xl border border-white/10">
      <ProjectProvider data={currentWorkspace}>
        <GatewayProviderClient models={mockTextModels}>
          <ReactFlowProvider>
            <MouseModeProvider>
              <Canvas readOnly={readOnly}>
                <Controls />
                {!readOnly && (
                  <>
                    <div className="absolute top-4 left-4 z-[50] flex items-center gap-2">
                      <div className="flex items-center rounded-full border bg-card/90 p-1 drop-shadow-xs backdrop-blur-sm">
                        <WorkspaceSelector
                          workspaces={workspaces}
                          currentWorkspace={currentWorkspace.id}
                          onWorkspaceChange={handleWorkspaceChange}
                        />
                      </div>
                    </div>
                    <TopRight onWorkspaceUpdate={handleWorkspaceUpdate} />
                    <Toolbar />
                  </>
                )}
              </Canvas>
            </MouseModeProvider>
          </ReactFlowProvider>
        </GatewayProviderClient>
      </ProjectProvider>
    </div>
  );
}
