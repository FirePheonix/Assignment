"""
Veo 3.1 Video Generation Utilities using Kie AI API
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class VeoVideoGenerator:
    """Handler for Veo 3.1 video generation via Kie AI"""
    
    BASE_URL = "https://api.kie.ai"
    
    # Veo 3.1 models
    MODELS = {
        "veo3": "veo3",  # Quality model
        "veo3_fast": "veo3_fast",  # Fast model
    }
    
    # Generation types
    GENERATION_TYPES = {
        "text_to_video": "TEXT_2_VIDEO",
        "image_to_video": "FIRST_AND_LAST_FRAMES_2_VIDEO",
        "reference_to_video": "REFERENCE_2_VIDEO",
    }
    
    # Aspect ratios
    ASPECT_RATIOS = {
        "16:9": "16:9",
        "9:16": "9:16",
        "auto": "Auto",
    }
    
    def __init__(self):
        self.api_key = settings.KIE_AI_API_KEY
        if not self.api_key:
            raise ValueError("KIE_AI_API_KEY not configured in settings")
    
    def generate_video(
        self,
        prompt: str,
        model: str = "veo3_fast",
        aspect_ratio: str = "16:9",
        generation_type: str = "text_to_video",
        image_urls: list = None,
        seeds: int = None,
        watermark: str = None,
        callback_url: str = None,
        enable_translation: bool = True,
    ) -> dict:
        """
        Generate video using Veo 3.1 AI
        
        Args:
            prompt: Text prompt describing the desired video content
            model: Model to use ('veo3' or 'veo3_fast')
            aspect_ratio: Video aspect ratio ('16:9', '9:16', or 'auto')
            generation_type: Type of generation ('text_to_video', 'image_to_video', 'reference_to_video')
            image_urls: List of image URLs (optional, for image-to-video modes)
            seeds: Random seed for reproducibility (10000-99999)
            watermark: Watermark text (optional)
            callback_url: Callback URL for completion notification (optional)
            enable_translation: Auto-translate prompt to English (default: True)
        
        Returns:
            dict: Response containing task_id for status polling
        """
        # Validate model
        if model not in self.MODELS:
            model = "veo3_fast"
        
        # Validate aspect ratio
        if aspect_ratio not in self.ASPECT_RATIOS:
            aspect_ratio = "16:9"
        
        # Validate generation type
        if generation_type not in self.GENERATION_TYPES:
            generation_type = "text_to_video"
        
        # Build request payload
        payload = {
            "prompt": prompt,
            "model": self.MODELS[model],
            "aspectRatio": self.ASPECT_RATIOS[aspect_ratio],
            "generationType": self.GENERATION_TYPES[generation_type],
            "enableTranslation": enable_translation,
        }
        
        # Add optional parameters
        if image_urls:
            payload["imageUrls"] = image_urls
        
        if seeds and 10000 <= seeds <= 99999:
            payload["seeds"] = seeds
        
        if watermark:
            payload["watermark"] = watermark
        
        if callback_url:
            payload["callBackUrl"] = callback_url
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/api/v1/veo/generate",
                json=payload,
                headers=headers,
                timeout=30,
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check response code
            if result.get("code") != 200:
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"Veo API error: {error_msg}")
                raise Exception(f"Veo API error: {error_msg}")
            
            # Extract task ID
            task_id = result.get("data", {}).get("taskId")
            if not task_id:
                raise Exception("No task ID returned from Veo API")
            
            logger.info(f"Veo video generation started: {task_id}")
            
            return {
                "task_id": task_id,
                "model": model,
                "aspect_ratio": aspect_ratio,
                "generation_type": generation_type,
            }
            
        except requests.RequestException as e:
            logger.error(f"Veo API request failed: {str(e)}")
            raise Exception(f"Failed to generate video: {str(e)}")
    
    def get_video_status(self, task_id: str) -> dict:
        """
        Get status of a video generation task
        
        Args:
            task_id: Task ID from generate_video()
        
        Returns:
            dict: Status information including resultUrls when complete
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/api/v1/veo/record-info",
                params={"taskId": task_id},
                headers=headers,
                timeout=30,
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check response code
            if result.get("code") != 200:
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"Veo status check error: {error_msg}")
                raise Exception(f"Veo status check error: {error_msg}")
            
            data = result.get("data", {})
            
            # Parse status
            success_flag = data.get("successFlag", 0)
            status_map = {
                0: "generating",
                1: "completed",
                2: "failed",
                3: "failed",
            }
            
            status = status_map.get(success_flag, "unknown")
            
            response_data = {
                "task_id": task_id,
                "status": status,
                "success_flag": success_flag,
            }
            
            # Add completion data if available
            if success_flag == 1 and data.get("response"):
                response_obj = data["response"]
                response_data.update({
                    "result_urls": response_obj.get("resultUrls", []),
                    "origin_urls": response_obj.get("originUrls", []),
                    "resolution": response_obj.get("resolution"),
                })
            
            # Add error data if failed
            if success_flag in [2, 3]:
                response_data.update({
                    "error_code": data.get("errorCode"),
                    "error_message": data.get("errorMessage", "Generation failed"),
                })
            
            # Add metadata
            response_data.update({
                "created_at": data.get("createTime"),
                "completed_at": data.get("completeTime"),
                "fallback_flag": data.get("fallbackFlag", False),
            })
            
            return response_data
            
        except requests.RequestException as e:
            logger.error(f"Veo status check failed: {str(e)}")
            raise Exception(f"Failed to get video status: {str(e)}")
    
    def get_1080p_video(self, task_id: str, index: int = 0) -> dict:
        """
        Get 1080P version of generated video
        
        Args:
            task_id: Task ID from generate_video()
            index: Video index (default: 0)
        
        Returns:
            dict: Response containing 1080P video URL
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/api/v1/veo/get-1080p-video",
                params={"taskId": task_id, "index": index},
                headers=headers,
                timeout=30,
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check response code
            if result.get("code") != 200:
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"Veo 1080P fetch error: {error_msg}")
                raise Exception(f"Veo 1080P fetch error: {error_msg}")
            
            data = result.get("data", {})
            result_url = data.get("resultUrl")
            
            if not result_url:
                raise Exception("No 1080P video URL returned")
            
            return {
                "task_id": task_id,
                "result_url": result_url,
            }
            
        except requests.RequestException as e:
            logger.error(f"Veo 1080P fetch failed: {str(e)}")
            raise Exception(f"Failed to get 1080P video: {str(e)}")
    
    def extend_video(
        self,
        task_id: str,
        prompt: str,
        seeds: int = None,
        watermark: str = None,
        callback_url: str = None,
    ) -> dict:
        """
        Extend an existing video with new content
        
        Args:
            task_id: Original video task ID
            prompt: Text prompt describing the extension
            seeds: Random seed for reproducibility (10000-99999)
            watermark: Watermark text (optional)
            callback_url: Callback URL for completion notification (optional)
        
        Returns:
            dict: Response containing new task_id for status polling
        """
        payload = {
            "taskId": task_id,
            "prompt": prompt,
        }
        
        # Add optional parameters
        if seeds and 10000 <= seeds <= 99999:
            payload["seeds"] = seeds
        
        if watermark:
            payload["watermark"] = watermark
        
        if callback_url:
            payload["callBackUrl"] = callback_url
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/api/v1/veo/extend",
                json=payload,
                headers=headers,
                timeout=30,
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check response code
            if result.get("code") != 200:
                error_msg = result.get("msg", "Unknown error")
                logger.error(f"Veo extend error: {error_msg}")
                raise Exception(f"Veo extend error: {error_msg}")
            
            # Extract new task ID
            new_task_id = result.get("data", {}).get("taskId")
            if not new_task_id:
                raise Exception("No task ID returned from Veo extend API")
            
            logger.info(f"Veo video extension started: {new_task_id}")
            
            return {
                "task_id": new_task_id,
                "original_task_id": task_id,
            }
            
        except requests.RequestException as e:
            logger.error(f"Veo extend request failed: {str(e)}")
            raise Exception(f"Failed to extend video: {str(e)}")


# Singleton instance
veo_generator = VeoVideoGenerator()
