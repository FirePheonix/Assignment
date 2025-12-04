"use client";

import { memo, useState } from "react";
import { NodeLayout } from "./node-layout";
import { Video as VideoIcon, X } from "lucide-react";

export interface VideoNodeProps {
  id: string;
  type: string;
  data: Record<string, any>;
}

export const VideoNode = memo(({ id }: VideoNodeProps) => {
  const [showPopup, setShowPopup] = useState(false);

  const handleClick = () => {
    setShowPopup(true);
  };

  return (
    <>
      <NodeLayout id={id} title="Video" hasSourceHandle={false}>
        <button
          onClick={handleClick}
          className="w-full p-8 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors"
        >
          <div className="flex flex-col items-center gap-3">
            <VideoIcon className="w-12 h-12 text-purple-400" />
            <span className="text-sm text-white/70">AI Video Generation</span>
          </div>
        </button>
      </NodeLayout>

      {/* Coming Soon Popup */}
      {showPopup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-gradient-to-br from-gray-900 to-black border border-white/20 rounded-2xl p-8 max-w-md relative">
            <button
              onClick={() => setShowPopup(false)}
              className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-white/70" />
            </button>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <VideoIcon className="w-8 h-8 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Video Generation
              </h3>
              <p className="text-white/60 mb-6">
                AI video generation is coming soon! This feature will create videos from text prompts and images.
              </p>
              <button
                onClick={() => setShowPopup(false)}
                className="w-full px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg text-white font-medium transition-colors"
              >
                Got it!
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
});

VideoNode.displayName = "VideoNode";
