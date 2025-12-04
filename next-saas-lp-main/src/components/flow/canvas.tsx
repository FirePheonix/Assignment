"use client";

import { useCallback, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type OnConnect,
  type OnNodesChange,
  type OnEdgesChange,
  type IsValidConnection,
  applyNodeChanges,
  applyEdgeChanges,
  useReactFlow,
  Panel,
  getOutgoers,
} from "@xyflow/react";
import { nanoid } from "nanoid";
import { useHotkeys } from "react-hotkeys-hook";
import { useDebouncedCallback } from "use-debounce";
import { nodeTypes } from "./nodes";
import { FlowToolbar } from "./toolbar";
import { SaveIndicator } from "./save-indicator";
import { NodeOperationsProvider } from "@/providers/node-operations-provider";
import { useFlowContext } from "@/providers/flow-provider";
import { isValidSourceTarget } from "@/lib/xyflow-helpers";

export function FlowCanvas() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const { getNode, updateNode, getNodes, getEdges } = useReactFlow();
  const { saveState, setSaveState } = useFlowContext();

  // Simulated save to Django backend
  const save = useDebouncedCallback(async () => {
    if (saveState.isSaving) {
      return;
    }

    try {
      setSaveState((prev) => ({ ...prev, isSaving: true }));

      // TODO: Replace with actual Django API call
      // await fetch('/api/flow/save', {
      //   method: 'POST',
      //   body: JSON.stringify({ nodes, edges }),
      // });

      console.log("Saving to Django backend...", { nodes, edges });

      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 500));

      setSaveState((prev) => ({ ...prev, lastSaved: new Date() }));
    } catch (error) {
      console.error("Error saving flow:", error);
    } finally {
      setSaveState((prev) => ({ ...prev, isSaving: false }));
    }
  }, 1000);

  const onNodesChange = useCallback<OnNodesChange>(
    (changes) => {
      setNodes((nds) => {
        const updated = applyNodeChanges(changes, nds);
        save();
        return updated;
      });
    },
    [save]
  );

  const onEdgesChange = useCallback<OnEdgesChange>(
    (changes) => {
      setEdges((eds) => {
        const updated = applyEdgeChanges(changes, eds);
        save();
        return updated;
      });
    },
    [save]
  );

  const onConnect = useCallback<OnConnect>(
    (connection) => {
      const newEdge: Edge = {
        id: nanoid(),
        type: "smoothstep",
        animated: true,
        ...connection,
      };
      setEdges((eds) => eds.concat(newEdge));
      save();
    },
    [save]
  );

  const isValidConnection = useCallback<IsValidConnection>(
    (connection) => {
      const nodes = getNodes();
      const edges = getEdges();
      
      const source = nodes.find((node) => node.id === connection.source);
      const target = nodes.find((node) => node.id === connection.target);

      if (!source || !target) {
        return false;
      }

      // Validate source/target compatibility
      if (!isValidSourceTarget(source, target)) {
        return false;
      }

      // Prevent cycles
      const hasCycle = (node: Node, visited = new Set<string>()): boolean => {
        if (visited.has(node.id)) {
          return false;
        }

        visited.add(node.id);

        for (const outgoer of getOutgoers(node, nodes, edges)) {
          if (outgoer.id === connection.source || hasCycle(outgoer, visited)) {
            return true;
          }
        }

        return false;
      };

      if (target.id === connection.source) {
        return false;
      }

      return !hasCycle(target);
    },
    [getNodes, getEdges]
  );

  const addNode = useCallback(
    (type: string, options?: Record<string, unknown>) => {
      const { data: nodeData, position, ...rest } = options ?? {};
      const newNode: Node = {
        id: nanoid(),
        type,
        data: {
          ...(nodeData ? nodeData : {}),
        },
        position: (position as { x: number; y: number }) || { x: 100, y: 100 },
        ...rest,
      };

      setNodes((nds) => nds.concat(newNode));
      save();

      return newNode.id;
    },
    [save]
  );

  const duplicateNode = useCallback(
    (id: string) => {
      const node = getNode(id);

      if (!node || !node.type) {
        return;
      }

      const { id: oldId, ...rest } = node;

      const newId = addNode(node.type, {
        ...rest,
        position: {
          x: node.position.x + 200,
          y: node.position.y + 200,
        },
        selected: true,
      });

      setTimeout(() => {
        updateNode(id, { selected: false });
        updateNode(newId, { selected: true });
      }, 0);
    },
    [addNode, getNode, updateNode]
  );

  const handleSelectAll = useCallback(() => {
    setNodes((nodes) =>
      nodes.map((node) => ({ ...node, selected: true }))
    );
  }, []);

  useHotkeys("meta+a", handleSelectAll, {
    enableOnContentEditable: false,
    preventDefault: true,
  });

  return (
    <NodeOperationsProvider addNode={addNode} duplicateNode={duplicateNode}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        isValidConnection={isValidConnection}
        nodeTypes={nodeTypes}
        fitView
        className="bg-gradient-to-br from-black via-gray-900 to-black"
      >
        <Background className="bg-black" />
        <Controls className="bg-white/10 backdrop-blur-xl border border-white/20" />
        <MiniMap className="bg-white/5 backdrop-blur-xl border border-white/20" />
        <FlowToolbar />
        <SaveIndicator />
      </ReactFlow>
    </NodeOperationsProvider>
  );
}
