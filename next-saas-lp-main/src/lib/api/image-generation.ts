/**
 * Image Generation API Service
 * Connects to Django backend for AI image generation
 */

const DJANGO_BACKEND = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://localhost:8000';

/**
 * Extract CSRF token from cookie string
 */
function getCsrfToken(cookieHeader?: string): string | null {
  if (!cookieHeader) return null;
  const match = cookieHeader.match(/csrftoken=([^;]+)/);
  return match ? match[1] : null;
}

export interface GenerateImageParams {
  prompt: string;
  modelId: string;
  size?: string;
  quality?: string;
  background?: string;
  output_format?: string;
  output_compression?: number;
  moderation?: string;
  n?: number;
}

export interface EditImageParams {
  images: Array<{ url: string; type: string }>;
  prompt?: string;
  size?: string;
  quality?: string;
  background?: string;
  output_format?: string;
  mask?: File;
}

export interface ImageGenerationResponse {
  success: boolean;
  image?: string; // base64
  images?: string[]; // base64 array
  format?: string;
  size?: string;
  quality?: string;
  error?: string;
}

/**
 * Convert base64 string to data URL
 */
function base64ToDataUrl(base64: string, format: string = 'png'): string {
  return `data:image/${format};base64,${base64}`;
}

/**
 * Convert data URL to Blob
 */
function dataUrlToBlob(dataUrl: string): Blob {
  const parts = dataUrl.split(',');
  const mimeMatch = parts[0].match(/:(.*?);/);
  const mime = mimeMatch ? mimeMatch[1] : 'image/png';
  const bstr = atob(parts[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new Blob([u8arr], { type: mime });
}

/**
 * Convert data URL to File object
 */
function dataUrlToFile(dataUrl: string, filename: string = 'image.png'): File {
  const blob = dataUrlToBlob(dataUrl);
  return new File([blob], filename, { type: blob.type });
}

/**
 * Generate image from text prompt using OpenAI
 * Uses GPT Image model for advanced generation
 */
export async function generateImage(params: GenerateImageParams, cookieHeader?: string, authToken?: string): Promise<ImageGenerationResponse> {
  try {
    const formData = new FormData();
    formData.append('prompt', params.prompt);
    
    // Add model parameter
    formData.append('model', params.modelId);
    
    if (params.size) formData.append('size', params.size);
    if (params.quality) formData.append('quality', params.quality);
    if (params.background) formData.append('background', params.background);
    if (params.output_format) formData.append('output_format', params.output_format);
    if (params.output_compression) formData.append('output_compression', params.output_compression.toString());
    if (params.moderation) formData.append('moderation', params.moderation);
    if (params.n) formData.append('n', params.n.toString());

    // Route to correct endpoint based on model
    const endpoint = params.modelId.startsWith('gpt-image')
      ? `${DJANGO_BACKEND}/api/ai/gpt-image/advanced/`
      : `${DJANGO_BACKEND}/api/ai/generate-image-openai/`;

    console.log('📤 Sending request to:', endpoint, 'with model:', params.modelId);

    const headers: HeadersInit = {};
    if (authToken) {
      headers['Authorization'] = `Token ${authToken}`;
      console.log('🔐 Using auth token');
    }
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
      const csrfToken = getCsrfToken(cookieHeader);
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
        console.log('🔐 Using CSRF token:', csrfToken);
      }
      console.log('🍪 Using cookie header');
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers,
      body: formData,
      credentials: 'include',
    });
    
    console.log('📥 Response:', response.status, response.statusText);

    if (!response.ok) {
      let errorMessage = 'Failed to generate image';
      try {
        const error = await response.json();
        console.error('❌ Django error response:', error);
        errorMessage = error.detail || error.error || errorMessage;
        
        // If authentication error, provide helpful message
        if (response.status === 401 || response.status === 403) {
          errorMessage = `Authentication required: ${errorMessage}. Please login to Django at http://localhost:8000/admin/`;
        }
      } catch (e) {
        const textError = await response.text();
        console.error('❌ Django error (text):', textError);
        errorMessage = textError || errorMessage;
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    
    // Convert base64 to data URL
    if (data.images && data.images.length > 0) {
      return {
        success: true,
        image: base64ToDataUrl(data.images[0], data.format),
        images: data.images.map((img: string) => base64ToDataUrl(img, data.format)),
        format: data.format,
        size: data.size,
        quality: data.quality,
      };
    }

    throw new Error('No image returned from API');
  } catch (error) {
    console.error('Image generation error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Edit images with multiple reference images
 * Automatically selects the right endpoint based on number of images
 */
export async function editImageWithReferences(params: EditImageParams, cookieHeader?: string, authToken?: string): Promise<ImageGenerationResponse> {
  try {
    const formData = new FormData();
    
    if (params.prompt) {
      formData.append('prompt', params.prompt);
    }

    // Add all reference images (now as data URLs)
    for (let i = 0; i < params.images.length; i++) {
      const imageData = params.images[i];
      
      // Convert data URL to File
      const file = dataUrlToFile(imageData.url, `image_${i}.png`);
      formData.append(`image_${i}`, file);
    }

    if (params.size) formData.append('size', params.size);
    if (params.quality) formData.append('quality', params.quality);
    if (params.background) formData.append('background', params.background);
    if (params.output_format) formData.append('output_format', params.output_format);

    // Choose endpoint based on scenario
    let endpoint: string;
    
    if (params.mask) {
      // Inpainting with mask
      endpoint = `${DJANGO_BACKEND}/api/ai/gpt-image/inpainting/`;
      formData.append('mask', params.mask);
    } else if (params.images.length > 1) {
      // Multiple reference images
      endpoint = `${DJANGO_BACKEND}/api/ai/gpt-image/multi-reference/`;
    } else {
      // Single image editing (use high-fidelity endpoint for quality)
      endpoint = `${DJANGO_BACKEND}/api/ai/gpt-image/high-fidelity/`;
    }

    console.log('🎨 Using endpoint:', endpoint, {
      imageCount: params.images.length,
      hasMask: !!params.mask,
      prompt: params.prompt,
    });

    console.log('🔑 Making fetch request:', {
      url: endpoint,
      method: 'POST',
      hasCookies: !!cookieHeader,
      formDataKeys: Array.from(formData.keys()),
    });

    const headers: HeadersInit = {};
    if (authToken) {
      headers['Authorization'] = `Token ${authToken}`;
      console.log('🔐 Using auth token for edit');
    }
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
      const csrfToken = getCsrfToken(cookieHeader);
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
        console.log('🔐 Using CSRF token for edit');
      }
      console.log('🍪 Using cookie header for edit');
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers,
      body: formData,
      credentials: 'include',
    });

    console.log('📡 Response status:', response.status, response.statusText);
    console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      let errorMessage = 'Failed to edit image';
      try {
        const error = await response.json();
        console.error('❌ Django error response:', error);
        errorMessage = error.detail || error.error || errorMessage;
        
        // If authentication error, provide helpful message
        if (response.status === 401 || response.status === 403) {
          errorMessage = `Authentication required: ${errorMessage}. Please login to Django at http://localhost:8000/admin/`;
        }
      } catch (e) {
        const textError = await response.text();
        console.error('❌ Django error (text):', textError);
        errorMessage = textError || errorMessage;
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    
    // Check if image is already a URL (Cloudinary) or base64
    if (data.image) {
      const isUrl = data.image.startsWith('http://') || data.image.startsWith('https://');
      
      return {
        success: true,
        image: isUrl ? data.image : base64ToDataUrl(data.image, data.format || 'png'),
        format: data.format,
        size: data.size,
        quality: data.quality,
      };
    }

    throw new Error('No image returned from API');
  } catch (error) {
    console.error('Image editing error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Generate image with transparent background
 */
export async function generateTransparentImage(params: {
  prompt: string;
  size?: string;
  quality?: string;
}): Promise<ImageGenerationResponse> {
  try {
    const formData = new FormData();
    formData.append('prompt', params.prompt);
    if (params.size) formData.append('size', params.size);
    if (params.quality) formData.append('quality', params.quality);

    const response = await fetch(`${DJANGO_BACKEND}/api/ai/gpt-image/transparent/`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to generate transparent image');
    }

    const data = await response.json();
    
    return {
      success: true,
      image: base64ToDataUrl(data.image, data.format),
      format: data.format,
      size: data.size,
      quality: data.quality,
    };
  } catch (error) {
    console.error('Transparent image generation error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Stream image generation with partial updates
 */
export async function streamImageGeneration(params: {
  prompt: string;
  size?: string;
  quality?: string;
  partial_images?: number;
  onPartial?: (index: number, imageBase64: string) => void;
  onComplete?: (imageBase64: string) => void;
  onError?: (error: string) => void;
}): Promise<void> {
  try {
    const formData = new FormData();
    formData.append('prompt', params.prompt);
    if (params.size) formData.append('size', params.size);
    if (params.quality) formData.append('quality', params.quality);
    if (params.partial_images) formData.append('partial_images', params.partial_images.toString());

    const response = await fetch(`${DJANGO_BACKEND}/api/ai/gpt-image/stream/`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to start streaming');
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No reader available');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      
      // Process complete SSE messages
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonData = line.substring(6);
          try {
            const event = JSON.parse(jsonData);
            
            if (event.type === 'partial' && params.onPartial) {
              params.onPartial(event.index, base64ToDataUrl(event.image, 'png'));
            } else if (event.type === 'complete' && params.onComplete) {
              params.onComplete(base64ToDataUrl(event.image, 'png'));
            } else if (event.type === 'error' && params.onError) {
              params.onError(event.error);
            }
          } catch (e) {
            console.error('Error parsing SSE event:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('Stream error:', error);
    if (params.onError) {
      params.onError(error instanceof Error ? error.message : 'Unknown error');
    }
  }
}
