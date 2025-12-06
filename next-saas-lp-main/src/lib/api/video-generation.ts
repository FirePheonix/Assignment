/**
 * Video Generation API Service
 * Handles communication with Django backend for multi-model video generation
 * Supports: Sora 2 (OpenAI), Veo 3.1 (Kie AI)
 */

import type { VideoModel } from '../models/video';

const DJANGO_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';

interface VideoGenerationOptions {
  prompt: string;
  model: VideoModel;
  size?: string;
  seconds?: number;
  aspectRatio?: string; // For Veo: "16:9", "9:16", "Auto"
  imageUrls?: string[]; // For Veo image-to-video
  generationType?: 'TEXT_2_VIDEO' | 'FIRST_AND_LAST_FRAMES_2_VIDEO' | 'REFERENCE_2_VIDEO';
  cookieHeader?: string;
}

interface VideoReferenceOptions extends VideoGenerationOptions {
  inputReference: File;
  generationType?: 'TEXT_2_VIDEO' | 'FIRST_AND_LAST_FRAMES_2_VIDEO' | 'REFERENCE_2_VIDEO';
  imageUrls?: string[];
}

interface VideoStatusResponse {
  success: boolean;
  video_id?: string; // For Sora
  task_id?: string; // For Veo
  status: 'queued' | 'in_progress' | 'completed' | 'failed' | 'generating';
  success_flag?: number; // For Veo: 0=generating, 1=completed, 2/3=failed
  progress?: number;  // 0-100 percentage (Sora)
  model: string;
  size?: string;
  seconds?: number;
  created_at?: number;
  video_urls?: string[]; // For Veo completed videos
  origin_urls?: string[]; // For Veo original quality
  resolution?: string;
  error?: {
    message: string;
    code?: string | number;
  };
}

/**
 * Get auth token for API requests
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('authToken');
}

/**
 * Convert data URL (base64) to File object
 */
function dataUrlToFile(dataUrl: string, filename: string): File {
  const arr = dataUrl.split(',');
  const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/png';
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, { type: mime });
}

/**
 * Generate video from text prompt - supports both Sora and Veo models
 */
export async function generateVideo(options: VideoGenerationOptions) {
  const { 
    prompt, 
    model, 
    size = '1280x720', 
    seconds = 8, 
    aspectRatio = '9:16', 
    imageUrls,
    generationType,
    cookieHeader 
  } = options;

  const formData = new FormData();
  formData.append('prompt', prompt);
  formData.append('model', model);
  
  // For Veo models, use aspect_ratio; for Sora, use size
  if (model.startsWith('veo')) {
    formData.append('aspect_ratio', aspectRatio);
    
    // Add image URLs if provided
    if (imageUrls && imageUrls.length > 0) {
      imageUrls.forEach(url => formData.append('image_urls', url));
      
      // Auto-determine generation type if not specified
      const genType = generationType || (imageUrls.length === 1 
        ? 'FIRST_AND_LAST_FRAMES_2_VIDEO' 
        : 'REFERENCE_2_VIDEO');
      formData.append('generation_type', genType);
    } else {
      formData.append('generation_type', generationType || 'TEXT_2_VIDEO');
    }
  } else {
    formData.append('size', size);
    formData.append('seconds', seconds.toString());
  }

  const authToken = getAuthToken();
  const headers: HeadersInit = {
    ...(authToken && { 'Authorization': `Token ${authToken}` }),
  };

  // Use unified endpoint for multi-model support
  const endpoint = model.startsWith('veo') 
    ? `${DJANGO_URL}/api/ai/generate-video/`
    : `${DJANGO_URL}/api/ai/sora/create/`;

  const response = await fetch(endpoint, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error('❌ Django error:', errorData);
    throw new Error(errorData.error || `Failed to generate video: ${response.statusText}`);
  }

  const result = await response.json();
  console.log(`✅ ${model} video job created:`, result);
  return result;
}

/**
 * Generate video with image reference - supports both Sora and Veo models
 */
export async function generateVideoWithReference(options: VideoReferenceOptions) {
  const { 
    prompt, 
    model, 
    inputReference, 
    size = '1280x720', 
    seconds = 8, 
    aspectRatio = '9:16',
    generationType = 'REFERENCE_2_VIDEO',
    imageUrls = [],
    cookieHeader 
  } = options;

  const formData = new FormData();
  formData.append('prompt', prompt);
  formData.append('model', model);
  
  // For Veo models
  if (model.startsWith('veo')) {
    formData.append('aspect_ratio', aspectRatio);
    formData.append('generation_type', generationType);
    
    // If imageUrls provided, use them; otherwise upload inputReference
    if (imageUrls.length > 0) {
      imageUrls.forEach(url => formData.append('image_urls', url));
    }
  } else {
    formData.append('size', size);
    formData.append('seconds', seconds.toString());
  }
  
  // Handle File (should already be a File object from server action)
  formData.append('input_reference', inputReference);

  const authToken = getAuthToken();
  const headers: HeadersInit = {
    ...(authToken && { 'Authorization': `Token ${authToken}` }),
  };

  // Use unified endpoint for multi-model support
  const endpoint = model.startsWith('veo')
    ? `${DJANGO_URL}/api/ai/generate-video/`
    : `${DJANGO_URL}/api/ai/sora/create-with-reference/`;

  const response = await fetch(endpoint, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error('❌ Django error (with reference):', errorData);
    throw new Error(errorData.error || `Failed to generate video with reference: ${response.statusText}`);
  }

  const result = await response.json();
  console.log(`✅ ${model} video job created with reference:`, result);
  return result;
}



/**
 * Get video generation status (for polling) - supports both Sora and Veo
 */
export async function getVideoStatus(
  videoId: string,
  model?: string
): Promise<VideoStatusResponse> {
  const authToken = getAuthToken();
  const headers: HeadersInit = {
    ...(authToken && { 'Authorization': `Token ${authToken}` }),
  };

  // Determine endpoint based on model
  const isVeo = model?.startsWith('veo');
  const endpoint = isVeo
    ? `${DJANGO_URL}/api/ai/veo/status/${videoId}/`
    : `${DJANGO_URL}/api/ai/sora/status/${videoId}/`;

  const response = await fetch(endpoint, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to get video status: ${response.statusText}`);
  }

  const data = await response.json();
  
  // Normalize Veo response to match interface
  if (isVeo) {
    return {
      ...data,
      video_id: data.task_id,
      status: data.success_flag === 1 ? 'completed' : 
              data.success_flag === 0 ? 'generating' : 'failed',
      model: model || 'veo3',
    };
  }

  return data;
}

/**
 * Download completed video content
 */
export async function downloadVideo(
  videoId: string,
  variant: 'video' | 'thumbnail' | 'spritesheet' = 'video'
) {
  const authToken = getAuthToken();
  const headers: HeadersInit = {
    ...(authToken && { 'Authorization': `Token ${authToken}` }),
  };

  const response = await fetch(
    `${DJANGO_URL}/api/ai/sora/download/${videoId}/?variant=${variant}`,
    {
      method: 'GET',
      headers,
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to download video: ${response.statusText}`);
  }

  return response.json();
}



/**
 * Poll video status until completion or failure - supports both Sora and Veo
 * Returns the final status response
 */
export async function pollVideoStatus(
  videoId: string,
  model?: string,
  options: {
    maxAttempts?: number;
    intervalMs?: number;
    onProgress?: (progress: number, status: string) => void;
  } = {}
): Promise<VideoStatusResponse> {
  const { maxAttempts = 120, intervalMs = 2000, onProgress } = options;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const status = await getVideoStatus(videoId, model);

    if (onProgress) {
      // Handle both Sora progress (0-100) and Veo success_flag (0/1/2/3)
      const progress = status.progress ?? (status.success_flag === 1 ? 100 : 50);
      onProgress(progress, status.status);
    }

    if (status.status === 'completed' || status.status === 'failed') {
      return status;
    }

    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }

  throw new Error('Video generation timed out');
}
