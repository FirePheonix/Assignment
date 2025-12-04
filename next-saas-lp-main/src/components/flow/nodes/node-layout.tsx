"use client";

import { ReactNode, useState } from "react";
import { Handle, Position, useReactFlow } from "@xyflow/react";
import { Copy, Trash2, Eye, MoreVertical } from "lucide-react";
import { useNodeOperations } from "@/providers/node-operations-provider";

interface NodeLayoutProps {
  id: string;
  title: string;
  children: ReactNode;
  className?: string;
  hasTargetHandle?: boolean;
  hasSourceHandle?: boolean;
}

export function NodeLayout({
  id,
  title,
  children,
  className = "",
  hasTargetHandle = true,
  hasSourceHandle = true,
}: NodeLayoutProps) {
  const { deleteElements, setCenter, getNode } = useReactFlow();
  const { duplicateNode } = useNodeOperations();
  const [showMenu, setShowMenu] = useState(false);

  const handleDelete = () => {
    deleteElements({ nodes: [{ id }] });
  };

  const handleFocus = () => {
    const node = getNode(id);
    if (!node) return;

    const { x, y } = node.position;
    const width = node.measured?.width ?? 0;

    setCenter(x + width / 2, y, { duration: 1000 });
  };

  return (
    <div className={`relative ${className}`}>
      {hasTargetHandle && (
        <Handle
          type="target"
          position={Position.Left}
          className="!bg-purple-500 !w-3 !h-3 !border-2 !border-white"
        />
      )}

      <div className="min-w-[300px] rounded-2xl border border-white/20 bg-gradient-to-br from-gray-900/90 to-black/90 backdrop-blur-xl shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
          <h3 className="text-sm font-medium text-white/90">{title}</h3>
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 rounded-lg hover:bg-white/10 transition-colors"
            >
              <MoreVertical className="w-4 h-4 text-white/70" />
            </button>

            {showMenu && (
              <div className="absolute right-0 top-8 w-40 rounded-lg border border-white/20 bg-black/95 backdrop-blur-xl shadow-xl z-50">
                <button
                  onClick={() => {
                    duplicateNode(id);
                    setShowMenu(false);
                  }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-white/70 hover:bg-white/10 transition-colors"
                >
                  <Copy className="w-3 h-3" />
                  Duplicate
                </button>
                <button
                  onClick={() => {
                    handleFocus();
                    setShowMenu(false);
                  }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-white/70 hover:bg-white/10 transition-colors"
                >
                  <Eye className="w-3 h-3" />
                  Focus
                </button>
                <button
                  onClick={() => {
                    handleDelete();
                    setShowMenu(false);
                  }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  <Trash2 className="w-3 h-3" />
                  Delete
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-4">{children}</div>
      </div>

      {hasSourceHandle && (
        <Handle
          type="source"
          position={Position.Right}
          className="!bg-purple-500 !w-3 !h-3 !border-2 !border-white"
        />
      )}
    </div>
  );
}
