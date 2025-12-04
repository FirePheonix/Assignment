import { TextNode } from "./text-node";
import { ImageNode } from "./image-node";
import { AudioNode } from "./audio-node";
import { VideoNode } from "./video-node";

export const nodeTypes = {
  text: TextNode,
  image: ImageNode,
  audio: AudioNode,
  video: VideoNode,
};
