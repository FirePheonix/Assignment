"use client";

import { useState, useCallback } from "react";
import { getIncomers, useReactFlow } from "@xyflow/react";
import { Play, RotateCcw } from "lucide-react";
import type { TextNodeProps } from "../text-node";
import { NodeLayout } from "../node-layout";
import { getTextFromTextNodes, getImagesFromImageNodes, getDescriptionsFromImageNodes } from "@/lib/xyflow-helpers";

export const TextTransform = ({ data, id, type }: TextNodeProps) => {
  const { updateNodeData, getNodes, getEdges } = useReactFlow();
  const [loading, setLoading] = useState(false);

  const handleGenerate = useCallback(async () => {
    setLoading(true);
    try {
      // Get incoming connected nodes
      const incomers = getIncomers({ id }, getNodes(), getEdges());
      
      // Extract data from connected nodes
      const textPrompts = getTextFromTextNodes(incomers);
      const images = getImagesFromImageNodes(incomers);
      const imageDescriptions = getDescriptionsFromImageNodes(incomers);

      // Build the prompt
      const content: string[] = [];
      
      if (data.instructions) {
        content.push("Instructions:", data.instructions, "");
      }
      
      if (textPrompts.length) {
        content.push("Text Input:", ...textPrompts, "");
      }
      
      if (imageDescriptions.length) {
        content.push("Image Descriptions:", ...imageDescriptions, "");
      }

      // TODO: Call Django API
      console.log("Generating with:", { content, images });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const generatedText = `Generated text based on:\n${content.join("\n")}\n\n[This will be replaced with actual AI-generated content from your Django backend]`;

      updateNodeData(id, {
        generated: { text: generatedText },
        updatedAt: new Date().toISOString(),
      });
    } catch (error) {
      console.error("Error generating text:", error);
    } finally {
      setLoading(false);
    }
  }, [id, data.instructions, getNodes, getEdges, updateNodeData]);

  const handleInstructionsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateNodeData(id, { instructions: e.target.value });
  };

  return (
    <NodeLayout id={id} title="Text">
      <div className="flex flex-col">
        {/* Output Display */}
        <div className="p-4 min-h-[120px] max-h-[300px] overflow-auto bg-black/20">
          {loading ? (
            <div className="flex items-center justify-center h-full text-white/50">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>
            </div>
          ) : data.generated?.text ? (
            <p className="text-sm text-white/90 whitespace-pre-wrap">
              {data.generated.text}
            </p>
          ) : (
            <p className="text-sm text-white/50 text-center">
              Connect nodes and press <Play className="inline w-3 h-3" /> to generate text
            </p>
          )}
        </div>

        {/* Instructions Input */}
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
            {data.generated?.text ? (
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
