"""
Video generation utilities for the Gemnar platform.
Supports multiple video generation providers with a unified interface.
"""

import logging
import requests
import tempfile
import os
from typing import Dict, Any, Optional, Tuple
from django.core.files.base import ContentFile
from website.models import EncryptedVariable

# Sentry integration for debugging breadcrumbs
try:
    import sentry_sdk

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger(__name__)


class VideoGenerationError(Exception):
    """Custom exception for video generation errors"""

    pass


class VideoGenerationService:
    """
    Unified video generation service that supports multiple providers.
    Currently supports:
    - OpenAI (placeholder for future video capabilities)
    - Runware API (for video generation)
    """

    def __init__(self):
        self.providers = {
            "openai": self._generate_openai_video,
            "runware": self._generate_runware_video,
        }

    def generate_video(
        self,
        prompt: str,
        provider: str = "runware",
        quality: str = "low",
        duration: float = 5.0,
        aspect_ratio: str = "9:16",  # Instagram format
        **kwargs,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a video using the specified provider.

        Args:
            prompt: Text description for video generation
            provider: Video generation provider ('openai', 'runware')
            quality: Quality setting ('low', 'high')
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            **kwargs: Additional provider-specific parameters

        Returns:
            Tuple of (video_url, metadata)

        Raises:
            VideoGenerationError: If video generation fails
        """
        if provider not in self.providers:
            raise VideoGenerationError(f"Unsupported provider: {provider}")

        try:
            return self.providers[provider](
                prompt=prompt,
                quality=quality,
                duration=duration,
                aspect_ratio=aspect_ratio,
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Video generation failed with {provider}: {str(e)}")
            raise VideoGenerationError(f"Video generation failed: {str(e)}")

    def _generate_openai_video(
        self,
        prompt: str,
        quality: str = "low",
        duration: float = 5.0,
        aspect_ratio: str = "9:16",
        **kwargs,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate video using OpenAI (placeholder for future capabilities).
        Currently raises NotImplementedError.
        """
        raise NotImplementedError("OpenAI video generation not yet available")

    def _generate_runware_video(
        self,
        prompt: str,
        quality: str = "low",
        duration: float = 5.0,
        aspect_ratio: str = "9:16",
        **kwargs,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate video using Runware API.
        """
        import uuid

        # Get Runware API credentials
        api_key = self._get_runware_api_key()
        if not api_key:
            raise VideoGenerationError("Runware API key not configured in variables")

        # Convert aspect ratio to dimensions
        width, height = self._get_dimensions_from_aspect_ratio(aspect_ratio, quality)

        # Prepare API request with correct Runware task-based format
        url = "https://api.runware.ai/v1"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Generate unique task UUID
        task_uuid = str(uuid.uuid4())

        # Adjust duration for video generation constraints (supports 5 or 8 seconds)
        if duration <= 5:
            adjusted_duration = 5
        else:
            adjusted_duration = 8

        # Use Runware's task-based request format with PixVerse model
        # Correct AIR ID provided by user: pixverse:1@3
        data = [
            {
                "taskType": "videoInference",
                "taskUUID": task_uuid,
                "deliveryMethod": "async",
                "positivePrompt": prompt,
                "duration": adjusted_duration,
                "width": width,
                "height": height,
                "model": "pixverse:1@3",  # Correct PixVerse AIR ID
                "numberResults": 1,
            }
        ]

        try:
            import json

            # Add Sentry breadcrumbs for debugging
            if SENTRY_AVAILABLE:
                sentry_sdk.add_breadcrumb(
                    category="video_generation",
                    message="Runware API Request",
                    level="info",
                    data={
                        "provider": "runware",
                        "url": url,
                        "task_uuid": task_uuid,
                        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "duration": adjusted_duration,
                        "width": width,
                        "height": height,
                        "model": "pixverse:1@3",
                        "headers": {
                            k: v
                            for k, v in headers.items()
                            if k.lower() != "authorization"
                        },
                    },
                )

            # Add debugging breadcrumbs for the request
            logger.info("🔍 Runware API Request Debug:")
            logger.info(f"URL: {url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Request Data: {json.dumps(data, indent=2)}")

            # Submit the task
            response = requests.post(url, json=data, headers=headers, timeout=30)

            # Add Sentry breadcrumb for response
            if SENTRY_AVAILABLE:
                sentry_sdk.add_breadcrumb(
                    category="video_generation",
                    message="Runware API Response",
                    level="info",
                    data={
                        "status_code": response.status_code,
                        "response_headers": dict(response.headers),
                        "response_size": len(response.text),
                        "task_uuid": task_uuid,
                    },
                )

            # Log response details
            logger.info("🔍 Runware API Response Debug:")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            logger.info(f"Response Text: {response.text}")

            response.raise_for_status()

            result = response.json()

            # Check if task was submitted successfully
            if not result or not result.get("data") or len(result["data"]) == 0:
                raise VideoGenerationError("Empty response from Runware API")

            task_result = result["data"][0]
            if task_result.get("error"):
                error_msg = task_result.get("error", "Unknown error")
                raise VideoGenerationError(f"Runware API error: {error_msg}")

            # Get the task UUID to poll for results
            submitted_task_uuid = task_result.get("taskUUID", task_uuid)

            # Poll for completion (Runware uses async processing)
            logger.info(f"Starting video generation for task: {submitted_task_uuid}")
            video_url = self._poll_runware_task(api_key, submitted_task_uuid)
            logger.info(f"Video generation completed: {video_url[:50]}...")

            metadata = {
                "provider": "runware",
                "prompt": prompt,
                "duration": duration,
                "quality": quality,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "task_uuid": submitted_task_uuid,
                "model": "pixverse:1@3",
            }

            return video_url, metadata

        except requests.exceptions.RequestException as e:
            # Add Sentry breadcrumb for request exception
            if SENTRY_AVAILABLE:
                error_data = {
                    "error_type": "RequestException",
                    "error_message": str(e),
                    "task_uuid": task_uuid,
                    "url": url,
                }
                if hasattr(e, "response") and e.response is not None:
                    error_data.update(
                        {
                            "response_status_code": e.response.status_code,
                            "response_headers": dict(e.response.headers),
                            "response_size": len(e.response.text)
                            if e.response.text
                            else 0,
                        }
                    )
                    try:
                        error_data["response_json"] = e.response.json()
                    except (ValueError, requests.exceptions.JSONDecodeError):
                        error_data["response_text"] = (
                            e.response.text[:500] + "..."
                            if len(e.response.text) > 500
                            else e.response.text
                        )

                sentry_sdk.add_breadcrumb(
                    category="video_generation",
                    message="Runware API Request Failed",
                    level="error",
                    data=error_data,
                )

            logger.error(f"Runware API request failed: {str(e)}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Runware API error details: {error_detail}")
                except (ValueError, requests.exceptions.JSONDecodeError):
                    logger.error(f"Runware API response text: {e.response.text}")
            raise VideoGenerationError(f"API request failed: {str(e)}")
        except Exception as e:
            # Add Sentry breadcrumb for general exception
            if SENTRY_AVAILABLE:
                sentry_sdk.add_breadcrumb(
                    category="video_generation",
                    message="Runware Video Generation Failed",
                    level="error",
                    data={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "task_uuid": task_uuid,
                        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    },
                )

            logger.error(f"Runware video generation failed: {str(e)}")
            raise VideoGenerationError(f"Video generation failed: {str(e)}")

    def _poll_runware_task(
        self, api_key: str, task_uuid: str, max_attempts: int = 60
    ) -> str:
        """
        Poll Runware API for task completion and return video URL.
        """
        import time

        url = "https://api.runware.ai/v1"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Add Sentry breadcrumb for polling start
        if SENTRY_AVAILABLE:
            sentry_sdk.add_breadcrumb(
                category="video_generation",
                message="Starting Runware Task Polling",
                level="info",
                data={
                    "task_uuid": task_uuid,
                    "max_attempts": max_attempts,
                    "polling_url": url,
                },
            )

        for attempt in range(max_attempts):
            try:
                # Query task status using getResponse
                query_data = [
                    {
                        "taskType": "getResponse",
                        "taskUUID": task_uuid,
                    }
                ]

                # Add Sentry breadcrumb for polling attempt
                if (
                    SENTRY_AVAILABLE and attempt % 10 == 0
                ):  # Log every 10th attempt to avoid spam
                    sentry_sdk.add_breadcrumb(
                        category="video_generation",
                        message=f"Runware Task Polling Attempt {attempt + 1}",
                        level="info",
                        data={
                            "task_uuid": task_uuid,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                        },
                    )

                response = requests.post(
                    url, json=query_data, headers=headers, timeout=30
                )
                response.raise_for_status()
                result = response.json()

                # Check for response structure
                if not result or not result.get("data") or len(result["data"]) == 0:
                    time.sleep(5)
                    continue

                task_result = result["data"][0]

                # Check for errors
                if task_result.get("error"):
                    error_msg = task_result.get("error", "Unknown error")

                    # Add Sentry breadcrumb for task error
                    if SENTRY_AVAILABLE:
                        sentry_sdk.add_breadcrumb(
                            category="video_generation",
                            message="Runware Task Error",
                            level="error",
                            data={
                                "task_uuid": task_uuid,
                                "error_message": error_msg,
                                "attempt": attempt + 1,
                                "task_result": task_result,
                            },
                        )

                    raise VideoGenerationError(f"Runware task error: {error_msg}")

                # Check if task is completed
                if task_result.get("videoUUID") and task_result.get("videoURL"):
                    video_url = task_result.get("videoURL")

                    # Add Sentry breadcrumb for successful completion
                    if SENTRY_AVAILABLE:
                        sentry_sdk.add_breadcrumb(
                            category="video_generation",
                            message="Runware Task Completed Successfully",
                            level="info",
                            data={
                                "task_uuid": task_uuid,
                                "video_uuid": task_result.get("videoUUID"),
                                "video_url_length": len(video_url) if video_url else 0,
                                "attempts_required": attempt + 1,
                                "completion_time_seconds": (attempt + 1) * 5,
                            },
                        )

                    return video_url

                # Task still processing, wait and retry
                time.sleep(5)

            except requests.exceptions.RequestException as e:
                # Add Sentry breadcrumb for polling exception
                if SENTRY_AVAILABLE:
                    error_data = {
                        "error_type": "RequestException",
                        "error_message": str(e),
                        "task_uuid": task_uuid,
                        "attempt": attempt + 1,
                        "url": url,
                    }
                    if hasattr(e, "response") and e.response is not None:
                        error_data.update(
                            {
                                "response_status_code": e.response.status_code,
                                "response_headers": dict(e.response.headers),
                            }
                        )

                    sentry_sdk.add_breadcrumb(
                        category="video_generation",
                        message="Runware Polling Request Failed",
                        level="error",
                        data=error_data,
                    )

                logger.error(f"Runware polling request failed: {str(e)}")
                if attempt == max_attempts - 1:
                    raise VideoGenerationError(f"Polling failed: {str(e)}")
                time.sleep(5)

        # Add Sentry breadcrumb for timeout
        if SENTRY_AVAILABLE:
            sentry_sdk.add_breadcrumb(
                category="video_generation",
                message="Runware Task Polling Timed Out",
                level="error",
                data={
                    "task_uuid": task_uuid,
                    "max_attempts": max_attempts,
                    "total_time_seconds": max_attempts * 5,
                },
            )

        logger.error(f"Video generation timed out after {max_attempts} attempts")
        raise VideoGenerationError(
            "Video generation timed out - task did not complete within expected time"
        )

    def _get_runware_api_key(self) -> Optional[str]:
        """Get Runware API key from environment variables"""
        import os

        try:
            api_key = os.getenv("RUNWARE_API_KEY")
            if api_key:
                return api_key

            # Fallback to encrypted variables if env var not found
            runware_var = EncryptedVariable.objects.filter(
                key="RUNWARE_API_KEY"
            ).first()
            if runware_var:
                return runware_var.get_decrypted_value()
        except Exception as e:
            logger.error(f"Failed to get Runware API key: {str(e)}")
        return None

    def _get_dimensions_from_aspect_ratio(
        self, aspect_ratio: str, quality: str
    ) -> Tuple[int, int]:
        """
        Convert aspect ratio string to width/height dimensions.
        Using KlingAI 2.1 Master supported dimensions.
        """
        # KlingAI 2.1 Master supported dimensions: 1920x1080 (16:9), 608x1080 (9:16), 1080x1080 (1:1)
        aspect_ratios = {
            "1:1": (1080, 1080),  # Square format
            "16:9": (1920, 1080),  # Landscape format
            "9:16": (608, 1080),  # Portrait format
            "4:3": (1920, 1080),  # Fallback to 16:9
            "3:4": (608, 1080),  # Fallback to 9:16
        }

        return aspect_ratios.get(aspect_ratio, aspect_ratios["9:16"])

    def generate_video_thumbnail(self, video_url: str) -> Optional[str]:
        """
        Generate thumbnail from video URL.
        Downloads video and extracts first frame as thumbnail.
        """
        try:
            # Download video temporarily
            response = requests.get(video_url, timeout=60)
            response.raise_for_status()

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                temp_video.write(response.content)
                temp_video_path = temp_video.name

            # Extract thumbnail using ffmpeg (if available)
            thumbnail_path = temp_video_path.replace(".mp4", "_thumb.jpg")

            # Try to use ffmpeg to extract thumbnail
            import subprocess

            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        temp_video_path,
                        "-vframes",
                        "1",
                        "-vf",
                        "scale=512:512:force_original_aspect_ratio=decrease",
                        thumbnail_path,
                    ],
                    check=True,
                    capture_output=True,
                )

                # Read thumbnail file
                with open(thumbnail_path, "rb") as f:
                    thumbnail_data = f.read()

                # Clean up temporary files
                os.unlink(temp_video_path)
                os.unlink(thumbnail_path)

                return ContentFile(thumbnail_data, name="thumbnail.jpg")

            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("ffmpeg not available, skipping thumbnail generation")
                os.unlink(temp_video_path)
                return None

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {str(e)}")
            return None


# Global service instance
video_service = VideoGenerationService()


def generate_video_for_brand_post(
    brand_post,
    prompt: str,
    provider: str = "runware",
    quality: str = "low",
    duration: float = 5.0,
) -> bool:
    """
    Generate video for a BrandInstagramPost and save it to the model.

    Args:
        brand_post: BrandInstagramPost instance
        prompt: Video generation prompt
        provider: Video generation provider
        quality: Quality setting
        duration: Video duration in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        # Generate video
        video_url, metadata = video_service.generate_video(
            prompt=prompt,
            provider=provider,
            quality=quality,
            duration=duration,
            aspect_ratio="9:16",  # Instagram format
        )

        # Download and save video
        response = requests.get(video_url, timeout=120)
        response.raise_for_status()

        # Save video to model
        video_content = ContentFile(response.content, name=f"video_{brand_post.id}.mp4")
        brand_post.video.save(f"video_{brand_post.id}.mp4", video_content, save=False)

        # Generate and save thumbnail
        thumbnail = video_service.generate_video_thumbnail(video_url)
        if thumbnail:
            brand_post.video_thumbnail.save(
                f"thumb_{brand_post.id}.jpg", thumbnail, save=False
            )

        # Update post metadata
        brand_post.video_prompt = prompt
        brand_post.is_video_post = True
        brand_post.video_duration = duration
        brand_post.video_quality = quality
        brand_post.save()

        logger.info(f"Successfully generated video for post {brand_post.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to generate video for post {brand_post.id}: {str(e)}")
        brand_post.error_message = f"Video generation failed: {str(e)}"
        brand_post.save()
        return False


def submit_video_generation_task(
    brand_post,
    prompt: str,
    provider: str = "runware",
    quality: str = "low",
    duration: float = 5.0,
) -> bool:
    """
    Submit video generation task asynchronously and return immediately.

    Args:
        brand_post: BrandInstagramPost instance
        prompt: Video generation prompt
        provider: Video generation provider
        quality: Quality setting
        duration: Video duration in seconds

    Returns:
        True if task was submitted successfully, False otherwise
    """
    try:
        import uuid
        import requests

        # Add Sentry breadcrumb for task submission start
        if SENTRY_AVAILABLE:
            sentry_sdk.add_breadcrumb(
                category="video_generation",
                message="Starting Video Generation Task Submission",
                level="info",
                data={
                    "post_id": brand_post.id if brand_post else None,
                    "prompt_length": len(prompt),
                    "prompt_preview": prompt[:100],
                    "provider": provider,
                    "quality": quality,
                    "duration": duration,
                },
            )

        # Get Runware API credentials
        api_key = video_service._get_runware_api_key()
        if not api_key:
            if SENTRY_AVAILABLE:
                sentry_sdk.add_breadcrumb(
                    category="video_generation",
                    message="Runware API Key Missing",
                    level="error",
                    data={"error": "API key not configured"},
                )
            raise VideoGenerationError("Runware API key not configured")

        # Convert aspect ratio to dimensions
        width, height = video_service._get_dimensions_from_aspect_ratio("9:16", quality)

        # Prepare API request
        url = "https://api.runware.ai/v1"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Headers for logging (masked API key)
        headers_for_logging = {
            "Authorization": f"Bearer {api_key[:10]}...",
            "Content-Type": "application/json",
        }

        # Generate unique task UUID
        task_uuid = str(uuid.uuid4())

        # Adjust duration for video generation constraints
        if duration <= 5:
            adjusted_duration = 5
        else:
            adjusted_duration = 8

        # Prepare task data for Runware API
        data = [
            {
                "taskType": "videoInference",
                "taskUUID": task_uuid,
                "positivePrompt": prompt,  # Runware uses positivePrompt for both image and video
                "width": width,
                "height": height,
                "duration": adjusted_duration,
                "fps": 24,
                "model": "pixverse:1@3",  # PixVerse AIR ID for video generation
                # Note: omitting seed for random generation (default behavior)
            }
        ]

        # Add Sentry breadcrumb for API request
        if SENTRY_AVAILABLE:
            sentry_sdk.add_breadcrumb(
                category="video_generation",
                message="Sending Request to Runware API",
                level="info",
                data={
                    "url": url,
                    "task_uuid": task_uuid,
                    "task_type": "videoInference",
                    "positive_prompt": prompt[:100],  # Runware uses positivePrompt
                    "width": width,
                    "height": height,
                    "duration": adjusted_duration,
                    "fps": 24,
                    "model": "pixverse:1@3",
                    "seed": "random",  # Using default random seed
                    "quality": quality,
                    "request_size": len(str(data)),
                },
            )

        logger.info(
            f"Submitting Runware task {task_uuid} for post {brand_post.id}: {prompt[:50]}..."
        )
        logger.debug(f"Request data: {data}")

        # Submit the task
        response = requests.post(url, json=data, headers=headers, timeout=30)

        # Add Sentry breadcrumb for API response
        if SENTRY_AVAILABLE:
            sentry_sdk.add_breadcrumb(
                category="video_generation",
                message="Received Response from Runware API",
                level="info",
                data={
                    "status_code": response.status_code,
                    "response_headers": dict(response.headers),
                    "response_size": len(response.text),
                    "task_uuid": task_uuid,
                    "response_text_preview": response.text[:500],
                },
            )

        logger.info(
            f"Runware API Response - Status: {response.status_code}, Size: {len(response.text)} bytes"
        )
        logger.debug(f"Response content: {response.text}")

        response.raise_for_status()
        result = response.json()

        # Check if task was submitted successfully
        if not result or not result.get("data") or len(result["data"]) == 0:
            raise VideoGenerationError("Empty response from Runware API")

        task_result = result["data"][0]
        if task_result.get("error"):
            error_msg = task_result.get("error", "Unknown error")
            raise VideoGenerationError(f"Runware API error: {error_msg}")

        # Get the submitted task UUID
        submitted_task_uuid = task_result.get("taskUUID", task_uuid)

        # Update post with task information
        brand_post.video_generation_task_uuid = submitted_task_uuid
        brand_post.video_generation_status = "pending"
        brand_post.video_prompt = prompt
        brand_post.is_video_post = True
        brand_post.video_duration = duration
        brand_post.video_quality = quality
        brand_post.save()

        logger.info(
            f"Successfully submitted video generation task {submitted_task_uuid} for post {brand_post.id}"
        )
        return True

    except requests.exceptions.RequestException as e:
        error_msg = f"Request to Runware API failed: {str(e)}"

        # Add Sentry breadcrumb for request failure
        if SENTRY_AVAILABLE:
            error_data = {
                "error_type": "RequestException",
                "error_message": str(e),
                "post_id": brand_post.id if brand_post else None,
                "task_uuid": task_uuid if "task_uuid" in locals() else None,
                "url": url if "url" in locals() else None,
            }
            if hasattr(e, "response") and e.response is not None:
                error_data.update(
                    {
                        "response_status_code": e.response.status_code,
                        "response_headers": dict(e.response.headers),
                        "response_text": e.response.text[:1000],
                    }
                )

            sentry_sdk.add_breadcrumb(
                category="video_generation",
                message="Runware API Request Failed",
                level="error",
                data=error_data,
            )

        logger.error(
            f"Failed to submit video generation task for post {brand_post.id}: {error_msg}"
        )
        brand_post.error_message = (
            f"Video generation task submission failed: {error_msg}"
        )
        brand_post.video_generation_status = "failed"
        brand_post.save()
        return False

    except VideoGenerationError as e:
        error_msg = str(e)

        # Add Sentry breadcrumb for video generation error
        if SENTRY_AVAILABLE:
            sentry_sdk.add_breadcrumb(
                category="video_generation",
                message="Video Generation Error",
                level="error",
                data={
                    "error_type": "VideoGenerationError",
                    "error_message": error_msg,
                    "post_id": brand_post.id if brand_post else None,
                    "task_uuid": task_uuid if "task_uuid" in locals() else None,
                },
            )

        logger.error(
            f"Failed to submit video generation task for post {brand_post.id}: {error_msg}"
        )
        brand_post.error_message = (
            f"Video generation task submission failed: {error_msg}"
        )
        brand_post.video_generation_status = "failed"
        brand_post.save()
        return False

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"

        # Add Sentry breadcrumb for unexpected error
        if SENTRY_AVAILABLE:
            sentry_sdk.add_breadcrumb(
                category="video_generation",
                message="Unexpected Error in Video Generation",
                level="error",
                data={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "post_id": brand_post.id if brand_post else None,
                    "task_uuid": task_uuid if "task_uuid" in locals() else None,
                },
            )

        logger.exception(
            f"Failed to submit video generation task for post {brand_post.id}: {error_msg}"
        )
        brand_post.error_message = (
            f"Video generation task submission failed: {error_msg}"
        )
        brand_post.video_generation_status = "failed"
        brand_post.save()
        return False


def check_video_generation_status(brand_post) -> str:
    """
    Check the status of a video generation task.

    Args:
        brand_post: BrandInstagramPost instance with task_uuid

    Returns:
        Status string: "pending", "processing", "completed", "failed"
    """
    if not brand_post.video_generation_task_uuid:
        return "none"

    try:
        import requests

        # Get Runware API credentials
        api_key = video_service._get_runware_api_key()
        if not api_key:
            logger.error("Runware API key not configured")
            return "failed"

        url = "https://api.runware.ai/v1"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Query task status
        query_data = [
            {
                "taskType": "getResponse",
                "taskUUID": brand_post.video_generation_task_uuid,
            }
        ]

        response = requests.post(url, json=query_data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        # Check for response structure
        if not result or not result.get("data") or len(result["data"]) == 0:
            return "processing"

        task_result = result["data"][0]

        # Check for errors
        if task_result.get("error"):
            error_msg = task_result.get("error", "Unknown error")
            brand_post.error_message = f"Video generation error: {error_msg}"
            brand_post.video_generation_status = "failed"
            brand_post.save()
            return "failed"

        # Check if task is completed
        if task_result.get("videoUUID") and task_result.get("videoURL"):
            video_url = task_result.get("videoURL")

            # Download and save the video
            if complete_video_generation(brand_post, video_url):
                brand_post.video_generation_status = "completed"
                brand_post.save()
                return "completed"
            else:
                brand_post.video_generation_status = "failed"
                brand_post.save()
                return "failed"

        # Task still processing
        if brand_post.video_generation_status != "processing":
            brand_post.video_generation_status = "processing"
            brand_post.save()

        return "processing"

    except Exception as e:
        logger.error(
            f"Failed to check video generation status for post {brand_post.id}: {str(e)}"
        )
        brand_post.error_message = f"Status check failed: {str(e)}"
        brand_post.video_generation_status = "failed"
        brand_post.save()
        return "failed"


def complete_video_generation(brand_post, video_url: str) -> bool:
    """
    Complete video generation by downloading and saving the video.

    Args:
        brand_post: BrandInstagramPost instance
        video_url: URL of the generated video

    Returns:
        True if successful, False otherwise
    """
    try:
        import requests
        from django.core.files.base import ContentFile

        # Download the video
        response = requests.get(video_url, timeout=120)
        response.raise_for_status()

        # Save video to model
        video_content = ContentFile(response.content, name=f"video_{brand_post.id}.mp4")
        brand_post.video.save(f"video_{brand_post.id}.mp4", video_content, save=False)

        # Generate and save thumbnail
        thumbnail = video_service.generate_video_thumbnail(video_url)
        if thumbnail:
            brand_post.video_thumbnail.save(
                f"thumb_{brand_post.id}.jpg", thumbnail, save=False
            )

        brand_post.save()
        logger.info(f"Successfully completed video generation for post {brand_post.id}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to complete video generation for post {brand_post.id}: {str(e)}"
        )
        brand_post.error_message = f"Video completion failed: {str(e)}"
        return False
