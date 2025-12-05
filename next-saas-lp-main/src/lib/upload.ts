

/**
 * Upload file to Cloudinary via Django backend
 * Returns permanent HTTPS URL that persists across workspace saves/loads
 */
export const uploadFile = async (
  file: File,
  folder: string = 'flow_generator/images'
): Promise<{ url: string; type: string }> => {
  const DJANGO_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';
  
  try {
    // Get auth token from localStorage
    const token = localStorage.getItem('auth_token');
    
    // Create form data
    const formData = new FormData();
    formData.append('image', file);
    formData.append('purpose', 'flow_generator_image');
    
    // Upload to Django backend (which uploads to Cloudinary)
    const response = await fetch(
      `${DJANGO_URL}/api/ai/upload-to-cloudinary/`,
      {
        method: 'POST',
        headers: {
          ...(token && { 'Authorization': `Token ${token}` }),
        },
        body: formData,
      }
    );
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Upload failed' }));
      throw new Error(error.error || `Upload failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    console.log('✅ File uploaded to Cloudinary:', data.url);
    
    return {
      url: data.url, // Permanent Cloudinary URL
      type: file.type,
    };
  } catch (error) {
    console.error('❌ File upload failed:', error);
    // Fallback to blob URL (temporary, but at least works for current session)
    const blobUrl = URL.createObjectURL(file);
    console.warn('⚠️ Using temporary blob URL as fallback:', blobUrl);
    return {
      url: blobUrl,
      type: file.type,
    };
  }
};
