"use client";

import { createContext, useContext, ReactNode } from "react";

interface NodeOperationsContextType {
  addNode: (type: string, options?: Record<string, unknown>) => string;
  duplicateNode: (id: string) => void;
}

const NodeOperationsContext = createContext<NodeOperationsContextType | undefined>(undefined);

export function NodeOperationsProvider({
  children,
  addNode,
  duplicateNode,
}: {
  children: ReactNode;
  addNode: (type: string, options?: Record<string, unknown>) => string;
  duplicateNode: (id: string) => void;
}) {
  return (
    <NodeOperationsContext.Provider value={{ addNode, duplicateNode }}>
      {children}
    </NodeOperationsContext.Provider>
  );
}

export function useNodeOperations() {
  const context = useContext(NodeOperationsContext);
  if (!context) {
    throw new Error("useNodeOperations must be used within NodeOperationsProvider");
  }
  return context;
}
