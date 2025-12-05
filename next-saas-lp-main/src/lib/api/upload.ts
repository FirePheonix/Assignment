/**
 * Image Upload API Service
 * Handles uploading images to public storage for use with video generation APIs
 */

const DJANGO_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';

/**
 * Upload image via Django backend to public storage
 * Django handles the actual upload to S3/Cloudinary/etc.
 */
export async function uploadImageViaDjango(
  dataUrl: string,
  cookieHeader?: string
): Promise<string> {
  try {
    // Convert data URL to blob
    const response = await fetch(dataUrl);
    const blob = await response.blob();
    
    // Create form data with image file
    const formData = new FormData();
    formData.append('image', blob, `ref-${Date.now()}.png`);
    
    const headers: HeadersInit = {};
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }
    
    // Upload to Django backend
    const uploadResponse = await fetch(
      `${DJANGO_URL}/api/ai/upload-reference-image/`,
      {
        method: 'POST',
        headers,
        body: formData,
      }
    );
    
    if (!uploadResponse.ok) {
      const error = await uploadResponse.json().catch(() => ({}));
      throw new Error(error.error || `Upload failed: ${uploadResponse.statusText}`);
    }
    
    const result = await uploadResponse.json();
    return result.url;
  } catch (error) {
    console.error('Image upload error:', error);
    throw error;
  }
}

/**
 * Upload image directly to S3 using presigned URL
 * This bypasses Django and uploads directly from client to S3
 */
export async function uploadImageToS3(
  dataUrl: string,
  cookieHeader?: string
): Promise<string> {
  try {
    // Convert data URL to blob
    const response = await fetch(dataUrl);
    const blob = await response.blob();
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }
    
    // Get presigned URL from Django backend
    const presignResponse = await fetch(
      `${DJANGO_URL}/api/upload/presigned-url/`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ 
          filename: `ref-${Date.now()}.png`,
          contentType: blob.type 
        }),
      }
    );
    
    if (!presignResponse.ok) {
      throw new Error(`Failed to get presigned URL: ${presignResponse.statusText}`);
    }
    
    const { uploadUrl, publicUrl } = await presignResponse.json();
    
    // Upload directly to S3
    await fetch(uploadUrl, {
      method: 'PUT',
      body: blob,
      headers: { 'Content-Type': blob.type }
    });
    
    return publicUrl;
  } catch (error) {
    console.error('S3 upload error:', error);
    throw error;
  }
}

/**
 * Upload image to Cloudinary via Django backend
 * Django handles the signed upload using server-side credentials
 */
export async function uploadImageToCloudinary(
  dataUrl: string,
  cookieHeader?: string
): Promise<string> {
  try {
    // Convert data URL to blob
    const response = await fetch(dataUrl);
    const blob = await response.blob();
    
    const formData = new FormData();
    formData.append('image', blob, `upload-${Date.now()}.png`);
    
    const headers: HeadersInit = {};
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }
    
    // Upload via Django backend (which uses Cloudinary)
    const uploadResponse = await fetch(
      `${DJANGO_URL}/api/ai/upload-to-cloudinary/`,
      {
        method: 'POST',
        headers,
        body: formData,
      }
    );
    
    if (!uploadResponse.ok) {
      const error = await uploadResponse.json().catch(() => ({}));
      throw new Error(error.error || `Cloudinary upload failed: ${uploadResponse.statusText}`);
    }
    
    const data = await uploadResponse.json();
    return data.url;
  } catch (error) {
    console.error('Cloudinary upload error:', error);
    throw error;
  }
}

/**
 * Upload multiple images and return array of public URLs
 * Uses Django backend by default
 */
export async function uploadMultipleImages(
  dataUrls: string[],
  cookieHeader?: string,
  method: 'django' | 's3' | 'cloudinary' = 'django'
): Promise<string[]> {
  const uploadFn = method === 'cloudinary' 
    ? uploadImageToCloudinary
    : method === 's3'
    ? (url: string) => uploadImageToS3(url, cookieHeader)
    : (url: string) => uploadImageViaDjango(url, cookieHeader);
  
  const uploadPromises = dataUrls.map(dataUrl => uploadFn(dataUrl));
  return Promise.all(uploadPromises);
}
