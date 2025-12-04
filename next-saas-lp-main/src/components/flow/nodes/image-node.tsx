"use client";

import { memo } from "react";
import { useNodeConnections } from "@xyflow/react";
import { ImagePrimitive } from "./image/primitive";
import { ImageTransform } from "./image/transform";

export interface ImageNodeProps {
  id: string;
  type: string;
  data: {
    imageUrl?: string;
    description?: string;
    instructions?: string;
    generated?: {
      url: string;
    };
    updatedAt?: string;
  };
}

export const ImageNode = memo((props: ImageNodeProps) => {
  const connections = useNodeConnections({
    id: props.id,
    handleType: "target",
  });

  const Component = connections.length ? ImageTransform : ImagePrimitive;

  return <Component {...props} />;
});

ImageNode.displayName = "ImageNode";
