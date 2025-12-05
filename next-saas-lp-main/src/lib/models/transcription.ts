import type { TersaModel } from '../providers';

export const transcriptionModels = {
  'openai-whisper-1': {
    id: 'openai-whisper-1',
    label: 'Whisper',
    provider: 'openai',
  },
} as const;

export type TranscriptionModel = keyof typeof transcriptionModels;
