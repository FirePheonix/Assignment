/**
 * Mock media API for development when Django backend is not available
 */

import { MediaItem, MediaQuota, MediaResponse } from '@/hooks/use-media-gallery';

// Mock media data
const mockMediaItems: MediaItem[] = [
  {
    id: 1,
    url: 'https://picsum.photos/1920/1080?random=1',
    thumbnail_url: 'https://picsum.photos/200/200?random=1',
    original_filename: 'sample_avatar.jpg',
    format: 'jpg',
    width: 1920,
    height: 1080,
    file_size: 245760,
    purpose: 'avatar',
    usage_count: 5,
    created_at: '2024-11-30T10:30:00Z',
    storage_type: 'cloudinary',
    public_id: 'sample_avatar'
  },
  {
    id: 2,
    url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
    thumbnail_url: 'https://picsum.photos/200/200?random=2',
    original_filename: 'funny_dog.mp4',
    format: 'mp4',
    width: 1280,
    height: 720,
    file_size: 5242880,
    purpose: 'content',
    usage_count: 12,
    created_at: '2024-11-29T15:45:00Z',
    storage_type: 'cloudinary',
    public_id: 'funny_dog'
  },
  {
    id: 3,
    url: 'https://picsum.photos/800/1200?random=3',
    thumbnail_url: 'https://picsum.photos/200/200?random=3',
    original_filename: 'portrait.jpg',
    format: 'jpg',
    width: 800,
    height: 1200,
    file_size: 156432,
    purpose: 'profile',
    usage_count: 3,
    created_at: '2024-11-29T09:20:00Z',
    storage_type: 'cloudinary',
    public_id: 'portrait'
  },
  {
    id: 4,
    url: 'https://picsum.photos/1600/900?random=4',
    thumbnail_url: 'https://picsum.photos/200/200?random=4',
    original_filename: 'basketball_action.jpg',
    format: 'jpg',
    width: 1600,
    height: 900,
    file_size: 312566,
    purpose: 'content',
    usage_count: 8,
    created_at: '2024-11-28T14:15:00Z',
    storage_type: 'cloudinary',
    public_id: 'basketball_action'
  },
  {
    id: 5,
    url: 'https://picsum.photos/900/900?random=5',
    thumbnail_url: 'https://picsum.photos/200/200?random=5',
    original_filename: 'professional_headshot.jpg',
    format: 'jpg',
    width: 900,
    height: 900,
    file_size: 198234,
    purpose: 'avatar',
    usage_count: 15,
    created_at: '2024-11-28T11:30:00Z',
    storage_type: 'cloudinary',
    public_id: 'professional_headshot'
  },
  {
    id: 6,
    url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
    thumbnail_url: 'https://picsum.photos/200/200?random=6',
    original_filename: 'nature_turtle.mp4',
    format: 'mp4',
    width: 1920,
    height: 1080,
    file_size: 8388608,
    purpose: 'content',
    usage_count: 22,
    created_at: '2024-11-27T16:45:00Z',
    storage_type: 'cloudinary',
    public_id: 'nature_turtle'
  },
  {
    id: 7,
    url: 'https://picsum.photos/1400/933?random=7',
    thumbnail_url: 'https://picsum.photos/200/200?random=7',
    original_filename: 'mountain_bike.jpg',
    format: 'jpg',
    width: 1400,
    height: 933,
    file_size: 267890,
    purpose: 'content',
    usage_count: 6,
    created_at: '2024-11-27T12:20:00Z',
    storage_type: 'cloudinary',
    public_id: 'mountain_bike'
  },
  {
    id: 8,
    url: 'https://picsum.photos/1200/800?random=8',
    thumbnail_url: 'https://picsum.photos/200/200?random=8',
    original_filename: 'delicious_meal.jpg',
    format: 'jpg',
    width: 1200,
    height: 800,
    file_size: 234567,
    purpose: 'content',
    usage_count: 11,
    created_at: '2024-11-26T18:30:00Z',
    storage_type: 'cloudinary',
    public_id: 'delicious_meal'
  },
  {
    id: 9,
    url: 'https://www.soundjay.com/misc/sounds/bell-ringing-05.wav',
    original_filename: 'background_music.mp3',
    format: 'mp3',
    file_size: 4194304,
    purpose: 'audio',
    usage_count: 7,
    created_at: '2024-11-26T14:15:00Z',
    storage_type: 'cloudinary',
    public_id: 'background_music'
  },
  {
    id: 10,
    url: 'https://picsum.photos/1000/1500?random=10',
    thumbnail_url: 'https://picsum.photos/200/200?random=10',
    original_filename: 'morning_coffee.jpg',
    format: 'jpg',
    width: 1000,
    height: 1500,
    file_size: 189345,
    purpose: 'content',
    usage_count: 4,
    created_at: '2024-11-25T08:45:00Z',
    storage_type: 'cloudinary',
    public_id: 'morning_coffee'
  },
  {
    id: 11,
    url: 'https://picsum.photos/1600/1067?random=11',
    thumbnail_url: 'https://picsum.photos/200/200?random=11',
    original_filename: 'landscape_sunset.jpg',
    format: 'jpg',
    width: 1600,
    height: 1067,
    file_size: 345678,
    purpose: 'background',
    usage_count: 9,
    created_at: '2024-11-24T19:30:00Z',
    storage_type: 'cloudinary',
    public_id: 'landscape_sunset'
  },
  {
    id: 12,
    url: 'https://picsum.photos/1920/1280?random=12',
    thumbnail_url: 'https://picsum.photos/200/200?random=12',
    original_filename: 'city_skyline.jpg',
    format: 'jpg',
    width: 1920,
    height: 1280,
    file_size: 456789,
    purpose: 'background',
    usage_count: 13,
    created_at: '2024-11-24T10:15:00Z',
    storage_type: 'cloudinary',
    public_id: 'city_skyline'
  },
  {
    id: 13,
    url: 'https://picsum.photos/1200/1200?random=13',
    thumbnail_url: 'https://picsum.photos/200/200?random=13',
    original_filename: 'abstract_art.jpg',
    format: 'jpg',
    width: 1200,
    height: 1200,
    file_size: 298765,
    purpose: 'art',
    usage_count: 2,
    created_at: '2024-11-23T16:20:00Z',
    storage_type: 'cloudinary',
    public_id: 'abstract_art'
  },
  {
    id: 14,
    url: 'https://picsum.photos/1400/900?random=14',
    thumbnail_url: 'https://picsum.photos/200/200?random=14',
    original_filename: 'nature_flowers.jpg',
    format: 'jpg',
    width: 1400,
    height: 900,
    file_size: 276543,
    purpose: 'content',
    usage_count: 14,
    created_at: '2024-11-23T09:45:00Z',
    storage_type: 'cloudinary',
    public_id: 'nature_flowers'
  },
  {
    id: 15,
    url: 'https://file-examples.com/storage/fe1fef0b69faf8b381e0cf9/2017/11/file_example_WAV_1MG.wav',
    original_filename: 'notification_sound.wav',
    format: 'wav',
    file_size: 1048576,
    purpose: 'audio',
    usage_count: 18,
    created_at: '2024-11-22T13:30:00Z',
    storage_type: 'cloudinary',
    public_id: 'notification_sound'
  }
];

const mockQuota: MediaQuota = {
  cloudinary_used: 45.7 * 1024 * 1024, // 45.7 MB
  cloudinary_limit: 100 * 1024 * 1024, // 100 MB
  local_used: 12.3 * 1024 * 1024, // 12.3 MB
  local_limit: 50 * 1024 * 1024, // 50 MB
  total_files: 15,
  max_files: 1000,
  usage_percentage: 45.7
};

export async function mockFetchMedia(
  storageType: 'all' | 'local' | 'cloudinary' = 'all',
  limit: number = 100,
  offset: number = 0
): Promise<MediaResponse> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300));

  let filteredItems = [...mockMediaItems];

  if (storageType !== 'all') {
    filteredItems = filteredItems.filter(item => item.storage_type === storageType);
  }

  // Apply pagination
  const paginatedItems = filteredItems.slice(offset, offset + limit);

  return {
    success: true,
    local_uploads: storageType === 'cloudinary' ? [] : paginatedItems.filter(item => item.storage_type === 'local'),
    cloudinary_uploads: storageType === 'local' ? [] : paginatedItems.filter(item => item.storage_type === 'cloudinary'),
    quota: mockQuota,
    total_local: mockMediaItems.filter(item => item.storage_type === 'local').length,
    total_cloudinary: mockMediaItems.filter(item => item.storage_type === 'cloudinary').length
  };
}

export async function mockUploadMedia(file: File, purpose: string = 'other'): Promise<MediaItem> {
  // Simulate upload delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  const newId = Math.max(...mockMediaItems.map(item => item.id)) + 1;
  const fileExtension = file.name.split('.').pop()?.toLowerCase() || 'jpg';
  
  const newItem: MediaItem = {
    id: newId,
    url: URL.createObjectURL(file), // In real app, this would be the uploaded URL
    thumbnail_url: URL.createObjectURL(file),
    original_filename: file.name,
    format: fileExtension,
    width: 1200,
    height: 800,
    file_size: file.size,
    purpose,
    usage_count: 0,
    created_at: new Date().toISOString(),
    storage_type: 'cloudinary',
    public_id: `uploaded_${newId}`
  };

  // Add to mock data
  mockMediaItems.unshift(newItem);
  
  return newItem;
}

export async function mockDeleteMedia(mediaId: number): Promise<void> {
  // Simulate delete delay
  await new Promise(resolve => setTimeout(resolve, 500));

  const index = mockMediaItems.findIndex(item => item.id === mediaId);
  if (index !== -1) {
    mockMediaItems.splice(index, 1);
  }
}

// Check if Django backend is available
export async function isDjangoBackendAvailable(): Promise<boolean> {
  try {
    const API_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';
    
    // Try to fetch Django root endpoint first (should always work)
    const response = await fetch(`${API_URL}/`, {
      method: 'HEAD',
      // No credentials needed for health check
    });
    
    // If we get any response (200, 403, etc.), Django is running
    return response.status < 500;
  } catch (error) {
    console.log('Django backend not available:', error);
    return false;
  }
}