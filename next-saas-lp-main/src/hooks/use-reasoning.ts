import { useState } from 'react';

export interface ReasoningState {
  isReasoning: boolean;
  isGenerating: boolean;
}

// Mock reasoning hook for AI model thinking display
export function useReasoning(): [
  ReasoningState,
  React.Dispatch<React.SetStateAction<ReasoningState>>
] {
  const [reasoning, setReasoning] = useState<ReasoningState>({
    isReasoning: false,
    isGenerating: false,
  });

  return [reasoning, setReasoning];
}
