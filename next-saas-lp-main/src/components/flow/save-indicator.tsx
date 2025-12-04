"use client";

import { Panel } from "@xyflow/react";
import { useFlowContext } from "@/providers/flow-provider";
import { Loader2, Check } from "lucide-react";

export function SaveIndicator() {
  const { saveState } = useFlowContext();

  return (
    <Panel position="top-right" className="mt-4 mr-4">
      <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 backdrop-blur-xl border border-white/20 text-sm text-white/70">
        {saveState.isSaving ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Saving...</span>
          </>
        ) : saveState.lastSaved ? (
          <>
            <Check className="w-4 h-4 text-green-400" />
            <span>
              Saved at {saveState.lastSaved.toLocaleTimeString()}
            </span>
          </>
        ) : (
          <span>No changes</span>
        )}
      </div>
    </Panel>
  );
}
