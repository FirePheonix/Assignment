import type { TersaModel, TersaProvider } from '@/lib/providers';
import { providers } from '@/lib/providers';

export type ImageSize = `${number}x${number}`;

type TersaImageModel = TersaModel & {
  providers: (TersaProvider & {
    modelId: string;
    getCost: (props?: {
      textInput?: number;
      imageInput?: number;
      output?: number;
      size?: string;
    }) => number;
  })[];
  sizes?: ImageSize[];
  supportsEdit?: boolean;
  providerOptions?: Record<string, Record<string, string>>;
};

export const imageModels: Record<string, TersaImageModel> = {
  'gpt-image-1': {
    label: 'GPT Image 1',
    chef: providers.openai,
    providers: [
      {
        ...providers.openai,
        modelId: 'gpt-image-1',
        getCost: (props) => {
          // GPT Image 1 uses similar pricing to DALL-E 3
          if (!props?.size) throw new Error('Size is required');
          if (props.size === '1024x1024') return 0.08;
          if (props.size === '1024x1792' || props.size === '1792x1024') return 0.12;
          if (props.size === '1536x1024' || props.size === '1024x1536') return 0.10;
          throw new Error('Size is not supported');
        },
      },
    ],
    sizes: ['1024x1024', '1024x1536', '1536x1024', '1024x1792', '1792x1024'],
    supportsEdit: true,
    providerOptions: {
      openai: {
        quality: 'high',
      },
    },
    default: true,
  },
  'dall-e-3': {
    label: 'DALL-E 3',
    chef: providers.openai,
    providers: [
      {
        ...providers.openai,
        modelId: 'dall-e-3',
        getCost: (props) => {
          if (!props?.size) throw new Error('Size is required');
          if (props.size === '1024x1024') return 0.08;
          if (props.size === '1024x1792' || props.size === '1792x1024') return 0.12;
          throw new Error('Size is not supported');
        },
      },
    ],
    sizes: ['1024x1024', '1024x1792', '1792x1024'],
    providerOptions: {
      openai: {
        quality: 'hd',
      },
    },
  },
  'dall-e-2': {
    label: 'DALL-E 2',
    chef: providers.openai,
    providers: [
      {
        ...providers.openai,
        modelId: 'dall-e-2',
        getCost: (props) => {
          if (!props?.size) throw new Error('Size is required');
          if (props.size === '1024x1024') return 0.02;
          if (props.size === '512x512') return 0.018;
          if (props.size === '256x256') return 0.016;
          throw new Error('Size is not supported');
        },
      },
    ],
    sizes: ['1024x1024', '512x512', '256x256'],
    priceIndicator: 'low',
  },
};
