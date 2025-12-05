import type { Node } from '@xyflow/react';

export const isValidSourceTarget = (source: Node, target: Node) => {
  // Video nodes cannot be sources
  if (source.type === 'video') {
    return false;
  }

  // Audio nodes can only connect to transcription
  if (source.type === 'audio' && target.type !== 'text') {
    return false;
  }

  // Additional validation rules can be added here
  return true;
};

// Helper functions to extract data from connected nodes
export const getTextFromTextNodes = (nodes: Node[]) => {
  return nodes
    .filter((node) => {
      const data = node.data as any;
      return node.type === 'text' && (data.generated?.text || data.text);
    })
    .map((node) => {
      const data = node.data as any;
      return (data.generated?.text || data.text) as string;
    });
};

export const getTranscriptionFromAudioNodes = (nodes: Node[]) => {
  return nodes
    .filter((node) => node.type === 'audio' && node.data.transcription)
    .map((node) => node.data.transcription as string);
};

export const getImagesFromImageNodes = (nodes: Node[]) => {
  return nodes
    .filter((node) => {
      const data = node.data as any;
      return node.type === 'image' && (data.content || data.generated?.url);
    })
    .map((node) => {
      const data = node.data as any;
      // Prefer generated image, fallback to uploaded content
      if (data.generated?.url) {
        return { url: data.generated.url, type: data.generated.type || 'image/png' };
      }
      return data.content as { url: string; type: string };
    });
};

export const getDescriptionsFromImageNodes = (nodes: Node[]) => {
  return nodes
    .filter((node) => node.type === 'image' && node.data.description)
    .map((node) => node.data.description as string);
};

export const getTweetContentFromTweetNodes = (nodes: Node[]) => {
  return nodes
    .filter((node) => node.type === 'tweet' && node.data.content)
    .map((node) => node.data.content as string);
};

export const getFilesFromFileNodes = (nodes: Node[]) => {
  return nodes
    .filter((node) => node.type === 'file' && node.data.content)
    .map((node) => node.data.content as { url: string; type: string });
};

export const getCodeFromCodeNodes = (nodes: Node[]) => {
  return nodes
    .filter((node) => node.type === 'code' && node.data.code)
    .map((node) => node.data.code as string);
};
