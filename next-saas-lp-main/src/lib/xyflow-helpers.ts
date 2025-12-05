import type { Node } from "@xyflow/react";

// Helper functions to extract data from connected nodes

export const getTextFromTextNodes = (nodes: Node[]) => {
  const texts = nodes
    .filter((node) => node.type === "text")
    .map((node) => node.data.text)
    .filter(Boolean) as string[];

  const generatedTexts = nodes
    .filter((node) => node.type === "text" && node.data.generated)
    .map((node) => (node.data.generated as any)?.text)
    .filter(Boolean) as string[];

  return [...texts, ...generatedTexts];
};

export const getImagesFromImageNodes = (nodes: Node[]) => {
  const sourceImages = nodes
    .filter((node) => node.type === "image" && node.data.imageUrl)
    .map((node) => ({ url: node.data.imageUrl }))
    .filter(Boolean);

  const generatedImages = nodes
    .filter((node) => node.type === "image" && node.data.generated)
    .map((node) => ({ url: (node.data.generated as any)?.url }))
    .filter(Boolean);

  return [...sourceImages, ...generatedImages];
};

export const getDescriptionsFromImageNodes = (nodes: Node[]) => {
  const descriptions = nodes
    .filter((node) => node.type === "image" && node.data.description)
    .map((node) => node.data.description)
    .filter(Boolean) as string[];

  return descriptions;
};

export const isValidSourceTarget = (source: Node, target: Node) => {
  // Video cannot be a source
  if (source.type === "video") {
    return false;
  }

  // Audio can only receive text
  if (target.type === "audio" && source.type !== "text") {
    return false;
  }

  return true;
};
