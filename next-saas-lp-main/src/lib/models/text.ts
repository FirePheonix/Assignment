import type { TersaModel } from '@/lib/providers';
import { providers } from '@/lib/providers';

type TersaTextModel = TersaModel & {
  providers: Array<{
    id: string;
    name: string;
    icon: any;
    modelId: string;
    getCost: (props: { inputTokens: number; outputTokens: number }) => number;
  }>;
  contextWindow?: number;
};

export const textModels: Record<string, TersaTextModel> = {
  'gpt-4o': {
    label: 'GPT-4o',
    chef: providers.openai,
    providers: [
      {
        ...providers.openai,
        modelId: 'gpt-4o',
        getCost: ({ inputTokens, outputTokens }) =>
          (inputTokens / 1000000) * 2.5 + (outputTokens / 1000000) * 10,
      },
    ],
    contextWindow: 128000,
    default: true,
  },
  'gpt-4o-mini': {
    label: 'GPT-4o Mini',
    chef: providers.openai,
    providers: [
      {
        ...providers.openai,
        modelId: 'gpt-4o-mini',
        getCost: ({ inputTokens, outputTokens }) =>
          (inputTokens / 1000000) * 0.15 + (outputTokens / 1000000) * 0.6,
      },
    ],
    contextWindow: 128000,
    priceIndicator: 'lowest',
  },
  'claude-3-5-sonnet': {
    label: 'Claude 3.5 Sonnet',
    chef: providers.anthropic,
    providers: [
      {
        ...providers.anthropic,
        modelId: 'claude-3-5-sonnet-20241022',
        getCost: ({ inputTokens, outputTokens }) =>
          (inputTokens / 1000000) * 3 + (outputTokens / 1000000) * 15,
      },
    ],
    contextWindow: 200000,
  },
  'claude-3-5-haiku': {
    label: 'Claude 3.5 Haiku',
    chef: providers.anthropic,
    providers: [
      {
        ...providers.anthropic,
        modelId: 'claude-3-5-haiku-20241022',
        getCost: ({ inputTokens, outputTokens }) =>
          (inputTokens / 1000000) * 0.8 + (outputTokens / 1000000) * 4,
      },
    ],
    contextWindow: 200000,
    priceIndicator: 'low',
  },
};
