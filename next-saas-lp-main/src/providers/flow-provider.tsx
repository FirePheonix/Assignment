"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import type { Node, Edge } from "@xyflow/react";

interface FlowState {
  isSaving: boolean;
  lastSaved: Date | null;
}

interface FlowContextType {
  saveState: FlowState;
  setSaveState: React.Dispatch<React.SetStateAction<FlowState>>;
}

const FlowContext = createContext<FlowContextType | undefined>(undefined);

export function FlowProvider({ children }: { children: ReactNode }) {
  const [saveState, setSaveState] = useState<FlowState>({
    isSaving: false,
    lastSaved: null,
  });

  return (
    <FlowContext.Provider value={{ saveState, setSaveState }}>
      {children}
    </FlowContext.Provider>
  );
}

export function useFlowContext() {
  const context = useContext(FlowContext);
  if (!context) {
    throw new Error("useFlowContext must be used within FlowProvider");
  }
  return context;
}
