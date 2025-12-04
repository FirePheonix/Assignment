from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, parser_classes, authentication_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authentication import TokenAuthentication

# Using token-based authentication only - no session auth needed

# Import Sentry for breadcrumbs
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None
from .serializers import (
    UserProfileSerializer,
    TaskSerializer,
    TaskCreateSerializer,
    TaskApplicationSerializer,
    TaskApplicationCreateSerializer,
    TweetConfigurationSerializer,
    BrandTweetSerializer,
    TweetStrategySerializer,
    BrandAssetSerializer,
)
from .services.account_deletion import (
    AccountDeletionService,
    get_account_deletion_preview,
)
from .models import (
    User,
    ReferralCode,
    Brand,
    Task,
    TaskApplication,
    TweetConfiguration,
    BrandTweet,
    TweetStrategy,
    BrandAsset,
)
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import timezone
import uuid
import os
import tempfile
import logging
import requests
import json
import base64
import stripe
import traceback
from PIL import Image
import io
import tweepy
from django.conf import settings
from .models import Tweet
import random
from website.utils import get_openai_client
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Removed Celery - using cron jobs for background tasks

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def get_csrf_token(request):
    """
    Public endpoint to get CSRF token.
    Used by Next.js frontend to ensure CSRF cookie is set before making authenticated requests.
    """
    from django.middleware.csrf import get_token
    csrf_token = get_token(request)
    return Response({"detail": "CSRF cookie set"})


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """
    Get current authenticated user info for Next.js frontend using Token Authentication.
    Returns user data if authenticated with valid token, 401 if not.
    """
    user_data = {
        "id": request.user.id,
        "username": request.user.username,
        "email": request.user.email,
        "first_name": request.user.first_name or "",
        "last_name": request.user.last_name or "",
    }
    
    return Response(user_data)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def custom_login(request):
    """
    Token-based login endpoint for Next.js frontend.
    Returns an authentication token that the frontend stores and sends with requests.
    """
    from django.contrib.auth import authenticate
    from rest_framework.authtoken.models import Token
    
    email = request.data.get("email", "").strip()
    password = request.data.get("password", "")
    
    if not email or not password:
        return Response(
            {"non_field_errors": ["Email and password are required."]},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find user by email
    try:
        user_obj = User.objects.get(email=email)
        username = user_obj.username
    except User.DoesNotExist:
        return Response(
            {"non_field_errors": ["Unable to log in with provided credentials."]},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Authenticate with username
    user = authenticate(
        request=request,
        username=username,
        password=password
    )
    
    if not user:
        return Response(
            {"non_field_errors": ["Unable to log in with provided credentials."]},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not user.is_active:
        return Response(
            {"non_field_errors": ["User account is disabled."]},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create token for user
    token, created = Token.objects.get_or_create(user=user)
    
    logger.info(f"[custom_login] User {user.email} logged in successfully with token")
    
    return Response({
        "token": token.key,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
        }
    })


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_creator(request):
    """
    Register a new creator account via API.
    """
    email = request.data.get("email", "").strip()
    password = request.data.get("password1", "")
    password2 = request.data.get("password2", "")
    username = request.data.get("username", "").strip()
    first_name = request.data.get("first_name", "").strip()
    last_name = request.data.get("last_name", "").strip()

    # Validation
    if not all([email, password, password2]):
        return Response(
            {"detail": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if password != password2:
        return Response(
            {"password1": ["Passwords do not match."]},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {"email": ["A user with this email already exists."]},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate username from email if not provided
    if not username:
        username = email.split('@')[0]
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response(
            {"username": ["This username is already taken."]},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from django.db import IntegrityError
        from django.contrib.auth import login
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Log the user in
        login(request, user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                }
            },
            status=status.HTTP_201_CREATED
        )

    except IntegrityError as e:
        return Response(
            {"detail": "An account with this information already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Creator registration error: {str(e)}")
        return Response(
            {"detail": "An error occurred during registration."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Change user password with proper validation.
    """
    old_password = request.data.get("old_password", "")
    new_password1 = request.data.get("new_password1", "")
    new_password2 = request.data.get("new_password2", "")
    
    logger.info(f"Password change attempt for user: {request.user.username}")
    logger.info(f"Old password provided: {bool(old_password)}")
    
    # Validation
    if not all([old_password, new_password1, new_password2]):
        logger.warning("Password change failed: Missing required fields")
        return Response(
            {"detail": "All fields are required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password1 != new_password2:
        logger.warning("Password change failed: New passwords don't match")
        return Response(
            {"new_password2": ["The two password fields didn't match."]},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify old password - use check_password instead of authenticate
    password_is_correct = request.user.check_password(old_password)
    logger.info(f"Old password check result: {password_is_correct}")
    
    if not password_is_correct:
        logger.warning("Password change failed: Incorrect old password")
        return Response(
            {"old_password": ["Your old password was entered incorrectly."]},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate new password
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    
    try:
        validate_password(new_password1, user=request.user)
    except ValidationError as e:
        return Response(
            {"new_password2": list(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    request.user.set_password(new_password1)
    request.user.save()
    
    return Response(
        {"detail": "Password has been changed successfully."},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_brand(request):
    """
    Register a new brand account via API.
    This is a simplified version without Stripe payment.
    """
    email = request.data.get("email", "").strip()
    password = request.data.get("password1", "")
    password2 = request.data.get("password2", "")
    brand_name = request.data.get("brand_name", "").strip()
    website = request.data.get("website", "").strip()

    # Validation
    if not all([email, password, password2, brand_name]):
        return Response(
            {"detail": "All fields are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if password != password2:
        return Response(
            {"password1": ["Passwords do not match."]},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {"email": ["A user with this email already exists."]},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from django.db import IntegrityError
        from django.contrib.auth import login
        from django.utils.text import slugify
        
        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        # Create brand
        brand = Brand.objects.create(
            name=brand_name,
            url=website or "",
            owner=user,
            slug=slugify(brand_name),
        )
        
        # Set as default brand for user
        user.default_brand = brand
        user.save()

        # Log the user in
        login(request, user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
                "brand": {
                    "id": brand.id,
                    "name": brand.name,
                    "slug": brand.slug,
                }
            },
            status=status.HTTP_201_CREATED
        )

    except IntegrityError as e:
        return Response(
            {"detail": "An account with this information already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Brand registration error: {str(e)}")
        return Response(
            {"detail": "An error occurred during registration."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view for getting and updating user profile
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Return the current user as the profile object
        """
        return self.request.user


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """
    Get the current user's profile
    """
    serializer = UserProfileSerializer(request.user, context={"request": request})
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def update_user_profile(request):
    """
    Update the current user's profile
    """
    serializer = UserProfileSerializer(
        request.user, data=request.data, partial=True, context={"request": request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    """
    Upload an image to Cloudinary and return its URL
    Used for profile pictures, banners, and other user uploads
    """
    try:
        import cloudinary
        import cloudinary.uploader
        from .cloud_storage_models import CloudinaryUpload, UserStorageQuota
        from PIL import Image as PILImage
        from io import BytesIO

        logger.info(f"Image upload request from user: {request.user.id}")

        if "image" not in request.FILES:
            return Response(
                {"error": "No image file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["image"]
        logger.info(f"Uploading: {image_file.name}, size: {image_file.size}, type: {image_file.content_type}")

        allowed_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
        ]

        if image_file.content_type not in allowed_types:
            return Response(
                {"error": "Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check file size (limit to 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "File too large. Maximum size is 10MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check user's storage quota
        quota, created = UserStorageQuota.objects.get_or_create(user=request.user)
        if not quota.has_space_for(image_file.size):
            return Response({
                "error": f"Storage quota exceeded. Used: {quota.get_usage_percentage()}%",
                "quota_used": quota.cloudinary_used + quota.local_used,
                "quota_limit": quota.cloudinary_limit + quota.local_limit,
            }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # Get image dimensions
        try:
            img = PILImage.open(image_file)
            width, height = img.size
            image_file.seek(0)  # Reset file pointer
        except Exception:
            width, height = None, None

        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET
        )

        # Upload to Cloudinary in user's folder
        purpose = request.data.get('purpose', 'profile_upload')
        user_folder = f"user_{request.user.id}/{purpose}"
        
        logger.info(f"Uploading to Cloudinary folder: {user_folder}")

        result = cloudinary.uploader.upload(
            image_file,
            folder=user_folder,
            resource_type='image',
            quality='auto',
            fetch_format='auto',
        )

        public_url = result['secure_url']
        logger.info(f"Cloudinary upload successful: {public_url}")

        # Create database record
        upload_record = CloudinaryUpload.objects.create(
            user=request.user,
            public_id=result['public_id'],
            secure_url=result['secure_url'],
            url=result.get('url', result['secure_url']),
            folder=user_folder,
            original_filename=image_file.name,
            format=result.get('format', image_file.name.split('.')[-1]),
            width=result.get('width', width),
            height=result.get('height', height),
            file_size=result.get('bytes', image_file.size),
            purpose=purpose if purpose in dict(CloudinaryUpload.UPLOAD_PURPOSES) else 'other',
        )

        # Update user's storage quota
        quota.add_cloudinary_usage(image_file.size)

        return Response({
            "url": public_url,
            "public_id": result['public_id'],
            "width": result.get('width'),
            "height": result.get('height'),
            "upload_id": upload_record.id,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"ERROR in upload_image: {str(e)}")
        traceback.print_exc()

        return Response(
            {"error": f"Server error during image upload: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def list_user_uploads(request):
    """
    List all uploads for the current user (local + Cloudinary)
    Supports filtering and pagination
    """
    try:
        from .models import Image
        from .cloud_storage_models import CloudinaryUpload, UserStorageQuota
        from django.db.models import Q
        
        # Get query parameters
        storage_type = request.GET.get('type', 'all')  # 'local', 'cloudinary', 'all'
        purpose = request.GET.get('purpose')  # For cloudinary uploads
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        format_type = request.GET.get('format', 'detailed')  # 'detailed' or 'instagram'
        
        # Instagram-specific simple format
        if format_type == 'instagram':
            uploads_list = []
            
            # Get local uploads
            if storage_type in ['local', 'all']:
                local_images = Image.objects.filter(user=request.user)[offset:offset+limit]
                for img in local_images:
                    uploads_list.append({
                        "id": img.id,
                        "image_url": request.build_absolute_uri(img.image.url) if img.image else None,
                        "public_id": f"local_{img.id}",
                        "created_at": img.created_at.isoformat(),
                    })
            
            # Get Cloudinary uploads
            if storage_type in ['cloudinary', 'all']:
                cloudinary_uploads = CloudinaryUpload.objects.filter(
                    user=request.user, is_deleted=False
                )[offset:offset+limit]
                for upload in cloudinary_uploads:
                    uploads_list.append({
                        "id": upload.id + 10000,  # Offset to avoid ID conflicts
                        "image_url": upload.secure_url,
                        "public_id": upload.public_id,
                        "created_at": upload.created_at.isoformat(),
                    })
            
            # Sort by creation date (newest first)
            uploads_list.sort(key=lambda x: x['created_at'], reverse=True)
            
            return Response(uploads_list, status=status.HTTP_200_OK)
        
        # Original detailed format
        response_data = {
            "success": True,
            "local_uploads": [],
            "cloudinary_uploads": [],
        }
        
        # Get local uploads
        if storage_type in ['local', 'all']:
            local_images = Image.objects.filter(user=request.user)
            if purpose:
                local_images = local_images.filter(
                    Q(title__icontains=purpose) | Q(alt_text__icontains=purpose)
                )
            local_images = local_images[offset:offset+limit]
            
            response_data['local_uploads'] = [{
                "id": img.id,
                "title": img.title,
                "url": request.build_absolute_uri(img.image.url) if img.image else None,
                "alt_text": img.alt_text,
                "created_at": img.created_at.isoformat(),
                "storage_type": "local",
            } for img in local_images]
        
        # Get Cloudinary uploads
        if storage_type in ['cloudinary', 'all']:
            cloudinary_uploads = CloudinaryUpload.objects.filter(
                user=request.user,
                is_deleted=False
            )
            if purpose:
                cloudinary_uploads = cloudinary_uploads.filter(purpose=purpose)
            cloudinary_uploads = cloudinary_uploads[offset:offset+limit]
            
            response_data['cloudinary_uploads'] = [{
                "id": upload.id,
                "public_id": upload.public_id,
                "url": upload.secure_url,
                "thumbnail_url": upload.get_thumbnail_url(200, 200),
                "original_filename": upload.original_filename,
                "format": upload.format,
                "width": upload.width,
                "height": upload.height,
                "file_size": upload.file_size,
                "purpose": upload.purpose,
                "usage_count": upload.usage_count,
                "created_at": upload.created_at.isoformat(),
                "storage_type": "cloudinary",
            } for upload in cloudinary_uploads]
        
        # Get storage quota info
        try:
            quota = UserStorageQuota.objects.get(user=request.user)
            response_data['quota'] = {
                "cloudinary_used": quota.cloudinary_used,
                "cloudinary_limit": quota.cloudinary_limit,
                "local_used": quota.local_used,
                "local_limit": quota.local_limit,
                "total_files": quota.total_files,
                "max_files": quota.max_files,
                "usage_percentage": quota.get_usage_percentage(),
            }
        except UserStorageQuota.DoesNotExist:
            response_data['quota'] = None
        
        response_data['total_local'] = Image.objects.filter(user=request.user).count()
        response_data['total_cloudinary'] = CloudinaryUpload.objects.filter(
            user=request.user, is_deleted=False
        ).count()
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing user uploads: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Failed to list uploads: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def delete_user_upload(request, image_id):
    """
    Delete a user's uploaded image (supports both local and Cloudinary)
    Query param: storage_type=local|cloudinary (default: local)
    """
    try:
        from .models import Image
        from .cloud_storage_models import CloudinaryUpload, UserStorageQuota
        from django.core.files.storage import default_storage
        import cloudinary.uploader
        
        storage_type = request.GET.get('storage_type', 'local')
        
        if storage_type == 'cloudinary':
            # Delete Cloudinary upload
            try:
                upload = CloudinaryUpload.objects.get(id=image_id, user=request.user)
            except CloudinaryUpload.DoesNotExist:
                return Response(
                    {"error": "Upload not found or you don't have permission"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Soft delete first (mark as deleted)
            upload.soft_delete()
            
            # Update quota
            try:
                quota = UserStorageQuota.objects.get(user=request.user)
                quota.remove_cloudinary_usage(upload.file_size)
            except UserStorageQuota.DoesNotExist:
                pass
            
            # Optionally: Actually delete from Cloudinary
            # (You might want to do this in a background task)
            try:
                cloudinary.config(
                    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                    api_key=settings.CLOUDINARY_API_KEY,
                    api_secret=settings.CLOUDINARY_API_SECRET
                )
                cloudinary.uploader.destroy(upload.public_id)
                logger.info(f"Deleted from Cloudinary: {upload.public_id}")
            except Exception as e:
                logger.warning(f"Failed to delete from Cloudinary: {str(e)}")
                # Don't fail the request if Cloudinary delete fails
            
            return Response({
                "success": True,
                "message": "Cloudinary upload deleted successfully",
                "storage_type": "cloudinary"
            }, status=status.HTTP_200_OK)
        
        else:
            # Delete local upload
            try:
                image = Image.objects.get(id=image_id, user=request.user)
            except Image.DoesNotExist:
                return Response(
                    {"error": "Image not found or you don't have permission"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete the actual file from storage
            if image.image:
                try:
                    if default_storage.exists(image.image.name):
                        default_storage.delete(image.image.name)
                        logger.info(f"Deleted file: {image.image.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete file: {str(e)}")
            
            # Delete database record
            image.delete()
            
            return Response({
                "success": True,
                "message": "Local image deleted successfully",
                "storage_type": "local"
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error deleting upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Failed to delete upload: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_instagram_image(request):
    """
    Upload an image for Instagram posting and return its URL
    """
    try:
        if "image" not in request.FILES:
            return Response(
                {"error": "No image file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["image"]

        # Validate file type
        allowed_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
        ]

        if image_file.content_type not in allowed_types:
            return Response(
                {
                    "error": "Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check file size (limit to 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "File too large. Maximum size is 10MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate unique filename for Instagram
        ext = os.path.splitext(image_file.name)[1]
        if not ext:
            if image_file.content_type == "image/jpeg":
                ext = ".jpg"
            elif image_file.content_type == "image/png":
                ext = ".png"
            elif image_file.content_type == "image/gif":
                ext = ".gif"
            elif image_file.content_type == "image/webp":
                ext = ".webp"
            else:
                ext = ".jpg"

        filename = f"instagram_{request.user.id}_{uuid.uuid4().hex}{ext}"

        # Save the file to instagram_uploads directory
        file_path = os.path.join("instagram_uploads", filename)
        path = default_storage.save(file_path, ContentFile(image_file.read()))

        # Verify the file was saved successfully
        if not default_storage.exists(path):
            return Response(
                {"error": "Failed to save image file to storage"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Return the URL
        file_url = default_storage.url(path)

        # Make sure we return a full URL
        if file_url.startswith("/"):
            file_url = request.build_absolute_uri(file_url)

        return Response({"url": file_url}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": f"Upload failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def generate_ai_image(request):
    """
    Generate AI image using Runware API for mobile app
    """
    try:
        # Get API key from environment
        api_key = os.getenv("RUNWARE_API_KEY")
        if not api_key:
            logger.error("RUNWARE_API_KEY environment variable not configured")
            return Response(
                {"error": "AI image generation service not configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Get form data
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get generation parameters
        width = int(request.data.get("width", 512))
        height = int(request.data.get("height", 512))
        steps = int(request.data.get("steps", 30))
        model = request.data.get("model", "runware:101@1")

        logger.info(
            f"Starting AI image generation - prompt: {prompt[:50]}..., model: {model}"
        )

        # Prepare base payload
        payload = [
            {
                "taskType": "imageInference",
                "taskUUID": str(uuid.uuid4()),
                "model": model,
                "positivePrompt": prompt,
                "width": width,
                "height": height,
                "steps": steps,
            }
        ]

        # Check if an image was uploaded for image-to-image generation
        if "image" in request.FILES:
            image_file = request.FILES["image"]
            strength = float(request.data.get("strength", 0.9))

            # Validate image file
            allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif"]
            if image_file.content_type not in allowed_types:
                return Response(
                    {
                        "error": "Invalid image file type. Only JPEG, PNG and GIF are allowed."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Read and encode the image
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

            # Add image-specific parameters
            payload[0].update({"seedImage": image_data, "strength": strength})
            logger.info("Image-to-image generation requested")

        # Make the API request
        logger.info("Making request to Runware API")
        response = requests.post(
            "https://api.runware.ai/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,  # 2 minutes timeout for AI generation
        )

        logger.info(f"Runware API response status: {response.status_code}")

        if response.status_code != 200:
            error_message = "AI image generation failed"
            try:
                error_data = response.json()
                error_message = error_data.get("error", error_message)
                logger.error(f"Runware API error: {error_data}")
            except (json.JSONDecodeError, ValueError):
                error_message = f"API error: {response.status_code}"
                logger.error(f"Runware API non-JSON error: {response.text[:500]}")

            return Response(
                {"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            response_data = response.json()
            logger.info(f"Runware API response type: {type(response_data)}")
            logger.info(
                f"Runware API response structure: {json.dumps(response_data, indent=2)[:1000]}..."
            )
        except json.JSONDecodeError:
            logger.error(
                f"Failed to parse Runware API response as JSON: {response.text[:500]}"
            )
            return Response(
                {"error": "Invalid response from AI service"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Handle different response formats
        image_url = None
        task_uuid = None

        # Case 1: Response is a list with results
        if isinstance(response_data, list) and len(response_data) > 0:
            result = response_data[0]
            if isinstance(result, dict):
                if result.get("taskType") == "imageInference" and "imageURL" in result:
                    image_url = result["imageURL"]
                    task_uuid = result.get("taskUUID")
                    logger.info(f"Found image URL in list format: {image_url}")
                elif "imageURL" in result:
                    # Sometimes the response might not have taskType but still has imageURL
                    image_url = result["imageURL"]
                    task_uuid = result.get("taskUUID")
                    logger.info(f"Found image URL without taskType: {image_url}")
                else:
                    logger.error(f"No imageURL found in result: {result}")

        # Case 2: Response is a dict with nested data
        elif isinstance(response_data, dict):
            # Check if there's a data field with results
            if (
                "data" in response_data
                and isinstance(response_data["data"], list)
                and len(response_data["data"]) > 0
            ):
                result = response_data["data"][0]
                if isinstance(result, dict) and "imageURL" in result:
                    image_url = result["imageURL"]
                    task_uuid = result.get("taskUUID")
                    logger.info(f"Found image URL in nested data format: {image_url}")
            # Check if the dict itself contains the image URL
            elif "imageURL" in response_data:
                image_url = response_data["imageURL"]
                task_uuid = response_data.get("taskUUID")
                logger.info(f"Found image URL in direct dict format: {image_url}")
            else:
                logger.error(f"No imageURL found in dict response: {response_data}")

        if image_url:
            logger.info("Successfully generated AI image, now uploading to Cloudinary...")
            
            # ✅ CLOUDINARY MIGRATION: Upload image to Cloudinary instead of returning URL directly
            try:
                import cloudinary.uploader
                from io import BytesIO
                from .cloud_storage_models import CloudinaryUpload, UserStorageQuota
                
                # Download image from Runware URL
                img_response = requests.get(image_url, timeout=30)
                img_response.raise_for_status()
                image_bytes = img_response.content
                
                # Check storage quota
                quota, _ = UserStorageQuota.objects.get_or_create(user=request.user)
                file_size = len(image_bytes)
                
                if not quota.has_space_for(file_size):
                    return Response({
                        "error": "Storage quota exceeded. Please delete old files or upgrade.",
                        "quota_used": quota.cloudinary_used,
                        "quota_limit": quota.cloudinary_limit,
                    }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                
                # Upload to Cloudinary
                cloudinary_result = cloudinary.uploader.upload(
                    BytesIO(image_bytes),
                    folder=f"user_{request.user.id}/flow_generator/images",
                    resource_type="image",
                    quality="auto",
                    fetch_format="auto",
                    public_id=f"img_{uuid.uuid4().hex[:12]}",
                )
                
                # Track in database
                upload_record = CloudinaryUpload.objects.create(
                    user=request.user,
                    public_id=cloudinary_result['public_id'],
                    secure_url=cloudinary_result['secure_url'],
                    url=cloudinary_result.get('url', cloudinary_result['secure_url']),
                    folder=f"user_{request.user.id}/flow_generator/images",
                    original_filename=f"runware_{uuid.uuid4().hex[:8]}.png",
                    format=cloudinary_result.get('format', 'png'),
                    width=cloudinary_result.get('width'),
                    height=cloudinary_result.get('height'),
                    file_size=cloudinary_result.get('bytes', file_size),
                    purpose='image_generation',
                )
                
                # Update quota
                quota.add_cloudinary_usage(upload_record.file_size)
                
                logger.info(f"✅ Image uploaded to Cloudinary: {cloudinary_result['secure_url']}")
                
                return Response({
                    "success": True,
                    "image": cloudinary_result['secure_url'],  # ✅ Cloudinary HTTPS URL
                    "format": cloudinary_result.get('format', 'png'),
                    "width": cloudinary_result.get('width'),
                    "height": cloudinary_result.get('height'),
                    "cloudinary_id": cloudinary_result['public_id'],
                    "thumbnail": upload_record.get_thumbnail_url(width=400, height=400),
                })
                
            except Exception as cloudinary_error:
                logger.error(f"Cloudinary upload failed: {str(cloudinary_error)}")
                # Fallback: return original URL if Cloudinary fails
                return Response({
                    "success": True,
                    "image": image_url,
                    "error_note": "Uploaded to Cloudinary failed, using direct URL",
                })
        else:
            # Log the full response for debugging
            logger.error(
                f"No image URL found in response. Full response: {json.dumps(response_data, indent=2)}"
            )
            return Response(
                {
                    "error": "No image URL found in AI service response",
                    "debug_response": (
                        response_data
                        if len(str(response_data)) < 1000
                        else "Response too large to include"
                    ),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.exception("Unexpected error during AI image generation")
        return Response(
            {"error": f"Image generation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def generate_ai_image_openai(request):
    """
    Generate AI image using OpenAI's image generation API for mobile app
    """
    try:
        # Get form data
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get generation parameters
        size = request.data.get(
            "size", "1024x1024"
        )  # auto, 1024x1024, 1536x1024, 1024x1536
        background = request.data.get("background", "auto")  # auto, transparent, opaque
        moderation = request.data.get("moderation", "auto")  # auto, low
        output_format = request.data.get("output_format", "png")  # png, jpeg, webp
        output_compression = request.data.get("output_compression", 100)  # 0-100
        quality = request.data.get("quality", "low")  # auto, high, medium, low
        n = int(request.data.get("n", 1))  # 1-10
        user = request.data.get("user", None)  # Optional user identifier

        # Validate parameters and convert "auto" values to defaults
        valid_sizes = ["auto", "1024x1024", "1536x1024", "1024x1536"]
        if size not in valid_sizes:
            size = "1024x1024"
        elif size == "auto":
            size = "1024x1024"  # Convert auto to default

        valid_backgrounds = ["auto", "transparent", "opaque"]
        if background not in valid_backgrounds:
            background = "auto"

        valid_moderations = ["auto", "low"]
        if moderation not in valid_moderations:
            moderation = "auto"

        valid_formats = ["png", "jpeg", "webp"]
        if output_format not in valid_formats:
            output_format = "png"

        valid_qualities = ["auto", "high", "medium", "low"]
        if quality not in valid_qualities:
            quality = "low"
        elif quality == "auto":
            quality = "low"  # Convert auto to default

        # Validate compression (0-100)
        try:
            output_compression = int(output_compression)
            output_compression = max(0, min(100, output_compression))
        except (ValueError, TypeError):
            output_compression = 100

        # Validate n (1-10)
        try:
            n = int(n)
            n = max(1, min(10, n))
        except (ValueError, TypeError):
            n = 1

        logger.info(
            f"Starting OpenAI image generation - prompt: {prompt[:50]}..., "
            f"size: {size}, background: {background}, quality: {quality}, "
            f"format: {output_format}, compression: {output_compression}"
        )

        # Import OpenAI client utility
        from website.utils import get_openai_client

        # Configure OpenAI client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Check if image-to-image is requested (not directly supported)
        if "image" in request.FILES:
            logger.warning("Image-to-image generation not directly supported")
            return Response(
                {
                    "error": "Image-to-image generation not supported. Use text-to-image instead."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate image using OpenAI's image generation model
        # Use DALL-E 3 for better quality, fallback to DALL-E 2 if not available
        model = "dall-e-3"

        # DALL-E 3 only supports certain sizes
        if size not in ["1024x1024", "1792x1024", "1024x1792"]:
            size = "1024x1024"

        generation_params = {
            "model": model,
            "prompt": prompt,
            "n": 1,  # DALL-E 3 only supports n=1
            "size": size,
            "quality": "standard" if quality in ["low", "auto"] else "hd",
            "response_format": "b64_json",  # Always use base64 for mobile apps
        }

        # Add optional user identifier if provided
        if user:
            generation_params["user"] = user

        try:
            response = client.images.generate(**generation_params)
        except Exception as dalle3_error:
            # Fallback to DALL-E 2 if DALL-E 3 fails
            logger.warning(f"DALL-E 3 failed, falling back to DALL-E 2: {dalle3_error}")
            generation_params.update(
                {
                    "model": "dall-e-2",
                    "quality": "standard",  # DALL-E 2 doesn't support 'hd' quality
                    "size": "1024x1024",  # DALL-E 2 supports limited sizes
                }
            )
            response = client.images.generate(**generation_params)

        # ✅ CLOUDINARY MIGRATION: Upload images to Cloudinary
        try:
            import cloudinary.uploader
            from io import BytesIO
            from .cloud_storage_models import CloudinaryUpload, UserStorageQuota
            
            cloudinary_urls = []
            quota, _ = UserStorageQuota.objects.get_or_create(user=request.user)
            
            for image in response.data:
                # Get image bytes
                if hasattr(image, "b64_json") and image.b64_json:
                    image_bytes = base64.b64decode(image.b64_json)
                elif hasattr(image, "url") and image.url:
                    img_response = requests.get(image.url)
                    image_bytes = img_response.content
                else:
                    continue
                
                # Check quota
                file_size = len(image_bytes)
                if not quota.has_space_for(file_size):
                    return Response({
                        "error": "Storage quota exceeded",
                        "quota_used": quota.cloudinary_used,
                        "quota_limit": quota.cloudinary_limit,
                    }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                
                # Upload to Cloudinary
                cloudinary_result = cloudinary.uploader.upload(
                    BytesIO(image_bytes),
                    folder=f"user_{request.user.id}/flow_generator/images",
                    resource_type="image",
                    quality="auto",
                    fetch_format="auto",
                    public_id=f"dalle_{uuid.uuid4().hex[:12]}",
                )
                
                # Track in database
                upload_record = CloudinaryUpload.objects.create(
                    user=request.user,
                    public_id=cloudinary_result['public_id'],
                    secure_url=cloudinary_result['secure_url'],
                    url=cloudinary_result.get('url', cloudinary_result['secure_url']),
                    folder=f"user_{request.user.id}/flow_generator/images",
                    original_filename=f"dalle_{uuid.uuid4().hex[:8]}.png",
                    format=cloudinary_result.get('format', 'png'),
                    width=cloudinary_result.get('width'),
                    height=cloudinary_result.get('height'),
                    file_size=cloudinary_result.get('bytes', file_size),
                    purpose='image_generation',
                )
                
                # Update quota
                quota.add_cloudinary_usage(upload_record.file_size)
                
                cloudinary_urls.append(cloudinary_result['secure_url'])
            
            logger.info(f"✅ Uploaded {len(cloudinary_urls)} images to Cloudinary")
            
            return Response({
                "success": True,
                "image": cloudinary_urls[0] if cloudinary_urls else None,  # ✅ First image URL
                "images": cloudinary_urls,  # ✅ All image URLs
                "format": "png",
                "model": generation_params["model"],
                "size": size,
                "quality": generation_params["quality"],
                "usage": getattr(response, "usage", None),
            })
            
        except Exception as cloudinary_error:
            logger.error(f"Cloudinary upload failed: {str(cloudinary_error)}")
            # Fallback to base64 if Cloudinary fails
            images_data = []
            for image in response.data:
                if hasattr(image, "b64_json") and image.b64_json:
                    images_data.append(f"data:image/png;base64,{image.b64_json}")
            return Response({
                "success": True,
                "image": images_data[0] if images_data else None,
                "images": images_data,
                "error_note": "Cloudinary upload failed, using base64",
            })

    except Exception as e:
        logger.exception("Unexpected error during OpenAI image generation")
        return Response(
            {"error": f"Image generation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def generate_ai_image_edit_openai(request):
    """
    Generate AI image using OpenAI's GPT-4V image editing API.
    Follows the simple working example exactly.
    """
    try:
        from openai import OpenAI
        import os

        # Get prompt from request
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get images from request
        images = []
        image_count = 0
        while f"image_{image_count}" in request.FILES:
            # Save uploaded file temporarily
            uploaded_file = request.FILES[f"image_{image_count}"]
            temp_path = f"/tmp/image_{image_count}.png"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
            images.append(open(temp_path, "rb"))
            image_count += 1

        if not images:
            return Response(
                {"error": "At least one image is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Initialize OpenAI client
        client = OpenAI()

        # Make the API call exactly like the example
        result = client.images.edit(
            model="gpt-image-1",
            image=images,  # Pass file objects directly
            prompt=prompt,
        )

        # ✅ CLOUDINARY MIGRATION: Upload to Cloudinary instead of returning base64
        try:
            import cloudinary.uploader
            from io import BytesIO
            from .cloud_storage_models import CloudinaryUpload, UserStorageQuota
            
            # Get image bytes from base64
            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)
            
            # Check quota
            quota, _ = UserStorageQuota.objects.get_or_create(user=request.user)
            file_size = len(image_bytes)
            
            if not quota.has_space_for(file_size):
                return Response({
                    "error": "Storage quota exceeded",
                    "quota_used": quota.cloudinary_used,
                    "quota_limit": quota.cloudinary_limit,
                }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            
            # Upload to Cloudinary
            cloudinary_result = cloudinary.uploader.upload(
                BytesIO(image_bytes),
                folder=f"user_{request.user.id}/flow_generator/images",
                resource_type="image",
                quality="auto",
                fetch_format="auto",
                public_id=f"gptimg_{uuid.uuid4().hex[:12]}",
            )
            
            # Track in database
            upload_record = CloudinaryUpload.objects.create(
                user=request.user,
                public_id=cloudinary_result['public_id'],
                secure_url=cloudinary_result['secure_url'],
                url=cloudinary_result.get('url', cloudinary_result['secure_url']),
                folder=f"user_{request.user.id}/flow_generator/images",
                original_filename=f"gptimage_{uuid.uuid4().hex[:8]}.png",
                format=cloudinary_result.get('format', 'png'),
                width=cloudinary_result.get('width'),
                height=cloudinary_result.get('height'),
                file_size=cloudinary_result.get('bytes', file_size),
                purpose='image_generation',
            )
            
            # Update quota
            quota.add_cloudinary_usage(upload_record.file_size)
            
            logger.info(f"✅ GPT Image uploaded to Cloudinary: {cloudinary_result['secure_url']}")
            
            return Response({
                "success": True,
                "image": cloudinary_result['secure_url'],  # ✅ Cloudinary URL
                "format": cloudinary_result.get('format', 'png'),
                "cloudinary_id": cloudinary_result['public_id'],
            })
            
        except Exception as cloudinary_error:
            logger.error(f"Cloudinary upload failed: {str(cloudinary_error)}")
            # Fallback to base64
            return Response({
                "image": f"data:image/png;base64,{image_base64}",
                "format": "base64",
                "error_note": "Cloudinary upload failed",
            })

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    finally:
        # Clean up temporary files
        for i in range(image_count):
            try:
                os.remove(f"/tmp/image_{i}.png")
            except OSError:
                pass
        # Close file handles
        for img in images:
            try:
                img.close()
            except OSError:
                pass


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@parser_classes([MultiPartParser, FormParser])
def gpt_image_multi_reference(request):
    """
    Generate AI image using GPT Image with multiple reference images.
    Supports uploading multiple images as references to generate a new composite image.
    NOTE: AllowAny for server-side calls from Next.js
    """
    try:
        from openai import OpenAI
        import base64
        import tempfile
        import os

        # Get prompt from request
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get optional parameters
        size = request.data.get("size", "1024x1024")
        quality = request.data.get("quality", "auto")
        background = request.data.get("background", "auto")
        output_format = request.data.get("output_format", "png")
        output_compression = int(request.data.get("output_compression", 100))
        
        # Get reference images
        images = []
        temp_paths = []
        image_count = 0
        
        while f"image_{image_count}" in request.FILES:
            uploaded_file = request.FILES[f"image_{image_count}"]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(uploaded_file.read())
            temp_file.close()
            temp_paths.append(temp_file.name)
            images.append(open(temp_file.name, "rb"))
            image_count += 1

        if not images:
            return Response(
                {"error": "At least one reference image is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Generating image with {len(images)} reference images")

        # Initialize OpenAI client from database
        from website.utils import get_openai_client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Make the API call with multiple images
        result = client.images.edit(
            model="gpt-image-1",
            image=images,
            prompt=prompt,
            size=size,
            quality=quality,
            background=background,
            output_format=output_format,
            output_compression=output_compression,
        )

        # ✅ CLOUDINARY MIGRATION: Upload to Cloudinary
        try:
            import cloudinary.uploader
            from io import BytesIO
            from .cloud_storage_models import CloudinaryUpload, UserStorageQuota
            
            # Get image bytes from base64
            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)
            file_size = len(image_bytes)
            
            # Check quota (only for authenticated users)
            if request.user.is_authenticated:
                quota, _ = UserStorageQuota.objects.get_or_create(user=request.user)
                if not quota.has_space_for(file_size):
                    return Response({
                        "error": "Storage quota exceeded",
                        "quota_used": quota.cloudinary_used,
                        "quota_limit": quota.cloudinary_limit,
                    }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            
            # Determine folder based on authentication
            folder = f"user_{request.user.id}/flow_generator/images" if request.user.is_authenticated else "anonymous/flow_generator/images"
            
            # Upload to Cloudinary
            cloudinary_result = cloudinary.uploader.upload(
                BytesIO(image_bytes),
                folder=folder,
                resource_type="image",
                quality="auto",
                fetch_format="auto",
                public_id=f"multiref_{uuid.uuid4().hex[:12]}",
            )
            
            # Track in database (only for authenticated users)
            if request.user.is_authenticated:
                upload_record = CloudinaryUpload.objects.create(
                    user=request.user,
                    public_id=cloudinary_result['public_id'],
                    secure_url=cloudinary_result['secure_url'],
                    url=cloudinary_result.get('url', cloudinary_result['secure_url']),
                    folder=folder,
                    original_filename=f"multiref_{uuid.uuid4().hex[:8]}.{output_format}",
                    format=cloudinary_result.get('format', output_format),
                    width=cloudinary_result.get('width'),
                    height=cloudinary_result.get('height'),
                    file_size=cloudinary_result.get('bytes', file_size),
                    purpose='image_generation',
                )
                
                # Update quota
                quota.add_cloudinary_usage(upload_record.file_size)
            
            logger.info(f"✅ Multi-ref image uploaded to Cloudinary: {cloudinary_result['secure_url']}")
            
            return Response({
                "success": True,
                "image": cloudinary_result['secure_url'],  # ✅ Cloudinary URL
                "format": cloudinary_result.get('format', output_format),
                "reference_count": len(images),
                "size": size,
                "quality": quality,
                "cloudinary_id": cloudinary_result['public_id'],
            })
            
        except Exception as cloudinary_error:
            logger.error(f"Cloudinary upload failed: {str(cloudinary_error)}")
            # Fallback to base64
            return Response({
                "success": True,
                "image": f"data:image/{output_format};base64,{image_base64}",
                "format": output_format,
                "reference_count": len(images),
                "error_note": "Cloudinary upload failed",
            })

    except Exception as e:
        logger.exception("Error in multi-reference image generation")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # Clean up temporary files
        for img in images:
            try:
                img.close()
            except:
                pass
        for path in temp_paths:
            try:
                os.remove(path)
            except:
                pass


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def gpt_image_inpainting(request):
    """
    Edit part of an image using a mask (inpainting).
    Requires an image and a mask to indicate which areas should be edited.
    """
    try:
        from openai import OpenAI
        import base64
        import tempfile
        import os

        # Get prompt from request
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get required image and mask
        if "image" not in request.FILES:
            return Response(
                {"error": "Image file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if "mask" not in request.FILES:
            return Response(
                {"error": "Mask file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get optional parameters
        size = request.data.get("size", "1024x1024")
        quality = request.data.get("quality", "high")
        background = request.data.get("background", "auto")
        output_format = request.data.get("output_format", "png")

        # Save uploaded files temporarily
        image_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        image_temp.write(request.FILES["image"].read())
        image_temp.close()

        mask_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        mask_temp.write(request.FILES["mask"].read())
        mask_temp.close()

        logger.info(f"Performing inpainting with mask")

        # Initialize OpenAI client from database
        from website.utils import get_openai_client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Open files for API call
        with open(image_temp.name, "rb") as image_file, open(mask_temp.name, "rb") as mask_file:
            result = client.images.edit(
                model="gpt-image-1",
                image=image_file,
                mask=mask_file,
                prompt=prompt,
                size=size,
                quality=quality,
                background=background,
                output_format=output_format,
            )

        # Get base64 image data
        image_base64 = result.data[0].b64_json

        return Response({
            "success": True,
            "image": image_base64,
            "format": output_format,
            "size": size,
            "quality": quality,
        })

    except Exception as e:
        logger.exception("Error in inpainting")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # Clean up temporary files
        try:
            os.remove(image_temp.name)
            os.remove(mask_temp.name)
        except:
            pass


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def gpt_image_high_fidelity(request):
    """
    Generate or edit images with high input fidelity.
    Preserves details from input images like faces, logos, and textures.
    """
    try:
        from openai import OpenAI
        import base64
        import tempfile
        import os

        # Get prompt from request
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get optional parameters
        size = request.data.get("size", "1024x1024")
        quality = request.data.get("quality", "high")
        background = request.data.get("background", "auto")
        output_format = request.data.get("output_format", "png")
        input_fidelity = "high"  # This is the key parameter for high fidelity

        # Get reference images
        images = []
        temp_paths = []
        image_count = 0
        
        while f"image_{image_count}" in request.FILES:
            uploaded_file = request.FILES[f"image_{image_count}"]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(uploaded_file.read())
            temp_file.close()
            temp_paths.append(temp_file.name)
            images.append(open(temp_file.name, "rb"))
            image_count += 1

        if not images:
            return Response(
                {"error": "At least one input image is required for high fidelity editing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Generating high fidelity image with {len(images)} input images")

        # Initialize OpenAI client from database
        from website.utils import get_openai_client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Make the API call (high quality by default)
        result = client.images.edit(
            model="gpt-image-1",
            image=images,
            prompt=prompt,
            size=size,
            quality=quality,
            background=background,
            output_format=output_format,
        )

        # Get base64 image data
        image_base64 = result.data[0].b64_json

        return Response({
            "success": True,
            "image": image_base64,
            "format": output_format,
            "input_count": len(images),
            "size": size,
            "quality": quality,
        })

    except Exception as e:
        logger.exception("Error in high fidelity image generation")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # Clean up temporary files
        for img in images:
            try:
                img.close()
            except:
                pass
        for path in temp_paths:
            try:
                os.remove(path)
            except:
                pass


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def gpt_image_generate_advanced(request):
    """
    Advanced GPT Image generation with all customization options.
    Supports transparent backgrounds, quality settings, format options, etc.
    NOTE: AllowAny for server-side calls from Next.js
    """
    try:
        from openai import OpenAI
        import base64

        # Get prompt from request
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get all optional parameters
        size = request.data.get("size", "auto")  # auto, 1024x1024, 1536x1024, 1024x1536
        quality = request.data.get("quality", "auto")  # auto, low, medium, high
        background = request.data.get("background", "auto")  # auto, transparent, opaque
        output_format = request.data.get("output_format", "png")  # png, jpeg, webp
        output_compression = int(request.data.get("output_compression", 100))  # 0-100
        moderation = request.data.get("moderation", "auto")  # auto, low
        n = int(request.data.get("n", 1))  # Number of images to generate (1-10)

        # Validate parameters
        valid_sizes = ["auto", "1024x1024", "1536x1024", "1024x1536"]
        if size not in valid_sizes:
            size = "auto"

        valid_qualities = ["auto", "low", "medium", "high"]
        if quality not in valid_qualities:
            quality = "auto"

        valid_backgrounds = ["auto", "transparent", "opaque"]
        if background not in valid_backgrounds:
            background = "auto"

        valid_formats = ["png", "jpeg", "webp"]
        if output_format not in valid_formats:
            output_format = "png"

        valid_moderations = ["auto", "low"]
        if moderation not in valid_moderations:
            moderation = "auto"

        # Validate compression and n
        output_compression = max(0, min(100, output_compression))
        n = max(1, min(10, n))

        logger.info(f"Advanced GPT image generation: prompt={prompt[:50]}..., size={size}, quality={quality}, background={background}")

        # Initialize OpenAI client from database
        from website.utils import get_openai_client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Generate image with all parameters
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
            quality=quality,
            background=background,
            output_format=output_format,
            output_compression=output_compression,
            moderation=moderation,
            n=n,
        )

        # Extract base64 images
        images_data = [img.b64_json for img in result.data]

        return Response({
            "success": True,
            "images": images_data,
            "count": len(images_data),
            "format": output_format,
            "size": size,
            "quality": quality,
            "background": background,
            "moderation": moderation,
        })

    except Exception as e:
        logger.exception("Error in advanced GPT image generation")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def gpt_image_transparent_background(request):
    """
    Generate images with transparent backgrounds using GPT Image.
    Perfect for sprites, logos, and design elements.
    """
    try:
        from openai import OpenAI
        import base64

        # Get prompt from request
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get optional parameters
        size = request.data.get("size", "1024x1024")
        quality = request.data.get("quality", "high")  # Transparency works best with medium/high quality
        output_format = request.data.get("output_format", "png")  # Only png and webp support transparency

        # Validate format for transparency
        if output_format not in ["png", "webp"]:
            output_format = "png"

        logger.info(f"Generating transparent background image: {prompt[:50]}...")

        # Initialize OpenAI client from database
        from website.utils import get_openai_client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Generate image with transparent background
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
            quality=quality,
            background="transparent",
            output_format=output_format,
        )

        # Get base64 image data
        image_base64 = result.data[0].b64_json

        return Response({
            "success": True,
            "image": image_base64,
            "format": output_format,
            "background": "transparent",
            "size": size,
            "quality": quality,
        })

    except Exception as e:
        logger.exception("Error generating transparent background image")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def gpt_image_streaming(request):
    """
    Stream image generation with partial images.
    Returns progressive image updates as the image is being generated.
    """
    try:
        from openai import OpenAI
        import base64
        from django.http import StreamingHttpResponse
        import json

        # Get prompt from request
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get optional parameters
        size = request.data.get("size", "1024x1024")
        quality = request.data.get("quality", "auto")
        partial_images = int(request.data.get("partial_images", 2))  # 0-3 partial images

        # Validate partial_images
        partial_images = max(0, min(3, partial_images))

        logger.info(f"Starting streaming image generation with {partial_images} partial images")

        # Initialize OpenAI client from database
        from website.utils import get_openai_client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        def generate_stream():
            """Generator function for streaming response"""
            try:
                stream = client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    stream=True,
                    partial_images=partial_images,
                )

                for event in stream:
                    if event.type == "image_generation.partial_image":
                        data = {
                            "type": "partial",
                            "index": event.partial_image_index,
                            "image": event.b64_json,
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                    elif event.type == "image_generation.done":
                        data = {
                            "type": "complete",
                            "image": event.b64_json,
                        }
                        yield f"data: {json.dumps(data)}\n\n"
            except Exception as e:
                error_data = {
                    "type": "error",
                    "error": str(e),
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        response = StreamingHttpResponse(
            generate_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    except Exception as e:
        logger.exception("Error in streaming image generation")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@parser_classes([MultiPartParser, FormParser])
def generate_ai_video(request, organization_pk=None, brand_pk=None):
    """
    Generate AI video using multi-model providers (Sora 2, Veo 3.1)
    Supports both Sora (OpenAI) and Veo (Kie AI) models
    NOTE: AllowAny for server-side calls from Next.js
    """
    try:
        # Get form data
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get model parameter (determines which provider to use)
        model = request.data.get("model", "sora2").lower()  # sora2, veo3, veo3_fast
        
        logger.info(
            f"Generating video for user {request.user.id} with model '{model}' and prompt: {prompt[:100]}"
        )

        # Route to appropriate provider based on model
        if model.startswith("veo"):
            return _generate_veo_video(request, prompt, model)
        else:
            return _generate_sora_video(request, prompt, model)

    except Exception as e:
        logger.exception("Unexpected error during video generation")
        return Response(
            {"error": f"Video generation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _generate_sora_video(request, prompt, model):
    """Generate video using Sora 2 (OpenAI) provider"""
    try:
        from website.video_utils import video_service

        # Get generation parameters
        provider = request.data.get("provider", "runware")  # runware, openai
        quality = request.data.get("quality", "low")  # low, high
        duration = float(request.data.get("duration", 5.0))  # seconds
        aspect_ratio = request.data.get("aspect_ratio", "9:16")  # Instagram format

        # Validate parameters
        valid_providers = ["runware", "openai"]
        if provider not in valid_providers:
            provider = "runware"

        valid_qualities = ["low", "high"]
        if quality not in valid_qualities:
            quality = "low"

        valid_aspect_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4"]
        if aspect_ratio not in valid_aspect_ratios:
            aspect_ratio = "9:16"

        # Clamp duration
        duration = max(1.0, min(duration, 60.0))

        # Generate video
        video_url, metadata = video_service.generate_video(
            prompt=prompt,
            provider=provider,
            quality=quality,
            duration=duration,
            aspect_ratio=aspect_ratio,
        )

        # Return success response
        response_data = {
            "success": True,
            "video_url": video_url,
            "model": "sora2",
            "metadata": {
                "provider": metadata.get("provider"),
                "prompt": prompt,
                "quality": quality,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "generation_id": metadata.get("generation_id"),
                "width": metadata.get("width"),
                "height": metadata.get("height"),
            },
        }

        logger.info(f"Successfully generated Sora video for user {request.user.id}")
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as video_error:
        logger.error(
            f"Sora video generation failed for user {request.user.id}: {str(video_error)}"
        )
        return Response(
            {"error": f"Video generation failed: {str(video_error)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _generate_veo_video(request, prompt, model):
    """Generate video using Veo 3.1 (Kie AI) provider"""
    try:
        from website.veo_utils import veo_generator

        # Get generation parameters
        aspect_ratio = request.data.get("aspect_ratio", "9:16")  # 16:9, 9:16, Auto
        generation_type = request.data.get("generation_type", "TEXT_2_VIDEO")
        
        # Optional parameters
        image_urls = request.data.getlist("image_urls", [])
        seeds = request.data.getlist("seeds", [])
        watermark = request.data.get("watermark", "false").lower() == "true"
        callback_url = request.data.get("callback_url", "")
        enable_translation = request.data.get("enable_translation", "true").lower() == "true"

        # Validate model
        valid_models = ["veo3", "veo3_fast"]
        if model not in valid_models:
            model = "veo3"

        # Validate aspect ratio for Veo
        valid_aspect_ratios = ["16:9", "9:16", "Auto"]
        if aspect_ratio not in valid_aspect_ratios:
            aspect_ratio = "9:16"

        # Validate generation type
        valid_generation_types = ["TEXT_2_VIDEO", "FIRST_AND_LAST_FRAMES_2_VIDEO", "REFERENCE_2_VIDEO"]
        if generation_type not in valid_generation_types:
            generation_type = "TEXT_2_VIDEO"

        # Generate video (async - returns task ID)
        result = veo_generator.generate_video(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            generation_type=generation_type,
            image_urls=image_urls if image_urls else None,
            seeds=seeds if seeds else None,
            watermark=watermark,
            callback_url=callback_url if callback_url else None,
            enable_translation=enable_translation,
        )

        # Return task info (Veo is async, client needs to poll for status)
        response_data = {
            "success": True,
            "task_id": result["task_id"],
            "model": model,
            "status": "generating",
            "metadata": {
                "prompt": prompt,
                "aspect_ratio": result.get("aspect_ratio"),
                "generation_type": result.get("generation_type"),
                "watermark": watermark,
            },
        }

        logger.info(f"Successfully initiated Veo video generation for user {request.user.id}, task_id: {result['task_id']}")
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as video_error:
        logger.error(
            f"Veo video generation failed for user {request.user.id}: {str(video_error)}"
        )
        return Response(
            {"error": f"Video generation failed: {str(video_error)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def generate_kling_video(request):
    """
    Generate video using Kling AI (AIML API)
    Supports image-to-video generation
    NOTE: AllowAny for server-side calls from Next.js
    """
    try:
        from website.kling_utils import kling_generator
        
        # Get JSON data
        image_url = request.data.get("image_url", "").strip()
        prompt = request.data.get("prompt", "").strip()
        
        if not image_url:
            return Response(
                {"error": "image_url is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not prompt:
            return Response(
                {"error": "prompt is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional parameters
        duration = int(request.data.get("duration", 5))  # 5 or 10 seconds
        cfg_scale = float(request.data.get("cfg_scale", 0.5))  # 0-1
        negative_prompt = request.data.get("negative_prompt", "")
        
        # Validate duration
        if duration not in [5, 10]:
            duration = 5
        
        logger.info(f"Generating Kling video with prompt: {prompt[:100]}")
        
        # Generate video (returns task info)
        result = kling_generator.generate_video(
            image_url=image_url,
            prompt=prompt,
            duration=duration,
            cfg_scale=cfg_scale,
            negative_prompt=negative_prompt if negative_prompt else None
        )
        
        # Return task info (client needs to poll for status)
        response_data = {
            "success": True,
            "generation_id": result.get("id"),
            "status": result.get("status", "queued"),
            "model": "kling",
            "metadata": {
                "prompt": prompt,
                "image_url": image_url,
                "duration": duration,
            },
        }
        
        logger.info(f"Kling task created: {result.get('id')}")
        return Response(response_data, status=status.HTTP_200_OK)
    
    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors from AIML API
        error_msg = str(e)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', str(e))
                
                # Check for specific error types
                if e.response.status_code == 403:
                    if 'verification' in error_msg.lower():
                        error_msg = "AIML API account verification required. Please verify your account at https://aimlapi.com/app/billing/verification"
                    elif 'credit' in error_msg.lower():
                        error_msg = "AIML API credits exhausted. Please add credits at https://aimlapi.com/app/billing"
                    status_code = status.HTTP_402_PAYMENT_REQUIRED
            except:
                pass
        
        logger.error(f"Kling video generation failed: {error_msg}")
        return Response(
            {
                "success": False,
                "error": error_msg,
                "error_type": "api_error"
            },
            status=status_code
        )
    
    except Exception as e:
        logger.error(f"Kling video generation failed: {str(e)}")
        return Response(
            {
                "success": False,
                "error": f"Video generation failed: {str(e)}",
                "error_type": "internal_error"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def get_kling_video_status(request, generation_id):
    """
    Check the status of a Kling video generation task
    Returns: status, video URL when complete
    NOTE: AllowAny for server-side calls from Next.js
    """
    try:
        from urllib.parse import unquote
        from website.kling_utils import kling_generator
        
        # URL decode the generation_id (handles special characters like : and /)
        generation_id = unquote(generation_id)
        
        # Get video status
        status_data = kling_generator.get_video_status(generation_id)
        
        # Format response
        video_status = status_data.get("status", "unknown")
        response_data = {
            "generation_id": generation_id,
            "status": video_status,
        }
        
        # Add video URL if completed
        if video_status == "completed":
            video_info = status_data.get("video", {})
            response_data["video_url"] = video_info.get("url")
            response_data["duration"] = video_info.get("duration")
        elif video_status == "error":
            response_data["error"] = status_data.get("error", "Generation failed")
        
        # Add metadata if present
        if "meta" in status_data:
            response_data["meta"] = status_data["meta"]
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error checking Kling video status for {generation_id}: {str(e)}")
        return Response(
            {"error": f"Failed to check status: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def get_veo_video_status(request, task_id):
    """
    Check the status of a Veo video generation task
    Returns: status, success_flag, video URLs when complete
    NOTE: AllowAny for server-side calls from Next.js
    """
    try:
        from website.veo_utils import veo_generator

        # Get video status
        status_data = veo_generator.get_video_status(task_id)
        
        # Format response
        success_flag = status_data.get("success_flag", 0)
        response_data = {
            "task_id": task_id,
            "status": status_data.get("status", "unknown"),
            "success_flag": success_flag,
        }

        # Add video URLs if generation is complete
        if success_flag == 1:
            response_data["video_urls"] = status_data.get("result_urls", [])
            response_data["origin_urls"] = status_data.get("origin_urls", [])
            response_data["resolution"] = status_data.get("resolution", "")
        elif success_flag in [2, 3]:
            response_data["error"] = {
                "code": status_data.get("error_code", 0),
                "message": status_data.get("error_message", "Generation failed"),
            }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error checking Veo video status for task {task_id}: {str(e)}")
        return Response(
            {"error": f"Failed to check video status: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def get_veo_1080p_video(request, task_id):
    """
    Get the 1080p version of a completed Veo video
    Returns: 1080p video URL
    NOTE: AllowAny for server-side calls from Next.js
    """
    try:
        from website.veo_utils import veo_generator

        # Get 1080p video
        hd_data = veo_generator.get_1080p_video(task_id)
        
        response_data = {
            "task_id": task_id,
            "video_url": hd_data.get("url", ""),
            "resolution": "1080p",
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting 1080p video for task {task_id}: {str(e)}")
        return Response(
            {"error": f"Failed to get 1080p video: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_reference_image(request):
    """
    Upload reference image to public storage and return URL
    Used for video generation APIs that require public image URLs (e.g., Veo)
    Requires authentication - files are organized by user ID
    """
    try:
        import uuid
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        from .models import Image

        image_file = request.FILES.get('image')
        if not image_file:
            return Response(
                {"error": "No image file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate unique filename with user ID
        ext = image_file.name.split('.')[-1] if '.' in image_file.name else 'png'
        filename = f"user_uploads/{request.user.id}/references/{uuid.uuid4()}.{ext}"
        
        # Save to media storage (will be publicly accessible)
        file_path = default_storage.save(filename, ContentFile(image_file.read()))
        
        # Build absolute URL
        public_url = request.build_absolute_uri(default_storage.url(file_path))
        
        # Create database record
        image_record = Image.objects.create(
            user=request.user,
            image=file_path,
            title=f"Reference image {uuid.uuid4().hex[:8]}",
            alt_text="AI-generated reference image"
        )
        
        logger.info(f"User {request.user.id} uploaded reference image: {public_url}")
        
        return Response({
            "success": True,
            "url": public_url,
            "filename": filename,
            "image_id": image_record.id,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Reference image upload failed: {str(e)}")
        return Response(
            {"error": f"Upload failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.AllowAny])  # Allow anonymous uploads for flow-generator
@parser_classes([MultiPartParser, FormParser])
def upload_to_cloudinary(request):
    """
    Upload image to Cloudinary and return public URL
    Used for Kling AI image-to-video generation and flow-generator
    Supports both authenticated and anonymous uploads
    Features: Validation, quota checking (for authenticated users), proper database tracking
    """
    try:
        import cloudinary
        import cloudinary.uploader
        from .cloud_storage_models import CloudinaryUpload, UserStorageQuota
        from PIL import Image as PILImage
        from io import BytesIO
        
        # Get image file
        image_file = request.FILES.get('image')
        if not image_file:
            return Response(
                {"error": "No image file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type (images and videos)
        allowed_types = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo'
        ]
        if image_file.content_type not in allowed_types:
            return Response(
                {"error": f"Invalid file type. Allowed: {', '.join(allowed_types)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 100MB for videos, 10MB for images)
        is_video = image_file.content_type.startswith('video/')
        max_size = (100 if is_video else 10) * 1024 * 1024
        if image_file.size > max_size:
            return Response(
                {"error": f"File too large. Maximum size is {max_size / (1024*1024)}MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check user's storage quota (only for authenticated users)
        if request.user.is_authenticated:
            quota, created = UserStorageQuota.objects.get_or_create(user=request.user)
            if not quota.has_space_for(image_file.size):
                return Response({
                    "error": f"Storage quota exceeded. Used: {quota.get_usage_percentage()}%",
                    "quota_used": quota.cloudinary_used + quota.local_used,
                    "quota_limit": quota.cloudinary_limit + quota.local_limit,
                }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        
        # Get image dimensions before upload
        try:
            img = PILImage.open(image_file)
            width, height = img.size
            image_file.seek(0)  # Reset file pointer
        except Exception:
            width, height = None, None
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET
        )
        
        # Determine purpose from request
        purpose = request.data.get('purpose', 'kling_reference')
        
        # Determine resource type (image or video)
        resource_type = 'video' if is_video else 'image'
        
        # Upload to Cloudinary with user-specific or anonymous folder
        if request.user.is_authenticated:
            user_folder = f"user_{request.user.id}/{purpose}"
            logger.info(f"User {request.user.id} uploading {image_file.name} ({resource_type}) to Cloudinary folder: {user_folder}")
        else:
            user_folder = f"anonymous/{purpose}"
            logger.info(f"Anonymous user uploading {image_file.name} ({resource_type}) to Cloudinary folder: {user_folder}")
        
        result = cloudinary.uploader.upload(
            image_file,
            folder=user_folder,
            resource_type=resource_type,
            quality='auto',  # Auto-optimize quality
            fetch_format='auto',  # Auto-convert to best format
        )
        
        public_url = result['secure_url']
        logger.info(f"Cloudinary upload successful: {public_url}")
        
        # Create proper database record with full metadata (only for authenticated users)
        upload_record = None
        if request.user.is_authenticated:
            upload_record = CloudinaryUpload.objects.create(
                user=request.user,
                public_id=result['public_id'],
                secure_url=result['secure_url'],
                url=result.get('url', result['secure_url']),
                folder=user_folder,
                original_filename=image_file.name,
                format=result.get('format', image_file.name.split('.')[-1]),
                width=result.get('width', width),
                height=result.get('height', height),
                file_size=result.get('bytes', image_file.size),
                purpose=purpose if purpose in dict(CloudinaryUpload.UPLOAD_PURPOSES) else 'other',
            )
            
            # Update user's storage quota
            quota.add_cloudinary_usage(image_file.size)
        
        return Response({
            "success": True,
            "url": public_url,
            "public_id": result['public_id'],
            "format": result['format'],
            "width": result.get('width'),
            "height": result.get('height'),
            "file_size": result.get('bytes'),
            "upload_id": upload_record.id if upload_record else None,
            "thumbnail_url": upload_record.get_thumbnail_url(width=300, height=300),
            "quota_used_percentage": quota.get_usage_percentage(),
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Cloudinary upload failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def generate_ai_audio(request):
    """
    Generate AI audio using AI/ML API with ElevenLabs eleven_turbo_v2_5 model
    Supports text-to-speech and audio file playback
    """
    try:
        # Debug logging
        logger.info(f"Audio generation request from user: {request.user}")
        logger.info(f"Request data keys: {request.data.keys()}")
        logger.info(f"Request FILES keys: {request.FILES.keys()}")
        
        # Check if it's text-to-speech or audio file upload
        text = request.data.get("text", "").strip()
        audio_file = request.FILES.get("audio_file")
        
        if audio_file:
            # Handle audio file upload - just store and return URL
            try:
                # Save the uploaded audio file
                file_name = f"audio_{uuid.uuid4()}.{audio_file.name.split('.')[-1]}"
                file_path = default_storage.save(
                    f"user_uploads/{request.user.id}/audio/{file_name}",
                    ContentFile(audio_file.read())
                )
                audio_url = default_storage.url(file_path)
                
                # Build full URL if it's relative
                if audio_url.startswith('/'):
                    audio_url = request.build_absolute_uri(audio_url)
                
                return Response({
                    "success": True,
                    "audio_url": audio_url,
                    "type": "uploaded",
                    "file_path": file_path,
                }, status=status.HTTP_200_OK)
                
            except Exception as upload_error:
                logger.error(f"Audio upload failed: {str(upload_error)}")
                return Response(
                    {"error": f"Audio upload failed: {str(upload_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        elif text:
            # Text-to-speech using AI/ML API with ElevenLabs eleven_turbo_v2_5 model
            try:
                # Get AIML API key from settings
                aiml_api_key = getattr(settings, 'AIML_API_KEY', None)
                if not aiml_api_key:
                    return Response(
                        {"error": "AIML API key not configured"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Get voice settings from request or use defaults
                voice = request.data.get("voice", "Rachel")  # Default: Rachel
                output_format = request.data.get("output_format", "mp3_44100_128")  # Default: mp3 44.1kHz 128kbps
                stability = request.data.get("stability")
                similarity_boost = request.data.get("similarity_boost")
                use_speaker_boost = request.data.get("use_speaker_boost")
                style = request.data.get("style")
                speed = request.data.get("speed")
                
                # AI/ML API endpoint for TTS
                url = "https://api.aimlapi.com/v1/tts"
                
                headers = {
                    "Authorization": f"Bearer {aiml_api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "elevenlabs/eleven_turbo_v2_5",
                    "text": text,
                    "voice": voice,
                    "output_format": output_format
                }
                
                # Add optional voice settings if provided
                voice_settings = {}
                if stability is not None:
                    voice_settings["stability"] = float(stability)
                if similarity_boost is not None:
                    voice_settings["similarity_boost"] = float(similarity_boost)
                if use_speaker_boost is not None:
                    voice_settings["use_speaker_boost"] = bool(use_speaker_boost)
                if style is not None:
                    voice_settings["style"] = float(style)
                if speed is not None:
                    voice_settings["speed"] = float(speed)
                
                if voice_settings:
                    data["voice_settings"] = voice_settings
                
                # Call AI/ML API
                response = requests.post(url, json=data, headers=headers, stream=True)
                
                if response.status_code != 201:
                    error_msg = response.text
                    logger.error(f"AI/ML API TTS error: {error_msg}")
                    return Response(
                        {"error": f"TTS generation failed: {error_msg}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Determine file extension based on output format
                file_ext = output_format.split('_')[0] if '_' in output_format else 'mp3'
                if file_ext in ['pcm', 'ulaw', 'alaw', 'opus']:
                    file_ext = 'wav' if file_ext in ['pcm', 'ulaw', 'alaw'] else file_ext
                
                # Stream the response content
                audio_content = b''
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        audio_content += chunk
                
                # Upload to Cloudinary instead of local storage
                import cloudinary.uploader
                import tempfile
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
                    tmp_file.write(audio_content)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Upload to Cloudinary
                    public_id = f"audio/tts_{uuid.uuid4()}"
                    cloudinary_result = cloudinary.uploader.upload(
                        tmp_file_path,
                        resource_type="video",  # Cloudinary uses 'video' for audio files
                        public_id=public_id,
                        folder=f"user_{request.user.id}",
                        format=file_ext
                    )
                    audio_url = cloudinary_result['secure_url']
                    logger.info(f"Successfully uploaded TTS audio to Cloudinary for user {request.user.id}")
                finally:
                    # Clean up temp file
                    import os
                    os.unlink(tmp_file_path)
                
                return Response({
                    "success": True,
                    "audio_url": audio_url,
                    "type": "generated",
                    "text": text,
                    "voice": voice,
                    "model": "elevenlabs/eleven_turbo_v2_5",
                    "output_format": output_format,
                    "cloudinary": True,
                }, status=status.HTTP_200_OK)
                
            except Exception as tts_error:
                logger.error(f"TTS generation failed: {str(tts_error)}")
                return Response(
                    {"error": f"TTS generation failed: {str(tts_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        else:
            return Response(
                {"error": "Either 'text' or 'audio_file' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.exception("Unexpected error during audio generation")
        return Response(
            {"error": f"Audio generation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def generate_instagram_video(request, organization_pk=None, brand_pk=None):
    """
    Generate AI video for Instagram posts
    """
    try:
        from website.video_utils import submit_video_generation_task
        from website.models import BrandInstagramPost

        # Get form data
        post_id = request.data.get("post_id")
        prompt = request.data.get("prompt", "").strip()

        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create the Instagram post
        if post_id:
            # Use existing post
            try:
                instagram_post = BrandInstagramPost.objects.get(id=post_id)
            except BrandInstagramPost.DoesNotExist:
                return Response(
                    {"error": "Instagram post not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Create new post for video generation
            from website.models import Brand

            # Get brand from URL parameters or request data
            brand_id = brand_pk or request.data.get("brand_id")
            if not brand_id:
                return Response(
                    {"error": "Brand ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                brand = Brand.objects.get(id=brand_id, owner=request.user)
            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Create new Instagram post
            content = request.data.get(
                "content", f"AI-generated video: {prompt[:50]}..."
            )
            scheduled_for = request.data.get("scheduled_for")

            instagram_post = BrandInstagramPost.objects.create(
                brand=brand,
                content=content,
                status="draft",
                is_video_post=True,
                scheduled_for=scheduled_for,
            )

        # Check permissions
        if instagram_post.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to modify this post"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get generation parameters
        quality = request.data.get("quality", "low")  # low, high
        duration = float(request.data.get("duration", 5.0))  # seconds

        # Validate parameters
        valid_qualities = ["low", "high"]
        if quality not in valid_qualities:
            quality = "low"

        # Clamp duration
        duration = max(1.0, min(duration, 60.0))

        # Add Sentry breadcrumb for API request start
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category="api",
                message="Starting Instagram Video Generation API Request",
                level="info",
                data={
                    "post_id": instagram_post.id,
                    "brand_id": instagram_post.brand.id,
                    "user_id": request.user.id,
                    "prompt_length": len(prompt),
                    "prompt_preview": prompt[:100],
                    "quality": quality,
                    "duration": duration,
                    "has_existing_post": bool(post_id),
                },
            )

        logger.info(
            f"Submitting video generation task for Instagram post {instagram_post.id} with prompt: {prompt[:100]}"
        )

        # Submit video generation task (async)
        success = submit_video_generation_task(
            instagram_post,
            prompt=prompt,
            provider="runware",
            quality=quality,
            duration=duration,
        )

        if success:
            # Add Sentry breadcrumb for successful submission
            if sentry_sdk:
                sentry_sdk.add_breadcrumb(
                    category="api",
                    message="Instagram Video Generation Task Submitted Successfully",
                    level="info",
                    data={
                        "post_id": instagram_post.id,
                        "task_uuid": instagram_post.video_generation_task_uuid,
                        "status": instagram_post.video_generation_status,
                    },
                )

            logger.info(
                f"Successfully submitted video generation task for Instagram post {instagram_post.id}"
            )
            return Response(
                {
                    "success": True,
                    "message": "Video generation task submitted successfully",
                    "post_id": instagram_post.id,
                    "task_uuid": instagram_post.video_generation_task_uuid,
                    "status": instagram_post.video_generation_status,
                },
                status=status.HTTP_200_OK,
            )
        else:
            # Add Sentry breadcrumb for failed submission
            if sentry_sdk:
                sentry_sdk.add_breadcrumb(
                    category="api",
                    message="Instagram Video Generation Task Submission Failed",
                    level="error",
                    data={
                        "post_id": instagram_post.id,
                        "error_message": instagram_post.error_message,
                        "status": instagram_post.video_generation_status,
                    },
                )

            return Response(
                {
                    "error": "Video generation task submission failed. Check post error message."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.exception("Unexpected error during Instagram video generation")
        return Response(
            {"error": f"Video generation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def check_video_generation_status(request, post_id):
    """
    Check the status of a video generation task for an Instagram post
    """
    try:
        from website.models import BrandInstagramPost
        from website.video_utils import check_video_generation_status

        # Get the Instagram post
        try:
            instagram_post = BrandInstagramPost.objects.get(id=post_id)
        except BrandInstagramPost.DoesNotExist:
            return Response(
                {"error": "Instagram post not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        if instagram_post.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to access this post"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check video generation status
        check_video_generation_status(instagram_post)

        # Refresh from database to get latest data
        instagram_post.refresh_from_db()

        response_data = {
            "post_id": post_id,
            "video_generation_status": instagram_post.video_generation_status,
            "task_uuid": instagram_post.video_generation_task_uuid,
            "is_video_post": instagram_post.is_video_post,
            "error_message": instagram_post.error_message,
            "updated_at": (
                instagram_post.updated_at.isoformat()
                if instagram_post.updated_at
                else None
            ),
        }

        # Add media URLs if video is completed
        if instagram_post.video_generation_status == "completed":
            response_data["video_url"] = instagram_post.get_media_url()
            response_data["thumbnail_url"] = instagram_post.get_thumbnail_url()

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(
            f"Unexpected error checking video generation status for post {post_id}"
        )
        return Response(
            {"error": f"Failed to check video generation status: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def users_feed(request):
    """
    Get a feed of users for the mobile app
    """
    users = User.objects.filter(is_active=True).exclude(id=request.user.id)[:20]

    user_data = []
    for user in users:
        # Create a proper username from available data
        display_username = user.username
        if "@" in user.username:
            # Extract username part from email
            display_username = user.username.split("@")[0]

        # If we have first and last name, use those instead
        if user.first_name and user.last_name:
            display_username = f"{user.first_name.lower()}{user.last_name.lower()}"
        elif user.first_name:
            display_username = user.first_name.lower()

        user_info = {
            "id": user.id,
            "username": display_username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "bio": user.bio,
            "instagram_handle": user.instagram_handle,
            "profile_picture": (user.profile_image.url if user.profile_image else None),
            "banner_image": (user.banner_image.url if user.banner_image else None),
            "additional_image1": (
                user.additional_image1.url if user.additional_image1 else None
            ),
            "additional_image2": (
                user.additional_image2.url if user.additional_image2 else None
            ),
            "story_price": float(user.story_price) if user.story_price else None,
            "post_price": float(user.post_price) if user.post_price else None,
            "reel_price": float(user.reel_price) if user.reel_price else None,
            "impressions_count": user.impressions_count,
        }

        # Build full URLs for images
        for img_field in [
            "profile_picture",
            "banner_image",
            "additional_image1",
            "additional_image2",
        ]:
            if user_info[img_field] and user_info[img_field].startswith("/"):
                user_info[img_field] = request.build_absolute_uri(user_info[img_field])

        user_data.append(user_info)

    return Response({"users": user_data})


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def public_user_profile(request, user_id):
    """
    Get public profile information for any user (no auth required)
    """
    try:
        user = User.objects.get(id=user_id)

        # Create a proper username from available data
        display_username = user.username
        if "@" in user.username:
            display_username = user.username.split("@")[0]

        if user.first_name and user.last_name:
            display_username = f"{user.first_name.lower()}{user.last_name.lower()}"
        elif user.first_name:
            display_username = user.first_name.lower()

        user_info = {
            "id": user.id,
            "username": display_username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "age": user.age,
            "bio": user.bio,
            "instagram_handle": user.instagram_handle,
            "profile_picture": user.profile_image.url if user.profile_image else None,
            "banner_image": user.banner_image.url if user.banner_image else None,
            "impressions_count": user.impressions_count,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

        # Build full URLs for images
        for img_field in ["profile_picture", "banner_image"]:
            if user_info[img_field] and user_info[img_field].startswith("/"):
                user_info[img_field] = request.build_absolute_uri(user_info[img_field])

        return Response(user_info)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_detail(request, user_id):
    """
    Get detailed information about a specific user
    """
    try:
        user = User.objects.get(id=user_id)

        # Create a proper username from available data
        display_username = user.username
        if "@" in user.username:
            # Extract username part from email
            display_username = user.username.split("@")[0]

        # If we have first and last name, use those instead
        if user.first_name and user.last_name:
            display_username = f"{user.first_name.lower()}{user.last_name.lower()}"
        elif user.first_name:
            display_username = user.first_name.lower()

        user_info = {
            "id": user.id,
            "username": display_username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "age": user.age,
            "bio": user.bio,
            "instagram_handle": user.instagram_handle,
            "profile_picture": user.profile_image.url if user.profile_image else None,
            "banner_image": user.banner_image.url if user.banner_image else None,
            "additional_image1": (
                user.additional_image1.url if user.additional_image1 else None
            ),
            "additional_image2": (
                user.additional_image2.url if user.additional_image2 else None
            ),
            "story_price": float(user.story_price) if user.story_price else None,
            "post_price": float(user.post_price) if user.post_price else None,
            "reel_price": float(user.reel_price) if user.reel_price else None,
            "impressions_count": user.impressions_count,
            "created_at": user.created_at.isoformat(),
        }

        # Build full URLs for images
        for img_field in [
            "profile_picture",
            "banner_image",
            "additional_image1",
            "additional_image2",
        ]:
            if user_info[img_field] and user_info[img_field].startswith("/"):
                user_info[img_field] = request.build_absolute_uri(user_info[img_field])

        return Response(user_info)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def track_profile_impression(request, user_id):
    """
    Track a profile impression when someone views a user's profile
    """
    try:
        from .models import ProfileImpression

        # Get the profile user being viewed
        try:
            profile_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Don't track self-impressions
        if profile_user == request.user:
            return Response(
                {
                    "success": True,
                    "message": "Self-impression not tracked",
                    "impressions_count": profile_user.impressions_count,
                }
            )

        # Get IP address
        ip_address = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        if not ip_address:
            ip_address = request.META.get("REMOTE_ADDR", "")

        user_agent = request.META.get("HTTP_USER_AGENT", "")
        referrer = request.META.get("HTTP_REFERER", "")

        # CustomSession removed - using Django's default sessions
        # session_obj = None
        # if hasattr(request, "session") and request.session.session_key:
        #     try:
        #         session_obj = Session.objects.get(
        #             session_key=request.session.session_key
        #         )
        #     except Session.DoesNotExist:
        #         pass

        # Check for recent impression from same IP to prevent spam
        from django.utils import timezone

        recent_cutoff = timezone.now() - timezone.timedelta(minutes=5)
        recent_impression = ProfileImpression.objects.filter(
            profile_user=profile_user,
            ip_address=ip_address,
            timestamp__gte=recent_cutoff,
        ).exists()

        if not recent_impression:
            # Create the impression record (the signal will handle updating impressions_count)
            ProfileImpression.objects.create(
                profile_user=profile_user,
                viewer=request.user,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                country=request.data.get("country", ""),
                city=request.data.get("city", ""),
            )

            # Refresh the user object to get the updated impressions_count from signal
            profile_user.refresh_from_db()

            return Response(
                {
                    "success": True,
                    "message": "Profile impression tracked successfully",
                    "impressions_count": profile_user.impressions_count,
                }
            )
        else:
            return Response(
                {
                    "success": True,
                    "message": "Recent impression already exists",
                    "impressions_count": profile_user.impressions_count,
                }
            )

    except Exception as e:
        return Response(
            {"error": f"Failed to track impression: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Referral System API Endpoints


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def referral_code(request):
    """
    GET: Get user's referral code and stats
    POST: Generate a new referral code for the user
    """
    from .models import ReferralCode

    if request.method == "GET":
        try:
            referral_code = ReferralCode.objects.get(user=request.user)

            data = {
                "code": referral_code.code,
                "referral_url": referral_code.get_referral_url(),
                "total_points": referral_code.total_points,
                "total_clicks": referral_code.total_clicks,
                "total_signups": referral_code.total_signups,
                "total_subscriptions": referral_code.total_subscriptions,
                "total_rewards_earned": float(referral_code.total_rewards_earned),
                "is_active": referral_code.is_active,
                "created_at": referral_code.created_at.isoformat(),
            }

            return Response(data)

        except ReferralCode.DoesNotExist:
            return Response(
                {"error": "No referral code found. Generate one first."},
                status=status.HTTP_404_NOT_FOUND,
            )

    elif request.method == "POST":
        try:
            # Check if user already has a referral code
            referral_code, created = ReferralCode.objects.get_or_create(
                user=request.user
            )

            if created:
                message = "Referral code generated successfully!"
            else:
                message = "You already have a referral code!"

            data = {
                "success": True,
                "message": message,
                "code": referral_code.code,
                "referral_url": referral_code.get_referral_url(),
                "total_points": referral_code.total_points,
                "total_clicks": referral_code.total_clicks,
                "total_signups": referral_code.total_signups,
                "total_subscriptions": referral_code.total_subscriptions,
                "total_rewards_earned": float(referral_code.total_rewards_earned),
                "is_active": referral_code.is_active,
                "created_at": referral_code.created_at.isoformat(),
            }

            return Response(
                data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": f"Error generating referral code: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def referral_dashboard(request):
    """
    Get comprehensive referral dashboard data
    """
    from .models import ReferralCode, ReferralBadge

    try:
        referral_code = ReferralCode.objects.get(user=request.user)

        # Get recent activities (last 10 of each)
        recent_clicks = referral_code.clicks.all()[:10]
        recent_signups = referral_code.signups.all()[:10]
        recent_subscriptions = referral_code.subscriptions.all()[:10]

        # Get user's badges
        badges = ReferralBadge.objects.filter(user=request.user)

        # Calculate points breakdown
        points_breakdown = {
            "clicks_points": referral_code.total_clicks * 1,
            "signups_points": referral_code.total_signups * 10,
            "subscriptions_points": referral_code.total_subscriptions * 50,
            "total_points": referral_code.total_points,
        }

        # Get user's rank
        user_rank = (
            ReferralCode.objects.filter(
                is_active=True, total_points__gt=referral_code.total_points
            ).count()
            + 1
        )

        data = {
            "referral_code": {
                "code": referral_code.code,
                "referral_url": referral_code.get_referral_url(),
                "total_points": referral_code.total_points,
                "total_clicks": referral_code.total_clicks,
                "total_signups": referral_code.total_signups,
                "total_subscriptions": referral_code.total_subscriptions,
                "total_rewards_earned": float(referral_code.total_rewards_earned),
                "is_active": referral_code.is_active,
                "created_at": referral_code.created_at.isoformat(),
                "rank": user_rank,
            },
            "points_breakdown": points_breakdown,
            "recent_clicks": [
                {
                    "ip_address": click.ip_address,
                    "timestamp": click.timestamp.isoformat(),
                    "country": click.country,
                    "city": click.city,
                }
                for click in recent_clicks
            ],
            "recent_signups": [
                {
                    "referred_user": signup.referred_user.username,
                    "timestamp": signup.timestamp.isoformat(),
                    "reward_given": signup.reward_given,
                    "reward_amount": float(signup.reward_amount),
                }
                for signup in recent_signups
            ],
            "recent_subscriptions": [
                {
                    "referred_user": subscription.referred_user.username,
                    "subscription_type": subscription.subscription_type,
                    "subscription_amount": float(subscription.subscription_amount),
                    "reward_amount": float(subscription.reward_amount),
                    "timestamp": subscription.timestamp.isoformat(),
                }
                for subscription in recent_subscriptions
            ],
            "badges": [
                {
                    "badge_type": badge.badge_type,
                    "badge_name": badge.get_badge_type_display(),
                    "earned_at": badge.earned_at.isoformat(),
                }
                for badge in badges
            ],
        }

        return Response(data)

    except ReferralCode.DoesNotExist:
        return Response(
            {"error": "No referral code found. Generate one first."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def referral_leaderboard(request):
    """
    Get referral leaderboard data
    """
    from .models import ReferralCode

    # Get period filter
    period = request.GET.get("period", "all_time")
    limit = int(request.GET.get("limit", 50))

    # Base queryset - only show users with points > 0
    queryset = ReferralCode.objects.filter(is_active=True, total_points__gt=0)

    # Filter by period if needed
    if period == "monthly":
        from datetime import datetime, timedelta

        month_ago = datetime.now() - timedelta(days=30)
        queryset = queryset.filter(created_at__gte=month_ago)
    elif period == "weekly":
        from datetime import datetime, timedelta

        week_ago = datetime.now() - timedelta(days=7)
        queryset = queryset.filter(created_at__gte=week_ago)

    # Order by points and get top performers
    top_referrers = queryset.order_by("-total_points", "-total_signups")[:limit]

    # Get current user's rank if they have a referral code
    user_rank = None
    user_stats = None
    try:
        user_code = request.user.referral_code
        if user_code.total_points > 0:
            higher_ranked = queryset.filter(
                total_points__gt=user_code.total_points
            ).count()
            user_rank = higher_ranked + 1
            user_stats = {
                "code": user_code.code,
                "total_points": user_code.total_points,
                "total_clicks": user_code.total_clicks,
                "total_signups": user_code.total_signups,
                "total_subscriptions": user_code.total_subscriptions,
                "rank": user_rank,
            }
    except (AttributeError, ReferralCode.DoesNotExist):
        pass

    leaderboard_data = []
    for idx, referrer in enumerate(top_referrers, 1):
        leaderboard_data.append(
            {
                "rank": idx,
                "username": referrer.user.username,
                "first_name": referrer.user.first_name,
                "last_name": referrer.user.last_name,
                "total_points": referrer.total_points,
                "total_clicks": referrer.total_clicks,
                "total_signups": referrer.total_signups,
                "total_subscriptions": referrer.total_subscriptions,
                "badge_count": referrer.user.referral_badges.count(),
            }
        )

    data = {
        "leaderboard": leaderboard_data,
        "period": period,
        "user_rank": user_rank,
        "user_stats": user_stats,
        "total_participants": queryset.count(),
    }

    return Response(data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def referral_badges(request):
    """
    Get user's referral badges and available badges
    """
    from .models import ReferralBadge

    # Get user's earned badges
    earned_badges = ReferralBadge.objects.filter(user=request.user)

    # Get all possible badges with progress
    all_badges = []
    badge_definitions = [
        {
            "type": "first_referral",
            "name": "First Referral",
            "requirement": 1,
            "metric": "signups",
        },
        {
            "type": "bronze_referrer",
            "name": "Bronze Referrer",
            "requirement": 5,
            "metric": "signups",
        },
        {
            "type": "silver_referrer",
            "name": "Silver Referrer",
            "requirement": 25,
            "metric": "signups",
        },
        {
            "type": "gold_referrer",
            "name": "Gold Referrer",
            "requirement": 100,
            "metric": "signups",
        },
        {
            "type": "platinum_referrer",
            "name": "Platinum Referrer",
            "requirement": 500,
            "metric": "signups",
        },
        {
            "type": "click_master",
            "name": "Click Master",
            "requirement": 1000,
            "metric": "clicks",
        },
        {
            "type": "subscription_ace",
            "name": "Subscription Ace",
            "requirement": 50,
            "metric": "subscriptions",
        },
    ]

    # Get user's current stats
    try:
        referral_code = request.user.referral_code
        current_stats = {
            "signups": referral_code.total_signups,
            "clicks": referral_code.total_clicks,
            "subscriptions": referral_code.total_subscriptions,
        }
    except (AttributeError, ReferralCode.DoesNotExist):
        current_stats = {"signups": 0, "clicks": 0, "subscriptions": 0}

    earned_badge_types = {badge.badge_type for badge in earned_badges}

    for badge_def in badge_definitions:
        current_value = current_stats.get(badge_def["metric"], 0)
        progress = min(current_value / badge_def["requirement"], 1.0) * 100

        all_badges.append(
            {
                "type": badge_def["type"],
                "name": badge_def["name"],
                "requirement": badge_def["requirement"],
                "metric": badge_def["metric"],
                "current_value": current_value,
                "progress": progress,
                "earned": badge_def["type"] in earned_badge_types,
                "earned_at": None,
            }
        )

    # Update earned_at for earned badges
    for badge in earned_badges:
        for badge_def in all_badges:
            if badge_def["type"] == badge.badge_type:
                badge_def["earned_at"] = badge.earned_at.isoformat()
                break

    data = {
        "earned_badges": [
            {
                "type": badge.badge_type,
                "name": badge.get_badge_type_display(),
                "earned_at": badge.earned_at.isoformat(),
            }
            for badge in earned_badges
        ],
        "all_badges": all_badges,
        "total_earned": len(earned_badges),
        "total_available": len(badge_definitions),
    }

    return Response(data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def track_referral_click(request):
    """
    Track a referral click from mobile app
    """
    try:
        from .models import ReferralCode, ReferralClick

        # Get referral code from request
        referral_code = request.data.get("referral_code")
        if not referral_code:
            return Response(
                {"error": "Referral code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find the referral code
        try:
            ref_code = ReferralCode.objects.get(code=referral_code, is_active=True)
        except ReferralCode.DoesNotExist:
            return Response(
                {"error": "Invalid referral code"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get IP address and user agent
        ip_address = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        if not ip_address:
            ip_address = request.META.get("REMOTE_ADDR", "")

        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Create or get existing click (prevents duplicates)
        click, created = ReferralClick.objects.get_or_create(
            referral_code=ref_code,
            ip_address=ip_address,
            defaults={
                "user_agent": user_agent,
                "country": request.data.get("country", ""),
                "city": request.data.get("city", ""),
            },
        )

        if created:
            # Update referral code stats
            ref_code.total_clicks += 1
            ref_code.save()

        return Response(
            {
                "success": True,
                "message": "Referral click tracked successfully",
                "click_id": click.id,
                "total_clicks": ref_code.total_clicks,
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to track referral click: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Stripe Account Connection API Endpoints


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stripe_account_status(request):
    """
    Get the current user's Stripe account connection status
    """
    try:
        user = request.user

        # Check if user has any brands with Stripe info
        brands_with_stripe = Brand.objects.filter(
            owner=user, stripe_customer_id__isnull=False
        ).exclude(stripe_customer_id="")

        stripe_connected = brands_with_stripe.exists()

        response_data = {
            "stripe_connected": stripe_connected,
            "brands_count": brands_with_stripe.count(),
            "brands": [],
        }

        if stripe_connected:
            for brand in brands_with_stripe:
                brand_data = {
                    "id": brand.id,
                    "name": brand.name,
                    "stripe_customer_id": brand.stripe_customer_id,
                    "stripe_subscription_id": brand.stripe_subscription_id,
                    "has_active_subscription": bool(brand.stripe_subscription_id),
                    "created_at": brand.created_at.isoformat(),
                }
                response_data["brands"].append(brand_data)

        return Response(response_data)

    except Exception as e:
        return Response(
            {"error": f"Failed to get Stripe status: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_stripe_customer(request):
    """
    Create a Stripe customer for the user's brand
    """
    try:
        # Get Stripe secret key
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe_secret_key:
            return Response(
                {"error": "Stripe not configured on server"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        stripe.api_key = stripe_secret_key

        # Get required data from request
        brand_name = request.data.get("brand_name", "").strip()
        brand_url = request.data.get("brand_url", "").strip()

        if not brand_name or not brand_url:
            return Response(
                {"error": "Brand name and URL are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate URL format
        if not brand_url.startswith(("http://", "https://")):
            brand_url = f"https://{brand_url}"

        user = request.user

        # Check if brand already exists for this user
        existing_brand = Brand.objects.filter(owner=user, name=brand_name).first()

        if existing_brand and existing_brand.stripe_customer_id:
            return Response(
                {"error": "Brand already has Stripe customer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            name=brand_name,
            description=f"Customer for {brand_name} - {user.email}",
            metadata={
                "user_id": user.id,
                "brand_name": brand_name,
                "brand_url": brand_url,
            },
        )

        # Create or update brand
        if existing_brand:
            existing_brand.stripe_customer_id = customer.id
            existing_brand.url = brand_url
            existing_brand.save()
            brand = existing_brand
        else:
            brand = Brand.objects.create(
                name=brand_name,
                url=brand_url,
                owner=user,
                stripe_customer_id=customer.id,
            )

        return Response(
            {
                "success": True,
                "message": "Stripe customer created successfully",
                "brand": {
                    "id": brand.id,
                    "name": brand.name,
                    "url": brand.url,
                    "stripe_customer_id": brand.stripe_customer_id,
                },
                "customer": {
                    "id": customer.id,
                    "email": customer.email,
                    "name": customer.name,
                },
            }
        )

    except stripe.error.StripeError as e:
        return Response(
            {"error": f"Stripe error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to create Stripe customer: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_stripe_subscription(request):
    """
    Create a Stripe subscription for the user's brand
    """
    try:
        # Get Stripe secret key
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe_secret_key:
            return Response(
                {"error": "Stripe not configured on server"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        stripe.api_key = stripe_secret_key

        # Get required data from request
        brand_id = request.data.get("brand_id")
        plan = request.data.get("plan", "starter")
        payment_method_id = request.data.get("payment_method_id")

        if not brand_id or not payment_method_id:
            return Response(
                {"error": "Brand ID and payment method are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the brand
        try:
            brand = Brand.objects.get(id=brand_id, owner=request.user)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not brand.stripe_customer_id:
            return Response(
                {"error": "Brand does not have a Stripe customer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get plan price ID
        plan_price_ids = {
            # "trial": os.environ.get("STRIPE_PRICE_1"),
            "starter": os.environ.get("STRIPE_PRICE_99"),
            "professional": os.environ.get("STRIPE_PRICE_199"),
            "enterprise": os.environ.get("STRIPE_PRICE_299"),
        }

        price_id = plan_price_ids.get(plan)
        if not price_id:
            return Response(
                {"error": "Invalid plan selected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=brand.stripe_customer_id,
        )

        # Set as default payment method
        stripe.Customer.modify(
            brand.stripe_customer_id,
            invoice_settings={
                "default_payment_method": payment_method_id,
            },
        )

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=brand.stripe_customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
        )

        # Update brand with subscription ID
        brand.stripe_subscription_id = subscription.id
        brand.save()

        # Handle referral subscription tracking
        from .views import handle_referral_subscription

        plan_prices = {"starter": 99, "professional": 199, "enterprise": 299}
        handle_referral_subscription(request.user, plan, plan_prices.get(plan, 99))

        return Response(
            {
                "success": True,
                "message": "Subscription created successfully",
                "subscription": {
                    "id": subscription.id,
                    "status": subscription.status,
                    "current_period_start": subscription.current_period_start,
                    "current_period_end": subscription.current_period_end,
                    "plan": plan,
                },
                "client_secret": (
                    subscription.latest_invoice.payment_intent.client_secret
                    if subscription.latest_invoice.payment_intent
                    else None
                ),
            }
        )

    except stripe.error.StripeError as e:
        return Response(
            {"error": f"Stripe error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to create subscription: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stripe_subscription_status(request, brand_id):
    """
    Get the subscription status for a specific brand
    """
    try:
        # Get the brand
        try:
            brand = Brand.objects.get(id=brand_id, owner=request.user)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not brand.stripe_subscription_id:
            return Response(
                {
                    "has_subscription": False,
                    "message": "No subscription found for this brand",
                }
            )

        # Get Stripe secret key
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe_secret_key:
            return Response(
                {"error": "Stripe not configured on server"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        stripe.api_key = stripe_secret_key

        # Get subscription from Stripe
        subscription = stripe.Subscription.retrieve(brand.stripe_subscription_id)

        # Get plan name from price ID
        plan_name = "unknown"
        price_id = (
            subscription.items.data[0].price.id if subscription.items.data else None
        )

        if price_id:
            # if price_id == os.environ.get("STRIPE_PRICE_1"):
            #     plan_name = "trial"
            if price_id == os.environ.get("STRIPE_PRICE_99"):
                plan_name = "starter"
            elif price_id == os.environ.get("STRIPE_PRICE_199"):
                plan_name = "professional"
            elif price_id == os.environ.get("STRIPE_PRICE_299"):
                plan_name = "enterprise"

        return Response(
            {
                "has_subscription": True,
                "subscription": {
                    "id": subscription.id,
                    "status": subscription.status,
                    "plan": plan_name,
                    "current_period_start": subscription.current_period_start,
                    "current_period_end": subscription.current_period_end,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "created": subscription.created,
                },
                "brand": {
                    "id": brand.id,
                    "name": brand.name,
                    "url": brand.url,
                },
            }
        )

    except stripe.error.StripeError as e:
        return Response(
            {"error": f"Stripe error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to get subscription status: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def cancel_stripe_subscription(request, brand_id):
    """
    Cancel a Stripe subscription for a specific brand
    """
    try:
        # Get the brand
        try:
            brand = Brand.objects.get(id=brand_id, owner=request.user)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not brand.stripe_subscription_id:
            return Response(
                {"error": "No subscription found for this brand"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get Stripe secret key
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe_secret_key:
            return Response(
                {"error": "Stripe not configured on server"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        stripe.api_key = stripe_secret_key

        # Cancel subscription (at period end by default)
        cancel_immediately = request.data.get("cancel_immediately", False)

        if cancel_immediately:
            subscription = stripe.Subscription.delete(brand.stripe_subscription_id)
        else:
            subscription = stripe.Subscription.modify(
                brand.stripe_subscription_id, cancel_at_period_end=True
            )

        return Response(
            {
                "success": True,
                "message": "Subscription cancelled successfully",
                "subscription": {
                    "id": subscription.id,
                    "status": subscription.status,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "canceled_at": getattr(subscription, "canceled_at", None),
                    "current_period_end": subscription.current_period_end,
                },
            }
        )

    except stripe.error.StripeError as e:
        return Response(
            {"error": f"Stripe error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to cancel subscription: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stripe_payment_methods(request, brand_id):
    """
    Get payment methods for a specific brand's Stripe customer
    """
    try:
        # Get the brand
        try:
            brand = Brand.objects.get(id=brand_id, owner=request.user)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not brand.stripe_customer_id:
            return Response(
                {"error": "Brand does not have a Stripe customer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get Stripe secret key
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe_secret_key:
            return Response(
                {"error": "Stripe not configured on server"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        stripe.api_key = stripe_secret_key

        # Get payment methods
        payment_methods = stripe.PaymentMethod.list(
            customer=brand.stripe_customer_id,
            type="card",
        )

        # Format payment methods for response
        formatted_methods = []
        for pm in payment_methods.data:
            formatted_methods.append(
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card": (
                        {
                            "brand": pm.card.brand,
                            "last4": pm.card.last4,
                            "exp_month": pm.card.exp_month,
                            "exp_year": pm.card.exp_year,
                        }
                        if pm.card
                        else None
                    ),
                    "created": pm.created,
                }
            )

        return Response(
            {
                "payment_methods": formatted_methods,
                "brand": {
                    "id": brand.id,
                    "name": brand.name,
                },
            }
        )

    except stripe.error.StripeError as e:
        return Response(
            {"error": f"Stripe error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to get payment methods: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stripe_plans(request):
    """
    Get available Stripe subscription plans
    """
    try:
        plans = [
            # {
            #     "id": "trial",
            #     "name": "Trial",
            #     "price": 1,
            #     "currency": "usd",
            #     "interval": "month",
            #     "features": ["Basic Analytics", "Email Templates", "24/7 Support"],
            #     "stripe_price_id": os.environ.get("STRIPE_PRICE_1", ""),
            # },
            {
                "id": "starter",
                "name": "Starter",
                "price": 99,
                "currency": "usd",
                "interval": "month",
                "features": ["Basic Analytics", "Email Templates", "24/7 Support"],
                "stripe_price_id": os.environ.get("STRIPE_PRICE_99", ""),
            },
            {
                "id": "professional",
                "name": "Professional",
                "price": 199,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Advanced Analytics",
                    "Lead Generation Tools",
                    "Automation Workflows",
                    "Priority Support",
                ],
                "stripe_price_id": os.environ.get("STRIPE_PRICE_199", ""),
            },
            {
                "id": "enterprise",
                "name": "Business",
                "price": 299,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Custom Analytics",
                    "Dedicated Account Manager",
                    "White-label Solutions",
                ],
                "stripe_price_id": os.environ.get("STRIPE_PRICE_299", ""),
            },
        ]

        return Response({"plans": plans})

    except Exception as e:
        return Response(
            {"error": f"Failed to get plans: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Stripe Webhook Endpoints


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    if not endpoint_secret:
        logger.error("Stripe webhook secret not configured")
        return HttpResponse("Webhook secret not configured", status=500)

    if not sig_header:
        logger.error("Missing Stripe signature header")
        return HttpResponse("Missing signature", status=400)

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid payload: {e}")
        return HttpResponse("Invalid payload", status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid signature: {e}")
        return HttpResponse("Invalid signature", status=400)

    # Handle the event
    try:
        if event["type"] == "payment_intent.succeeded":
            handle_payment_intent_succeeded(event["data"]["object"])

        elif event["type"] == "payment_intent.payment_failed":
            handle_payment_intent_failed(event["data"]["object"])

        elif event["type"] == "invoice.payment_succeeded":
            handle_invoice_payment_succeeded(event["data"]["object"])

        elif event["type"] == "invoice.payment_failed":
            handle_invoice_payment_failed(event["data"]["object"])

        elif event["type"] == "customer.subscription.created":
            handle_subscription_created(event["data"]["object"])

        elif event["type"] == "customer.subscription.updated":
            handle_subscription_updated(event["data"]["object"])

        elif event["type"] == "customer.subscription.deleted":
            handle_subscription_deleted(event["data"]["object"])

        # elif event["type"] == "customer.subscription.trial_will_end":
        #     handle_subscription_trial_will_end(event["data"]["object"])

        elif event["type"] == "customer.created":
            handle_customer_created(event["data"]["object"])

        elif event["type"] == "customer.updated":
            handle_customer_updated(event["data"]["object"])

        elif event["type"] == "customer.deleted":
            handle_customer_deleted(event["data"]["object"])

        else:
            logger.info(f"Unhandled event type: {event['type']}")

        return HttpResponse("Success", status=200)

    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return HttpResponse(f"Webhook handler failed: {str(e)}", status=500)


def handle_payment_intent_succeeded(payment_intent):
    """Handle successful payment intent"""
    logger.info(f"Payment succeeded: {payment_intent['id']}")

    # Get customer ID from payment intent
    customer_id = payment_intent.get("customer")
    if not customer_id:
        logger.warning(f"No customer ID in payment intent {payment_intent['id']}")
        return

    try:
        # Find the brand associated with this customer
        brand = Brand.objects.get(stripe_customer_id=customer_id)

        # Log successful payment
        logger.info(f"Payment successful for brand: {brand.name} (ID: {brand.id})")

        # You can add additional logic here, such as:
        # - Sending confirmation emails
        # - Updating subscription status
        # - Triggering analytics events

    except Brand.DoesNotExist:
        logger.warning(f"No brand found for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")


def handle_payment_intent_failed(payment_intent):
    """Handle failed payment intent"""
    logger.warning(f"Payment failed: {payment_intent['id']}")

    customer_id = payment_intent.get("customer")
    if not customer_id:
        logger.warning(f"No customer ID in payment intent {payment_intent['id']}")
        return

    try:
        brand = Brand.objects.get(stripe_customer_id=customer_id)

        # Log failed payment
        logger.warning(f"Payment failed for brand: {brand.name} (ID: {brand.id})")

        # You can add additional logic here, such as:
        # - Sending payment failure notifications
        # - Triggering retry mechanisms
        # - Updating subscription status

    except Brand.DoesNotExist:
        logger.warning(f"No brand found for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")


def handle_invoice_payment_succeeded(invoice):
    """Handle successful invoice payment"""
    logger.info(f"Invoice payment succeeded: {invoice['id']}")

    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    if not customer_id:
        logger.warning(f"No customer ID in invoice {invoice['id']}")
        return

    try:
        brand = Brand.objects.get(stripe_customer_id=customer_id)

        # Update subscription status if needed
        if subscription_id and brand.stripe_subscription_id == subscription_id:
            # Update payment date and subscription status
            from django.utils import timezone

            brand.last_payment_date = timezone.now()
            brand.stripe_subscription_status = "active"
            brand.save()

            logger.info(
                f"Invoice payment successful for brand: {brand.name} (ID: {brand.id})"
            )

            # You can add additional logic here, such as:
            # - Extending subscription period
            # - Sending receipt emails
            # - Updating analytics

    except Brand.DoesNotExist:
        logger.warning(f"No brand found for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error handling invoice payment success: {str(e)}")


def handle_invoice_payment_failed(invoice):
    """Handle failed invoice payment"""
    logger.warning(f"Invoice payment failed: {invoice['id']}")

    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    if not customer_id:
        logger.warning(f"No customer ID in invoice {invoice['id']}")
        return

    try:
        brand = Brand.objects.get(stripe_customer_id=customer_id)

        if subscription_id and brand.stripe_subscription_id == subscription_id:
            # Update subscription status to indicate payment failure
            brand.stripe_subscription_status = "past_due"
            brand.save()

            logger.warning(
                f"Invoice payment failed for brand: {brand.name} (ID: {brand.id}) - status updated to past_due"
            )

            # You can add additional logic here, such as:
            # - Sending payment failure notifications
            # - Triggering dunning management
            # - Notifying admin team
            # - Triggering retry mechanisms

    except Brand.DoesNotExist:
        logger.warning(f"No brand found for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error handling invoice payment failure: {str(e)}")


def handle_subscription_created(subscription):
    """Handle subscription creation"""
    logger.info(f"Subscription created: {subscription['id']}")

    customer_id = subscription.get("customer")
    if not customer_id:
        logger.warning(f"No customer ID in subscription {subscription['id']}")
        return

    try:
        brand = Brand.objects.get(stripe_customer_id=customer_id)

        # Update brand with subscription ID and status if not already set
        if not brand.stripe_subscription_id:
            brand.stripe_subscription_id = subscription["id"]
            brand.stripe_subscription_status = subscription.get("status", "active")
            brand.save()
            logger.info(
                f"Updated brand {brand.name} with subscription ID: {subscription['id']} and status: {brand.stripe_subscription_status}"
            )

    except Brand.DoesNotExist:
        logger.warning(f"No brand found for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error handling subscription creation: {str(e)}")


def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    logger.info(f"Subscription updated: {subscription['id']}")

    customer_id = subscription.get("customer")
    if not customer_id:
        logger.warning(f"No customer ID in subscription {subscription['id']}")
        return

    try:
        brand = Brand.objects.get(stripe_customer_id=customer_id)

        # Check if subscription belongs to this brand
        if brand.stripe_subscription_id == subscription["id"]:
            status = subscription.get("status")

            # Update brand subscription status
            brand.stripe_subscription_status = status
            brand.save()

            logger.info(
                f"Subscription {subscription['id']} for brand {brand.name} updated to status: {status}"
            )

            # Handle different subscription statuses
            if status == "canceled":
                # You might want to update brand status or send notifications
                logger.info(f"Subscription canceled for brand: {brand.name}")
            elif status == "past_due":
                # Handle past due subscriptions
                logger.warning(f"Subscription past due for brand: {brand.name}")
            elif status == "active":
                # Subscription is active
                logger.info(f"Subscription active for brand: {brand.name}")

    except Brand.DoesNotExist:
        logger.warning(f"No brand found for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error handling subscription update: {str(e)}")


def handle_subscription_deleted(subscription):
    """Handle subscription deletion"""
    logger.info(f"Subscription deleted: {subscription['id']}")

    customer_id = subscription.get("customer")
    if not customer_id:
        logger.warning(f"No customer ID in subscription {subscription['id']}")
        return

    try:
        brand = Brand.objects.get(stripe_customer_id=customer_id)

        # Check if this is the brand's subscription
        if brand.stripe_subscription_id == subscription["id"]:
            # Clear the subscription ID and status
            brand.stripe_subscription_id = None
            brand.stripe_subscription_status = None
            brand.save()
            logger.info(f"Cleared subscription data for brand: {brand.name}")

            # You can add additional logic here, such as:
            # - Sending cancellation confirmation
            # - Updating user permissions
            # - Triggering win-back campaigns

    except Brand.DoesNotExist:
        logger.warning(f"No brand found for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error handling subscription deletion: {str(e)}")


# def handle_subscription_trial_will_end(subscription):
#     """Handle subscription trial ending soon"""
#     logger.info(f"Subscription trial will end: {subscription['id']}")

#     customer_id = subscription.get("customer")
#     if not customer_id:
#         logger.warning(f"No customer ID in subscription {subscription['id']}")
#         return

#     try:
#         brand = Brand.objects.get(stripe_customer_id=customer_id)

#         if brand.stripe_subscription_id == subscription["id"]:
#             logger.info(f"Trial ending soon for brand: {brand.name}")

#             # You can add additional logic here, such as:
#             # - Sending trial ending notifications
#             # - Offering conversion incentives
#             # - Updating UI to show trial status

#     except Brand.DoesNotExist:
#         logger.warning(f"No brand found for customer {customer_id}")
#     except Exception as e:
#         logger.error(f"Error handling trial ending: {str(e)}")


def handle_customer_created(customer):
    """Handle customer creation"""
    logger.info(f"Customer created: {customer['id']}")

    # Usually customers are created through your API, so this might be redundant
    # But you can add additional logic here if needed
    pass


def handle_customer_updated(customer):
    """Handle customer updates"""
    logger.info(f"Customer updated: {customer['id']}")

    try:
        brand = Brand.objects.get(stripe_customer_id=customer["id"])

        # You can sync customer data here if needed
        # For example, update email, name, etc.
        logger.info(f"Customer {customer['id']} updated for brand: {brand.name}")

    except Brand.DoesNotExist:
        logger.warning(f"No brand found for customer {customer['id']}")
    except Exception as e:
        logger.error(f"Error handling customer update: {str(e)}")


def handle_customer_deleted(customer):
    """Handle customer deletion"""
    logger.info(f"Customer deleted: {customer['id']}")

    try:
        brand = Brand.objects.get(stripe_customer_id=customer["id"])

        # Clear all Stripe data from brand
        brand.stripe_customer_id = None
        brand.stripe_subscription_id = None
        brand.stripe_subscription_status = None
        brand.save()

        logger.info(f"Cleared all Stripe data for brand: {brand.name}")

    except Brand.DoesNotExist:
        logger.warning(f"No brand found for customer {customer['id']}")
    except Exception as e:
        logger.error(f"Error handling customer deletion: {str(e)}")


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stripe_webhook_test(request):
    """Test endpoint to verify webhook is working"""
    return Response(
        {
            "message": "Webhook endpoint is working",
            "timestamp": timezone.now().isoformat(),
        }
    )


# ===================== TASK MANAGEMENT API VIEWS =====================


@api_view(["GET", "POST"])
@permission_classes(
    [permissions.IsAuthenticatedOrReadOnly]
)  # Allow unauthenticated GET requests
def tasks_list(request):
    """
    GET: List all active tasks with filtering (public access)
    POST: Create a new task (authenticated users only)
    """
    if request.method == "GET":
        tasks = Task.objects.filter(is_active=True)

        # Apply filters
        category = request.GET.get("category")
        if category:
            tasks = tasks.filter(category=category)

        genre = request.GET.get("genre")
        if genre:
            tasks = tasks.filter(genre=genre)

        incentive_type = request.GET.get("incentive_type")
        if incentive_type:
            tasks = tasks.filter(incentive_type=incentive_type)

        # Pagination
        page_size = int(request.GET.get("page_size", 20))
        page = int(request.GET.get("page", 1))
        offset = (page - 1) * page_size

        tasks = tasks.order_by("-created_at")[offset : offset + page_size]

        serializer = TaskSerializer(tasks, many=True, context={"request": request})
        return Response(
            {
                "tasks": serializer.data,
                "count": tasks.count(),
                "page": page,
                "page_size": page_size,
            }
        )

    elif request.method == "POST":
        serializer = TaskCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            task = serializer.save()
            response_serializer = TaskSerializer(task, context={"request": request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def task_detail(request, task_id):
    """
    GET: Retrieve a specific task
    PUT/PATCH: Update a task (brand owner only)
    DELETE: Delete a task (brand owner only)
    """
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = TaskSerializer(task, context={"request": request})
        return Response(serializer.data)

    elif request.method in ["PUT", "PATCH"]:
        # Check if user is the task owner
        if task.brand != request.user:
            return Response(
                {"error": "You can only update your own tasks"},
                status=status.HTTP_403_FORBIDDEN,
            )

        partial = request.method == "PATCH"
        serializer = TaskCreateSerializer(task, data=request.data, partial=partial)
        if serializer.is_valid():
            task = serializer.save()
            response_serializer = TaskSerializer(task, context={"request": request})
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        # Check if user is the task owner
        if task.brand != request.user:
            return Response(
                {"error": "You can only delete your own tasks"},
                status=status.HTTP_403_FORBIDDEN,
            )

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_tasks(request):
    """Get tasks created by the current user"""
    tasks = Task.objects.filter(brand=request.user).order_by("-created_at")

    # Apply filters
    status_filter = request.GET.get("status")
    if status_filter == "active":
        tasks = tasks.filter(is_active=True)
    elif status_filter == "inactive":
        tasks = tasks.filter(is_active=False)

    serializer = TaskSerializer(tasks, many=True, context={"request": request})
    return Response({"tasks": serializer.data})


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def task_applications(request, task_id):
    """
    GET: List applications for a specific task (task owner only)
    POST: Apply to a task (creators only)
    """
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        # Check if user is the task owner
        if task.brand != request.user:
            return Response(
                {"error": "You can only view applications for your own tasks"},
                status=status.HTTP_403_FORBIDDEN,
            )

        applications = task.applications.all().order_by("-applied_at")
        serializer = TaskApplicationSerializer(
            applications, many=True, context={"request": request}
        )
        return Response({"applications": serializer.data})

    elif request.method == "POST":
        serializer = TaskApplicationCreateSerializer(
            data=request.data, context={"request": request, "task": task}
        )
        if serializer.is_valid():
            application = serializer.save()
            response_serializer = TaskApplicationSerializer(
                application, context={"request": request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
def application_detail(request, application_id):
    """
    GET: Retrieve a specific application
    PATCH: Update application status (task owner only)
    """
    try:
        application = TaskApplication.objects.get(id=application_id)
    except TaskApplication.DoesNotExist:
        return Response(
            {"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        # Check if user is the task owner or the applicant
        if (
            application.task.brand != request.user
            and application.creator != request.user
        ):
            return Response(
                {
                    "error": "You can only view your own applications or applications to your tasks"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TaskApplicationSerializer(
            application, context={"request": request}
        )
        return Response(serializer.data)

    elif request.method == "PATCH":
        # Check if user is the task owner
        if application.task.brand != request.user:
            return Response(
                {"error": "You can only update applications for your own tasks"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Only allow status updates
        allowed_fields = ["status"]
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        if "status" in update_data:
            valid_statuses = ["PENDING", "ACCEPTED", "REJECTED", "COMPLETED"]
            if update_data["status"] not in valid_statuses:
                return Response(
                    {"error": f"Invalid status. Must be one of: {valid_statuses}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = TaskApplicationSerializer(
            application, data=update_data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            application = serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_applications(request):
    """Get applications submitted by the current user"""
    applications = TaskApplication.objects.filter(creator=request.user).order_by(
        "-applied_at"
    )

    # Apply filters
    status_filter = request.GET.get("status")
    if status_filter:
        applications = applications.filter(status=status_filter)

    serializer = TaskApplicationSerializer(
        applications, many=True, context={"request": request}
    )
    return Response({"applications": serializer.data})


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Twitter Brand Configuration API Endpoints

# Test endpoint to verify authentication is disabled
@api_view(["GET", "POST"])
@permission_classes([permissions.AllowAny])
def test_auth_disabled(request):
    return Response({"status": "success", "message": "Authentication is disabled", "user": str(request.user)})

@api_view(["POST"])
@permission_classes([permissions.AllowAny])  # Temporary for testing
def save_twitter_config(request, brand_id):
    """
    Save Twitter API configuration for a specific brand
    """
    print(f"DEBUG: save_twitter_config called with brand_id: {brand_id}")
    print(f"DEBUG: request.user: {request.user}")
    print(f"DEBUG: request.user.is_authenticated: {request.user.is_authenticated}")
    
    try:
        # For now, just get the first brand - we'll fix auth later
        brand = Brand.objects.get(id=brand_id)
        print(f"DEBUG: Found brand: {brand.name}")
    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Get configuration data
    api_key = request.data.get("api_key", "").strip()
    api_secret = request.data.get("api_secret", "").strip()
    access_token = request.data.get("access_token", "").strip()
    access_token_secret = request.data.get("access_token_secret", "").strip()
    bearer_token = request.data.get("bearer_token", "").strip()

    # Validate required fields
    if not api_key or not api_secret:
        return Response(
            {"error": "API Key and Secret are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Save configuration
    brand.twitter_api_key = api_key
    brand.twitter_api_secret = api_secret
    brand.twitter_access_token = access_token
    brand.twitter_access_token_secret = access_token_secret
    brand.twitter_bearer_token = bearer_token
    brand.save()

    # Try to get username from Twitter API
    try:
        if bearer_token:
            client = tweepy.Client(bearer_token=bearer_token)
            user = client.get_me()
            if user.data:
                brand.twitter_username = user.data.username
                brand.save()
    except Exception as e:
        logger.warning(f"Could not fetch Twitter username: {e}")

    return Response({
        "success": True,
        "message": "Twitter configuration saved successfully",
        "username": brand.twitter_username,
    })


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def get_twitter_config(request, brand_id):
    """
    Get masked Twitter API configuration for a specific brand
    """
    try:
        brand = Brand.objects.get(id=brand_id, owner=request.user)
    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response({
        **brand.get_masked_twitter_keys(),
        "username": brand.twitter_username,
        "configured": brand.has_twitter_config,
    })


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def test_twitter_connection(request, brand_id):
    """
    Test Twitter API connection for a specific brand
    """
    try:
        brand = Brand.objects.get(id=brand_id)
    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not brand.has_twitter_config:
        return Response(
            {"error": "Twitter not configured for this brand"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Use full OAuth 1.0a authentication for better compatibility
        client = tweepy.Client(
            bearer_token=brand.twitter_bearer_token,
            consumer_key=brand.twitter_api_key,
            consumer_secret=brand.twitter_api_secret,
            access_token=brand.twitter_access_token,
            access_token_secret=brand.twitter_access_token_secret,
        )
        user = client.get_me()
        
        if user.data:
            # Update username if we got it
            if user.data.username != brand.twitter_username:
                brand.twitter_username = user.data.username
                brand.save()
                
            return Response({
                "success": True,
                "username": user.data.username,
                "user_id": user.data.id,
                "name": user.data.name,
            })
        else:
            return Response({
                "success": False,
                "error": "Could not authenticate with Twitter API",
            })
            
    except tweepy.Unauthorized:
        return Response({
            "success": False,
            "error": "Invalid Twitter API credentials",
        })
    except tweepy.TooManyRequests:
        return Response({
            "success": False,
            "error": "Twitter API rate limit exceeded. Please try again later.",
        })
    except Exception as e:
        logger.error(f"Twitter connection test failed: {e}")
        return Response({
            "success": False,
            "error": f"Connection test failed: {str(e)}",
        })


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def send_test_tweet(request, brand_id):
    """
    Send a test tweet for a specific brand
    """
    try:
        brand = Brand.objects.get(id=brand_id, owner=request.user)
    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not brand.has_twitter_config:
        return Response(
            {"error": "Twitter not configured for this brand"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    content = request.data.get("content", "").strip()
    if not content:
        return Response(
            {"error": "Tweet content is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(content) > 280:
        return Response(
            {"error": "Tweet content exceeds 280 characters"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Create Twitter client
        client = tweepy.Client(
            bearer_token=brand.twitter_bearer_token,
            consumer_key=brand.twitter_api_key,
            consumer_secret=brand.twitter_api_secret,
            access_token=brand.twitter_access_token,
            access_token_secret=brand.twitter_access_token_secret,
            wait_on_rate_limit=True,
        )

        # Send tweet
        response = client.create_tweet(text=content)

        if response.data:
            tweet_id = response.data["id"]
            username = brand.twitter_username or "unknown"
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"

            # Save test tweet to database
            BrandTweet.objects.create(
                brand=brand,
                content=content,
                tweet_id=tweet_id,
                status="posted",
                posted_at=timezone.now(),
            )

            return Response({
                "success": True,
                "tweet_id": tweet_id,
                "tweet_url": tweet_url,
                "username": username,
            })
        else:
            return Response({
                "success": False,
                "error": "Failed to post tweet - no response data",
            })

    except tweepy.Unauthorized:
        return Response({
            "success": False,
            "error": "Twitter API authorization failed. Check your credentials.",
            "error_type": "authorization",
        })
    except tweepy.Forbidden as e:
        error_msg = str(e)
        if "write" in error_msg.lower():
            return Response({
                "success": False,
                "error": "Twitter API access level too low. Upgrade to Basic access or higher.",
                "error_type": "access_level",
            })
        return Response({
            "success": False,
            "error": f"Twitter API forbidden: {error_msg}",
            "error_type": "forbidden",
        })
    except Exception as e:
        logger.error(f"Failed to send test tweet: {e}")
        return Response({
            "success": False,
            "error": f"Failed to send tweet: {str(e)}",
        })


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def disconnect_twitter(request, brand_id):
    """
    Disconnect Twitter from a specific brand
    """
    try:
        brand = Brand.objects.get(id=brand_id, owner=request.user)
    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Clear Twitter configuration
    brand.twitter_api_key = ""
    brand.twitter_api_secret = ""
    brand.twitter_access_token = ""
    brand.twitter_access_token_secret = ""
    brand.twitter_bearer_token = ""
    brand.twitter_username = ""
    brand.save()

    return Response({
        "success": True,
        "message": "Twitter disconnected successfully",
    })


# Twitter API Endpoints - using the newer functions above


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_twitter_config(request, brand_id):
    """
    Get masked Twitter API configuration for a specific brand
    """
    try:
        brand = Brand.objects.get(id=brand_id, organization__users=request.user)
    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response({
        **brand.get_masked_twitter_keys(),
        "username": brand.twitter_username,
        "configured": brand.has_twitter_config,
    })


# Removed duplicate test_twitter_connection function - using the one above with proper TokenAuthentication

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def send_test_tweet(request, brand_id):
    """
    Send a test tweet for a specific brand
    """
    try:
        brand = Brand.objects.get(id=brand_id, organization__users=request.user)
    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not brand.has_twitter_config:
        return Response(
            {"error": "Twitter not configured for this brand"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    content = request.data.get("content", "").strip()
    if not content:
        return Response(
            {"error": "Tweet content is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(content) > 280:
        return Response(
            {"error": "Tweet content exceeds 280 characters"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Create Twitter client
        client = tweepy.Client(
            bearer_token=brand.twitter_bearer_token,
            consumer_key=brand.twitter_api_key,
            consumer_secret=brand.twitter_api_secret,
            access_token=brand.twitter_access_token,
            access_token_secret=brand.twitter_access_token_secret,
            wait_on_rate_limit=True,
        )

        # Send tweet
        response = client.create_tweet(text=content)

        if response.data:
            tweet_id = response.data["id"]
            username = brand.twitter_username or "unknown"
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"

            # Save test tweet to database
            BrandTweet.objects.create(
                brand=brand,
                content=content,
                tweet_id=tweet_id,
                status="posted",
                posted_at=timezone.now(),
            )

            return Response({
                "success": True,
                "tweet_id": tweet_id,
                "tweet_url": tweet_url,
                "username": username,
            })
        else:
            return Response({
                "success": False,
                "error": "Failed to post tweet - no response data",
            })

    except tweepy.Unauthorized:
        return Response({
            "success": False,
            "error": "Twitter API authorization failed. Check your credentials.",
            "error_type": "authorization",
        })
    except tweepy.Forbidden as e:
        error_msg = str(e)
        if "write" in error_msg.lower():
            return Response({
                "success": False,
                "error": "Twitter API access level too low. Upgrade to Basic access or higher.",
                "error_type": "access_level",
            })
        return Response({
            "success": False,
            "error": f"Twitter API forbidden: {error_msg}",
            "error_type": "forbidden",
        })
    except Exception as e:
        logger.error(f"Failed to send test tweet: {e}")
        return Response({
            "success": False,
            "error": f"Failed to send tweet: {str(e)}",
        })


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def disconnect_twitter(request, brand_id):
    """
    Disconnect Twitter from a specific brand
    """
    try:
        brand = Brand.objects.get(id=brand_id, organization__users=request.user)
    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Clear Twitter configuration
    brand.twitter_api_key = ""
    brand.twitter_api_secret = ""
    brand.twitter_access_token = ""
    brand.twitter_access_token_secret = ""
    brand.twitter_bearer_token = ""
    brand.twitter_username = ""
    brand.save()

    return Response({
        "success": True,
        "message": "Twitter disconnected successfully",
    })


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def post_tweet(request):
    """
    Post a tweet using the configured Twitter API credentials
    """
    try:
        # Get tweet content from request
        tweet_content = request.data.get("content")
        if not tweet_content:
            return Response(
                {"error": "Tweet content is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the brand if specified
        brand_id = request.data.get("brand_id")
        brand = None
        if brand_id:
            try:
                brand = Brand.objects.get(id=brand_id)
                if not brand.has_twitter_config:
                    return Response(
                        {"error": "Brand does not have Twitter API configuration"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Create Twitter API v2 client using brand credentials
        if not brand or not brand.has_twitter_config:
            return Response(
                {
                    "error": "Brand does not have Twitter configuration. Please connect Twitter to your brand first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = tweepy.Client(
            bearer_token=brand.twitter_bearer_token,
            consumer_key=brand.twitter_api_key,
            consumer_secret=brand.twitter_api_secret,
            access_token=brand.twitter_access_token,
            access_token_secret=brand.twitter_access_token_secret,
            wait_on_rate_limit=True,
        )

        # Post tweet using API v2
        response = client.create_tweet(text=tweet_content)

        if response.data:
            tweet_id = response.data["id"]
            username = brand.twitter_username if brand else settings.TWITTER_USERNAME
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"

            # Save tweet to database
            if brand:
                # Use BrandTweet for brand-specific tweets
                tweet = BrandTweet.objects.create(
                    brand=brand,
                    content=tweet_content,
                    tweet_id=tweet_id,
                    status="posted",
                    posted_at=timezone.now(),
                )

                # Process Twitter mentions in the tweet content
                from .utils import process_tweet_mentions

                process_tweet_mentions(
                    tweet=tweet,
                    organization=brand.organization,
                    user=request.user if hasattr(request, "user") else None,
                )

                # Send Slack notification if brand has Slack configured
                if brand.has_slack_config:
                    try:
                        import requests

                        tweet_url = f"https://twitter.com/{brand.twitter_username}/status/{response.data['id']}"
                        message = (
                            f"🐦 *Brand Tweet Posted for {brand.name}*\n"
                            f"Content: {tweet_content[:150]}{'...' if len(tweet_content) > 150 else ''}\n"
                            f"Tweet URL: {tweet_url}\n"
                            f"Posted via API by: {request.user.username}"
                        )

                        payload = {
                            "text": message,
                            "username": f"Gemnar Bot - {brand.name}",
                            "icon_emoji": ":bird:",
                        }

                        if brand.slack_channel:
                            payload["channel"] = brand.slack_channel

                        requests.post(brand.slack_webhook_url, json=payload, timeout=10)
                    except Exception:
                        pass  # Don't fail tweet posting if Slack fails

            else:
                # Use Tweet for user-specific tweets (legacy)
                # Note: Tweet model requires a configuration, so we need to create one or use existing
                config, created = TweetConfiguration.objects.get_or_create(
                    user=request.user,
                    defaults={
                        "name": "Default Configuration",
                        "prompt_template": "Generate a tweet about {topic}",
                        "topics": ["general"],
                        "tones": ["professional"],
                        "keywords": [],
                        "hashtags": [],
                    },
                )
                tweet = Tweet.objects.create(
                    configuration=config,
                    content=tweet_content,
                    tweet_id=tweet_id,
                    status="posted",
                    posted_at=timezone.now(),
                )

                # Send general Slack notification for user tweet
                try:
                    from website.utils.slack_notifications import SlackNotifier

                    SlackNotifier.send_custom_notification(
                        title="Tweet Posted via API",
                        details=f"User {request.user.username} posted a tweet via API",
                        severity="info",
                    )
                except Exception:
                    pass  # Don't fail tweet posting if Slack fails

            return Response(
                {
                    "success": True,
                    "tweet_id": tweet_id,
                    "tweet_url": tweet_url,
                    "posted_at": tweet.posted_at.isoformat(),
                }
            )
        else:
            return Response(
                {"error": "Failed to post tweet - no response data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except tweepy.Unauthorized:
        return Response(
            {
                "error": "Twitter API authorization failed. Please check your credentials."
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )
    except tweepy.Forbidden as e:
        return Response(
            {"error": f"Twitter API access forbidden: {str(e)}"},
            status=status.HTTP_403_FORBIDDEN,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to post tweet: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def get_twitter_credentials(brand=None, user=None):
    """
    Get Twitter credentials with proper fallback logic.
    Returns (bearer_token, consumer_key, consumer_secret, access_token, access_token_secret)
    """
    if brand and brand.has_twitter_config:
        return (
            brand.twitter_bearer_token,
            brand.twitter_api_key,
            brand.twitter_api_secret,
            brand.twitter_access_token,
            brand.twitter_access_token_secret,
        )
    elif user and user.has_twitter_config:
        return (
            user.twitter_bearer_token,
            user.twitter_api_key,
            user.twitter_api_secret,
            user.twitter_access_token,
            user.twitter_access_token_secret,
        )
    else:
        # Fall back to global settings only if they exist
        global_bearer = getattr(settings, "TWITTER_BEARER_TOKEN", None)
        global_key = getattr(settings, "TWITTER_API_KEY", None)
        global_secret = getattr(settings, "TWITTER_API_SECRET", None)
        global_access = getattr(settings, "TWITTER_ACCESS_TOKEN", None)
        global_access_secret = getattr(settings, "TWITTER_ACCESS_TOKEN_SECRET", None)

        if all(
            [
                global_bearer,
                global_key,
                global_secret,
                global_access,
                global_access_secret,
            ]
        ):
            return (
                global_bearer,
                global_key,
                global_secret,
                global_access,
                global_access_secret,
            )
        else:
            return None


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def check_twitter_credentials(request):
    """
    Check if the Twitter API credentials are valid and return access level info
    """
    try:
        # Get the brand if specified
        brand_id = request.GET.get("brand_id")
        brand = None
        if brand_id:
            try:
                brand = Brand.objects.get(id=brand_id)
                if not brand.has_twitter_config:
                    return Response(
                        {"error": "Brand does not have Twitter API configuration"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Get Twitter credentials using helper function
        credentials = get_twitter_credentials(
            brand=brand, user=request.user if not brand else None
        )

        if not credentials:
            return Response(
                {
                    "error": "No valid Twitter credentials found. Please connect Twitter to your account or brand."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        (
            bearer_token,
            consumer_key,
            consumer_secret,
            access_token,
            access_token_secret,
        ) = credentials

        # Create Twitter API v2 client
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True,
        )

        # Verify credentials by getting user info
        me = client.get_me()
        if not me.data:
            return Response(
                {"error": "Unable to verify Twitter credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "success": True,
                "username": me.data.username,
                "name": me.data.name,
                "id": me.data.id,
            }
        )

    except tweepy.Unauthorized:
        return Response(
            {"error": "Invalid Twitter credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to check credentials: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_tweet_history(request):
    """
    Get tweet history for the user or brand
    """
    try:
        # Get the brand if specified
        brand_id = request.GET.get("brand_id")
        brand = None
        if brand_id:
            try:
                brand = Brand.objects.get(id=brand_id)
            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Query tweets
        if brand:
            # Use BrandTweet for brand-specific tweets
            tweets = BrandTweet.objects.filter(brand=brand).order_by("-posted_at")
        else:
            # Use Tweet for user-specific tweets (legacy) - fix the relationship
            tweets = Tweet.objects.filter(configuration__user=request.user).order_by(
                "-posted_at"
            )

        # Basic pagination
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        start = (page - 1) * page_size
        end = start + page_size

        tweets_data = []
        for tweet in tweets[start:end]:
            if brand:
                # BrandTweet model
                username = brand.twitter_username
                tweet_url = tweet.tweet_url or (
                    f"https://twitter.com/{username}/status/{tweet.tweet_id}"
                    if tweet.tweet_id
                    else None
                )
                tweets_data.append(
                    {
                        "id": tweet.id,
                        "content": tweet.content,
                        "status": tweet.status,
                        "tweet_id": tweet.tweet_id,
                        "tweet_url": tweet_url,
                        "posted_at": (
                            tweet.posted_at.isoformat() if tweet.posted_at else None
                        ),
                        "error_message": tweet.error_message,
                        "scheduled_for": (
                            tweet.scheduled_for.isoformat()
                            if tweet.scheduled_for
                            else None
                        ),
                    }
                )
            else:
                # Tweet model (legacy)
                username = settings.TWITTER_USERNAME
                tweet_url = (
                    f"https://twitter.com/{username}/status/{tweet.tweet_id}"
                    if tweet.tweet_id
                    else None
                )
                tweets_data.append(
                    {
                        "id": tweet.id,
                        "content": tweet.content,
                        "status": tweet.status,
                        "tweet_id": tweet.tweet_id,
                        "tweet_url": tweet_url,
                        "posted_at": (
                            tweet.posted_at.isoformat() if tweet.posted_at else None
                        ),
                        "error_message": tweet.error_message,
                    }
                )

        return Response(
            {
                "tweets": tweets_data,
                "total": tweets.count(),
                "page": page,
                "page_size": page_size,
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to get tweet history: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Tweet Configuration API Endpoints
@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def tweet_configurations(request):
    """
    List and create tweet configurations
    """
    try:
        if request.method == "GET":
            # Get brand_id from query params
            brand_id = request.GET.get("brand_id")

            # Query configurations
            configs = TweetConfiguration.objects.filter(
                brand_id=brand_id if brand_id else None,
                user=request.user if not brand_id else None,
            ).order_by("-created_at")

            serializer = TweetConfigurationSerializer(configs, many=True)
            return Response(serializer.data)

        elif request.method == "POST":
            serializer = TweetConfigurationSerializer(data=request.data)
            if serializer.is_valid():
                # Set user if no brand specified
                if not serializer.validated_data.get("brand"):
                    serializer.validated_data["user"] = request.user
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": f"Failed to process tweet configurations: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Brand Tweets API Endpoints
@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def brand_tweets(request):
    """
    List and create brand tweets
    """
    try:
        if request.method == "GET":
            # Get query parameters
            brand_id = request.GET.get("brand_id")
            status_filter = request.GET.get("status")
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 20))

            # Build query
            if brand_id:
                tweets = BrandTweet.objects.filter(brand_id=brand_id)
            else:
                # If no brand_id, return empty queryset (or you could return all brands owned by user)
                tweets = BrandTweet.objects.none()

            if status_filter:
                tweets = tweets.filter(status=status_filter)

            tweets = tweets.order_by("-created_at")

            # Paginate results
            start = (page - 1) * page_size
            end = start + page_size

            serializer = BrandTweetSerializer(tweets[start:end], many=True)

            return Response(
                {
                    "tweets": serializer.data,
                    "total": tweets.count(),
                    "page": page,
                    "page_size": page_size,
                }
            )

        elif request.method == "POST":
            serializer = BrandTweetSerializer(data=request.data)
            if serializer.is_valid():
                # Check brand ownership if brand is specified
                brand = serializer.validated_data.get("brand")
                if brand:
                    # Validate user owns the brand
                    if brand.owner != request.user:
                        return Response(
                            {"error": "Not authorized to create tweets for this brand"},
                            status=status.HTTP_403_FORBIDDEN,
                        )
                else:
                    # Set user if no brand specified
                    serializer.validated_data["user"] = request.user

                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": f"Failed to process brand tweets: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def brand_tweet_detail(request, tweet_id):
    """
    Retrieve, update or delete a brand tweet
    """
    try:
        tweet = BrandTweet.objects.get(id=tweet_id)

        # Check permissions
        if tweet.brand and tweet.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to access this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif not tweet.brand and tweet.user != request.user:
            return Response(
                {"error": "Not authorized to access this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "GET":
            serializer = BrandTweetSerializer(tweet)
            return Response(serializer.data)

        elif request.method == "PUT":
            serializer = BrandTweetSerializer(tweet, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == "DELETE":
            tweet.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except BrandTweet.DoesNotExist:
        return Response({"error": "Tweet not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": f"Failed to process brand tweet: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def post_tweet_now(request, tweet_id):
    """
    Post a brand tweet immediately
    """
    try:
        tweet = BrandTweet.objects.get(id=tweet_id)

        # Check permissions
        if tweet.brand and tweet.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to post this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif not tweet.brand and tweet.user != request.user:
            return Response(
                {"error": "Not authorized to post this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if tweet can be posted
        if not tweet.can_be_posted:
            return Response(
                {"error": "Tweet cannot be posted. Check status and content."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create Twitter API client using brand credentials
        if not tweet.brand or not tweet.brand.has_twitter_config:
            return Response(
                {
                    "error": "Brand does not have Twitter configuration. Please connect Twitter to your brand first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = tweepy.Client(
            bearer_token=tweet.brand.twitter_bearer_token,
            consumer_key=tweet.brand.twitter_api_key,
            consumer_secret=tweet.brand.twitter_api_secret,
            access_token=tweet.brand.twitter_access_token,
            access_token_secret=tweet.brand.twitter_access_token_secret,
            wait_on_rate_limit=True,
        )

        # Prepare media ids if image present
        media_ids = None
        if tweet.image:
            try:
                # Upload media using v1.1 API
                import tweepy as tweepy_v1

                api = tweepy_v1.API(
                    tweepy_v1.OAuth1UserHandler(
                        consumer_key=tweet.brand.twitter_api_key,
                        consumer_secret=tweet.brand.twitter_api_secret,
                        access_token=tweet.brand.twitter_access_token,
                        access_token_secret=tweet.brand.twitter_access_token_secret,
                    ),
                    wait_on_rate_limit=True,
                )
                uploaded = api.media_upload(filename=tweet.image.path)
                media_ids = [uploaded.media_id]
            except Exception as media_e:
                # Fail posting if media fails to upload to avoid text-only posting when image expected
                tweet.status = "failed"
                tweet.error_message = f"Failed to upload image: {media_e}"
                tweet.save()
                return Response(
                    {"error": tweet.error_message},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Post tweet (with media if available)
        response = client.create_tweet(text=tweet.content, media_ids=media_ids)

        # Update tweet record with URL
        tweet.tweet_id = response.data["id"]
        tweet.posted_at = timezone.now()
        tweet.status = "posted"
        tweet.tweet_url = tweet.get_twitter_url()
        tweet.save()

        # Send Slack notification if brand has Slack configured
        if tweet.brand and tweet.brand.has_slack_config:
            try:
                import requests

                tweet_url = f"https://twitter.com/{tweet.brand.twitter_username}/status/{response.data['id']}"
                message = (
                    f"🐦 *Brand Tweet Posted for {tweet.brand.name}*\n"
                    f"Content: {tweet.content[:150]}{'...' if len(tweet.content) > 150 else ''}\n"
                    f"Tweet URL: {tweet_url}\n"
                    f"Posted via API by: {request.user.username}"
                )

                payload = {
                    "text": message,
                    "username": f"Gemnar Bot - {tweet.brand.name}",
                    "icon_emoji": ":bird:",
                }

                if tweet.brand.slack_channel:
                    payload["channel"] = tweet.brand.slack_channel

                requests.post(tweet.brand.slack_webhook_url, json=payload, timeout=10)
            except Exception:
                pass  # Don't fail tweet posting if Slack fails

        # Send real-time notification using existing TweetQueueConsumer
        channel_layer = get_channel_layer()
        if tweet.brand and tweet.brand.organization:
            async_to_sync(channel_layer.group_send)(
                f"tweet_queue_{tweet.brand.organization.id}_{tweet.brand.id}",
                {
                    "type": "tweet_posted",
                    "tweet_id": tweet.id,
                    "posted_at": timezone.now().isoformat(),
                    "tweet_url": f"https://twitter.com/{tweet.brand.twitter_username}/status/{response.data['id']}",
                },
            )

        serializer = BrandTweetSerializer(tweet)
        return Response(serializer.data)

    except BrandTweet.DoesNotExist:
        return Response({"error": "Tweet not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Update tweet with error
        if "tweet" in locals():
            tweet.error_message = str(e)
            tweet.status = "failed"
            tweet.save()

        return Response(
            {"error": f"Failed to post tweet: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def refresh_brand_tweet_metrics(request, tweet_id):
    """Refresh metrics for a brand tweet (global)."""
    try:
        tweet = BrandTweet.objects.get(id=tweet_id)

        # Permission: must own brand
        if tweet.brand and tweet.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to refresh this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if tweet.status != "posted" or not tweet.tweet_id:
            return Response(
                {"error": "Cannot refresh metrics for non-posted tweet"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not tweet.brand or not tweet.brand.has_twitter_config:
            return Response(
                {"error": "Brand does not have Twitter configuration"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, message = tweet.refresh_metrics()
        if not success:
            return Response(
                {"error": message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        from .serializers import BrandTweetSerializer

        serializer = BrandTweetSerializer(tweet, context={"request": request})
        return Response({"success": True, "message": message, "tweet": serializer.data})
    except BrandTweet.DoesNotExist:
        return Response({"error": "Tweet not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": f"Failed to refresh metrics: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_tweet_content(request):
    """
    Generate tweet content using AI
    """
    try:
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "AI service not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Get parameters
        prompt = request.data.get("prompt")
        topic = request.data.get("topic")
        tone = request.data.get("tone")
        keywords = request.data.get("keywords", [])
        hashtags = request.data.get("hashtags", [])

        if not all([prompt, topic, tone]):
            return Response(
                {"error": "Prompt, topic, and tone are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate prompt contains required placeholders
        if not all(ph in prompt for ph in ["{topic}", "{tone}"]):
            return Response(
                {"error": "Prompt must contain {topic} and {tone} placeholders"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If keywords provided, validate placeholder exists
        if keywords and "{keywords}" not in prompt:
            return Response(
                {
                    "error": "Prompt must contain {keywords} placeholder when keywords are provided"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Format prompt with parameters
        try:
            formatted_prompt = prompt.format(
                topic=topic,
                tone=tone,
                keywords=(
                    ", ".join(keywords[:3]) if keywords else "no specific keywords"
                ),
                hashtags=" ".join(hashtags[:3]) if hashtags else "",
            )
        except KeyError as e:
            return Response(
                {"error": f"Invalid placeholder in prompt: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Error formatting prompt: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enhanced system message
        system_message = f"""You are a professional social media manager crafting engaging tweets.

Your task is to create a tweet that is:
1. Exactly matching the requested tone: {tone}
2. Focused specifically on the topic: {topic}
3. Under 280 characters
4. Engaging and authentic
5. Action-oriented when appropriate
6. Using natural, conversational language

Additional guidelines:
- Don't use hashtags unless specifically requested
- Avoid generic or templated-sounding language
- Focus on providing value to the reader
- Make it sound like a real person wrote it
- Do NOT wrap the tweet in quotes - return the raw tweet text only
- Do NOT add any formatting or punctuation around the tweet"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": formatted_prompt},
            ],
            max_tokens=100,
            temperature=0.7,
        )

        generated_content = response.choices[0].message.content.strip()

        # Remove quotes if the AI wrapped the content in quotes
        if generated_content.startswith('"') and generated_content.endswith('"'):
            generated_content = generated_content[1:-1]
        # Also remove single quotes
        if generated_content.startswith("'") and generated_content.endswith("'"):
            generated_content = generated_content[1:-1]

        # Validate the generated content
        if len(generated_content) > 280:
            generated_content = generated_content[:277] + "..."

        return Response(
            {
                "content": generated_content,
                "prompt_used": formatted_prompt,
                "system_message": system_message,  # Include for debugging
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to generate tweet content: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Priority 1: Core Missing Features - Tweet Analytics
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def tweet_analytics(request):
    """
    Get tweet analytics for a brand or user
    """
    try:
        # Get brand_id from query params
        brand_id = request.GET.get("brand_id")

        # Get analytics data
        if brand_id:
            # Brand-specific analytics
            try:
                brand = Brand.objects.get(id=brand_id)
                tweets = BrandTweet.objects.filter(brand=brand)

                # Early exit if no posted tweets exist for this brand
                if not BrandTweet.has_posted_tweets(brand=brand):
                    analytics_data = {
                        "total_tweets": tweets.count(),
                        "posted_tweets": 0,
                        "scheduled_tweets": tweets.filter(status="approved").count(),
                        "failed_tweets": tweets.filter(status="failed").count(),
                        "engagement_rate": 0.0,
                        "recent_activity": [],
                        "message": "No posted tweets found for this brand",
                    }
                    return Response(analytics_data)

            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            # User-specific analytics - get tweets from all user's brands
            user_brands = Brand.objects.filter(owner=request.user)
            tweets = BrandTweet.objects.filter(brand__in=user_brands)

            # Early exit if no posted tweets exist for any of user's brands
            if not BrandTweet.has_posted_tweets():
                analytics_data = {
                    "total_tweets": tweets.count(),
                    "posted_tweets": 0,
                    "scheduled_tweets": tweets.filter(status="approved").count(),
                    "failed_tweets": tweets.filter(status="failed").count(),
                    "engagement_rate": 0.0,
                    "recent_activity": [],
                    "message": "No posted tweets found",
                }
                return Response(analytics_data)

        # Calculate analytics
        total_tweets = tweets.count()
        posted_tweets = tweets.filter(status="posted").count()
        scheduled_tweets = tweets.filter(status="approved").count()
        failed_tweets = tweets.filter(status="failed").count()

        # Get recent activity (last 10 tweets)
        recent_activity = tweets.order_by("-created_at")[:10].values(
            "id", "content", "status", "created_at", "posted_at"
        )

        # Calculate engagement metrics (if available)
        engagement_rate = 0.0
        if posted_tweets > 0:
            # This would need Twitter API integration for real metrics
            engagement_rate = 2.5  # Placeholder

        analytics_data = {
            "total_tweets": total_tweets,
            "posted_tweets": posted_tweets,
            "scheduled_tweets": scheduled_tweets,
            "failed_tweets": failed_tweets,
            "engagement_rate": engagement_rate,
            "recent_activity": list(recent_activity),
        }

        return Response(analytics_data)

    except Exception as e:
        return Response(
            {"error": f"Failed to get tweet analytics: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Priority 1: Core Missing Features - Delete Tweet
@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def delete_tweet(request, tweet_id):
    """
    Delete a tweet from Twitter and database
    """
    try:
        # Get the tweet
        try:
            tweet = BrandTweet.objects.get(id=tweet_id)
        except BrandTweet.DoesNotExist:
            return Response(
                {"error": "Tweet not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        if tweet.brand and tweet.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to delete this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif not tweet.brand and tweet.user != request.user:
            return Response(
                {"error": "Not authorized to delete this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Delete from Twitter if it was posted
        if tweet.tweet_id and tweet.status == "posted":
            try:
                import tweepy

                # Create Twitter API client using brand credentials
                if not tweet.brand or not tweet.brand.has_twitter_config:
                    print(
                        "Brand does not have Twitter configuration, skipping Twitter deletion"
                    )
                else:
                    client = tweepy.Client(
                        bearer_token=tweet.brand.twitter_bearer_token,
                        consumer_key=tweet.brand.twitter_api_key,
                        consumer_secret=tweet.brand.twitter_api_secret,
                        access_token=tweet.brand.twitter_access_token,
                        access_token_secret=tweet.brand.twitter_access_token_secret,
                        wait_on_rate_limit=True,
                    )

                    # Delete tweet from Twitter
                    client.delete_tweet(tweet.tweet_id)

            except Exception as e:
                # Log error but continue with database deletion
                print(f"Failed to delete tweet from Twitter: {str(e)}")

        # Delete from database
        tweet.delete()

        return Response(
            {"success": True, "message": "Tweet deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to delete tweet: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Priority 1: Core Missing Features - Update Tweet Schedule
@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def update_tweet_schedule(request, tweet_id):
    """
    Update tweet schedule
    """
    try:
        # Get the tweet
        try:
            tweet = BrandTweet.objects.get(id=tweet_id)
        except BrandTweet.DoesNotExist:
            return Response(
                {"error": "Tweet not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        if tweet.brand and tweet.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to update this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif not tweet.brand and tweet.user != request.user:
            return Response(
                {"error": "Not authorized to update this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if tweet can be rescheduled
        if tweet.status == "posted":
            return Response(
                {"error": "Cannot reschedule a posted tweet"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get new schedule from request
        scheduled_for_str = request.data.get("scheduled_for")
        if not scheduled_for_str:
            return Response(
                {"error": "scheduled_for is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse the datetime
        try:
            from datetime import datetime

            scheduled_for = datetime.fromisoformat(
                scheduled_for_str.replace("Z", "+00:00")
            )
            if scheduled_for.tzinfo is None:
                scheduled_for = timezone.make_aware(scheduled_for)
        except ValueError as e:
            return Response(
                {"error": f"Invalid datetime format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update tweet schedule
        tweet.scheduled_for = scheduled_for
        tweet.save()

        return Response(
            {
                "success": True,
                "message": "Tweet schedule updated successfully",
                "scheduled_for": scheduled_for.isoformat(),
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to update tweet schedule: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Phase 2: AI Integration - Generate Tweet Image
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_tweet_image(request, tweet_id):
    """
    Generate AI image for a tweet
    """
    try:
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "AI service not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Get the tweet
        try:
            tweet = BrandTweet.objects.get(id=tweet_id)
        except BrandTweet.DoesNotExist:
            return Response(
                {"error": "Tweet not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        if tweet.brand and tweet.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to modify this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif not tweet.brand and tweet.user != request.user:
            return Response(
                {"error": "Not authorized to modify this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get prompt from request
        prompt = request.data.get("prompt")
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Clean and validate prompt
        prompt = prompt.strip()
        if len(prompt) > 1000:  # OpenAI has prompt length limits
            prompt = prompt[:1000]

        # Remove any potentially problematic characters
        import re

        prompt = re.sub(r"[^\w\s\-.,!?()]", "", prompt)

        # Generate image using OpenAI DALL-E
        try:
            # Create a tweet-specific prompt (limit tweet content to avoid long prompts)
            tweet_content = (
                tweet.content[:200] if len(tweet.content) > 200 else tweet.content
            )
            image_prompt = f"Create a professional social media image for: {tweet_content}. {prompt}"

            # Ensure prompt is not too long for OpenAI
            if len(image_prompt) > 1000:
                image_prompt = image_prompt[:1000]

            logger.info(f"Generating image with prompt: {image_prompt[:100]}...")

            response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                n=1,
                size="1024x1024",
                quality="standard",
            )

            if not response.data or not response.data[0].url:
                return Response(
                    {"error": "No image generated by OpenAI"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            image_url = response.data[0].url

            # Download and save the image
            import requests
            from django.core.files.base import ContentFile

            image_response = requests.get(image_url, timeout=30)
            if image_response.status_code == 200:
                # Save image to tweet
                image_name = f"tweet_{tweet_id}_ai_image_{uuid.uuid4().hex[:8]}.png"
                tweet.image.save(
                    image_name, ContentFile(image_response.content), save=True
                )

                # Build full URL for the image
                from django.contrib.sites.models import Site

                try:
                    current_site = Site.objects.get_current()
                    protocol = "https" if getattr(settings, "USE_TLS", True) else "http"
                    full_image_url = (
                        f"{protocol}://{current_site.domain}{tweet.image.url}"
                    )
                except Exception:
                    # Fallback to manual domain construction
                    if settings.DEBUG:
                        # Development environment
                        full_image_url = f"http://localhost:8000{tweet.image.url}"
                    else:
                        # Production environment
                        domain = getattr(settings, "SITE_DOMAIN", "gemnar.com")
                        protocol = (
                            "https" if getattr(settings, "USE_TLS", True) else "http"
                        )
                        full_image_url = f"{protocol}://{domain}{tweet.image.url}"

                # Include serialized tweet so clients can update without refetch
                from .serializers import BrandTweetSerializer

                serializer = BrandTweetSerializer(tweet, context={"request": request})
                return Response(
                    {
                        "success": True,
                        "image_url": full_image_url,
                        "message": "Image generated successfully",
                        "tweet": serializer.data,
                    }
                )
            else:
                return Response(
                    {
                        "error": f"Failed to download generated image: HTTP {image_response.status_code}"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"OpenAI image generation error: {error_msg}")

            # Handle specific OpenAI errors
            if "content_policy_violation" in error_msg.lower():
                return Response(
                    {
                        "error": "The prompt violates OpenAI's content policy. Please try a different prompt."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif "billing" in error_msg.lower() or "quota" in error_msg.lower():
                return Response(
                    {
                        "error": "OpenAI billing/quota issue. Please check your OpenAI account."
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            elif "rate_limit" in error_msg.lower():
                return Response(
                    {"error": "OpenAI rate limit exceeded. Please try again later."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            else:
                return Response(
                    {"error": f"Failed to generate image: {error_msg}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

    except Exception as e:
        logger.error(f"Unexpected error in generate_tweet_image: {str(e)}")
        return Response(
            {"error": f"Failed to generate tweet image: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_tweet_text(request, tweet_id):
    """
    Generate AI text for a tweet
    """
    logger.info(f"Starting API AI tweet generation for tweet_id: {tweet_id}")

    try:
        # Import get_openai_client with detailed error handling
        try:
            from website.utils import get_openai_client

            logger.info("Successfully imported get_openai_client in API")
        except ImportError as e:
            logger.error(f"Failed to import get_openai_client in API: {e}")
            return Response(
                {"error": f"Import error: {str(e)}. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(f"Unexpected error importing get_openai_client in API: {e}")
            return Response(
                {"error": f"Import error: {str(e)}. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Get OpenAI client with detailed logging
        try:
            client = get_openai_client()
            if not client:
                logger.error("OpenAI client returned None in API - key not configured")
                return Response(
                    {"error": "AI service not available - API key not configured"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            logger.info("OpenAI client created successfully in API")
        except Exception as e:
            logger.error(f"Error creating OpenAI client in API: {e}")
            return Response(
                {"error": f"Failed to create AI client: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Get the tweet
        try:
            tweet = BrandTweet.objects.get(id=tweet_id)
        except BrandTweet.DoesNotExist:
            return Response(
                {"error": "Tweet not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        if tweet.brand and tweet.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to modify this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif not tweet.brand and tweet.user != request.user:
            return Response(
                {"error": "Not authorized to modify this tweet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get parameters from request
        prompt = request.data.get("prompt", "")
        topic = request.data.get("topic", "")
        tone = request.data.get("tone", "professional")
        keywords = request.data.get("keywords", [])
        hashtags = request.data.get("hashtags", [])

        # Create AI prompt
        ai_prompt = f"""
        Generate an engaging tweet about {topic or "social media"}.
        Tone: {tone}
        Keywords to include: {", ".join(keywords) if keywords else "none"}
        Hashtags to include: {" ".join(hashtags) if hashtags else "none"}
        Additional context: {prompt}
        
        Make it engaging, authentic, and under 280 characters.
        """

        logger.info(f"API generating tweet with prompt: {ai_prompt[:100]}...")

        # Generate content using OpenAI
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional social media manager crafting engaging tweets. Keep responses under 280 characters and make them authentic and engaging.",
                    },
                    {"role": "user", "content": ai_prompt},
                ],
                max_tokens=100,
                temperature=0.7,
            )

            generated_content = response.choices[0].message.content.strip()

            # Remove quotes if the AI wrapped the content in quotes
            if generated_content.startswith('"') and generated_content.endswith('"'):
                generated_content = generated_content[1:-1]
            # Also remove single quotes
            if generated_content.startswith("'") and generated_content.endswith("'"):
                generated_content = generated_content[1:-1]

            logger.info(f"API successfully generated: {generated_content[:50]}...")

            # Update tweet content
            tweet.content = generated_content
            tweet.ai_prompt = ai_prompt
            tweet.save()

            return Response(
                {
                    "success": True,
                    "content": generated_content,
                    "prompt_used": ai_prompt,
                    "message": "Tweet text generated successfully",
                }
            )

        except Exception as openai_error:
            logger.error(f"OpenAI API error in API: {str(openai_error)}")
            if "authentication" in str(openai_error).lower():
                return Response(
                    {"error": "Invalid OpenAI API key. Please check configuration."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            elif "rate_limit" in str(openai_error).lower():
                return Response(
                    {"error": "OpenAI rate limit exceeded. Please try again later."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            else:
                return Response(
                    {"error": f"Failed to generate tweet text: {str(openai_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

    except Exception as e:
        logger.error(f"Unexpected error in API tweet generation: {str(e)}")
        return Response(
            {"error": f"Failed to generate tweet text: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Instagram API Endpoints
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def post_instagram(request):
    """
    Post to Instagram using the configured Instagram API credentials
    """
    try:
        # Get post content and media from request
        post_content = request.data.get("content", "")
        image_file = request.FILES.get("image")
        image_url = request.data.get("image_url")
        video_file = request.FILES.get("video")
        video_url = request.data.get("video_url")

        # Check if we have content or media
        if (
            not post_content
            and not image_file
            and not image_url
            and not video_file
            and not video_url
        ):
            return Response(
                {
                    "error": "Either content, image file, image URL, video file, or video URL is required"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the brand if specified, default to user's first brand
        brand_id = request.data.get("brand_id")
        brand = None
        if brand_id:
            try:
                brand = Brand.objects.get(id=brand_id, owner=request.user)
                if not brand.has_instagram_config:
                    return Response(
                        {"error": "Brand does not have Instagram API configuration"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found or not owned by user"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Get user's first brand with Instagram config if no brand_id specified
            brand = Brand.objects.filter(
                owner=request.user,
                instagram_access_token__isnull=False,
                instagram_user_id__isnull=False,
                instagram_app_id__isnull=False,
                instagram_app_secret__isnull=False,
            ).first()
            if not brand:
                return Response(
                    {
                        "error": "No brand found with Instagram API configuration for user"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create Instagram post record
        from .models import BrandInstagramPost
        from django.core.files.base import ContentFile
        import requests

        # Handle image URL by downloading it
        final_image_file = image_file
        if image_url and not image_file:
            try:
                # Download the image from the URL
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()

                # Create a file-like object from the downloaded content
                import os
                from urllib.parse import urlparse

                parsed_url = urlparse(image_url)
                filename = os.path.basename(parsed_url.path) or "instagram_image.jpg"

                final_image_file = ContentFile(response.content, name=filename)
            except Exception as e:
                return Response(
                    {"error": f"Failed to download image from URL: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Handle video URL by downloading it
        final_video_file = video_file
        if video_url and not video_file:
            try:
                # Download the video from the URL
                response = requests.get(video_url, timeout=30)
                response.raise_for_status()

                # Create a file-like object from the downloaded content
                import os
                from urllib.parse import urlparse

                parsed_url = urlparse(video_url)
                filename = os.path.basename(parsed_url.path) or "instagram_video.mp4"

                final_video_file = ContentFile(response.content, name=filename)
            except Exception as e:
                return Response(
                    {"error": f"Failed to download video from URL: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create Instagram post with image or video
        if final_video_file:
            instagram_post = BrandInstagramPost.objects.create(
                brand=brand,
                content=post_content,
                video=final_video_file,
                is_video_post=True,
                status="approved",
            )
        else:
            instagram_post = BrandInstagramPost.objects.create(
                brand=brand,
                content=post_content,
                image=final_image_file,
                status="approved",
            )

        # Post to Instagram
        success, error = instagram_post.post_to_instagram()

        if success:
            return Response(
                {
                    "success": True,
                    "post_id": instagram_post.id,
                    "instagram_id": instagram_post.instagram_id,
                    "instagram_url": instagram_post.instagram_url,
                    "posted_at": (
                        instagram_post.posted_at.isoformat()
                        if instagram_post.posted_at
                        else None
                    ),
                    "content": instagram_post.content,
                    "status": instagram_post.status,
                }
            )
        else:
            return Response(
                {
                    "success": False,
                    "error": error,
                    "post_id": instagram_post.id,
                    "status": instagram_post.status,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response(
            {"error": f"Failed to post to Instagram: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def check_instagram_credentials(request):
    """
    Check if the Instagram API credentials are valid
    """
    try:
        # Get the brand if specified
        brand_id = request.GET.get("brand_id")
        brand = None

        if brand_id:
            try:
                brand = Brand.objects.get(id=brand_id)

                # Check if user owns this brand
                if brand.owner != request.user:
                    return Response(
                        {"error": "Not authorized to access this brand"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if not brand.has_instagram_config:
                    return Response(
                        {"error": "Brand does not have Instagram API configuration"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"error": "Brand ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Test Instagram API connection
        import requests

        access_token = brand.instagram_access_token
        user_id = brand.instagram_user_id

        # Validate required fields
        if not access_token or access_token.strip() == "":
            return Response(
                {"error": "Instagram access token is missing or empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_id or user_id.strip() == "":
            return Response(
                {"error": "Instagram user ID is missing or empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate Instagram User ID format
        # Instagram Business Account IDs are typically numeric and longer than Facebook User IDs
        if not user_id.isdigit():
            return Response(
                {
                    "error": "Instagram user ID must be numeric. Please ensure you're using the Instagram Business Account ID, not a Facebook User ID."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Instagram Business Account IDs are typically 15-20 digits, while Facebook User IDs are shorter
        if len(user_id) < 10:
            return Response(
                {
                    "error": "Instagram user ID appears to be too short. Please ensure you're using the Instagram Business Account ID from your Facebook app settings, not a Facebook User ID."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Detect likely Basic Display token (older heuristic IGQV prefix)
        # but don't block outright.
        basic_display_suspected = access_token.startswith("IGQV")
        # Always attempt Graph API (v18.0) so user gets definitive feedback.
        url = f"https://graph.facebook.com/v18.0/{user_id}"
        params = {
            "fields": "id,username,account_type",
            "access_token": access_token,
        }
        api_type = "Instagram Graph API"

        print(f"DEBUG: Checking {api_type} credentials for brand {brand_id}")
        print(f"DEBUG: Instagram API URL: {url}")
        print(f"DEBUG: Instagram API params: {params}")

        response = requests.get(url, params=params, timeout=10)
        print(f"DEBUG: Instagram API response status: {response.status_code}")
        print(f"DEBUG: Instagram API response body: {response.text}")

        if response.status_code == 200:
            user_data = response.json()
            payload = {
                "success": True,
                "username": user_data.get("username"),
                "account_type": user_data.get("account_type", "instagram"),
                "user_id": user_data.get("id"),
            }
            if basic_display_suspected:
                payload["warning"] = (
                    "Token prefix suggests Basic Display (IGQV...). "
                    "Basic Display tokens cannot publish media. If posting "
                    "fails, generate a Graph API token with "
                    "instagram_content_publish permission."
                )
                payload["basic_display_suspected"] = True
            return Response(payload)
        else:
            # Enhanced error handling for Instagram API errors
            error_message = "Unable to verify Instagram credentials"
            error_details = {}
            error_code = None
            # Default HTTP status for validation-type issues unless overridden
            http_status = status.HTTP_400_BAD_REQUEST

            try:
                error_data = response.json()
                if "error" in error_data:
                    error_detail = error_data["error"]
                    error_code = error_detail.get("code", None)
                    error_subcode = error_detail.get("error_subcode", "unknown")
                    error_message = error_detail.get(
                        "message", "Unknown Instagram API error"
                    )

                    error_details = {
                        "code": error_code or "unknown",
                        "subcode": error_subcode,
                        "type": error_detail.get("type", "unknown"),
                        "fbtrace_id": error_detail.get("fbtrace_id", ""),
                    }

                    # Provide specific guidance based on error codes
                    if error_code == 190:
                        error_message = (
                            "Access token is invalid or expired. Please "
                            "refresh your Instagram connection."
                        )
                        http_status = status.HTTP_401_UNAUTHORIZED
                    elif error_code == 100:
                        error_message = (
                            "Invalid Instagram user ID. Error 100 typically "
                            "means you're using a Facebook User ID instead of "
                            "an Instagram Business Account ID. Please ensure "
                            "you're using the correct Instagram Business "
                            "Account ID from your Facebook app settings."
                        )
                        http_status = status.HTTP_400_BAD_REQUEST
                    elif error_code == 104:
                        error_message = (
                            "Instagram API rate limit exceeded. Please try again later."
                        )
                        http_status = status.HTTP_429_TOO_MANY_REQUESTS
                    elif error_code == 1:
                        error_message = (
                            "Instagram API error. Please check your app "
                            "permissions and configuration."
                        )
                        http_status = status.HTTP_502_BAD_GATEWAY
                    else:
                        # Unhandled Instagram error code: treat as upstream
                        # failure
                        http_status = status.HTTP_502_BAD_GATEWAY

            except (ValueError, KeyError) as e:
                print(f"DEBUG: Failed to parse Instagram API error response: {e}")
                error_message = (
                    "Instagram API returned status "
                    f"{response.status_code}: {response.text}"
                )
                http_status = status.HTTP_502_BAD_GATEWAY

            return Response(
                {
                    "success": False,
                    "error": error_message,
                    "error_details": error_details,
                    "status_code": response.status_code,
                    "upstream_status": response.status_code,
                    "mapped_http_status": http_status,
                    "response_text": response.text[
                        :500
                    ],  # Limit response text for security
                },
                status=http_status,
            )

    except Exception as e:
        print(f"DEBUG: Exception in check_instagram_credentials: {e}")
        return Response(
            {"error": f"Failed to check Instagram credentials: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_instagram_post_history(request):
    """
    Get Instagram post history for the user or brand
    """
    try:
        # Get the brand if specified
        brand_id = request.GET.get("brand_id")
        brand = None
        if brand_id:
            try:
                brand = Brand.objects.get(id=brand_id)
            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Query Instagram posts
        from .models import BrandInstagramPost

        posts = BrandInstagramPost.objects.filter(
            brand=brand if brand else None
        ).order_by("-posted_at")

        # Basic pagination
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))
        start = (page - 1) * page_size
        end = start + page_size

        posts_data = []
        for post in posts[start:end]:
            posts_data.append(
                {
                    "id": post.id,
                    "content": post.content,
                    "status": post.status,
                    "instagram_id": post.instagram_id,
                    "instagram_url": post.instagram_url,
                    "posted_at": (
                        post.posted_at.isoformat() if post.posted_at else None
                    ),
                    "error_message": post.error_message,
                    "image_url": post.get_thumbnail_url(),
                }
            )

        return Response(
            {
                "posts": posts_data,
                "total": posts.count(),
                "page": page,
                "page_size": page_size,
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to get Instagram post history: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Brand Instagram Posts API Endpoints
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def test_auth(request):
    """Test endpoint to verify authentication"""
    return Response(
        {
            "user": request.user.username,
            "user_id": request.user.id,
            "is_authenticated": request.user.is_authenticated,
            "headers": dict(request.headers),
        }
    )


@api_view(["GET", "POST"])
def test_auth_debug(request):
    """Debug endpoint to test authentication without requiring it"""
    auth_header = request.headers.get("Authorization", "Not found")
    user_info = {
        "user": str(request.user),
        "user_id": getattr(request.user, "id", "N/A"),
        "is_authenticated": request.user.is_authenticated,
        "is_anonymous": request.user.is_anonymous,
        "auth_header": auth_header,
        "method": request.method,
        "all_headers": dict(request.headers),
    }

    print(f"DEBUG: test_auth_debug called with: {user_info}")

    return Response(user_info)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def debug_instagram_config(request):
    """
    Debug Instagram configuration for a brand
    """
    try:
        brand_id = request.GET.get("brand_id")
        if not brand_id:
            return Response(
                {"error": "Brand ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            brand = Brand.objects.get(id=brand_id)

            # Check if user owns this brand
            if brand.owner != request.user:
                return Response(
                    {"error": "Not authorized to access this brand"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Return debug information (masked for security)
        def mask_token(token, show_chars=8):
            if not token or len(token) <= show_chars * 2:
                return "Not set" if not token else f"{token[:3]}...{token[-3:]}"
            return f"{token[:show_chars]}...{token[-show_chars:]}"

        debug_info = {
            "brand_id": brand.id,
            "brand_name": brand.name,
            "has_instagram_config": brand.has_instagram_config,
            "instagram_username": brand.instagram_username,
            "instagram_user_id": brand.instagram_user_id,
            "instagram_access_token": mask_token(brand.instagram_access_token),
            "instagram_app_id": mask_token(brand.instagram_app_id),
            "instagram_app_secret": mask_token(brand.instagram_app_secret),
            "config_status": {
                "has_access_token": bool(brand.instagram_access_token),
                "has_user_id": bool(brand.instagram_user_id),
                "has_username": bool(brand.instagram_username),
                "has_app_id": bool(brand.instagram_app_id),
                "has_app_secret": bool(brand.instagram_app_secret),
            },
            "missing_fields": [],
        }

        # Check which fields are missing
        if not brand.instagram_access_token:
            debug_info["missing_fields"].append("instagram_access_token")
        if not brand.instagram_user_id:
            debug_info["missing_fields"].append("instagram_user_id")
        if not brand.instagram_app_id:
            debug_info["missing_fields"].append("instagram_app_id")
        if not brand.instagram_app_secret:
            debug_info["missing_fields"].append("instagram_app_secret")

        # Test API connection if credentials are present
        if brand.has_instagram_config:
            try:
                import requests

                # Test with Instagram API
                # Heuristic: IGQV historically indicates Basic Display long-lived token.
                # IGAA can be a valid Graph token; do not auto-classify it as Basic Display.
                is_basic_display_suspect = brand.instagram_access_token.startswith(
                    "IGQV"
                )
                if is_basic_display_suspect:
                    url = "https://graph.facebook.com/v18.0/me"
                    params = {
                        "fields": "id,username,account_type",
                        "access_token": brand.instagram_access_token,
                    }
                    api_type = "Graph API (suspected legacy Basic Display token)"
                else:
                    url = f"https://graph.facebook.com/v18.0/{brand.instagram_user_id}"
                    params = {
                        "fields": "id,username,account_type",
                        "access_token": brand.instagram_access_token,
                    }
                    api_type = "Instagram Graph API"

                response = requests.get(url, params=params, timeout=10)
                debug_info["api_test"] = {
                    "api_type": api_type,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "suspect_basic_display": is_basic_display_suspect,
                    "token_length": len(brand.instagram_access_token or ""),
                    "token_prefix": (brand.instagram_access_token or "")[:6],
                    "response": (
                        response.json() if response.status_code == 200 else None
                    ),
                    "error": response.json() if response.status_code != 200 else None,
                }
            except Exception as e:
                debug_info["api_test"] = {
                    "api_type": "Unknown",
                    "status_code": None,
                    "success": False,
                    "error": str(e),
                }

        return Response(debug_info)

    except Exception as e:
        return Response(
            {"error": f"Failed to debug Instagram config: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def brand_instagram_posts(request):
    """
    List and create brand Instagram posts
    """
    try:
        from .models import BrandInstagramPost
        from .serializers import BrandInstagramPostSerializer

        # Enhanced authentication debugging
        print("DEBUG: Authentication check for brand_instagram_posts")
        print(f"DEBUG: User: {request.user}")
        print(f"DEBUG: User is authenticated: {request.user.is_authenticated}")
        print(f"DEBUG: User ID: {getattr(request.user, 'id', 'N/A')}")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request headers: {dict(request.headers)}")
        print(
            f"DEBUG: Authorization header: {request.headers.get('Authorization', 'Not found')}"
        )

        # Check if user is anonymous
        if request.user.is_anonymous:
            print("DEBUG: User is anonymous - authentication failed")
            return Response(
                {"error": "Authentication required. Please log in again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if request.method == "GET":
            # Get query parameters
            brand_id = request.GET.get("brand_id")
            status_filter = request.GET.get("status")
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 20))

            # Build query
            if brand_id:
                # Filter by specific brand
                posts = BrandInstagramPost.objects.filter(brand_id=brand_id)
            else:
                # Get all posts for user's brands
                from .models import Brand

                user_brands = Brand.objects.filter(owner=request.user)
                posts = BrandInstagramPost.objects.filter(brand__in=user_brands)

            if status_filter:
                posts = posts.filter(status=status_filter)

            posts = posts.order_by("-created_at")

            # Paginate results
            start = (page - 1) * page_size
            end = start + page_size

            serializer = BrandInstagramPostSerializer(
                posts[start:end], many=True, context={"request": request}
            )

            return Response(
                {
                    "posts": serializer.data,
                    "total": posts.count(),
                    "page": page,
                    "page_size": page_size,
                }
            )

        elif request.method == "POST":
            print("DEBUG: Processing POST request")
            print(f"DEBUG: Request data: {request.data}")
            print(f"DEBUG: Request FILES: {request.FILES}")
            print(f"DEBUG: Content type: {request.content_type}")

            # Check if user has brands
            from .models import Brand

            user_brands = Brand.objects.filter(owner=request.user)
            print(f"DEBUG: User brands count: {user_brands.count()}")
            if user_brands.exists():
                print(f"DEBUG: First brand: {user_brands.first()}")

            serializer = BrandInstagramPostSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                post = serializer.save()
                print(f"DEBUG: Created post with ID: {post.id}")
                print(f"DEBUG: Post image: {post.image}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print(f"DEBUG: Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"DEBUG: Exception in brand_instagram_posts: {e}")
        return Response(
            {"error": f"Failed to process brand Instagram posts: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def brand_instagram_post_detail(request, post_id):
    """
    Get, update, or delete a specific brand Instagram post
    """
    try:
        from .models import BrandInstagramPost
        from .serializers import BrandInstagramPostSerializer

        post = BrandInstagramPost.objects.get(id=post_id)

        # Check permissions
        if post.brand and post.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to access this post"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "GET":
            serializer = BrandInstagramPostSerializer(post)
            return Response(serializer.data)

        elif request.method == "PUT":
            serializer = BrandInstagramPostSerializer(
                post, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == "DELETE":
            post.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except BrandInstagramPost.DoesNotExist:
        return Response(
            {"error": "Instagram post not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to process Instagram post: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def post_instagram_now(request, post_id):
    """
    Post a brand Instagram post immediately
    """
    try:
        from .models import BrandInstagramPost
        from .serializers import BrandInstagramPostSerializer

        post = BrandInstagramPost.objects.get(id=post_id)

        # Check permissions
        if post.brand and post.brand.owner != request.user:
            # For organization brands, check if user is admin of the organization
            if hasattr(post.brand, "organization"):
                org_user = post.brand.organization.organization_users.filter(
                    user=request.user
                ).first()
                if not org_user or not org_user.is_admin:
                    return Response(
                        {"success": False, "error": "Not authorized to post this"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                return Response(
                    {"success": False, "error": "Not authorized to post this"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Validate that the post's brand has proper Instagram configuration
        if not post.brand.has_instagram_config:
            return Response(
                {
                    "success": False,
                    "error": "Brand does not have Instagram configuration. Please connect your Instagram account first.",
                    "details": {
                        "brand_name": post.brand.name,
                        "has_access_token": bool(post.brand.instagram_access_token),
                        "has_user_id": bool(post.brand.instagram_user_id),
                        "has_app_id": bool(post.brand.instagram_app_id),
                        "has_app_secret": bool(post.brand.instagram_app_secret),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Additional validation for Instagram user ID specifically
        if (
            not post.brand.instagram_user_id
            or post.brand.instagram_user_id.strip() == ""
        ):
            return Response(
                {
                    "success": False,
                    "error": "Invalid Instagram user ID. Please check your Instagram account configuration. More specifically, the issue is that the user id is not set. Please check your Instagram account configuration.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Auto-approve the post if it's in draft status (like test posts)
        if post.status == "draft":
            post.status = "approved"
            post.save()

        # Check if post can be posted with detailed error info
        if not post.can_be_posted():
            # Provide detailed error information
            reasons = []
            if post.status != "approved":
                reasons.append(f"status is '{post.status}' (needs 'approved')")
            if not post.brand.has_instagram_config:
                reasons.append("brand missing Instagram configuration")
                reasons.append(f"Brand: {post.brand.name} (ID: {post.brand.id})")
                reasons.append(f"Instagram user ID: {post.brand.instagram_user_id}")
                reasons.append(
                    f"Access token exists: {bool(post.brand.instagram_access_token)}"
                )
            if not bool(post.content.strip() or post.has_media()):
                reasons.append("content and media are both empty")

            detailed_error = f"Instagram post cannot be posted: {', '.join(reasons)}"
            return Response(
                {"success": False, "error": detailed_error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Post to Instagram using the post's original brand
        try:
            success, error = post.post_to_instagram()

            if success:
                serializer = BrandInstagramPostSerializer(post)
                return Response(
                    {
                        "success": True,
                        "message": "Instagram post published successfully!",
                        "post": serializer.data,
                    }
                )
            else:
                return Response(
                    {"success": False, "error": error},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            return Response(
                {"success": False, "error": f"Failed to post to Instagram: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except BrandInstagramPost.DoesNotExist:
        return Response(
            {"success": False, "error": "Instagram post not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"success": False, "error": f"Failed to post to Instagram: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_instagram_content(request):
    """
    Generate Instagram post content using AI
    """
    try:
        # Get parameters
        prompt = request.data.get("prompt")
        topics = request.data.get("topics", [])
        tones = request.data.get("tones", [])
        keywords = request.data.get("keywords", [])
        hashtags = request.data.get("hashtags", [])

        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Format prompt with parameters
        formatted_prompt = prompt.format(
            topic=random.choice(topics) if topics else "",
            tone=random.choice(tones) if tones else "",
            keywords=(
                ", ".join(random.sample(keywords, min(3, len(keywords))))
                if keywords
                else ""
            ),
            hashtags=(
                " ".join(random.sample(hashtags, min(5, len(hashtags))))
                if hashtags
                else ""
            ),
        )

        # Call OpenAI API
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional social media manager crafting engaging Instagram posts with captions and hashtags.",
                },
                {"role": "user", "content": formatted_prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )

        generated_content = response.choices[0].message.content.strip()

        return Response({"content": generated_content, "prompt_used": formatted_prompt})

    except Exception as e:
        return Response(
            {"error": f"Failed to generate Instagram content: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Phase 3: Brand Management - Connect Brand Twitter
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def connect_brand_twitter(request, brand_id):
    """
    Connect Twitter account to a brand
    """
    try:
        # Get the brand
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        if brand.owner != request.user:
            return Response(
                {"error": "Not authorized to modify this brand"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get Twitter credentials from request
        api_key = request.data.get("api_key")
        api_secret = request.data.get("api_secret")
        access_token = request.data.get("access_token")
        access_token_secret = request.data.get("access_token_secret")
        bearer_token = request.data.get("bearer_token")

        if not all(
            [api_key, api_secret, access_token, access_token_secret, bearer_token]
        ):
            return Response(
                {"error": "All Twitter API credentials are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Test Twitter credentials
        try:
            import tweepy

            # Create Twitter API client
            client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True,
            )

            # Verify credentials by getting user info
            me = client.get_me()
            if not me.data:
                return Response(
                    {"error": "Unable to verify Twitter credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Save credentials to brand
            brand.twitter_api_key = api_key
            brand.twitter_api_secret = api_secret
            brand.twitter_access_token = access_token
            brand.twitter_access_token_secret = access_token_secret
            brand.twitter_bearer_token = bearer_token
            brand.twitter_username = me.data.username
            brand.save()

            # Send real-time notification using existing TweetQueueConsumer
            channel_layer = get_channel_layer()
            if brand.organization:
                async_to_sync(channel_layer.group_send)(
                    f"tweet_queue_{brand.organization.id}_{brand.id}",
                    {
                        "type": "brand_connected",
                        "brand_id": brand.id,
                        "platform": "twitter",
                        "username": me.data.username,
                        "message": f"Twitter account @{me.data.username} connected successfully",
                    },
                )

            return Response(
                {
                    "success": True,
                    "username": me.data.username,
                    "user_id": me.data.id,
                    "message": f"Twitter account @{me.data.username} connected successfully",
                }
            )

        except tweepy.Unauthorized:
            return Response(
                {
                    "error": "Invalid Twitter credentials. Please check your API keys and tokens."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to connect Twitter: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response(
            {"error": f"Failed to connect brand Twitter: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Brand Assets API Endpoints
@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def brand_assets(request):
    """
    List and upload brand assets
    """
    try:
        if request.method == "GET":
            # Get query parameters
            brand_id = request.GET.get("brand_id")
            asset_type = request.GET.get("asset_type")
            tags = request.GET.get("tags")
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 20))

            if not brand_id:
                return Response(
                    {"error": "brand_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check brand access
            try:
                brand = Brand.objects.get(id=brand_id)
                # Add permission check here based on your brand ownership model
                # For now, assume any authenticated user can access
            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Build query
            assets = BrandAsset.objects.filter(brand_id=brand_id, is_active=True)

            if asset_type:
                assets = assets.filter(asset_type=asset_type)

            if tags:
                tag_list = [tag.strip() for tag in tags.split(",")]
                for tag in tag_list:
                    assets = assets.filter(tags__contains=[tag])

            assets = assets.order_by("-created_at")

            # Paginate results
            start = (page - 1) * page_size
            end = start + page_size

            serializer = BrandAssetSerializer(assets[start:end], many=True)

            return Response(
                {
                    "assets": serializer.data,
                    "total": assets.count(),
                    "page": page,
                    "page_size": page_size,
                }
            )

        elif request.method == "POST":
            # Validate required fields
            brand_id = request.data.get("brand_id")
            if not brand_id:
                return Response(
                    {"error": "brand_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check brand access
            try:
                brand = Brand.objects.get(id=brand_id)
                # Add permission check here
            except Brand.DoesNotExist:
                return Response(
                    {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Create asset
            serializer = BrandAssetSerializer(data=request.data)
            if serializer.is_valid():
                asset = serializer.save(brand=brand)
                return Response(
                    BrandAssetSerializer(asset).data, status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": f"Failed to process brand assets: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Phase 3: Brand Management - Test Brand Twitter
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def test_brand_twitter(request, brand_id):
    """
    Test brand Twitter credentials and send a test tweet
    """
    try:
        # Get the brand
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions
        if brand.owner != request.user:
            return Response(
                {"error": "Not authorized to test this brand"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if brand has Twitter configuration
        if not brand.has_twitter_config:
            return Response(
                {"error": "Brand does not have Twitter API configuration"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get test tweet content
        test_content = request.data.get(
            "content", "This is a test tweet from Gemnar Twitter automation! 🚀"
        )

        # Test Twitter connection and send tweet
        try:
            import tweepy

            # Create Twitter API client
            client = tweepy.Client(
                bearer_token=brand.twitter_bearer_token,
                consumer_key=brand.twitter_api_key,
                consumer_secret=brand.twitter_api_secret,
                access_token=brand.twitter_access_token,
                access_token_secret=brand.twitter_access_token_secret,
                wait_on_rate_limit=True,
            )

            # First verify credentials
            me = client.get_me()
            if not me.data:
                return Response(
                    {"error": "Unable to verify Twitter credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Send test tweet
            response = client.create_tweet(text=test_content)

            if response.data:
                tweet_id = response.data["id"]
                tweet_url = (
                    f"https://twitter.com/{brand.twitter_username}/status/{tweet_id}"
                )

                # Send Slack notification if brand has Slack configured
                if brand.has_slack_config:
                    try:
                        import requests

                        message = (
                            f"🧪 *Test Tweet Posted for {brand.name}*\n"
                            f"Content: {test_content}\n"
                            f"Tweet URL: {tweet_url}\n"
                            f"Posted by: {request.user.username}"
                        )

                        payload = {
                            "text": message,
                            "username": f"Gemnar Bot - {brand.name}",
                            "icon_emoji": ":test_tube:",
                        }

                        if brand.slack_channel:
                            payload["channel"] = brand.slack_channel

                        requests.post(brand.slack_webhook_url, json=payload, timeout=10)
                    except Exception:
                        pass  # Don't fail test tweet if Slack fails

                return Response(
                    {
                        "success": True,
                        "tweet_id": tweet_id,
                        "tweet_url": tweet_url,
                        "username": brand.twitter_username,
                        "message": "Test tweet sent successfully",
                    }
                )
            else:
                return Response(
                    {"error": "Failed to send test tweet - no response data"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except tweepy.Unauthorized:
            return Response(
                {
                    "error": "Invalid Twitter credentials. Please check your API keys and tokens."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except tweepy.Forbidden as e:
            return Response(
                {"error": f"Twitter API access forbidden: {str(e)}"},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to send test tweet: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response(
            {"error": f"Failed to test brand Twitter: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def brand_asset_detail(request, asset_id):
    """
    Get, update, or delete a specific brand asset
    """
    try:
        asset = BrandAsset.objects.get(id=asset_id)

        # Check permissions - add your brand ownership logic here
        # For now, assume any authenticated user can access

        if request.method == "GET":
            serializer = BrandAssetSerializer(asset)
            return Response(serializer.data)

        elif request.method == "PUT":
            serializer = BrandAssetSerializer(asset, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == "DELETE":
            # Soft delete by setting is_active to False
            asset.is_active = False
            asset.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    except BrandAsset.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": f"Failed to process brand asset: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def brand_asset_upload(request):
    """
    Upload a new brand asset file
    """
    try:
        brand_id = request.data.get("brand_id")
        file = request.FILES.get("file")
        name = request.data.get("name")
        asset_type = request.data.get("asset_type", "image")
        description = request.data.get("description", "")
        tags = request.data.get("tags", "")

        if not brand_id:
            return Response(
                {"error": "brand_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not file:
            return Response(
                {"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not name:
            return Response(
                {"error": "name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check brand access
        try:
            brand = Brand.objects.get(id=brand_id)
            # Add permission check here
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Validate file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "File size must be less than 10MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Create the asset
        asset = BrandAsset.objects.create(
            brand=brand,
            name=name,
            asset_type=asset_type,
            file=file,
            description=description,
            tags=tag_list,
        )

        serializer = BrandAssetSerializer(asset)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": f"Failed to upload brand asset: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def brand_asset_usage(request, asset_id):
    """
    Get usage statistics for a brand asset
    """
    try:
        asset = BrandAsset.objects.get(id=asset_id)

        # Get usage in tweets and Instagram posts
        tweet_usage = asset.tweets.all().count()
        instagram_usage = asset.instagram_posts.all().count()

        # Get recent posts using this asset
        recent_tweets = asset.tweets.order_by("-created_at")[:5]
        recent_instagram = asset.instagram_posts.order_by("-created_at")[:5]

        usage_data = {
            "asset_id": asset.id,
            "asset_name": asset.name,
            "total_usage": asset.usage_count,
            "tweet_usage": tweet_usage,
            "instagram_usage": instagram_usage,
            "recent_tweets": [
                {
                    "id": tweet.id,
                    "content": tweet.content[:100],
                    "status": tweet.status,
                    "created_at": tweet.created_at,
                }
                for tweet in recent_tweets
            ],
            "recent_instagram": [
                {
                    "id": post.id,
                    "content": post.content[:100],
                    "status": post.status,
                    "created_at": post.created_at,
                }
                for post in recent_instagram
            ],
        }

        return Response(usage_data)

    except BrandAsset.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": f"Failed to get asset usage: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Phase 4B: Background Task Status - Get Task Status
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_task_status(request, task_id):
    """
    Get the status of a background task (for Instagram reels)
    """
    try:
        # This is for Instagram reel generation tasks, not Celery
        # Check if task_id corresponds to a BrandInstagramPost or similar
        from .models import BrandInstagramPost

        # Try to find an Instagram post with this task ID
        try:
            instagram_post = BrandInstagramPost.objects.get(
                id=task_id, brand__owner=request.user
            )

            response_data = {
                "task_id": task_id,
                "status": instagram_post.status,
                "ready": instagram_post.status in ["posted", "failed"],
                "type": "instagram_post",
            }

            if instagram_post.status == "failed":
                response_data["error"] = instagram_post.error_message
            elif instagram_post.status == "posted":
                response_data["result"] = {
                    "instagram_id": instagram_post.instagram_id,
                    "content": instagram_post.content,
                }

            return Response(response_data)

        except BrandInstagramPost.DoesNotExist:
            # Could be other types of tasks - expand as needed
            return Response(
                {"error": "Task not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

    except Exception as e:
        return Response(
            {"error": f"Failed to get task status: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Phase 4B: Background Task Status - Get User's Active Tasks
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_user_active_tasks(request):
    """
    Get all active background tasks for the current user
    """
    try:
        # Get user's brand tweets that are being processed
        user_brands = Brand.objects.filter(owner=request.user)
        brand_tweets = BrandTweet.objects.filter(
            brand__in=user_brands, status__in=["draft", "approved", "failed"]
        ).order_by("-created_at")

        # Combine and format results
        active_tasks = []

        for tweet in brand_tweets:
            active_tasks.append(
                {
                    "task_type": "brand_tweet_generation",
                    "task_id": f"brand_tweet_{tweet.id}",
                    "brand_name": tweet.brand.name,
                    "status": tweet.status,
                    "content": (
                        tweet.content[:100] + "..."
                        if len(tweet.content) > 100
                        else tweet.content
                    ),
                    "created_at": tweet.created_at.isoformat(),
                    "scheduled_for": (
                        tweet.scheduled_for.isoformat() if tweet.scheduled_for else None
                    ),
                    "error_message": (
                        tweet.error_message if tweet.status == "failed" else None
                    ),
                }
            )

        return Response(
            {
                "active_tasks": active_tasks,
                "total_count": len(active_tasks),
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to get active tasks: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Phase 4C: Background Sync - Force Sync User Data
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def force_sync_user_data(request):
    """
    Force sync user's tweet data and status
    """
    try:
        from .tasks import retry_failed_tweets, post_approved_tweets

        # Trigger background tasks
        retry_task = retry_failed_tweets.delay()
        post_task = post_approved_tweets.delay()

        return Response(
            {
                "success": True,
                "message": "Background sync initiated",
                "tasks": {
                    "retry_failed_tweets": retry_task.id,
                    "post_approved_tweets": post_task.id,
                },
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to initiate background sync: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Phase 4C: Background Sync - Get Sync Status
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_sync_status(request):
    """
    Get the current sync status for user's data
    """
    try:
        # Get user's tweet statistics - get tweets from all user's brands
        user_brands = Brand.objects.filter(owner=request.user)
        brand_tweets = BrandTweet.objects.filter(brand__in=user_brands)

        # Calculate sync status
        total_tweets = brand_tweets.count()
        posted_tweets = brand_tweets.filter(status="posted").count()
        failed_tweets = brand_tweets.filter(status="failed").count()
        pending_tweets = brand_tweets.filter(status__in=["draft", "approved"]).count()

        sync_status = {
            "total_tweets": total_tweets,
            "posted_tweets": posted_tweets,
            "failed_tweets": failed_tweets,
            "pending_tweets": pending_tweets,
            "last_sync": timezone.now().isoformat(),
            "sync_health": "healthy" if failed_tweets == 0 else "needs_attention",
        }

        return Response(sync_status)

    except Exception as e:
        return Response(
            {"error": f"Failed to get sync status: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Account Deletion API Endpoints


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def account_deletion_preview_api(request):
    """
    API endpoint to get preview of what data will be deleted
    """
    try:
        preview = get_account_deletion_preview(request.user)
        return Response({"success": True, "preview": preview})
    except Exception as e:
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def delete_account_api(request):
    """
    API endpoint to delete user account

    Expected payload:
    {
        "password": "user_password",
        "reason": "optional_reason",
        "feedback": "optional_feedback"
    }
    """
    try:
        password = request.data.get("password", "")
        reason = request.data.get("reason", "")
        feedback = request.data.get("feedback", "")

        # Validate required fields
        if not password:
            return Response(
                {"success": False, "error": "Password is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify password
        if not request.user.check_password(password):
            return Response(
                {"success": False, "error": "Incorrect password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Proceed with deletion
        deletion_service = AccountDeletionService(request.user)
        result = deletion_service.delete_account(reason=reason, feedback=feedback)

        if result["success"]:
            return Response(
                {
                    "success": True,
                    "message": "Account deleted successfully",
                    "summary": result["summary"],
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"success": False, "error": result["error"]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Error in delete_account_api: {str(e)}")
        return Response(
            {"success": False, "error": "An unexpected error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Brand Management API endpoints
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def organizations_list(request):
    """
    Get all organizations for the authenticated user
    """
    try:
        from organizations.models import Organization
        
        print(f"DEBUG: Fetching organizations for user: {request.user.username}")
        
        organizations = Organization.objects.filter(users=request.user)
        print(f"DEBUG: Found {organizations.count()} organizations for user")

        organizations_data = []
        for org in organizations:
            # Check if user is admin
            org_user = org.organization_users.filter(user=request.user).first()
            is_admin = org_user.is_admin if org_user else False
            
            organizations_data.append({
                "id": org.id,
                "name": org.name,
                "is_admin": is_admin,
                "created": org.created.isoformat() if hasattr(org, 'created') else None,
            })

        print(f"DEBUG: Returning {len(organizations_data)} organizations")
        return Response(organizations_data)

    except Exception as e:
        print(f"DEBUG: Error in organizations_list: {e}")
        return Response(
            {"error": f"Failed to fetch organizations: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_organization(request):
    """
    Create a new organization for the authenticated user
    """
    try:
        from organizations.models import Organization, OrganizationUser, OrganizationOwner
        
        print(f"DEBUG: Creating organization for user: {request.user.username}")
        print(f"DEBUG: Request data: {request.data}")
        
        name = request.data.get("name")
        if not name:
            return Response(
                {"error": "Organization name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Create organization
        organization = Organization.objects.create(name=name)
        
        # First create OrganizationUser
        org_user = OrganizationUser.objects.create(
            user=request.user,
            organization=organization,
            is_admin=True
        )
        
        # Then create OrganizationOwner with the OrganizationUser instance
        OrganizationOwner.objects.create(
            organization=organization,
            organization_user=org_user
        )
        
        print(f"DEBUG: Created organization: ID={organization.id}, Name={organization.name}")
        
        return Response(
            {
                "id": organization.id,
                "name": organization.name,
                "is_admin": True,
                "created": organization.created.isoformat() if hasattr(organization, 'created') else None,
            },
            status=status.HTTP_201_CREATED,
        )
        
    except Exception as e:
        print(f"DEBUG: Error in create_organization: {e}")
        return Response(
            {"error": f"Failed to create organization: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([permissions.IsAuthenticated])
def update_organization(request, organization_id):
    """
    Update an organization (admin only)
    """
    try:
        from organizations.models import Organization
        
        organization = Organization.objects.get(id=organization_id)
        
        # Check if user is admin
        org_user = organization.organization_users.filter(user=request.user).first()
        if not org_user or not org_user.is_admin:
            return Response(
                {"error": "Only organization admins can update organizations"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        name = request.data.get("name")
        if name:
            organization.name = name
            organization.save()
        
        return Response(
            {
                "id": organization.id,
                "name": organization.name,
                "is_admin": True,
                "created": organization.created.isoformat() if hasattr(organization, 'created') else None,
            }
        )
        
    except Organization.DoesNotExist:
        return Response(
            {"error": "Organization not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to update organization: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def delete_organization(request, organization_id):
    """
    Delete an organization (admin only)
    """
    try:
        from organizations.models import Organization
        
        organization = Organization.objects.get(id=organization_id)
        
        # Check if user is admin
        org_user = organization.organization_users.filter(user=request.user).first()
        if not org_user or not org_user.is_admin:
            return Response(
                {"error": "Only organization admins can delete organizations"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        org_name = organization.name
        organization.delete()
        
        return Response(
            {"message": f"Organization '{org_name}' has been deleted"},
            status=status.HTTP_200_OK,
        )
        
    except Organization.DoesNotExist:
        return Response(
            {"error": "Organization not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to delete organization: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def brands_list(request):
    """
    Get all brands for the authenticated user
    """
    try:
        print(
            f"DEBUG: Fetching brands for user: {request.user.username} (ID: {request.user.id})"
        )
        print(f"DEBUG: User is authenticated: {request.user.is_authenticated}")
        print(f"DEBUG: User email: {request.user.email}")

        # Check all brands in the database
        all_brands = Brand.objects.all()
        print(f"DEBUG: Total brands in database: {all_brands.count()}")
        for brand in all_brands:
            print(
                f"DEBUG: All brands - ID={brand.id}, Name={brand.name}, Owner={brand.owner.username}"
            )

        brands = Brand.objects.filter(owner=request.user)
        print(f"DEBUG: Found {brands.count()} brands for user")

        brands_data = []
        for brand in brands:
            print(
                ("DEBUG: Brand: ID={id}, Name={name}, Owner={owner}").format(
                    id=brand.id,
                    name=brand.name,
                    owner=brand.owner.username,
                )
            )
            # Owner-only full credentials (temp; may mask later)
            # Sensitive fields included so mobile app can prefill edit form.
            base_data = {
                "id": brand.id,
                "name": brand.name,
                "slug": brand.slug,
                "url": brand.url,
                "description": brand.description,
                "is_default": brand.is_default,
                # Organization info
                "organization_id": brand.organization.id if brand.organization else None,
                "organization_name": brand.organization.name if brand.organization else None,
                # Twitter subset
                "has_twitter_config": brand.has_twitter_config,
                "twitter_username": brand.twitter_username,
                "twitter_api_key": brand.twitter_api_key,
                "twitter_api_secret": brand.twitter_api_secret,
                "twitter_access_token": brand.twitter_access_token,
                "twitter_access_token_secret": brand.twitter_access_token_secret,  # noqa: E501
                "twitter_bearer_token": brand.twitter_bearer_token,
                # Instagram subset (full for editing)
                "has_instagram_config": brand.has_instagram_config,
                "instagram_username": brand.instagram_username,
                "instagram_access_token": brand.instagram_access_token,
                "instagram_user_id": brand.instagram_user_id,
                "instagram_app_id": brand.instagram_app_id,
                "instagram_app_secret": brand.instagram_app_secret,
                "instagram_business_id": brand.instagram_business_id,
                # Slack status (non-secret)
                "has_slack_config": brand.has_slack_config,
                "slack_webhook_url": brand.slack_webhook_url,
                "slack_channel": brand.slack_channel,
                "slack_notifications_enabled": brand.slack_notifications_enabled,  # noqa: E501
                # Timestamps
                "created_at": brand.created_at.isoformat(),
                "updated_at": brand.updated_at.isoformat(),
            }

            brands_data.append(base_data)

        print(f"DEBUG: Returning {len(brands_data)} brands")
        return Response(brands_data)

    except Exception as e:
        print(f"DEBUG: Error in brands_list: {e}")
        return Response(
            {"error": f"Failed to fetch brands: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def get_brand_by_slug(request, slug):
    """
    Get a specific brand by slug for the authenticated user
    """
    try:
        print(f"DEBUG: Fetching brand with slug: {slug} for user: {request.user.username}")
        
        # Get brand by slug 
        try:
            brand = Brand.objects.get(slug=slug)
        except Brand.DoesNotExist:
            print(f"DEBUG: Brand with slug '{slug}' not found")
            return Response(
                {"error": "Brand not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return the same data format as brands_list for consistency
        brand_data = {
            "id": brand.id,
            "name": brand.name,
            "slug": brand.slug,
            "url": brand.url,
            "description": brand.description,
            "is_default": brand.is_default,
            # Organization info
            "organization_id": brand.organization.id if brand.organization else None,
            "organization_name": brand.organization.name if brand.organization else None,
            # Twitter subset
            "has_twitter_config": brand.has_twitter_config,
            "twitter_username": brand.twitter_username,
            "twitter_api_key": brand.twitter_api_key,
            "twitter_api_secret": brand.twitter_api_secret,
            "twitter_access_token": brand.twitter_access_token,
            "twitter_access_token_secret": brand.twitter_access_token_secret,
            "twitter_bearer_token": brand.twitter_bearer_token,
            # Instagram subset
            "has_instagram_config": brand.has_instagram_config,
            "instagram_username": brand.instagram_username,
            "instagram_access_token": brand.instagram_access_token,
            "instagram_user_id": brand.instagram_user_id,
            "instagram_app_id": brand.instagram_app_id,
            "instagram_app_secret": brand.instagram_app_secret,
            "instagram_business_id": brand.instagram_business_id,
            # Slack status
            "has_slack_config": brand.has_slack_config,
            "slack_webhook_url": brand.slack_webhook_url,
            "slack_channel": brand.slack_channel,
            "slack_notifications_enabled": brand.slack_notifications_enabled,
            # Timestamps
            "created_at": brand.created_at.isoformat(),
            "updated_at": brand.updated_at.isoformat(),
        }

        print(f"DEBUG: Returning brand data for slug '{slug}': {brand.name}")
        return Response(brand_data)

    except Exception as e:
        print(f"DEBUG: Error in get_brand_by_slug: {e}")
        return Response(
            {"error": f"Failed to fetch brand: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Slack Integration API Endpoints
@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def brand_slack_config(request, brand_id):
    """Get or update Slack configuration for a brand"""
    try:
        brand = Brand.objects.get(id=brand_id)

        # Check permissions
        if brand.owner != request.user:
            return Response(
                {"error": "Not authorized to configure this brand"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "GET":
            # Return current Slack configuration (masked webhook URL)
            config = {
                "slack_webhook_url": (
                    brand.slack_webhook_url[:50] + "..."
                    if brand.slack_webhook_url
                    else None
                ),
                "slack_channel": brand.slack_channel,
                "slack_notifications_enabled": brand.slack_notifications_enabled,
                "has_slack_config": brand.has_slack_config,
            }
            return Response(config)

        elif request.method == "POST":
            # Update Slack configuration
            webhook_url = request.data.get("slack_webhook_url")
            channel = request.data.get("slack_channel", "")
            enabled = request.data.get("slack_notifications_enabled", False)

            # Validate webhook URL
            if webhook_url and not webhook_url.startswith("https://hooks.slack.com/"):
                return Response(
                    {"error": "Invalid Slack webhook URL"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update brand
            brand.slack_webhook_url = webhook_url
            brand.slack_channel = channel
            brand.slack_notifications_enabled = bool(enabled)
            brand.save()

            return Response(
                {
                    "success": True,
                    "message": "Slack configuration updated successfully",
                    "has_slack_config": brand.has_slack_config,
                }
            )

    except Brand.DoesNotExist:
        return Response({"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": f"Failed to configure Slack: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_brand(request):
    """
    Create a new brand for the authenticated user
    """
    try:
        from organizations.models import Organization
        
        print(
            f"DEBUG: Creating brand for user: {request.user.username} (ID: {request.user.id})"
        )
        print(f"DEBUG: Request data: {request.data}")

        name = request.data.get("name")
        url = request.data.get("url")
        description = request.data.get("description", "")
        organization_id = request.data.get("organization_id")

        if not name or not url:
            return Response(
                {"error": "Name and URL are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        organization = None
        if organization_id:
            try:
                organization = Organization.objects.get(
                    id=organization_id, 
                    users=request.user
                )
            except Organization.DoesNotExist:
                return Response(
                    {"error": "Organization not found or you don't have access"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create brand
        brand = Brand.objects.create(
            name=name,
            url=url,
            description=description,
            owner=request.user,
            organization=organization,
        )

        print(
            f"DEBUG: Created brand: ID={brand.id}, Name={brand.name}, Owner={brand.owner.username}, Organization={organization.name if organization else 'None'}"
        )

        return Response(
            {
                "id": brand.id,
                "name": brand.name,
                "slug": brand.slug,
                "url": brand.url,
                "description": brand.description,
                "has_twitter_config": brand.has_twitter_config,
                "has_instagram_config": brand.has_instagram_config,
                "organization_id": organization.id if organization else None,
                "organization_name": organization.name if organization else None,
                "is_default": brand.is_default,
                "created_at": brand.created_at.isoformat(),
                "updated_at": brand.updated_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        print(f"DEBUG: Error in create_brand: {e}")
        return Response(
            {"error": f"Failed to create brand: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def test_slack_webhook(request, brand_id):
    """Test Slack webhook for a brand"""
    try:
        brand = Brand.objects.get(id=brand_id)

        # Check permissions
        if brand.owner != request.user:
            return Response(
                {"error": "Not authorized to test this brand's Slack"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not brand.has_slack_config:
            return Response(
                {"error": "Slack is not configured for this brand"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send test message
        test_message = (
            f"🧪 *Test notification* from Gemnar\n\n"
            f"This is a test message for {brand.name}. "
            f"If you see this, your Slack integration is working correctly!\n\n"
            f"✅ Slack notifications are now enabled for tweet queue alerts."
        )

        success = brand.send_slack_notification(test_message)

        if success:
            return Response(
                {
                    "success": True,
                    "message": "Test notification sent successfully",
                }
            )
        else:
            return Response(
                {"error": "Failed to send test notification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Brand.DoesNotExist:
        return Response({"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": f"Failed to test Slack webhook: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT", "PATCH", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def update_brand(request, brand_id):
    """
    Update a brand's information including Instagram credentials, or delete the brand
    """
    try:
        brand = Brand.objects.get(id=brand_id)

        # Check permissions
        if brand.owner != request.user:
            return Response(
                {"error": "Not authorized to access this brand"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Handle DELETE request
        if request.method == "DELETE":
            brand.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        print(f"DEBUG: Updating brand {brand_id} for user: {request.user.username}")
        print(f"DEBUG: Request data: {request.data}")

        # Update basic brand information
        if "name" in request.data:
            brand.name = request.data["name"]
        if "url" in request.data:
            brand.url = request.data["url"]
        if "description" in request.data:
            brand.description = request.data["description"]

        # Update Instagram credentials
        instagram_credentials_updated = False
        if any(
            key in request.data
            for key in [
                "instagram_access_token",
                "instagram_user_id",
                "instagram_username",
                "instagram_app_id",
                "instagram_app_secret",
                "instagram_business_id",
            ]
        ):
            instagram_credentials_updated = True

            # Validate Instagram credentials before saving
            if (
                "instagram_access_token" in request.data
                and "instagram_user_id" in request.data
            ):
                # Validate that the fields are not empty
                access_token = request.data["instagram_access_token"].strip()
                user_id = request.data["instagram_user_id"].strip()
                app_id = request.data.get("instagram_app_id", "").strip()
                app_secret = request.data.get("instagram_app_secret", "").strip()

                if not access_token:
                    return Response(
                        {"error": "Instagram access token cannot be empty"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not user_id:
                    return Response(
                        {"error": "Instagram user ID cannot be empty"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not app_id:
                    return Response(
                        {"error": "Instagram app ID cannot be empty"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not app_secret:
                    return Response(
                        {"error": "Instagram app secret cannot be empty"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Validate user_id is numeric
                if not user_id.isdigit():
                    return Response(
                        {"error": "Instagram user ID must be numeric"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Validate app_id is numeric
                if not app_id.isdigit():
                    return Response(
                        {"error": "Instagram app ID must be numeric"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                import requests

                # Use the validated and stripped values

                # Test the credentials with Instagram Graph API.
                # Previous implementation rejected tokens starting with 'IGAA' assuming Basic Display API.
                # That heuristic caused valid tokens to be rejected, so we now attempt validation for all tokens.
                url = f"https://graph.facebook.com/v18.0/{user_id}"
                params = {
                    "fields": "id,username,account_type",
                    "access_token": access_token,
                }
                api_type = "Instagram Graph API"

                try:
                    print(
                        f"DEBUG: Validating {api_type} credentials for user_id: {user_id}"
                    )
                    print(f"DEBUG: Instagram API URL: {url}")
                    print(f"DEBUG: Instagram API params: {params}")

                    response = requests.get(url, params=params, timeout=10)
                    print(
                        f"DEBUG: Instagram API response status: {response.status_code}"
                    )
                    print(f"DEBUG: Instagram API response body: {response.text}")

                    if response.status_code != 200:
                        error_message = f"Invalid Instagram credentials. API returned status {response.status_code}"
                        try:
                            error_data = response.json()
                            if "error" in error_data:
                                error_detail = error_data["error"]
                                error_code = error_detail.get("code")
                                error_message = f"Instagram API error: {error_detail.get('message', 'Unknown error')}"

                                # Provide specific guidance for common errors
                                if error_code == 190:
                                    if "Cannot parse access token" in error_detail.get(
                                        "message", ""
                                    ):
                                        error_message = "Invalid access token format. Please ensure you're using a valid Instagram access token."
                                    else:
                                        error_message = "Invalid or expired access token. Please generate a new Instagram access token from your Facebook app."
                                elif error_code == 100:
                                    error_message = "Invalid user ID. Please check your Instagram Business Account ID."
                                elif error_code == 104:
                                    error_message = "Instagram API rate limit exceeded. Please try again later."
                                elif error_code == 10:
                                    error_message = "Instagram API permissions error. Your app may not have the required permissions."
                                elif error_code == 1:
                                    error_message = "Instagram API error. Please check your app permissions and configuration."
                        except (ValueError, KeyError, TypeError):
                            pass
                        return Response(
                            {"error": error_message},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    user_data = response.json()
                    if "error" in user_data:
                        return Response(
                            {
                                "error": f"Instagram API error: {user_data['error'].get('message', 'Unknown error')}"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Update the username from the API response if not provided
                    if "instagram_username" not in request.data and user_data.get(
                        "username"
                    ):
                        brand.instagram_username = user_data["username"]

                    print(
                        f"DEBUG: Instagram credentials validated successfully for user: {user_data.get('username')} using {api_type}"
                    )

                except requests.exceptions.RequestException as e:
                    print(f"DEBUG: Request exception during Instagram validation: {e}")
                    return Response(
                        {
                            "error": f"Failed to validate Instagram credentials: {str(e)}"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Save the credentials
            if "instagram_access_token" in request.data:
                brand.instagram_access_token = request.data["instagram_access_token"]
            if "instagram_user_id" in request.data:
                brand.instagram_user_id = request.data["instagram_user_id"]
            if "instagram_username" in request.data:
                brand.instagram_username = request.data["instagram_username"]
            if "instagram_app_id" in request.data:
                brand.instagram_app_id = request.data["instagram_app_id"]
            if "instagram_app_secret" in request.data:
                brand.instagram_app_secret = request.data["instagram_app_secret"]
            if "instagram_business_id" in request.data:
                brand.instagram_business_id = request.data["instagram_business_id"]

        # Update Twitter credentials
        if "twitter_api_key" in request.data:
            brand.twitter_api_key = request.data["twitter_api_key"]
        if "twitter_api_secret" in request.data:
            brand.twitter_api_secret = request.data["twitter_api_secret"]
        if "twitter_access_token" in request.data:
            brand.twitter_access_token = request.data["twitter_access_token"]
        if "twitter_access_token_secret" in request.data:
            brand.twitter_access_token_secret = request.data[
                "twitter_access_token_secret"
            ]
        if "twitter_bearer_token" in request.data:
            brand.twitter_bearer_token = request.data["twitter_bearer_token"]
        if "twitter_username" in request.data:
            brand.twitter_username = request.data["twitter_username"]

        # Update Slack configuration
        if "slack_webhook_url" in request.data:
            brand.slack_webhook_url = request.data["slack_webhook_url"]
        if "slack_channel" in request.data:
            brand.slack_channel = request.data["slack_channel"]
        if "slack_notifications_enabled" in request.data:
            brand.slack_notifications_enabled = request.data[
                "slack_notifications_enabled"
            ]

        brand.save()

        print(f"DEBUG: Updated brand: ID={brand.id}, Name={brand.name}")

        response_data = {
            "id": brand.id,
            "name": brand.name,
            "slug": brand.slug,
            "url": brand.url,
            "description": brand.description,
            # Twitter
            "has_twitter_config": brand.has_twitter_config,
            "twitter_username": brand.twitter_username,
            "twitter_api_key": brand.twitter_api_key,
            "twitter_api_secret": brand.twitter_api_secret,
            "twitter_access_token": brand.twitter_access_token,
            "twitter_access_token_secret": brand.twitter_access_token_secret,
            "twitter_bearer_token": brand.twitter_bearer_token,
            # Instagram
            "has_instagram_config": brand.has_instagram_config,
            "instagram_username": brand.instagram_username,
            "instagram_access_token": brand.instagram_access_token,
            "instagram_user_id": brand.instagram_user_id,
            "instagram_app_id": brand.instagram_app_id,
            "instagram_app_secret": brand.instagram_app_secret,
            "instagram_business_id": brand.instagram_business_id,
            # Slack
            "has_slack_config": brand.has_slack_config,
            "slack_webhook_url": brand.slack_webhook_url,
            "slack_channel": brand.slack_channel,
            "slack_notifications_enabled": brand.slack_notifications_enabled,  # noqa: E501
            # Meta
            "created_at": brand.created_at.isoformat(),
            "updated_at": brand.updated_at.isoformat(),
        }

        if instagram_credentials_updated:
            response_data["instagram_credentials_validated"] = True
            response_data[
                "message"
            ] = "Instagram credentials saved and validated successfully!"

        return Response(response_data, status=status.HTTP_200_OK)

    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        print(f"DEBUG: Error in update_brand: {e}")
        return Response(
            {"error": f"Failed to update brand: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def delete_brand(request, brand_id):
    """
    Delete a brand
    """
    try:
        brand = Brand.objects.get(id=brand_id)

        # Check permissions
        if brand.owner != request.user:
            return Response(
                {"error": "Not authorized to delete this brand"},
                status=status.HTTP_403_FORBIDDEN,
            )

        brand_name = brand.name
        brand.delete()
        
        return Response(
            {"message": f"Brand '{brand_name}' has been deleted"},
            status=status.HTTP_200_OK,
        )

    except Brand.DoesNotExist:
        return Response(
            {"error": "Brand not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to delete brand: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def set_brand_default(request, brand_id):
    """
    Set a brand as the default for its organization
    """
    try:
        brand = Brand.objects.get(id=brand_id)

        # Check permissions - user must be admin of the organization
        if not brand.organization:
            return Response(
                {"error": "Brand must belong to an organization"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        org_user = brand.organization.organization_users.filter(
            user=request.user
        ).first()
        if not org_user or not org_user.is_admin:
            return Response(
                {"error": "Only organization admins can set default brands"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Set this brand as default (model logic handles unsetting others)
        brand.is_default = True
        brand.save()

        return Response(
            {
                "success": True,
                "message": f"{brand.name} has been set as the default brand for {brand.organization.name}",
                "brand_id": brand.id,
                "is_default": True,
            }
        )

    except Brand.DoesNotExist:
        return Response({"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": f"Failed to set brand as default: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def tweet_strategies(request):
    """Get all active tweet strategies"""
    try:
        strategies = TweetStrategy.objects.filter(is_active=True).order_by(
            "category", "name"
        )
        serializer = TweetStrategySerializer(strategies, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {"error": f"Failed to fetch tweet strategies: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def tweet_strategies_by_category(request):
    """Get tweet strategies grouped by category"""
    try:
        strategies = TweetStrategy.objects.filter(is_active=True).order_by(
            "category", "name"
        )

        # Group strategies by category
        categorized = {}
        for strategy in strategies:
            category = strategy.get_category_display()
            if category not in categorized:
                categorized[category] = []

            strategy_data = TweetStrategySerializer(strategy).data
            categorized[category].append(strategy_data)

        return Response(categorized)
    except Exception as e:
        return Response(
            {"error": f"Failed to fetch categorized tweet strategies: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_tweet_with_strategy(request):
    """Generate a tweet using a specific strategy for a brand"""
    try:
        strategy_id = request.data.get("strategy_id")
        brand_id = request.data.get("brand_id")
        context = request.data.get("context", {})
        additional_prompt = request.data.get("additional_prompt", "")
        website_url = request.data.get("website_url", "")

        if not strategy_id or not brand_id:
            return Response(
                {"error": "strategy_id and brand_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the strategy
        try:
            strategy = TweetStrategy.objects.get(id=strategy_id, is_active=True)
        except TweetStrategy.DoesNotExist:
            return Response(
                {"error": "Tweet strategy not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get the brand and verify user has access
        try:
            brand = Brand.objects.get(id=brand_id, owner=request.user)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Add additional prompt and website URL to context
        if additional_prompt:
            context["additional_prompt"] = additional_prompt
        if website_url:
            context["website_url"] = website_url

        # Generate tweet using the strategy
        result = strategy.generate_tweet_for_brand(brand, **context)

        if result["success"]:
            # Create a draft BrandTweet with the generated content
            brand_tweet = BrandTweet.objects.create(
                brand=brand,
                content=result["content"],
                ai_prompt=result["prompt_used"],
                status="draft",
                strategy=strategy,
            )

            # Process Twitter mentions in the tweet content
            from .utils import process_tweet_mentions

            process_tweet_mentions(
                tweet=brand_tweet,
                organization=brand.organization,
                user=request.user if hasattr(request, "user") else None,
            )

            # Generate tracking link
            tracking_url = brand_tweet.get_tracking_url()

            # Add tracking link to tweet content if it doesn't already have one
            if tracking_url and not brand_tweet.content.endswith(tracking_url):
                brand_tweet.content = f"{brand_tweet.content}\n\n{tracking_url}"
                brand_tweet.tracking_link = tracking_url
                brand_tweet.save()

            # Return the generated tweet data
            return Response(
                {
                    "success": True,
                    "tweet": BrandTweetSerializer(brand_tweet).data,
                    "strategy_used": result["strategy_used"],
                    "prompt_used": result["prompt_used"],
                }
            )
        else:
            from .utils.slack_notifications import SlackNotifier

            error_detail = result.get("error", "Unknown error")
            SlackNotifier.send_error_notification(
                error_type="TweetGenerationFailure",
                error_message=f"Strategy {strategy.id} brand {brand.id}: {error_detail}",
                request_info={
                    "path": request.path,
                    "method": request.method,
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                    "ip": request.META.get("REMOTE_ADDR"),
                },
                user_info={
                    "username": getattr(request.user, "username", "anon"),
                    "id": getattr(request.user, "id", None),
                },
            )
            return Response(
                {"error": f"Failed to generate tweet: {error_detail}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        try:
            from .utils.slack_notifications import SlackNotifier

            SlackNotifier.send_error_notification(
                error_type="TweetGenerationException",
                error_message=str(e),
                request_info={
                    "path": request.path,
                    "method": request.method,
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                    "ip": request.META.get("REMOTE_ADDR"),
                },
                user_info={
                    "username": getattr(request.user, "username", "anon"),
                    "id": getattr(request.user, "id", None),
                },
            )
        except Exception:
            pass
        return Response(
            {"error": f"Failed to generate tweet with strategy: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def tweet_strategy_detail(request, strategy_id):
    """Get details for a specific tweet strategy"""
    try:
        strategy = TweetStrategy.objects.get(id=strategy_id, is_active=True)
        serializer = TweetStrategySerializer(strategy)
        return Response(serializer.data)
    except TweetStrategy.DoesNotExist:
        return Response(
            {"error": "Tweet strategy not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to fetch tweet strategy: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def test_website_content(request):
    """Test website content extraction for preview"""
    try:
        url = request.data.get("url")

        if not url:
            return Response(
                {"error": "URL is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Import here to avoid circular imports
        from bs4 import BeautifulSoup
        import requests

        # Fetch website content
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract title
            title = soup.find("title")
            title_text = title.get_text().strip() if title else "No title found"

            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            description = (
                meta_desc.get("content", "").strip()
                if meta_desc
                else "No description found"
            )

            # Extract headings
            headings = []
            for tag in ["h1", "h2", "h3"]:
                elements = soup.find_all(tag)
                for elem in elements[:3]:  # Limit to first 3 of each type
                    text = elem.get_text().strip()
                    if text:
                        headings.append(f"{tag.upper()}: {text}")

            # Extract some paragraph content
            paragraphs = []
            for p in soup.find_all("p")[:5]:  # First 5 paragraphs
                text = p.get_text().strip()
                if text and len(text) > 20:  # Only meaningful paragraphs
                    paragraphs.append(text[:200] + "..." if len(text) > 200 else text)

            return Response(
                {
                    "success": True,
                    "content": {
                        "title": title_text,
                        "description": description,
                        "headings": headings,
                        "paragraphs": paragraphs,
                        "url": url,
                    },
                }
            )

        except requests.RequestException as e:
            return Response(
                {"error": f"Failed to fetch website: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        return Response(
            {"error": f"Failed to test website content: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_from_prompt(request):
    """Generate a tweet from a custom prompt"""
    try:
        prompt = request.data.get("prompt")
        brand_id = request.data.get("brand_id")
        website_url = request.data.get("website_url")

        if not prompt or not brand_id:
            return Response(
                {"error": "prompt and brand_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the brand and verify user has access
        try:
            brand = Brand.objects.get(id=brand_id, owner=request.user)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Build the AI prompt
        ai_prompt = f"""Create a tweet for the brand "{brand.name}".
        
Brand description: {brand.description or "No description provided"}

Custom request: {prompt}"""

        # Add website content if provided
        if website_url:
            try:
                from bs4 import BeautifulSoup
                import requests

                response = requests.get(website_url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "html.parser")

                # Extract key content
                title = soup.find("title")
                title_text = title.get_text().strip() if title else ""

                meta_desc = soup.find("meta", attrs={"name": "description"})
                description = meta_desc.get("content", "").strip() if meta_desc else ""

                # Add to prompt
                ai_prompt += f"""

Website content to reference:
- URL: {website_url}
- Title: {title_text}
- Description: {description}"""

            except Exception:
                # If website fails, continue without it
                ai_prompt += (
                    f"\n\nNote: Could not fetch website content from {website_url}"
                )

        ai_prompt += """

Requirements:
- Maximum 280 characters
- Engaging and relevant to the brand
- Include relevant hashtags if appropriate
- Natural, conversational tone

Please provide only the tweet text, no additional commentary."""

        # Generate content using OpenAI
        try:
            client = get_openai_client()

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a social media expert who creates engaging tweets for brands.",
                    },
                    {"role": "user", "content": ai_prompt},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()

            # Remove quotes if the AI wrapped the content in quotes
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            # Also remove single quotes
            if content.startswith("'") and content.endswith("'"):
                content = content[1:-1]

            # Clean up common formatting issues
            if content.startswith("Tweet: "):
                content = content[7:]

            return Response(
                {"success": True, "content": content, "prompt_used": ai_prompt}
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to generate content: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response(
            {"error": f"Failed to generate from prompt: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Enhanced Asset Management APIs
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def brand_asset_analytics(request, brand_id):
    """
    Get comprehensive analytics for brand assets
    """
    try:
        from .models import BrandAsset
        from django.db.models import Count, Avg, Sum
        from django.utils import timezone
        from datetime import timedelta

        # Check brand access
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get date range (last 30 days by default)
        days = int(request.GET.get("days", 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Asset analytics
        assets = BrandAsset.objects.filter(brand=brand, created_at__gte=start_date)

        analytics = {
            "total_assets": BrandAsset.objects.filter(brand=brand).count(),
            "active_assets": BrandAsset.objects.filter(
                brand=brand, is_active=True
            ).count(),
            "assets_by_type": list(
                assets.values("asset_type").annotate(count=Count("id"))
            ),
            "total_file_size": assets.aggregate(total_size=Sum("file_size"))[
                "total_size"
            ]
            or 0,
            "avg_file_size": assets.aggregate(avg_size=Avg("file_size"))["avg_size"]
            or 0,
            "most_used_assets": list(
                BrandAsset.objects.filter(brand=brand)
                .order_by("-usage_count")[:10]
                .values("id", "name", "usage_count", "asset_type")
            ),
            "recent_uploads": list(
                assets.order_by("-created_at")[:10].values(
                    "id", "name", "asset_type", "created_at"
                )
            ),
            "usage_trends": {
                "total_usage": assets.aggregate(total_usage=Sum("usage_count"))[
                    "total_usage"
                ]
                or 0,
                "avg_usage_per_asset": assets.aggregate(avg_usage=Avg("usage_count"))[
                    "avg_usage"
                ]
                or 0,
            },
        }

        return Response(analytics)

    except Exception as e:
        return Response(
            {"error": f"Failed to get asset analytics: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def brand_asset_search(request, brand_id):
    """
    Advanced search for brand assets with filtering and sorting
    """
    try:
        from .models import BrandAsset
        from django.db.models import Q

        # Check brand access
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get query parameters
        query = request.GET.get("q", "")
        asset_type = request.GET.get("asset_type")
        tags = request.GET.get("tags")
        sort_by = request.GET.get("sort_by", "-created_at")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))

        # Build query
        assets = BrandAsset.objects.filter(brand=brand, is_active=True)

        # Text search
        if query:
            assets = assets.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(tags__contains=[query])
            )

        # Filter by asset type
        if asset_type:
            assets = assets.filter(asset_type=asset_type)

        # Filter by tags
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            for tag in tag_list:
                assets = assets.filter(tags__contains=[tag])

        # Sort
        if sort_by not in [
            "name",
            "-name",
            "created_at",
            "-created_at",
            "usage_count",
            "-usage_count",
        ]:
            sort_by = "-created_at"
        assets = assets.order_by(sort_by)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size

        serializer = BrandAssetSerializer(assets[start:end], many=True)

        return Response(
            {
                "assets": serializer.data,
                "total": assets.count(),
                "page": page,
                "page_size": page_size,
                "search_params": {
                    "query": query,
                    "asset_type": asset_type,
                    "tags": tags,
                    "sort_by": sort_by,
                },
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to search assets: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def brand_asset_bulk_operations(request, brand_id):
    """
    Perform bulk operations on brand assets (delete, activate, deactivate)
    """
    try:
        from .models import BrandAsset

        # Check brand access
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        operation = request.data.get("operation")
        asset_ids = request.data.get("asset_ids", [])

        if not operation or not asset_ids:
            return Response(
                {"error": "operation and asset_ids are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if operation not in ["delete", "activate", "deactivate"]:
            return Response(
                {"error": "Invalid operation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assets = BrandAsset.objects.filter(brand=brand, id__in=asset_ids)
        affected_count = 0

        if operation == "delete":
            affected_count = assets.count()
            assets.delete()
        elif operation == "activate":
            affected_count = assets.update(is_active=True)
        elif operation == "deactivate":
            affected_count = assets.update(is_active=False)

        return Response(
            {
                "success": True,
                "operation": operation,
                "affected_count": affected_count,
                "message": f"Successfully {operation}d {affected_count} assets",
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to perform bulk operation: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Instagram Analytics APIs
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def instagram_analytics(request, brand_id):
    """
    Get comprehensive analytics for Instagram posts
    """
    try:
        from .models import BrandInstagramPost
        from django.db.models import Count, Avg
        from django.utils import timezone
        from datetime import timedelta

        # Check brand access
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get date range (last 30 days by default)
        days = int(request.GET.get("days", 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get posts in date range
        posts = BrandInstagramPost.objects.filter(
            brand=brand, created_at__gte=start_date
        )

        analytics = {
            "overview": {
                "total_posts": BrandInstagramPost.objects.filter(brand=brand).count(),
                "posts_this_period": posts.count(),
                "posted_posts": posts.filter(status="posted").count(),
                "failed_posts": posts.filter(status="failed").count(),
                "draft_posts": posts.filter(status="draft").count(),
                "approved_posts": posts.filter(status="approved").count(),
            },
            "performance": {
                "success_rate": (
                    posts.filter(status="posted").count() / posts.count() * 100
                    if posts.count() > 0
                    else 0
                ),
                "avg_posts_per_day": posts.count() / days if days > 0 else 0,
                "posts_with_images": posts.filter(image__isnull=False).count(),
                "posts_with_content": posts.filter(content__isnull=False)
                .exclude(content="")
                .count(),
            },
            "trends": {
                "posts_by_day": list(
                    posts.extra(select={"day": "date(created_at)"})
                    .values("day")
                    .annotate(count=Count("id"))
                    .order_by("day")
                ),
                "posts_by_status": list(
                    posts.values("status").annotate(count=Count("id"))
                ),
            },
            "recent_activity": {
                "recent_posts": list(
                    posts.order_by("-created_at")[:10].values(
                        "id", "content", "status", "created_at", "posted_at"
                    )
                ),
                "recent_failures": list(
                    posts.filter(status="failed")
                    .order_by("-created_at")[:5]
                    .values("id", "content", "error_message", "created_at")
                ),
            },
            "content_analysis": {
                "avg_content_length": posts.aggregate(
                    avg_length=Avg("content__length")
                )["avg_length"]
                or 0,
                "posts_with_hashtags": posts.filter(content__icontains="#").count(),
                "posts_with_mentions": posts.filter(content__icontains="@").count(),
            },
        }

        return Response(analytics)

    except Exception as e:
        return Response(
            {"error": f"Failed to get Instagram analytics: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def instagram_performance_metrics(request, brand_id):
    """
    Get detailed performance metrics for Instagram posts
    """
    try:
        from .models import BrandInstagramPost
        from django.db.models import Count, Avg, Max, Min
        from django.utils import timezone
        from datetime import timedelta

        # Check brand access
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get date range
        days = int(request.GET.get("days", 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get posted posts in date range
        posted_posts = BrandInstagramPost.objects.filter(
            brand=brand, status="posted", posted_at__gte=start_date
        )

        metrics = {
            "posting_frequency": {
                "total_posts": posted_posts.count(),
                "posts_per_day": posted_posts.count() / days if days > 0 else 0,
                "best_posting_days": list(
                    posted_posts.extra(
                        select={"day_of_week": "strftime('%w', posted_at)"}
                    )
                    .values("day_of_week")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:3]
                ),
                "best_posting_hours": list(
                    posted_posts.extra(select={"hour": "strftime('%H', posted_at)"})
                    .values("hour")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:5]
                ),
            },
            "content_performance": {
                "posts_with_images": posted_posts.filter(image__isnull=False).count(),
                "posts_without_images": posted_posts.filter(image__isnull=True).count(),
                "avg_content_length": posted_posts.aggregate(
                    avg_length=Avg("content__length")
                )["avg_length"]
                or 0,
                "longest_content": posted_posts.aggregate(
                    max_length=Max("content__length")
                )["max_length"]
                or 0,
                "shortest_content": posted_posts.aggregate(
                    min_length=Min("content__length")
                )["min_length"]
                or 0,
            },
            "error_analysis": {
                "total_failures": BrandInstagramPost.objects.filter(
                    brand=brand, status="failed", created_at__gte=start_date
                ).count(),
                "common_errors": list(
                    BrandInstagramPost.objects.filter(
                        brand=brand, status="failed", created_at__gte=start_date
                    )
                    .values("error_message")
                    .annotate(count=Count("id"))
                    .order_by("-count")[:5]
                ),
            },
            "scheduling_insights": {
                "scheduled_posts": BrandInstagramPost.objects.filter(
                    brand=brand, scheduled_for__isnull=False, created_at__gte=start_date
                ).count(),
                "immediate_posts": posted_posts.filter(
                    scheduled_for__isnull=True
                ).count(),
                "avg_scheduling_lead_time": posted_posts.filter(
                    scheduled_for__isnull=False
                ).aggregate(avg_lead_time=Avg("scheduled_for__hour"))["avg_lead_time"]
                or 0,
            },
        }

        return Response(metrics)

    except Exception as e:
        return Response(
            {"error": f"Failed to get performance metrics: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Real-time Notifications APIs
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def instagram_notifications(request, brand_id):
    """
    Get real-time notifications for Instagram posts
    """
    try:
        from .models import BrandInstagramPost
        from django.utils import timezone
        from datetime import timedelta

        # Check brand access
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return Response(
                {"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get recent notifications (last 24 hours)
        hours = int(request.GET.get("hours", 24))
        end_date = timezone.now()
        start_date = end_date - timedelta(hours=hours)

        # Get recent posts
        recent_posts = BrandInstagramPost.objects.filter(
            brand=brand, created_at__gte=start_date
        ).order_by("-created_at")

        notifications = []

        for post in recent_posts:
            notification = {
                "id": post.id,
                "type": "instagram_post",
                "title": f"Instagram Post #{post.id}",
                "message": f"Post status changed to {post.status}",
                "status": post.status,
                "created_at": post.created_at.isoformat(),
                "updated_at": post.updated_at.isoformat(),
                "priority": "high" if post.status == "failed" else "normal",
            }

            if post.status == "posted":
                notification["message"] = "Post successfully published to Instagram"
                notification["data"] = {
                    "instagram_id": post.instagram_id,
                    "instagram_url": post.instagram_url,
                    "posted_at": post.posted_at.isoformat() if post.posted_at else None,
                }
            elif post.status == "failed":
                notification["message"] = f"Post failed: {post.error_message}"
                notification["data"] = {
                    "error_message": post.error_message,
                }
            elif post.status == "approved":
                notification["message"] = "Post approved and ready for publishing"
            elif post.status == "draft":
                notification["message"] = "New draft post created"

            notifications.append(notification)

        return Response(
            {
                "notifications": notifications,
                "total": len(notifications),
                "unread_count": len(
                    [n for n in notifications if n["status"] in ["failed", "posted"]]
                ),
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to get notifications: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read
    """
    try:
        # For now, we'll just return success
        # In a full implementation, you'd have a Notification model
        return Response(
            {
                "success": True,
                "message": "Notification marked as read",
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to mark notification as read: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def instagram_webhook_status(request, brand_id):
    """
    Get WebSocket connection status and recent events
    """
    try:
        # Check brand access
        try:
            brand = Brand.objects.get(id=brand_id)
        except Brand.DoesNotExist:
            return Response({"error": "Brand not found"})
        # This would typically check WebSocket connection status
        # For now, return a mock status
        status = {
            "connected": True,
            "last_heartbeat": timezone.now().isoformat(),
            "room_name": f"instagram_queue_{brand.organization.pk}_{brand.pk}",
            "recent_events": [
                {
                    "type": "instagram_post_posted",
                    "timestamp": timezone.now().isoformat(),
                    "data": {"message": "Post published successfully"},
                }
            ],
        }

        return Response(status)

    except Exception as e:
        return Response(
            {"error": f"Failed to get WebSocket status: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_instagram_image_to_production(request):
    """
    Upload an image for Instagram posting directly to production server
    Returns the full production URL
    """
    try:
        if "image" not in request.FILES:
            return Response(
                {"error": "No image file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["image"]

        # Validate file type
        allowed_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
        ]

        if image_file.content_type not in allowed_types:
            return Response(
                {
                    "error": "Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check file size (limit to 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "File too large. Maximum size is 10MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate unique filename for Instagram
        ext = os.path.splitext(image_file.name)[1]
        if not ext:
            if image_file.content_type == "image/jpeg":
                ext = ".jpg"
            elif image_file.content_type == "image/png":
                ext = ".png"
            elif image_file.content_type == "image/gif":
                ext = ".gif"
            elif image_file.content_type == "image/webp":
                ext = ".webp"
            else:
                ext = ".jpg"

        filename = f"instagram_{request.user.id}_{uuid.uuid4().hex}{ext}"

        # Save the file to instagram_uploads directory
        file_path = os.path.join("instagram_uploads", filename)
        path = default_storage.save(file_path, ContentFile(image_file.read()))

        # Verify the file was saved successfully
        if not default_storage.exists(path):
            return Response(
                {"error": "Failed to save image file to storage"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Build the production URL
        from django.contrib.sites.models import Site
        from django.conf import settings

        try:
            current_site = Site.objects.get_current()
            protocol = "https" if getattr(settings, "USE_TLS", True) else "http"
            production_url = f"{protocol}://{current_site.domain}/media/{path}"
        except Exception:
            # Fallback to manual domain construction
            domain = getattr(settings, "SITE_DOMAIN", "gemnar.com")
            production_url = f"https://{domain}/media/{path}"

        return Response(
            {"url": production_url, "local_path": path, "filename": filename},
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            {"error": f"Upload failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_instagram_video(request):
    """
    Upload video file for Instagram posts
    """
    try:
        video_file = request.FILES.get("video")

        if not video_file:
            return Response(
                {"error": "No video file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file type
        allowed_types = ["video/mp4", "video/mov", "video/avi", "video/quicktime"]
        if video_file.content_type not in allowed_types:
            return Response(
                {"error": "Invalid video file type. Supported formats: MP4, MOV, AVI"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file size (max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if video_file.size > max_size:
            return Response(
                {"error": "Video file too large. Maximum size is 100MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate unique filename
        import uuid

        filename = f"instagram_videos/{uuid.uuid4()}_{video_file.name}"

        # Save file to media storage
        from django.core.files.storage import default_storage

        file_path = default_storage.save(filename, video_file)

        # Get the URL
        file_url = default_storage.url(file_path)

        return Response(
            {
                "success": True,
                "url": file_url,
                "filename": filename,
                "size": video_file.size,
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(f"Error in upload_instagram_video: {str(e)}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return Response(
            {"error": f"Upload failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def check_video_generation_status_by_task(request, task_uuid):
    """
    Check the status of a video generation task by task UUID
    """
    try:
        from website.models import BrandInstagramPost

        # Find the post with this task UUID
        try:
            instagram_post = BrandInstagramPost.objects.get(
                video_generation_task_uuid=task_uuid
            )
        except BrandInstagramPost.DoesNotExist:
            return Response(
                {"error": "Video generation task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permissions
        if instagram_post.brand.owner != request.user:
            return Response(
                {"error": "Not authorized to view this task"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Return status information
        response_data = {
            "task_uuid": task_uuid,
            "status": instagram_post.video_generation_status,
            "post_id": instagram_post.id,
        }

        # Add video URL if completed
        if (
            instagram_post.video_generation_status == "completed"
            and instagram_post.video
        ):
            response_data["video_url"] = instagram_post.video.url
            response_data["thumbnail_url"] = (
                instagram_post.video_thumbnail.url
                if instagram_post.video_thumbnail
                else None
            )

        # Add error message if failed
        if instagram_post.video_generation_status == "failed":
            response_data["error"] = instagram_post.error_message

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in check_video_generation_status_by_task: {str(e)}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return Response(
            {"error": f"Internal server error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================================
# SORA 2 VIDEO GENERATION ENDPOINTS
# Essential endpoints for Sora 2 video generation workflow
# ============================================================================

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def sora_create_video(request):
    """
    Create a new Sora video generation job from text prompt.
    Supports both sora-2 and sora-2-pro models.
    Returns video_id for status polling.
    """
    try:
        from website.utils import get_openai_client

        # Get prompt from request
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get parameters
        model = request.data.get("model", "sora-2")
        size = request.data.get("size", "1280x720")
        seconds = int(request.data.get("seconds", "8"))
        
        # Validate model
        valid_models = ["sora-2", "sora-2-pro"]
        if model not in valid_models:
            model = "sora-2"
        
        # Validate size
        valid_sizes = ["1280x720", "1920x1080", "1080x1920", "720x1280"]
        if size not in valid_sizes:
            size = "1280x720"

        logger.info(f"Creating Sora video: model={model}, size={size}, seconds={seconds}s")

        # Initialize OpenAI client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Create video generation job
        video_job = client.videos.create(
            model=model,
            prompt=prompt,
            size=size,
            seconds=seconds,
        )

        return Response({
            "success": True,
            "video_id": video_job.id,
            "status": video_job.status,
            "model": video_job.model,
            "progress": getattr(video_job, 'progress', 0),
            "size": video_job.size,
            "seconds": video_job.seconds,
            "created_at": video_job.created_at,
        })

    except Exception as e:
        logger.exception("Error creating Sora video")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def sora_create_video_with_reference(request):
    """
    Create a Sora video with an input image as the first frame.
    The image guides the generation and acts as a reference.
    Returns video_id for status polling.
    """
    try:
        from website.utils import get_openai_client

        # Get prompt from request
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get reference image
        if "input_reference" not in request.FILES:
            return Response(
                {"error": "Input reference image is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reference_image = request.FILES["input_reference"]

        # Get parameters
        model = request.data.get("model", "sora-2-pro")  # Use pro for better quality with references
        size = request.data.get("size", "1280x720")
        seconds = int(request.data.get("seconds", "8"))
        
        # Validate parameters
        valid_models = ["sora-2", "sora-2-pro"]
        if model not in valid_models:
            model = "sora-2-pro"
        
        valid_sizes = ["1280x720", "1920x1080", "1080x1920", "720x1280"]
        if size not in valid_sizes:
            size = "1280x720"

        logger.info(f"Creating Sora video with reference: model={model}, size={size}, seconds={seconds}s")

        # Initialize OpenAI client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Parse video dimensions from size parameter (e.g., "720x1280")
        width, height = map(int, size.split('x'))
        
        # Load and resize reference image to match video dimensions
        image_data = reference_image.read()
        img = Image.open(io.BytesIO(image_data))
        
        # Resize image to exact video dimensions
        img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Save resized image to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img_resized.save(temp_file, format='JPEG', quality=95)
        temp_file.close()
        
        logger.info(f"Resized reference image from {img.size} to {img_resized.size} ({width}x{height})")

        try:
            # Create video with reference image
            with open(temp_file.name, "rb") as image_file:
                video_job = client.videos.create(
                    model=model,
                    prompt=prompt,
                    size=size,
                    seconds=seconds,
                    input_reference=image_file,
                )

            return Response({
                "success": True,
                "video_id": video_job.id,
                "status": video_job.status,
                "model": video_job.model,
                "progress": getattr(video_job, 'progress', 0),
                "size": video_job.size,
                "seconds": video_job.seconds,
                "has_reference": True,
                "created_at": video_job.created_at,
            })

        finally:
            # Clean up temp file
            try:
                os.remove(temp_file.name)
            except:
                pass

    except Exception as e:
        logger.exception("Error creating Sora video with reference")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def sora_get_video_status(request, video_id):
    """
    Get the current status of a Sora video generation job.
    Returns status, progress percentage (0-100), and job details.
    Used for polling until completion.
    """
    try:
        from website.utils import get_openai_client

        # Initialize OpenAI client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Retrieve video status
        video = client.videos.retrieve(video_id)

        response_data = {
            "success": True,
            "video_id": video.id,
            "status": video.status,  # queued, in_progress, completed, failed
            "progress": getattr(video, 'progress', 0),  # 0-100 percentage
            "model": video.model,
            "size": getattr(video, 'size', None),
            "seconds": getattr(video, 'seconds', None),
            "created_at": video.created_at,
        }

        # Add error info if failed
        if video.status == "failed":
            error_info = getattr(video, 'error', None)
            if error_info:
                response_data["error"] = {
                    "message": getattr(error_info, 'message', 'Video generation failed'),
                    "code": getattr(error_info, 'code', None),
                }

        logger.info(f"Sora video {video_id} status: {video.status}, progress: {response_data['progress']}%")

        return Response(response_data)

    except Exception as e:
        logger.exception(f"Error getting Sora video status {video_id}")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def sora_download_video(request, video_id):
    """
    Download the completed Sora video as MP4.
    Returns base64 encoded video for easy transfer to frontend.
    Only works after status is 'completed'.
    """
    try:
        from website.utils import get_openai_client
        import base64

        # Get variant (video, thumbnail, spritesheet)
        variant = request.GET.get('variant', 'video')
        valid_variants = ['video', 'thumbnail', 'spritesheet']
        if variant not in valid_variants:
            variant = 'video'

        # Initialize OpenAI client
        client = get_openai_client()
        if not client:
            return Response(
                {"error": "OpenAI API key is not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Download video content
        content = client.videos.download_content(video_id, variant=variant)

        # Determine content type
        content_types = {
            'video': 'video/mp4',
            'thumbnail': 'image/webp',
            'spritesheet': 'image/jpeg',
        }
        content_type = content_types.get(variant, 'application/octet-stream')

        # Read content as bytes
        video_bytes = content.read()

        # Return base64 encoded for JSON response
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')

        logger.info(f"Downloaded Sora video {video_id}, variant={variant}, size={len(video_bytes)} bytes")

        return Response({
            "success": True,
            "video_id": video_id,
            "variant": variant,
            "content": video_base64,
            "content_type": content_type,
            "size_bytes": len(video_bytes),
        })

    except Exception as e:
        logger.exception(f"Error downloading Sora video {video_id}")
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# Instagram Image/Video Upload to Cloudinary
# ============================================================================

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_instagram_image(request):
    """Upload image or video to Cloudinary for Instagram posts"""
    try:
        import cloudinary
        import cloudinary.uploader
        from django.conf import settings
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        
        file = request.FILES.get('image')
        if not file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine resource type based on file type
        resource_type = 'video' if file.content_type.startswith('video/') else 'image'
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder=f"instagram/{request.user.id}",
            resource_type=resource_type,
            transformation=[
                {'quality': 'auto'},
                {'fetch_format': 'auto'}
            ] if resource_type == 'image' else None
        )
        
        # Store upload record in database (optional - you can create a model for this)
        # For now, just return the URL
        
        return Response({
            "url": result['secure_url'],
            "public_id": result['public_id'],
            "resource_type": resource_type,
            "format": result.get('format'),
            "width": result.get('width'),
            "height": result.get('height'),
        })
        
    except ImportError:
        logger.error("Cloudinary not installed. Install with: pip install cloudinary")
        return Response(
            {"error": "Cloudinary integration not configured"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.exception(f"Error uploading to Cloudinary: {str(e)}")
        return Response(
            {"error": f"Upload failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_instagram_image_to_production(request):
    """Upload image or video to Cloudinary for Instagram posts (production endpoint)"""
    # Same as upload_instagram_image but can have different folder structure or settings
    return upload_instagram_image(request)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def list_user_uploads(request):
    """List user's uploaded images/videos from Cloudinary"""
    try:
        import cloudinary
        import cloudinary.api
        from django.conf import settings
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        
        # Get user's uploads from Cloudinary
        folder = f"instagram/{request.user.id}"
        
        # Get both images and videos
        images = cloudinary.api.resources(
            type="upload",
            prefix=folder,
            resource_type="image",
            max_results=100
        )
        
        videos = cloudinary.api.resources(
            type="upload",
            prefix=folder,
            resource_type="video",
            max_results=100
        )
        
        # Combine and format results
        all_uploads = []
        
        for resource in images.get('resources', []):
            all_uploads.append({
                'id': hash(resource['public_id']),  # Generate numeric ID from public_id
                'image_url': resource['secure_url'],
                'public_id': resource['public_id'],
                'created_at': resource['created_at'],
                'resource_type': 'image',
                'format': resource.get('format'),
            })
        
        for resource in videos.get('resources', []):
            all_uploads.append({
                'id': hash(resource['public_id']),
                'image_url': resource['secure_url'],
                'public_id': resource['public_id'],
                'created_at': resource['created_at'],
                'resource_type': 'video',
                'format': resource.get('format'),
            })
        
        # Sort by created_at (newest first)
        all_uploads.sort(key=lambda x: x['created_at'], reverse=True)
        
        return Response(all_uploads)
        
    except ImportError:
        logger.error("Cloudinary not installed")
        return Response([], status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception(f"Error listing uploads from Cloudinary: {str(e)}")
        return Response(
            {"error": f"Failed to list uploads: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([permissions.IsAuthenticated])
def delete_user_upload(request, image_id):
    """Delete user's uploaded image/video from Cloudinary"""
    try:
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api
        from django.conf import settings
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        
        # Get the public_id from request body
        public_id = request.data.get('public_id')
        
        if not public_id:
            return Response(
                {"error": "public_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the file belongs to the user
        if not public_id.startswith(f"instagram/{request.user.id}/"):
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Try to delete as image first, then as video
        try:
            cloudinary.uploader.destroy(public_id, resource_type="image")
        except:
            cloudinary.uploader.destroy(public_id, resource_type="video")
        
        return Response({"success": True})
        
    except ImportError:
        return Response(
            {"error": "Cloudinary integration not configured"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.exception(f"Error deleting upload from Cloudinary: {str(e)}")
        return Response(
            {"error": f"Delete failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
