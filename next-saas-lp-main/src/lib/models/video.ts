import type { TersaModel } from '../providers';
import { providers } from '../providers';

export const videoModels = {
  'sora-2': {
    id: 'sora-2',
    label: 'Sora 2 (Fast)',
    chef: providers.openai,
    providers: [providers.openai],
    provider: 'openai',
    default: true,
    sizes: ['1280x720', '1920x1080', '1080x1920', '720x1280'],
    durations: [4, 8, 12, 16, 20],
    supportsReference: true,
    supportsRemix: true,
  },
  'sora-2-pro': {
    id: 'sora-2-pro',
    label: 'Sora 2 Pro (Quality)',
    chef: providers.openai,
    providers: [providers.openai],
    provider: 'openai',
    sizes: ['1280x720', '1920x1080', '1080x1920', '720x1280'],
    durations: [4, 8, 12, 16, 20],
    supportsReference: true,
    supportsRemix: true,
  },
  'veo3': {
    id: 'veo3',
    label: 'Veo 3 (Quality)',
    chef: providers.openai, // Using openai provider as placeholder
    providers: [providers.openai],
    provider: 'kieai',
    aspectRatios: ['16:9', '9:16', 'Auto'],
    supportsReference: true, // Supports imageUrls for image-to-video
    supportsRemix: false,
    generationTypes: ['TEXT_2_VIDEO', 'FIRST_AND_LAST_FRAMES_2_VIDEO', 'REFERENCE_2_VIDEO'],
  },
  'veo3_fast': {
    id: 'veo3_fast',
    label: 'Veo 3 Fast',
    chef: providers.openai, // Using openai provider as placeholder
    providers: [providers.openai],
    provider: 'kieai',
    aspectRatios: ['16:9', '9:16', 'Auto'],
    supportsReference: true, // Supports imageUrls for image-to-video
    supportsRemix: false,
    generationTypes: ['TEXT_2_VIDEO', 'FIRST_AND_LAST_FRAMES_2_VIDEO', 'REFERENCE_2_VIDEO'],
  },
  'kling-v2.1': {
    id: 'kling-v2.1',
    label: 'Kling AI v2.1',
    chef: providers.openai, // Using openai provider as placeholder
    providers: [providers.openai],
    provider: 'aiml',
    durations: [5, 10],
    supportsReference: true, // Image-to-video only
    supportsRemix: false,
  },
  'runway-gen3': {
    id: 'runway-gen3',
    label: 'Gen-3 Alpha',
    chef: providers.runway,
    providers: [providers.runway],
    provider: 'runway',
  },
  'luma-dream-machine': {
    id: 'luma-dream-machine',
    label: 'Dream Machine',
    chef: providers.luma,
    providers: [providers.luma],
    provider: 'luma',
  },
} as const;

export type VideoModel = keyof typeof videoModels;
