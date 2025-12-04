"use client";

import { memo } from "react";
import { useNodeConnections, useReactFlow } from "@xyflow/react";
import { TextPrimitive } from "./text/primitive";
import { TextTransform } from "./text/transform";

export interface TextNodeProps {
  id: string;
  type: string;
  data: {
    text?: string;
    instructions?: string;
    generated?: {
      text: string;
    };
    updatedAt?: string;
  };
}

export const TextNode = memo((props: TextNodeProps) => {
  const connections = useNodeConnections({
    id: props.id,
    handleType: "target",
  });

  // If node has incoming connections, it's a transform node
  // Otherwise it's a primitive (simple text input)
  const Component = connections.length ? TextTransform : TextPrimitive;

  return <Component {...props} />;
});

TextNode.displayName = "TextNode";
