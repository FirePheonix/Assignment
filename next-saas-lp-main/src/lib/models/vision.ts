import type { TersaModel } from '../providers';

export const visionModels = {
  'openai-gpt-4o': {
    id: 'openai-gpt-4o',
    label: 'GPT-4o',
    provider: 'openai',
  },
  'openai-gpt-4o-mini': {
    id: 'openai-gpt-4o-mini',
    label: 'GPT-4o Mini',
    provider: 'openai',
  },
  'anthropic-claude-3.5-sonnet': {
    id: 'anthropic-claude-3.5-sonnet',
    label: 'Claude 3.5 Sonnet',
    provider: 'anthropic',
  },
} as const;

export type VisionModel = keyof typeof visionModels;
