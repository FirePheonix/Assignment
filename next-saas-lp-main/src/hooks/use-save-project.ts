import { useState } from 'react';

export interface SaveState {
  isSaving: boolean;
  lastSaved: Date | null;
}

export function useSaveProject(): [SaveState, React.Dispatch<React.SetStateAction<SaveState>>] {
  const [saveState, setSaveState] = useState<SaveState>({
    isSaving: false,
    lastSaved: null,
  });

  return [saveState, setSaveState];
}
