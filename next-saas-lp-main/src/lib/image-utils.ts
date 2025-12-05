/**
 * Image utility functions for handling blob URLs and base64 conversions
 */

/**
 * Convert a blob URL or data URL to base64 data URL
 * Works in browser context only
 */
export async function urlToBase64DataUrl(url: string): Promise<string> {
  // If already a data URL, return as-is
  if (url.startsWith('data:')) {
    return url;
  }

  // Convert blob URL or regular URL to base64 data URL
  return new Promise((resolve, reject) => {
    fetch(url)
      .then(response => response.blob())
      .then(blob => {
        const reader = new FileReader();
        reader.onloadend = () => {
          if (typeof reader.result === 'string') {
            resolve(reader.result);
          } else {
            reject(new Error('Failed to convert blob to data URL'));
          }
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      })
      .catch(reject);
  });
}

/**
 * Convert multiple image URLs to base64 data URLs
 */
export async function urlsToBase64DataUrls(
  images: Array<{ url: string; type: string }>
): Promise<Array<{ url: string; type: string }>> {
  const convertedImages = await Promise.all(
    images.map(async (img) => {
      try {
        const base64Url = await urlToBase64DataUrl(img.url);
        return { url: base64Url, type: img.type };
      } catch (error) {
        console.error('Error converting image to base64:', error);
        throw error;
      }
    })
  );
  
  return convertedImages;
}

/**
 * Get image dimensions from a URL
 */
export async function getImageDimensions(url: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.width, height: img.height });
    };
    img.onerror = reject;
    img.src = url;
  });
}
