import { useNodeConnections } from '@xyflow/react';
import { VideoPrimitive } from './primitive';
import { VideoTransform } from './transform';

export type VideoNodeProps = {
  type: string;
  data: {
    content?: {
      url: string;
      type: string;
    };
    generated?: {
      url: string;
      type: string;
      videoId?: string;
    };
    updatedAt?: string;
    model?: string;
    instructions?: string;
    width?: number;
    height?: number;
    size?: string;
    seconds?: number;
  };
  id: string;
};

export const VideoNode = (props: VideoNodeProps) => {
  const connections = useNodeConnections({
    id: props.id,
    handleType: 'target',
  });
  const Component = connections.length ? VideoTransform : VideoPrimitive;

  return <Component {...props} title="Video" />;
};

