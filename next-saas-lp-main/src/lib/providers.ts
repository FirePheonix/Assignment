import * as Icons from './icons';

export type PriceBracket = 'lowest' | 'low' | 'high' | 'highest';

export type TersaProvider = {
  id: string;
  name: string;
  icon: any;
};

export const providers: Record<string, TersaProvider> = {
  openai: {
    id: 'openai',
    name: 'OpenAI',
    icon: Icons.OpenAiIcon,
  },
  anthropic: {
    id: 'anthropic',
    name: 'Anthropic',
    icon: Icons.AnthropicIcon,
  },
  google: {
    id: 'google',
    name: 'Google',
    icon: Icons.GoogleIcon,
  },
  meta: {
    id: 'meta',
    name: 'Meta',
    icon: Icons.MetaIcon,
  },
  xai: {
    id: 'xai',
    name: 'xAI',
    icon: Icons.XaiIcon,
  },
  groq: {
    id: 'groq',
    name: 'Groq',
    icon: Icons.GroqIcon,
  },
  mistral: {
    id: 'mistral',
    name: 'Mistral',
    icon: Icons.MistralIcon,
  },
  luma: {
    id: 'luma',
    name: 'Luma',
    icon: Icons.LumaIcon,
  },
  minimax: {
    id: 'minimax',
    name: 'Minimax',
    icon: Icons.MinimaxIcon,
  },
  cohere: {
    id: 'cohere',
    name: 'Cohere',
    icon: Icons.CohereIcon,
  },
  deepseek: {
    id: 'deepseek',
    name: 'DeepSeek',
    icon: Icons.DeepSeekIcon,
  },
  runway: {
    id: 'runway',
    name: 'Runway',
    icon: Icons.RunwayIcon,
  },
  together: {
    id: 'together',
    name: 'Together',
    icon: Icons.TogetherIcon,
  },
  replicate: {
    id: 'replicate',
    name: 'Replicate',
    icon: Icons.ReplicateIcon,
  },
  perplexity: {
    id: 'perplexity',
    name: 'Perplexity',
    icon: Icons.PerplexityIcon,
  },
  elevenlabs: {
    id: 'elevenlabs',
    name: 'ElevenLabs',
    icon: Icons.OpenAiIcon, // Reusing OpenAI icon for now
  },
};

export type TersaModel = {
  icon?: any;
  label: string;
  chef: TersaProvider;
  providers: TersaProvider[];
  legacy?: boolean;
  priceIndicator?: PriceBracket;
  disabled?: boolean;
  default?: boolean;
  voices?: string[];
};
