"use client";

import { useReactFlow } from "@xyflow/react";
import type { TextNodeProps } from "../text-node";
import { NodeLayout } from "../node-layout";

export const TextPrimitive = ({ data, id, type }: TextNodeProps) => {
  const { updateNodeData } = useReactFlow();

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateNodeData(id, { text: e.target.value });
  };

  return (
    <NodeLayout id={id} title="Text" hasSourceHandle hasTargetHandle={false}>
      <div className="p-4">
        <textarea
          value={data.text || ""}
          onChange={handleChange}
          placeholder="Enter your text..."
          className="w-full h-40 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
        />
      </div>
    </NodeLayout>
  );
};
