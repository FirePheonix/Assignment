"use client";

import { memo, useState } from "react";
import { NodeLayout } from "./node-layout";
import { Play } from "lucide-react";

interface CodeNodeProps {
  id: string;
  data: {
    code?: string;
    language?: string;
    output?: string;
  };
}

export const CodeNode = memo(({ id, data }: CodeNodeProps) => {
  const [code, setCode] = useState(data.code || "");
  const [output, setOutput] = useState(data.output || "");

  const handleRun = async () => {
    // TODO: Call Django API to execute code
    console.log("Running code:", code);
    setOutput("Code execution output will appear here...");
  };

  return (
    <NodeLayout id={id} title="Code Executor">
      <div className="space-y-3">
        <div>
          <label className="text-xs text-white/50 mb-1 block">Code</label>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter your code here..."
            className="w-full px-3 py-2 bg-black/50 border border-white/10 rounded-lg text-sm text-green-400 font-mono placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-purple-500"
            rows={8}
          />
        </div>

        <button
          onClick={handleRun}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg text-sm font-medium text-white transition-colors"
        >
          <Play className="w-4 h-4" />
          Run Code
        </button>

        {output && (
          <div>
            <label className="text-xs text-white/50 mb-1 block">Output</label>
            <div className="px-3 py-2 bg-black/50 border border-white/10 rounded-lg text-sm text-white/90 font-mono min-h-[60px]">
              {output}
            </div>
          </div>
        )}
      </div>
    </NodeLayout>
  );
});

CodeNode.displayName = "CodeNode";
