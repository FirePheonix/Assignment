"use client";

import { Canvas } from "@/components/flow-components/canvas";
import { ProjectProvider } from "@/providers/project-provider";
import { GatewayProviderClient } from "@/providers/gateway-provider";
import { ReactFlowProvider } from "@xyflow/react";
import { Controls, MouseModeProvider } from "@/components/flow-components/controls";
import { TopRight } from "@/components/flow-components/top-right";
import { WorkspaceSelector } from "@/components/flow-components/workspace-selector";
import "@xyflow/react/dist/style.css";
import { use, useState, useEffect } from "react";
import { publicWorkspaceApi, workspaceApi } from "@/lib/workspace-api";
import type { Workspace } from "@/lib/workspace-api";
import { Button } from "@/components/flow-components/ui/button";
import { Download, AlertCircle, Lock } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { UserAvatar } from "@/components/user-avatar";
import Link from "next/link";

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

export default function PublicWorkspacePage({ params }: { params: Promise<{ slug: string }> }) {
  // Use React's `use` hook to unwrap the params Promise
  const { slug } = use(params);
  
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('auth_token');
    setIsAuthenticated(!!token);
  }, []);

  useEffect(() => {
    const loadWorkspace = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Try to load as public workspace first
        const data = await publicWorkspaceApi.getBySlug(slug);
        setWorkspace(data);
      } catch (err) {
        console.error('Error loading workspace:', err);
        setError(err instanceof Error ? err.message : 'Workspace not found');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadWorkspace();
  }, [slug]);

  const handleImportWorkspace = async () => {
    if (!workspace) return;

    if (!isAuthenticated) {
      toast.error('Please login to import this workspace');
      router.push(`/login?redirect=${encodeURIComponent(`/flow-generator/${workspace.slug}`)}`);
      return;
    }

    try {
      setIsImporting(true);
      const importedWorkspace = await workspaceApi.importWorkspace(workspace.id);
      
      toast.success('Workspace imported successfully!');
      
      // Redirect to the imported workspace
      router.push(`/flow-generator/${importedWorkspace.slug}`);
    } catch (error) {
      console.error('Error importing workspace:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to import workspace');
    } finally {
      setIsImporting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="h-[calc(100vh-6rem)] w-full rounded-2xl overflow-hidden border border-white/10 bg-black flex items-center justify-center">
        <p className="text-muted-foreground">Loading workspace...</p>
      </div>
    );
  }

  if (error || !workspace) {
    return (
      <div className="h-[calc(100vh-6rem)] w-full rounded-2xl overflow-hidden border border-white/10 bg-black flex flex-col items-center justify-center gap-4">
        <AlertCircle className="w-12 h-12 text-red-500" />
        <p className="text-red-400 text-lg">{error || 'Workspace not found'}</p>
        <Button onClick={() => router.push('/feed')} variant="outline">
          Browse Feed
        </Button>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-6rem)] w-full overflow-hidden bg-black rounded-2xl border border-white/10 relative">
      {/* Read-Only Banner */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[60] flex items-center gap-2 px-6 py-3 bg-amber-500/10 border border-amber-500/20 rounded-full backdrop-blur-sm">
        <Lock className="w-4 h-4 text-amber-500" />
        <span className="text-sm text-amber-500 font-medium">Read-Only Mode</span>
        <Button
          size="sm"
          onClick={handleImportWorkspace}
          disabled={isImporting}
          className="ml-2 gap-2"
        >
          <Download className="w-4 h-4" />
          {isImporting ? 'Importing...' : 'Import to Edit'}
        </Button>
      </div>

      {/* Workspace Info */}
      <div className="absolute top-4 left-4 z-[50] bg-card/90 backdrop-blur-sm rounded-lg border border-white/10 p-3 max-w-sm">
        <h2 className="font-semibold text-white mb-1">{workspace.name}</h2>
        {workspace.description && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-2">{workspace.description}</p>
        )}
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <Link 
            href={`/users/${workspace.userId}`}
            className="flex items-center gap-1.5 hover:text-purple-400 transition-colors"
          >
            <UserAvatar 
              user={{ 
                profile_picture: workspace.userProfilePicture,
                username: workspace.userName 
              }} 
              size="sm" 
            />
            <span>By {workspace.userName}</span>
          </Link>
          <span>•</span>
          <span>{workspace.viewCount} views</span>
          <span>•</span>
          <span>{workspace.cloneCount} imports</span>
        </div>
      </div>

      <ProjectProvider data={workspace}>
        <GatewayProviderClient models={mockTextModels}>
          <ReactFlowProvider>
            <MouseModeProvider>
              <Canvas readOnly={true}>
                <Controls />
              </Canvas>
            </MouseModeProvider>
          </ReactFlowProvider>
        </GatewayProviderClient>
      </ProjectProvider>
    </div>
  );
}
