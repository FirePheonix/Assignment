"use client";

import { useState } from "react";
import { useReactFlow } from "@xyflow/react";
import { Upload, Image as ImageIcon } from "lucide-react";
import type { ImageNodeProps } from "../image-node";
import { NodeLayout } from "../node-layout";

export const ImagePrimitive = ({ data, id }: ImageNodeProps) => {
  const { updateNodeData } = useReactFlow();
  const [uploading, setUploading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      // Create local preview
      const reader = new FileReader();
      reader.onload = (e) => {
        const imageUrl = e.target?.result as string;
        updateNodeData(id, { imageUrl });
      };
      reader.readAsDataURL(file);

      // TODO: Upload to server
      console.log("Uploading image:", file);
    } catch (error) {
      console.error("Error uploading image:", error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <NodeLayout id={id} title="Image" hasTargetHandle={false}>
      <div className="p-4">
        {data.imageUrl ? (
          <div className="relative group">
            <img
              src={data.imageUrl}
              alt="Uploaded"
              className="w-full h-auto rounded-lg"
            />
            <label className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer rounded-lg">
              <Upload className="w-6 h-6 text-white" />
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          </div>
        ) : (
          <label className="flex flex-col items-center justify-center h-40 bg-white/5 border-2 border-dashed border-white/10 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
            {uploading ? (
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
            ) : (
              <>
                <ImageIcon className="w-8 h-8 text-white/30 mb-2" />
                <span className="text-sm text-white/50">Click to upload image</span>
              </>
            )}
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
        )}
      </div>
    </NodeLayout>
  );
};
