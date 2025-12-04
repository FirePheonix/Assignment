from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from urllib.parse import urlparse

# Guarded import: on some setups (e.g., username disabled in allauth),
# importing dj_rest_auth.registration.serializers can raise at import time.
# Fall back to a plain DRF Serializer to keep imports safe in tests/checks.
try:
    from dj_rest_auth.registration.serializers import (
        RegisterSerializer as BaseRegisterSerializer,
    )
except Exception:  # pragma: no cover - defensive import fallback
    BaseRegisterSerializer = serializers.Serializer
from .models import (
    Task,
    TaskApplication,
    TweetConfiguration,
    BrandTweet,
    TweetStrategy,
    BrandInstagramPost,
    BrandAsset,
    Brand,
)

User = get_user_model()


class RegisterSerializer(BaseRegisterSerializer):
    """
    Custom registration serializer that adds missing _has_phone_field attribute
    without any phone field requirements
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add the missing attribute that some code expects
        # Set to False since we don't want phone field requirements
        self._has_phone_field = False


class EmailLoginSerializer(serializers.Serializer):
    """
    Custom login serializer that accepts email instead of username
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            # Find user by email
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    _("Unable to log in with provided credentials."),
                    code="authorization",
                )

            # Authenticate with username
            user = authenticate(
                request=self.context.get("request"),
                username=username,
                password=password,
            )

            if not user:
                raise serializers.ValidationError(
                    _("Unable to log in with provided credentials."),
                    code="authorization",
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    _("User account is disabled."), code="authorization"
                )

            attrs["user"] = user
            return attrs
        else:
            raise serializers.ValidationError(
                _('Must include "email" and "password".'), code="authorization"
            )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data
    """

    # Read-only URL fields
    profile_picture = serializers.SerializerMethodField(read_only=True)
    banner_image = serializers.SerializerMethodField(read_only=True)
    additional_image1 = serializers.SerializerMethodField(read_only=True)
    additional_image2 = serializers.SerializerMethodField(read_only=True)

    # Write-only fields (set images via URL returned from upload endpoint)
    profile_picture_url = serializers.CharField(write_only=True, required=False)
    banner_image_url = serializers.CharField(write_only=True, required=False)
    additional_image1_url = serializers.CharField(write_only=True, required=False)
    additional_image2_url = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "age",
            "instagram_handle",
            "bio",
            # Image URL getters (read-only)
            "profile_picture",
            "banner_image",
            "additional_image1",
            "additional_image2",
            # Write-only setters
            "profile_picture_url",
            "banner_image_url",
            "additional_image1_url",
            "additional_image2_url",
            "story_price",
            "post_price",
            "reel_price",
            "impressions_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "username",
            "impressions_count",
            "created_at",
            "updated_at",
            "profile_picture",
            "banner_image",
            "additional_image1",
            "additional_image2",
        ]

    # ---------- URL getters (read-only) ----------
    def get_profile_picture(self, obj):
        if obj.profile_image:
            # If it's a Cloudinary URL stored directly, return it
            if obj.profile_image.name and ('cloudinary.com' in obj.profile_image.name or obj.profile_image.name.startswith('https://')):
                return obj.profile_image.name
            
            request = self.context.get("request")
            if request:
                # Build absolute URL for /media/ path
                file_url = obj.profile_image.url
                if file_url.startswith("/"):
                    # It's an absolute path, build full URL
                    return request.build_absolute_uri(file_url)
                else:
                    # It's already a full URL
                    return file_url
            return obj.profile_image.url
        return None

    def get_banner_image(self, obj):
        if obj.banner_image:
            # If it's a Cloudinary URL stored directly, return it
            if obj.banner_image.name and ('cloudinary.com' in obj.banner_image.name or obj.banner_image.name.startswith('https://')):
                return obj.banner_image.name
            
            request = self.context.get("request")
            if request:
                file_url = obj.banner_image.url
                if file_url.startswith("/"):
                    return request.build_absolute_uri(file_url)
                else:
                    return file_url
            return obj.banner_image.url
        return None

    def get_additional_image1(self, obj):
        if obj.additional_image1:
            # If it's a Cloudinary URL stored directly, return it
            if obj.additional_image1.name and ('cloudinary.com' in obj.additional_image1.name or obj.additional_image1.name.startswith('https://')):
                return obj.additional_image1.name
            
            request = self.context.get("request")
            if request:
                file_url = obj.additional_image1.url
                if file_url.startswith("/"):
                    return request.build_absolute_uri(file_url)
                else:
                    return file_url
            return obj.additional_image1.url
        return None

    def get_additional_image2(self, obj):
        if obj.additional_image2:
            # If it's a Cloudinary URL stored directly, return it
            if obj.additional_image2.name and ('cloudinary.com' in obj.additional_image2.name or obj.additional_image2.name.startswith('https://')):
                return obj.additional_image2.name
            
            request = self.context.get("request")
            if request:
                file_url = obj.additional_image2.url
                if file_url.startswith("/"):
                    return request.build_absolute_uri(file_url)
                else:
                    return file_url
            return obj.additional_image2.url
        return None

    def _convert_url_to_path(self, url):
        """
        Convert a full URL to a relative file path for Django FileField.
        Handles both absolute URLs, Cloudinary URLs, and relative paths.
        """
        if not url:
            return None

        # If it's a Cloudinary URL, return it as-is (full URL)
        if 'cloudinary.com' in url or url.startswith('https://res.cloudinary.com'):
            return url

        # Parse the URL to extract just the path component
        parsed_url = urlparse(url)
        path = parsed_url.path

        # Remove the MEDIA_URL prefix if present
        media_url = settings.MEDIA_URL.rstrip("/")  # Remove trailing slash
        if path.startswith(media_url + "/"):
            # Strip /media/ prefix
            relative_path = path[len(media_url) + 1 :]
        elif path.startswith("/"):
            # Handle absolute paths that might not have media prefix
            # /user_uploads/file.jpg -> user_uploads/file.jpg
            relative_path = path[1:]  # Remove leading slash
        else:
            # Already a relative path
            relative_path = path

        return relative_path

    # ---------- Update handling ----------
    def update(self, instance, validated_data):
        """Handle updating user including image URL mapping"""
        # Handle image URL fields
        image_field_mappings = {
            "profile_picture_url": "profile_image",
            "banner_image_url": "banner_image",
            "additional_image1_url": "additional_image1",
            "additional_image2_url": "additional_image2",
        }

        for url_field, image_field in image_field_mappings.items():
            url = validated_data.pop(url_field, None)
            if url:
                # Convert URL to relative path
                relative_path = self._convert_url_to_path(url)
                if relative_path:
                    # Update the image field with the relative path
                    setattr(instance, image_field, relative_path)

        # Update remaining scalar fields normally
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model with read operations"""

    brand_username = serializers.CharField(source="brand.username", read_only=True)
    brand_email = serializers.CharField(source="brand.email", read_only=True)
    application_count = serializers.ReadOnlyField()
    accepted_applications_count = serializers.ReadOnlyField()
    user_has_applied = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "category",
            "genre",
            "incentive_type",
            "barter_details",
            "pay_amount",
            "deadline",
            "is_active",
            "brand",
            "brand_username",
            "brand_email",
            "application_count",
            "accepted_applications_count",
            "user_has_applied",
            "created_at",
        ]
        read_only_fields = ["id", "brand", "created_at"]

    def get_user_has_applied(self, obj):
        """Check if the current user has applied to this task"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.applications.filter(creator=request.user).exists()
        return False


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Task instances"""

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "category",
            "genre",
            "incentive_type",
            "barter_details",
            "pay_amount",
            "deadline",
        ]

    def validate(self, data):
        """Validate task data based on incentive type"""
        incentive_type = data.get("incentive_type")

        if incentive_type == "BARTER" and not data.get("barter_details"):
            raise serializers.ValidationError(
                "Barter details are required when incentive type is 'BARTER'"
            )

        if incentive_type == "PAY" and not data.get("pay_amount"):
            raise serializers.ValidationError(
                "Pay amount is required when incentive type is 'PAY'"
            )

        if (
            incentive_type == "PAY"
            and data.get("pay_amount")
            and data["pay_amount"] <= 0
        ):
            raise serializers.ValidationError("Pay amount must be greater than 0")

        return data

    def create(self, validated_data):
        """Create task with the current user as brand"""
        validated_data["brand"] = self.context["request"].user
        return super().create(validated_data)


class SimpleUserSerializer(serializers.ModelSerializer):
    """Minimal user info for nested representations"""

    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "instagram_handle",
            "profile_picture",
        )

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        if obj.profile_image:
            # Return absolute URL
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None


class TaskApplicationSerializer(serializers.ModelSerializer):
    """Serializer for TaskApplication model with read operations"""

    creator_username = serializers.CharField(source="creator.username", read_only=True)
    creator_email = serializers.CharField(source="creator.email", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)
    task_category = serializers.CharField(source="task.category", read_only=True)
    task_incentive_type = serializers.CharField(
        source="task.incentive_type", read_only=True
    )

    # NEW: nested user field for frontend convenience
    user = SimpleUserSerializer(source="creator", read_only=True)

    class Meta:
        model = TaskApplication
        fields = [
            "id",
            "task",
            "creator",
            "creator_username",
            "creator_email",
            "task_title",
            "task_category",
            "task_incentive_type",
            "status",
            "message",
            "applied_at",
            "updated_at",
            "user",  # added field
        ]
        read_only_fields = [
            "id",
            "task",
            "creator",
            "applied_at",
            "updated_at",
        ]


class TaskApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TaskApplication instances"""

    message = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = TaskApplication
        fields = ["message"]

    def validate_message(self, value):
        """Validate the message field"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()

    def validate(self, data):
        """Validate application data"""
        task = self.context.get("task")
        user = self.context.get("request").user

        if not task:
            raise serializers.ValidationError("Task is required")

        if not task.is_active:
            raise serializers.ValidationError("Cannot apply to inactive task")

        if task.brand == user:
            raise serializers.ValidationError("Cannot apply to your own task")

        # Check if user has already applied
        if TaskApplication.objects.filter(task=task, creator=user).exists():
            raise serializers.ValidationError("You have already applied to this task")

        return data

    def create(self, validated_data):
        """Create application with task and creator from context"""
        validated_data["task"] = self.context["task"]
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)


class TweetConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TweetConfiguration
        fields = [
            "id",
            "brand",
            "topics",
            "tones",
            "keywords",
            "hashtags",
            "prompt_template",
            "schedule",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BrandTweetSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(read_only=True)
    can_be_posted = serializers.BooleanField(read_only=True)
    assets = serializers.SerializerMethodField()
    asset_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of asset IDs to attach to this tweet",
    )
    scheduledFor = serializers.SerializerMethodField()
    brandId = serializers.SerializerMethodField()
    imageUrl = serializers.SerializerMethodField()

    class Meta:
        model = BrandTweet
        fields = [
            "id",
            "brand",
            "brandId",
            "content",
            "image",
            "imageUrl",
            "status",
            "status_display",
            "can_be_posted",
            "assets",
            "asset_ids",
            "scheduled_for",
            "scheduledFor",
            "posted_at",
            "tweet_id",
            "tweet_url",
            # Metrics fields
            "like_count",
            "retweet_count",
            "reply_count",
            "quote_count",
            "bookmark_count",
            "metrics_last_updated",
            "error_message",
            "ai_prompt",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tweet_id",
            "tweet_url",
            "posted_at",
            "created_at",
            "updated_at",
            "like_count",
            "retweet_count",
            "reply_count",
            "quote_count",
            "bookmark_count",
            "metrics_last_updated",
        ]

    def get_scheduledFor(self, obj):
        return obj.scheduled_for.isoformat() if obj.scheduled_for else None

    def get_brandId(self, obj):
        return obj.brand.id if obj.brand else 0

    def get_imageUrl(self, obj):
        if obj.image:
            from django.contrib.sites.models import Site
            from django.conf import settings

            try:
                current_site = Site.objects.get_current()
                protocol = "https" if getattr(settings, "USE_TLS", True) else "http"
                return f"{protocol}://{current_site.domain}{obj.image.url}"
            except Exception:
                # Fallback to manual domain construction
                if settings.DEBUG:
                    # Development environment
                    return f"http://localhost:8000{obj.image.url}"
                else:
                    # Production environment
                    domain = getattr(settings, "SITE_DOMAIN", "gemnar.com")
                    protocol = "https" if getattr(settings, "USE_TLS", True) else "http"
                    return f"{protocol}://{domain}{obj.image.url}"
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure all string fields are not None
        string_fields = [
            "content",
            "status",
            "tweet_id",
            "tweet_url",
            "error_message",
            "ai_prompt",
            "status_display",
        ]
        for field in string_fields:
            if data.get(field) is None:
                data[field] = ""
        # Ensure date fields are None, not empty string
        for field in ["scheduledFor", "posted_at"]:
            if not data.get(field):
                data[field] = None
        return data

    def create(self, validated_data):
        asset_ids = validated_data.pop("asset_ids", [])
        tweet = super().create(validated_data)
        if asset_ids:
            assets = BrandAsset.objects.filter(
                id__in=asset_ids, brand=tweet.brand, is_active=True
            )
            tweet.assets.set(assets)
            # Increment usage count for each asset
            for asset in assets:
                asset.increment_usage()
        return tweet

    def update(self, instance, validated_data):
        asset_ids = validated_data.pop("asset_ids", None)
        tweet = super().update(instance, validated_data)
        if asset_ids is not None:
            assets = BrandAsset.objects.filter(
                id__in=asset_ids, brand=tweet.brand, is_active=True
            )
            tweet.assets.set(assets)
            # Increment usage count for newly added assets
            for asset in assets:
                if not instance.assets.filter(id=asset.id).exists():
                    asset.increment_usage()
        return tweet

    def get_assets(self, obj):
        """Get serialized assets for this tweet"""
        # Avoid circular import by importing here

        assets_data = []
        for asset in obj.assets.all():
            assets_data.append(
                {
                    "id": asset.id,
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "file_url": asset.get_file_url(),
                    "thumbnail_url": asset.get_thumbnail_url(),
                    "description": asset.description,
                    "tags": asset.tags,
                    "file_size": asset.file_size,
                    "width": asset.width,
                    "height": asset.height,
                    "duration": asset.duration,
                    "is_active": asset.is_active,
                    "usage_count": asset.usage_count,
                    "created_at": asset.created_at,
                    "updated_at": asset.updated_at,
                }
            )
        return assets_data


class TweetStrategySerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )

    class Meta:
        model = TweetStrategy
        fields = [
            "id",
            "name",
            "category",
            "category_display",
            "description",
            "prompt_template",
            "example_output",
            "tone_suggestions",
            "hashtag_suggestions",
            "timing_suggestions",
            "is_active",
            "usage_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "usage_count", "created_at", "updated_at"]


class BrandInstagramPostSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(read_only=True)
    can_be_posted = serializers.BooleanField(read_only=True)
    thumbnail_url = serializers.CharField(source="get_thumbnail_url", read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)
    assets = serializers.SerializerMethodField()
    asset_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of asset IDs to attach to this Instagram post",
    )

    class Meta:
        model = BrandInstagramPost
        fields = [
            "id",
            "brand",
            "content",
            "image",
            "image_url",
            "video",
            "video_thumbnail",
            "status",
            "status_display",
            "can_be_posted",
            "thumbnail_url",
            "assets",
            "asset_ids",
            "scheduled_for",
            "posted_at",
            "instagram_id",
            "instagram_url",
            "error_message",
            "ai_prompt",
            "video_prompt",
            "is_video_post",
            "video_duration",
            "video_quality",
            "video_generation_task_uuid",
            "video_generation_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "instagram_id",
            "instagram_url",
            "posted_at",
            "video_generation_task_uuid",
            "video_generation_status",
            "created_at",
            "updated_at",
        ]

    def get_image_url(self, obj):
        """Get absolute URL for the image"""
        if obj.image:
            request = self.context.get("request")
            if request:
                file_url = obj.image.url
                if file_url.startswith("/"):
                    # It's an absolute path, build full URL
                    return request.build_absolute_uri(file_url)
                else:
                    # It's already a full URL
                    return file_url
            return obj.image.url
        return None

    def create(self, validated_data):
        asset_ids = validated_data.pop("asset_ids", [])

        # Ensure brand is set from the request user
        if "brand" not in validated_data:
            # Get the user's default brand or first brand
            user = self.context["request"].user
            try:
                brand = Brand.objects.filter(owner=user).first()
                if brand:
                    validated_data["brand"] = brand
                else:
                    raise serializers.ValidationError("No brand found for user")
            except Brand.DoesNotExist:
                raise serializers.ValidationError("No brand found for user")

        post = super().create(validated_data)
        if asset_ids:
            assets = BrandAsset.objects.filter(
                id__in=asset_ids, brand=post.brand, is_active=True
            )
            post.assets.set(assets)
            # Increment usage count for each asset
            for asset in assets:
                asset.increment_usage()
        return post

    def update(self, instance, validated_data):
        asset_ids = validated_data.pop("asset_ids", None)
        post = super().update(instance, validated_data)
        if asset_ids is not None:
            assets = BrandAsset.objects.filter(
                id__in=asset_ids, brand=post.brand, is_active=True
            )
            post.assets.set(assets)
            # Increment usage count for newly added assets
            for asset in assets:
                if not instance.assets.filter(id=asset.id).exists():
                    asset.increment_usage()
        return post

    def get_assets(self, obj):
        """Get serialized assets for this Instagram post"""
        # Avoid circular import by importing here

        assets_data = []
        for asset in obj.assets.all():
            assets_data.append(
                {
                    "id": asset.id,
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "file_url": asset.get_file_url(),
                    "thumbnail_url": asset.get_thumbnail_url(),
                    "description": asset.description,
                    "tags": asset.tags,
                    "file_size": asset.file_size,
                    "width": asset.width,
                    "height": asset.height,
                    "duration": asset.duration,
                    "is_active": asset.is_active,
                    "usage_count": asset.usage_count,
                    "created_at": asset.created_at,
                    "updated_at": asset.updated_at,
                }
            )
        return assets_data


class BrandAssetSerializer(serializers.ModelSerializer):
    """Serializer for BrandAsset model"""

    file_url = serializers.CharField(source="get_file_url", read_only=True)
    thumbnail_url = serializers.CharField(source="get_thumbnail_url", read_only=True)
    file_extension = serializers.CharField(read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    is_video = serializers.BooleanField(read_only=True)

    class Meta:
        model = BrandAsset
        fields = [
            "id",
            "brand",
            "name",
            "asset_type",
            "file",
            "file_url",
            "thumbnail",
            "thumbnail_url",
            "description",
            "tags",
            "file_size",
            "width",
            "height",
            "duration",
            "file_extension",
            "is_image",
            "is_video",
            "is_active",
            "usage_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "file_size",
            "width",
            "height",
            "duration",
            "file_extension",
            "is_image",
            "is_video",
            "usage_count",
            "created_at",
            "updated_at",
        ]


# Twitter Integration Serializers
from .models import TwitterConfig, QueuedTweet, TwitterAnalytics


class TwitterConfigSerializer(serializers.ModelSerializer):
    """Serializer for Twitter configuration"""
    
    class Meta:
        model = TwitterConfig
        fields = [
            'id',
            'brand',
            'api_key', 
            'api_secret',
            'access_token',
            'access_token_secret',
            'bearer_token',
            'twitter_username',
            'twitter_user_id',
            'is_active',
            'last_verified',
            'verification_error',
            'created_at',
            'updated_at'
        ]
        extra_kwargs = {
            'api_secret': {'write_only': True},
            'access_token': {'write_only': True},
            'access_token_secret': {'write_only': True},
            'bearer_token': {'write_only': True},
        }


class QueuedTweetSerializer(serializers.ModelSerializer):
    """Serializer for queued tweets"""
    
    class Meta:
        model = QueuedTweet
        fields = [
            'id',
            'brand',
            'content',
            'media_urls',
            'scheduled_time',
            'status',
            'tweet_id',
            'posted_at',
            'error_message',
            'ai_generated',
            'prompt_used',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['tweet_id', 'posted_at', 'status']


class TwitterAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for Twitter analytics"""
    
    class Meta:
        model = TwitterAnalytics
        fields = [
            'id',
            'brand',
            'date',
            'followers_count',
            'following_count',
            'tweets_count',
            'likes_count',
            'daily_impressions',
            'daily_engagements',
            'daily_retweets',
            'daily_likes',
            'daily_replies',
            'engagement_rate',
            'created_at',
            'updated_at'
        ]


class BrandInstagramPostSerializer(serializers.ModelSerializer):
    """Serializer for Instagram posts with brand information"""
    
    brand = serializers.SerializerMethodField(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        source='brand',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = BrandInstagramPost
        fields = [
            'id',
            'brand',
            'brand_id',
            'content',
            'image',
            'image_url',
            'video',
            'video_url',
            'video_thumbnail',
            'status',
            'instagram_id',
            'instagram_url',
            'scheduled_for',
            'posted_at',
            'error_message',
            'is_video_post',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['instagram_id', 'instagram_url', 'posted_at', 'created_at', 'updated_at']
    
    def get_brand(self, obj):
        """Return brand information"""
        return {
            'id': obj.brand.id,
            'name': obj.brand.name,
        }
