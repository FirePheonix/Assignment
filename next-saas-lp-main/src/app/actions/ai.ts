'use server';

import { cookies } from 'next/headers';
import { generateImage, editImageWithReferences } from '@/lib/api/image-generation';

export const generateImageAction = async (params: {
  prompt: string;
  modelId: string;
  instructions?: string;
  projectId: string;
  nodeId: string;
  size?: string;
  authToken?: string;
}): Promise<
  | {
      nodeData: {
        generated: { url: string; type: string };
        updatedAt: string;
      };
    }
  | {
      error: string;
    }
> => {
  try {
    console.log('🎨 SERVER: Generating image with:', params);
    
    // Get cookies from Next.js request to forward to Django
    const cookieStore = await cookies();
    const cookieHeader = cookieStore.toString();
    console.log('🍪 Forwarding cookies to Django:', cookieHeader ? 'present' : 'none');
    
    // Combine prompt and instructions
    const fullPrompt = params.instructions 
      ? `${params.instructions}\n\n${params.prompt}`
      : params.prompt;
    
    // Call Django backend API
    const response = await generateImage({
      prompt: fullPrompt,
      modelId: params.modelId,
      size: params.size || 'auto',
      quality: 'auto',
      background: 'auto',
      output_format: 'png',
    }, cookieHeader, params.authToken);
    
    if (!response.success || !response.image) {
      throw new Error(response.error || 'Failed to generate image');
    }
    
    return {
      nodeData: {
        generated: {
          url: response.image, // This is now a data URL with base64
          type: `image/${response.format || 'png'}`,
        },
        updatedAt: new Date().toISOString(),
      },
    };
  } catch (error) {
    console.error('Image generation error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const editImageAction = async (params: {
  images: Array<{ url: string; type: string }>;
  prompt?: string;
  nodeId: string;
  projectId: string;
  modelId: string;
  size?: string;
  authToken?: string;
}): Promise<
  | {
      nodeData: {
        generated: { url: string; type: string };
        updatedAt: string;
      };
    }
  | {
      error: string;
    }
> => {
  try {
    console.log('✏️ SERVER: Editing/Generating image with references:', {
      ...params,
      imageCount: params.images.length,
      imageUrls: params.images.map(img => img.url.substring(0, 50) + '...'),
    });
    
    // Get cookies from Next.js request to forward to Django
    const cookieStore = await cookies();
    const cookieHeader = cookieStore.toString();
    console.log('🍪 Forwarding cookies to Django:', cookieHeader ? 'present' : 'none');
    
    // Call Django backend API with multiple image references
    const response = await editImageWithReferences({
      images: params.images,
      prompt: params.prompt || 'Generate a new image using these references',
      size: params.size || 'auto',
      quality: 'high',
      background: 'auto',
      output_format: 'png',
    }, cookieHeader, params.authToken);
    
    if (!response.success || !response.image) {
      throw new Error(response.error || 'Failed to edit image');
    }
    
    return {
      nodeData: {
        generated: {
          url: response.image, // This is now a data URL with base64
          type: `image/${response.format || 'png'}`,
        },
        updatedAt: new Date().toISOString(),
      },
    };
  } catch (error) {
    console.error('Image editing error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const generateTextAction = async (params: {
  prompt: string;
  model: string;
  systemPrompt?: string;
}): Promise<
  | {
      success: true;
      text: string;
      cost: number;
    }
  | {
      error: string;
    }
> => {
  try {
    // TODO: Replace with actual AI SDK call
    console.log('Generating text with:', params);

    // Mock response
    return {
      success: true,
      text: 'This is generated text from ' + params.model,
      cost: 0.001,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const transcribeAudioAction = async (params: {
  audioUrl: string;
  model: string;
}): Promise<
  | {
      success: true;
      text: string;
      cost: number;
    }
  | {
      error: string;
    }
> => {
  try {
    console.log('Transcribing audio with:', params);
    return {
      success: true,
      text: 'Transcribed text from audio',
      cost: 0.006,
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const generateSpeechAction = async (params: {
  text: string;
  voice?: string;
  modelId: string;
  nodeId: string;
  projectId: string;
  instructions?: string;
}): Promise<
  | {
      success: true;
      audioUrl: string;
      cost: number;
      nodeData: {
        generated?: {
          url: string;
        };
        updatedAt?: number;
      };
    }
  | {
      error: string;
    }
> => {
  try {
    console.log('Generating speech with:', params);
    
    // Note: This is a placeholder that will be replaced by direct client-side API call
    // The audio generation requires authentication cookies which are only available client-side
    // This action is kept for compatibility but should be called from the client
    throw new Error('Audio generation must be called from client-side component');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const getTweetData = async (tweetUrl: string): Promise<
  | {
      success: true;
      content: string;
      author: string;
    }
  | {
      error: string;
    }
> => {
  try {
    console.log('Fetching tweet data:', tweetUrl);
    return {
      success: true,
      content: 'Sample tweet content',
      author: '@username',
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};

export const generateVideoAction = async (params: {
  prompt: string;
  modelId: string;
  referenceMedia?: Array<{ url: string; type: string }>;
  projectId: string;
  nodeId: string;
  size?: string;
  seconds?: number;
}): Promise<
  | {
      nodeData: {
        generated: { url: string; type: string; videoId?: string };
        updatedAt: string;
      };
    }
  | {
      error: string;
    }
> => {
  try {
    console.log('🎬 SERVER: Generating video with:', {
      ...params,
      referenceMediaCount: params.referenceMedia?.length || 0,
      referenceMediaTypes: params.referenceMedia?.map(m => m.type) || [],
    });

    const { generateVideo, generateVideoWithReference, pollVideoStatus, downloadVideo } = await import('@/lib/api/video-generation');
    
    // Get cookies for Django authentication
    const cookieStore = await cookies();
    const cookieHeader = cookieStore.toString();

    // Check model type
    const isSoraModel = params.modelId === 'sora-2' || params.modelId === 'sora-2-pro';
    const isVeoModel = params.modelId === 'veo3' || params.modelId === 'veo3_fast';
    const isKlingModel = params.modelId === 'kling-v2.1';
    
    // Check if we have reference images
    const imageReferences = params.referenceMedia?.filter(m => m.type.startsWith('image/'));
    
    // Kling requires reference image (image-to-video only)
    if (isKlingModel && (!imageReferences || imageReferences.length === 0)) {
      return {
        error: 'Kling AI requires a reference image for video generation. Please add an image to the video node.'
      };
    }
    
    if (!isSoraModel && !isVeoModel && !isKlingModel) {
      // Unsupported model - return dummy video
      console.log(`⚠️ Unsupported model ${params.modelId}, returning dummy video`);
      const videoUrl = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4';
      return {
        nodeData: {
          generated: {
            url: videoUrl,
            type: 'video/mp4',
          },
          updatedAt: new Date().toISOString(),
        },
      };
    }

    // Video generation (Sora, Veo, or Kling)
    let result;
    let videoIdOrTaskId: string;
    
    if (imageReferences && imageReferences.length > 0) {
      if (isKlingModel) {
        // Kling: Requires image-to-video with Cloudinary upload
        console.log(`🎬 Uploading reference image to Cloudinary for Kling...`);
        
        const { uploadImageToCloudinary } = await import('@/lib/api/upload');
        const imageUrl = await uploadImageToCloudinary(imageReferences[0].url, cookieHeader);
        
        console.log(`✅ Cloudinary URL: ${imageUrl}`);
        console.log(`🎬 Creating Kling video from image`);
        
        // Generate via Django Kling endpoint
        const response = await fetch(`${process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000'}/api/ai/kling/generate/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(cookieHeader && { Cookie: cookieHeader }),
          },
          body: JSON.stringify({
            image_url: imageUrl,
            prompt: params.prompt,
            duration: params.seconds || 5,
            cfg_scale: 0.5,
          }),
        });
        
        if (!response.ok) {
          throw new Error(`Kling generation failed: ${response.statusText}`);
        }
        
        result = await response.json();
        videoIdOrTaskId = result.generation_id;
        
        console.log(`🎬 Kling task created: ${videoIdOrTaskId}`);
        
        // Poll for completion
        let lastLoggedStatus = '';
        const startTime = Date.now();
        const maxWaitTime = 1200000; // 20 minutes
        
        while (Date.now() - startTime < maxWaitTime) {
          const statusResponse = await fetch(
            `${process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000'}/api/ai/kling/status/${encodeURIComponent(videoIdOrTaskId)}/`,
            {
              headers: cookieHeader ? { Cookie: cookieHeader } : {},
            }
          );
          
          const statusData = await statusResponse.json();
          const status = statusData.status;
          
          if (status !== lastLoggedStatus) {
            console.log(`🎬 Kling status: ${status}`);
            lastLoggedStatus = status;
          }
          
          if (status === 'completed') {
            const videoUrl = statusData.video_url;
            console.log(`🎬 Kling video ready: ${videoUrl}`);
            
            return {
              nodeData: {
                generated: {
                  url: videoUrl,
                  type: 'video/mp4',
                  videoId: videoIdOrTaskId,
                },
                updatedAt: new Date().toISOString(),
              },
            };
          } else if (status === 'error') {
            throw new Error(statusData.error || 'Kling generation failed');
          }
          
          await new Promise(resolve => setTimeout(resolve, 10000)); // Poll every 10s
        }
        
        throw new Error('Kling video generation timed out');
        
      } else if (isVeoModel) {
        // Veo: Upload images to get public URLs, then pass to API
        console.log(`🎬 Uploading ${imageReferences.length} reference image(s) for Veo...`);
        
        const { uploadImageViaDjango } = await import('@/lib/api/upload');
        
        const imageUrls: string[] = [];
        for (const imageRef of imageReferences.slice(0, 3)) { // Veo supports max 3 images
          try {
            const publicUrl = await uploadImageViaDjango(imageRef.url, cookieHeader);
            imageUrls.push(publicUrl);
            console.log(`✅ Uploaded: ${publicUrl}`);
          } catch (error) {
            console.error(`❌ Failed to upload image:`, error);
            // Continue without this image
          }
        }
        
        // Generate with or without images
        const generationType = imageUrls.length > 0 
          ? (imageUrls.length === 1 ? 'FIRST_AND_LAST_FRAMES_2_VIDEO' : 'REFERENCE_2_VIDEO')
          : 'TEXT_2_VIDEO';
        
        console.log(`🎬 Creating Veo video (${generationType}, ${imageUrls.length} images)`);
        
        result = await generateVideo({
          prompt: params.prompt,
          model: params.modelId as any,
          aspectRatio: params.size?.includes('1920') ? '16:9' : '9:16',
          imageUrls: imageUrls.length > 0 ? imageUrls : undefined,
          generationType,
          cookieHeader,
        });
      } else {
        // Sora: Direct file upload support
        const referenceUrl = imageReferences[0].url;
        
        console.log(`🎬 Using image reference for Sora: ${referenceUrl.substring(0, 100)}...`);
        
        if (referenceUrl.startsWith('data:')) {
          const response = await fetch(referenceUrl);
          const blob = await response.blob();
          const referenceFile = new File([blob], 'reference.png', { type: blob.type });
          
          console.log(`🎬 Creating Sora video with reference image (${Math.round(blob.size / 1024)}KB)`);
          
          result = await generateVideoWithReference({
            prompt: params.prompt,
            model: params.modelId as any,
            inputReference: referenceFile,
            size: params.size || '1280x720',
            seconds: params.seconds || 8,
            cookieHeader,
          });
        } else {
          throw new Error('Reference image must be a data URL (base64)');
        }
      }
    } else {
      // Basic text-to-video
      console.log(`🎬 Creating ${params.modelId} video without reference (text-to-video)`);
      
      result = await generateVideo({
        prompt: params.prompt,
        model: params.modelId as any,
        size: params.size || '1280x720',
        seconds: params.seconds || 8,
        aspectRatio: isVeoModel ? (params.size?.includes('1920') ? '16:9' : '9:16') : undefined,
        cookieHeader,
      });
    }
    
    // Get video/task ID based on model type
    videoIdOrTaskId = isVeoModel ? (result as any).task_id : (result as any).video_id;
    console.log(`🎬 Video job created: ${videoIdOrTaskId} (${params.modelId})`);

    // Poll for completion with progress logging
    console.log(`🎬 Polling status for ${params.modelId} video ${videoIdOrTaskId}...`);
    
    let lastLoggedProgress = 0;
    const finalStatus = await pollVideoStatus(videoIdOrTaskId, params.modelId, cookieHeader, {
      maxAttempts: 120,
      intervalMs: 2000,
      onProgress: (progress, status) => {
        // Log every 10% increment to avoid spam
        if (progress - lastLoggedProgress >= 10 || progress === 100) {
          console.log(`🎬 Video generation: ${progress}% (${status})`);
          lastLoggedProgress = progress;
        }
      },
    });

    if (finalStatus.status === 'failed') {
      throw new Error(finalStatus.error?.message || 'Video generation failed');
    }

    console.log(`🎬 Video ${videoIdOrTaskId} completed!`);

    // For Veo, return the video URL directly
    if (isVeoModel) {
      const videoUrl = finalStatus.video_urls?.[0] || finalStatus.origin_urls?.[0];
      if (!videoUrl) {
        throw new Error('No video URL returned from Veo');
      }
      
      console.log(`🎬 Veo video URL: ${videoUrl}`);
      
      return {
        nodeData: {
          generated: {
            url: videoUrl,
            type: 'video/mp4',
            videoId: videoIdOrTaskId,
          },
          updatedAt: new Date().toISOString(),
        },
      };
    }

    // For Sora, download the video
    console.log(`🎬 Downloading Sora video ${videoIdOrTaskId}...`);
    const downloadResult = await downloadVideo(videoIdOrTaskId, 'video', cookieHeader);
    
    // Convert base64 to data URL
    const videoDataUrl = `data:${downloadResult.content_type};base64,${downloadResult.content}`;
    
    return {
      nodeData: {
        generated: {
          url: videoDataUrl,
          type: downloadResult.content_type,
          videoId: videoIdOrTaskId,
        },
        updatedAt: new Date().toISOString(),
      },
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};
