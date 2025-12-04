"""
Kling AI Video Generation Utilities
Handles video generation using AIML API's Kling AI models
"""

import requests
import time
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class KlingVideoGenerator:
    """
    Kling AI Video Generator using AIML API
    Supports image-to-video generation
    """
    
    BASE_URL = "https://api.aimlapi.com/v2"
    MODEL = "kling-video/v2.1/standard/image-to-video"
    
    def __init__(self):
        self.api_key = settings.AIML_API_KEY
        if not self.api_key:
            raise ValueError("AIML_API_KEY not configured in settings")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_video(
        self,
        image_url: str,
        prompt: str,
        duration: int = 5,
        cfg_scale: float = 0.5,
        negative_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a video generation task
        
        Args:
            image_url: Direct link to image or Base64-encoded local image
            prompt: Text description of the scene/action
            duration: Video length in seconds (5 or 10)
            cfg_scale: How closely to follow the prompt (0-1)
            negative_prompt: Elements to avoid in the video
        
        Returns:
            dict with 'id' (generation_id) and 'status'
        """
        url = f"{self.BASE_URL}/generate/video/kling/generation"
        
        payload = {
            "model": self.MODEL,
            "image_url": image_url,
            "prompt": prompt,
            "type": "image-to-video",
            "duration": duration,
            "cfg_scale": cfg_scale,
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        try:
            logger.info(f"Creating Kling video generation task with prompt: {prompt[:100]}")
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Kling task created: {result.get('id')}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Kling video generation failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_video_status(self, generation_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation task
        
        Args:
            generation_id: The ID returned from generate_video()
        
        Returns:
            dict with 'id', 'status', 'video' (if completed), 'error', 'meta'
            
        Status values:
            - queued: Task is waiting in queue
            - generating: Task is being processed
            - completed: Video is ready
            - error: Generation failed
        """
        url = f"{self.BASE_URL}/generate/video/kling/generation"
        params = {"generation_id": generation_id}
        
        try:
            response = requests.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            status = result.get('status')
            
            if status == 'completed':
                logger.info(f"Kling video {generation_id} completed")
            elif status == 'error':
                logger.error(f"Kling video {generation_id} failed: {result.get('error')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Kling video status: {str(e)}")
            raise
    
    def poll_until_complete(
        self,
        generation_id: str,
        max_attempts: int = 120,
        poll_interval: int = 10
    ) -> Dict[str, Any]:
        """
        Poll the generation status until completion or failure
        
        Args:
            generation_id: The ID to poll
            max_attempts: Maximum number of polling attempts
            poll_interval: Seconds between polls
        
        Returns:
            Final status dict with video URL if successful
        
        Raises:
            TimeoutError: If max_attempts reached without completion
            ValueError: If generation failed
        """
        logger.info(f"Polling Kling video {generation_id} (max {max_attempts} attempts)")
        
        for attempt in range(max_attempts):
            result = self.get_video_status(generation_id)
            status = result.get('status')
            
            if status == 'completed':
                video_url = result.get('video', {}).get('url')
                if not video_url:
                    raise ValueError("Video completed but no URL provided")
                logger.info(f"Kling video ready: {video_url}")
                return result
            
            elif status == 'error':
                error_msg = result.get('error', 'Unknown error')
                raise ValueError(f"Kling video generation failed: {error_msg}")
            
            elif status in ['queued', 'generating']:
                if attempt % 6 == 0:  # Log every minute
                    logger.info(f"Still {status}... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(poll_interval)
            
            else:
                logger.warning(f"Unknown status: {status}")
                time.sleep(poll_interval)
        
        raise TimeoutError(f"Kling video generation timed out after {max_attempts * poll_interval}s")
    
    def generate_and_wait(
        self,
        image_url: str,
        prompt: str,
        duration: int = 5,
        cfg_scale: float = 0.5,
        negative_prompt: Optional[str] = None,
        max_wait_time: int = 1200
    ) -> str:
        """
        Convenience method: Generate video and wait for completion
        
        Args:
            image_url: Direct link to image or Base64-encoded local image
            prompt: Text description of the scene/action
            duration: Video length in seconds (5 or 10)
            cfg_scale: How closely to follow the prompt (0-1)
            negative_prompt: Elements to avoid
            max_wait_time: Maximum seconds to wait
        
        Returns:
            Video URL
        """
        # Start generation
        result = self.generate_video(
            image_url=image_url,
            prompt=prompt,
            duration=duration,
            cfg_scale=cfg_scale,
            negative_prompt=negative_prompt
        )
        
        generation_id = result.get('id')
        if not generation_id:
            raise ValueError("No generation ID returned")
        
        # Poll until complete
        max_attempts = max_wait_time // 10
        final_result = self.poll_until_complete(
            generation_id=generation_id,
            max_attempts=max_attempts,
            poll_interval=10
        )
        
        return final_result.get('video', {}).get('url')


# Singleton instance
kling_generator = KlingVideoGenerator()
