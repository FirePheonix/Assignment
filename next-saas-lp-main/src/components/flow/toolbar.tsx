"use client";

import { Panel, useReactFlow } from "@xyflow/react";
import { nodeButtons } from "@/lib/node-buttons";
import { useNodeOperations } from "@/providers/node-operations-provider";

export function FlowToolbar() {
  const { getViewport } = useReactFlow();
  const { addNode } = useNodeOperations();

  const handleAddNode = (type: string, options?: Record<string, unknown>) => {
    const viewport = getViewport();

    // Calculate center of viewport
    const centerX =
      -viewport.x / viewport.zoom + window.innerWidth / 2 / viewport.zoom;
    const centerY =
      -viewport.y / viewport.zoom + window.innerHeight / 2 / viewport.zoom;

    const position = { x: centerX, y: centerY };
    const { data: nodeData, ...rest } = options ?? {};

    addNode(type, {
      position,
      data: {
        ...(nodeData ? nodeData : {}),
      },
      ...rest,
    });
  };

  return (
    <Panel
      position="bottom-center"
      className="mb-4 flex items-center gap-2 rounded-full border border-white/20 bg-white/5 backdrop-blur-xl p-2 shadow-lg"
    >
      {nodeButtons.map((button) => (
        <button
          key={button.id}
          onClick={() => handleAddNode(button.id, button.data)}
          className="group flex items-center gap-2 px-4 py-2 rounded-full hover:bg-white/10 transition-all text-white/70 hover:text-white"
          title={button.label}
        >
          <button.icon className="w-4 h-4" />
          <span className="text-sm">{button.label}</span>
        </button>
      ))}
    </Panel>
  );
}
