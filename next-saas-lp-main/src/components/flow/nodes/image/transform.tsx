"use client";

import { useState, useCallback } from "react";
import { getIncomers, useReactFlow } from "@xyflow/react";
import { Play, RotateCcw, Image as ImageIcon } from "lucide-react";
import type { ImageNodeProps } from "../image-node";
import { NodeLayout } from "../node-layout";
import { getTextFromTextNodes, getImagesFromImageNodes } from "@/lib/xyflow-helpers";

export const ImageTransform = ({ data, id }: ImageNodeProps) => {
  const { updateNodeData, getNodes, getEdges } = useReactFlow();
  const [loading, setLoading] = useState(false);

  const handleGenerate = useCallback(async () => {
    setLoading(true);
    try {
      const incomers = getIncomers({ id }, getNodes(), getEdges());
      const textPrompts = getTextFromTextNodes(incomers);
      const images = getImagesFromImageNodes(incomers);

      const content: string[] = [];
      
      if (data.instructions) {
        content.push("Instructions:", data.instructions);
      }
      
      if (textPrompts.length) {
        content.push("Text Prompts:", ...textPrompts);
      }

      console.log("Generating image with:", { content, inputImages: images });

      // TODO: Call Django API
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Placeholder image
      const generatedUrl = `https://placehold.co/512x512/8b5cf6/white?text=${encodeURIComponent("AI Generated")}`;

      updateNodeData(id, {
        generated: { url: generatedUrl },
        updatedAt: new Date().toISOString(),
      });
    } catch (error) {
      console.error("Error generating image:", error);
    } finally {
      setLoading(false);
    }
  }, [id, data.instructions, getNodes, getEdges, updateNodeData]);

  const handleInstructionsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateNodeData(id, { instructions: e.target.value });
  };

  return (
    <NodeLayout id={id} title="Image" hasTargetHandle>
      <div className="flex flex-col">
        {/* Image Display */}
        <div className="aspect-square bg-black/20 flex items-center justify-center">
          {loading ? (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          ) : data.generated?.url ? (
            <img
              src={data.generated.url}
              alt="Generated"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="text-center p-4">
              <ImageIcon className="w-12 h-12 text-white/30 mx-auto mb-2" />
              <p className="text-sm text-white/50">
                Connect nodes and press <Play className="inline w-3 h-3" /> to generate
              </p>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="p-4 border-t border-white/10">
          <textarea
            value={data.instructions || ""}
            onChange={handleInstructionsChange}
            placeholder="Enter instructions (optional)..."
            className="w-full h-20 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
          />
        </div>

        {/* Generate Button */}
        <div className="p-4 pt-0">
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 disabled:bg-purple-500/50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-white transition-colors"
          >
            {data.generated?.url ? (
              <>
                <RotateCcw className="w-4 h-4" />
                Regenerate
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Generate
              </>
            )}
          </button>
        </div>
      </div>
    </NodeLayout>
  );
};
