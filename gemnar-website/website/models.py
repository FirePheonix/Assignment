from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import random
import uuid
import logging


# Reserved brand names/slugs that cannot be used for brand profiles
RESERVED_BRAND_NAMES = [
    # URL patterns from website/urls.py
    "tweet-dashboard",
    "tweet-config",
    "tweet-history",
    "tweet",
    "tweet-analytics",
    "send-test-tweet",
    "twitter-api-diagnostic",
    "signup",
    "process-payment",
    "landing",
    "creator",
    "business",
    "terms",
    "privacy",
    "about",
    "help",
    "report-issue",
    "blog",
    "contact",
    "services",
    "status",
    "feed",
    "marketing-grade",
    "text-to-image",
    "ref",
    "referral",
    "company",
    "leaderboard",
    "api",
    "brand",
    # URL patterns from main urls.py
    "accounts",
    "chat",
    "organizations",
    "favicon.ico",
    # Common system paths
    "admin",
    "static",
    "media",
    "robots.txt",
    "sitemap.xml",
    "sitemap",
    "favicon",
    "apple-touch-icon",
    "manifest.json",
    # Django/Web standards
    "login",
    "logout",
    "register",
    "password",
    "reset",
    "confirm",
    "activate",
    "dashboard",
    "settings",
    "profile",
    "account",
    "user",
    "users",
    # HTTP methods and common paths
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "head",
    "options",
    "www",
    "ftp",
    "mail",
    "email",
    "support",
    "info",
    "news",
    # Gemnar specific
    "gemnar",
    "platform",
    "marketing",
    "analytics",
    "campaigns",
    "insights",
    "automation",
    "ai",
    "intelligence",
    "data",
    # Common brand conflicts
    "app",
    "mobile",
    "web",
    "website",
    "site",
    "home",
    "index",
    "search",
    "explore",
    "discover",
    "trending",
    "popular",
    # Technical terms
    "error",
    "success",
    "warning",
    "info",
    "debug",
    "test",
    "demo",
    "sample",
    "example",
    "null",
    "undefined",
    "admin",
    "root",
    # Social media
    "facebook",
    "twitter",
    "instagram",
    "linkedin",
    "youtube",
    "tiktok",
    "pinterest",
    "snapchat",
    "whatsapp",
    "telegram",
    # Business terms that might cause confusion
    "enterprise",
    "premium",
    "pro",
    "plus",
    "basic",
    "free",
    "trial",
    "pricing",
    "plans",
    "features",
    "solutions",
]


# Create your models here.


class User(AbstractUser):
    """Custom user model with additional fields"""

    # Override email field to make it unique
    email = models.EmailField(max_length=254, unique=True, verbose_name="email address")

    bio = models.TextField(
        max_length=500, blank=True, help_text="Tell us about yourself"
    )
    age = models.IntegerField(null=True, blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(
        upload_to="profile_images/", blank=True, null=True
    )
    banner_image = models.ImageField(upload_to="banner_images/", blank=True, null=True)
    additional_image1 = models.ImageField(
        upload_to="additional_images/", blank=True, null=True
    )
    additional_image2 = models.ImageField(
        upload_to="additional_images/", blank=True, null=True
    )
    story_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price for story posts",
    )
    post_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price for regular posts",
    )
    reel_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price for reels",
    )

    # Profile analytics
    impressions_count = models.PositiveIntegerField(
        default=0, help_text="Number of times this profile has been viewed"
    )

    # Twitter API Configuration
    twitter_api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twitter API Key (Consumer Key)",
    )
    twitter_api_secret = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twitter API Secret (Consumer Secret)",
    )
    twitter_access_token = models.CharField(
        max_length=255, blank=True, null=True, help_text="Twitter Access Token"
    )
    twitter_access_token_secret = models.CharField(
        max_length=255, blank=True, null=True, help_text="Twitter Access Token Secret"
    )
    twitter_bearer_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twitter Bearer Token (required for API v2)",
    )
    twitter_username = models.CharField(
        max_length=100, blank=True, null=True, help_text="Twitter username"
    )

    # Creator-specific fields
    name = models.CharField(
        max_length=200, blank=True, help_text="Creator display name"
    )
    description = models.TextField(
        max_length=1000, blank=True, help_text="Creator description/bio"
    )
    instagram_url = models.URLField(blank=True, help_text="Instagram profile URL")

    # Creator portfolio fields (6 photos/videos)
    photo1 = models.ImageField(upload_to="creator_photos/", blank=True, null=True)
    photo2 = models.ImageField(upload_to="creator_photos/", blank=True, null=True)
    photo3 = models.ImageField(upload_to="creator_photos/", blank=True, null=True)
    photo4 = models.ImageField(upload_to="creator_photos/", blank=True, null=True)
    photo5 = models.ImageField(upload_to="creator_photos/", blank=True, null=True)
    photo6 = models.ImageField(upload_to="creator_photos/", blank=True, null=True)

    # Creator brand preferences (5 brands they want to work with)
    brand1 = models.CharField(max_length=100, blank=True)
    brand2 = models.CharField(max_length=100, blank=True)
    brand3 = models.CharField(max_length=100, blank=True)
    brand4 = models.CharField(max_length=100, blank=True)
    brand5 = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    @property
    def has_twitter_config(self):
        """Check if user has complete Twitter API configuration"""
        return all(
            [
                self.twitter_api_key,
                self.twitter_api_secret,
                self.twitter_access_token,
                self.twitter_access_token_secret,
                self.twitter_bearer_token,
            ]
        )

    def get_masked_twitter_keys(self):
        """Get masked version of Twitter keys for display"""

        def mask_key(key):
            if not key or len(key) < 8:
                return "Not configured"
            return key[:4] + "..." + key[-4:]

        return {
            "api_key": mask_key(self.twitter_api_key),
            "api_secret": mask_key(self.twitter_api_secret),
            "access_token": mask_key(self.twitter_access_token),
            "access_token_secret": mask_key(self.twitter_access_token_secret),
            "bearer_token": mask_key(self.twitter_bearer_token),
        }


class ProfileImpression(models.Model):
    """Track individual profile impressions"""

    # The user whose profile was viewed
    profile_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="profile_impressions"
    )

    # The user who viewed the profile (optional - can be anonymous)
    viewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="profile_views",
    )

    # Session tracking removed - replaced by analytics service
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    # Location data
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    referrer = models.URLField(blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profile Impression"
        verbose_name_plural = "Profile Impressions"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["profile_user", "-timestamp"]),
            models.Index(fields=["viewer", "-timestamp"]),
            models.Index(fields=["ip_address", "-timestamp"]),
            models.Index(fields=["-timestamp"]),
        ]
        # Prevent multiple impressions from same IP for same profile within short time
        # This can be adjusted based on business needs
        unique_together = [("profile_user", "ip_address", "timestamp")]

    def __str__(self):
        viewer_str = self.viewer.username if self.viewer else "Anonymous"
        return f"{viewer_str} viewed {self.profile_user.username}'s profile"


class OrganizationInvitation(models.Model):
    """Model for organization invitations sent by email"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("expired", "Expired"),
    ]

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_invitations"
    )
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_invitations",
    )

    class Meta:
        unique_together = ["organization", "email"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invitation to {self.email} for {self.organization.name}"

    def is_expired(self):
        """Check if invitation has expired"""
        return timezone.now() > self.expires_at

    def can_be_accepted(self):
        """Check if invitation can be accepted"""
        return self.status == "pending" and not self.is_expired()

    def save(self, *args, **kwargs):
        # Set expiration date to 7 days from now if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)  # Ensure the brand is saved correctly


class Brand(models.Model):
    """Brand model (formerly Business)"""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    url = models.URLField()
    description = models.TextField(max_length=1000, blank=True)
    logo = models.ImageField(upload_to="brand_logos/", blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="brands")

    # Organization association
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="brands",
        null=True,
        blank=True,
        help_text="Organization this brand belongs to",
    )

    # Payment fields
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=(
            "Current Stripe subscription status (active, canceled, past_due, etc.)"
        ),
    )
    last_payment_date = models.DateTimeField(
        null=True, blank=True, help_text="Date of last successful payment"
    )

    # Cashfree payment fields
    cashfree_customer_id = models.CharField(max_length=255, blank=True, null=True)
    cashfree_order_id = models.CharField(max_length=255, blank=True, null=True)
    cashfree_payment_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Current Cashfree payment status (PAID, PENDING, FAILED, etc.)",
    )
    preferred_payment_method = models.CharField(
        max_length=20,
        choices=[("stripe", "Stripe"), ("cashfree", "Cashfree")],
        default="stripe",
        help_text="Preferred payment method for this brand",
    )

    # Twitter API Configuration for brand-specific posting
    twitter_api_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twitter API Key (Consumer Key) for this brand",
    )
    twitter_api_secret = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twitter API Secret (Consumer Secret) for this brand",
    )
    twitter_access_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twitter Access Token for this brand",
    )
    twitter_access_token_secret = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twitter Access Token Secret for this brand",
    )
    twitter_bearer_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Twitter Bearer Token for this brand (required for API v2)",
    )
    twitter_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Twitter username for this brand",
    )

    # Instagram API Configuration for brand-specific posting
    instagram_access_token = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Instagram Access Token for this brand",
    )
    instagram_user_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Instagram User ID for this brand",
    )
    instagram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Instagram username for this brand",
    )
    instagram_app_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Instagram App ID for this brand",
    )
    instagram_app_secret = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Instagram App Secret for this brand",
    )
    instagram_business_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=(
            "Meta Business ID associated with the Instagram/Facebook app integration"
        ),
    )
    instagram_user_token = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text=(
            "Explicit user access token (mirrors long-lived user access "
            "token; stored separately for clarity)."
        ),
    )
    instagram_app_token = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text=(
            "Last generated app access token (client_credentials). "
            "Optional; may expire quickly and is not always required."
        ),
    )
    instagram_oauth_state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Temporary OAuth state token for Instagram authentication flow",
    )
    instagram_connected_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when Instagram account was connected",
    )

    # Slack Integration for notifications
    slack_webhook_url = models.URLField(
        blank=True,
        null=True,
        help_text="Slack webhook URL for tweet queue notifications",
    )
    slack_channel = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Slack channel for notifications (optional)",
    )
    slack_notifications_enabled = models.BooleanField(
        default=False,
        help_text="Enable Slack notifications for this brand",
    )

    # Default brand selection
    is_default = models.BooleanField(
        default=False,
        help_text="Mark this brand as the default for its organization",
    )

    # AI Credits system
    credits_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Current AI credits balance for this brand",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            from django.utils.text import slugify

            self.slug = slugify(self.name)

        # Check if slug is reserved
        if self.slug.lower() in RESERVED_BRAND_NAMES:
            raise ValidationError(
                f"The brand name '{self.name}' cannot be used as it conflicts "
                f"with system URLs. Please choose a different name."
            )

        # Ensure slug is unique
        original_slug = self.slug
        counter = 1
        while Brand.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            # Also check if the numbered slug is reserved
            candidate_slug = f"{original_slug}-{counter}"
            if candidate_slug.lower() in RESERVED_BRAND_NAMES:
                counter += 1
                continue
            self.slug = candidate_slug
            counter += 1

        # Handle default brand logic - only one default per organization
        if self.is_default and self.organization:
            # Unset any other default brands in the same organization
            Brand.objects.filter(
                organization=self.organization, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("website:brand_profile", kwargs={"slug": self.slug})

    @property
    def has_twitter_config(self):
        """Check if brand has complete Twitter API configuration"""
        return all(
            [
                self.twitter_api_key,
                self.twitter_api_secret,
                self.twitter_access_token,
                self.twitter_access_token_secret,
                self.twitter_bearer_token,
            ]
        )

    @property
    def has_instagram_config(self):
        """Check if brand has complete Instagram API configuration"""
        # Consider config valid if we have an explicit user token or legacy access token
        token_present = bool(
            (self.instagram_user_token and self.instagram_user_token.strip())
            or (self.instagram_access_token and self.instagram_access_token.strip())
        )
        # Check if we have the minimum required: token and user_id
        # App credentials can be either per-brand or global (from settings)
        has_basic_config = all([
            token_present,
            self.instagram_user_id and self.instagram_user_id.strip(),
        ])
        
        # If basic config exists, check for credentials (per-brand or global)
        if has_basic_config:
            from django.conf import settings
            has_app_credentials = bool(
                (self.instagram_app_id and self.instagram_app_secret) or
                (getattr(settings, 'INSTAGRAM_APP_ID', None) and getattr(settings, 'INSTAGRAM_APP_SECRET', None))
            )
            return has_app_credentials
        
        return False

    @property
    def has_slack_config(self):
        """Check if brand has Slack notifications configured"""
        return bool(self.slack_webhook_url and self.slack_notifications_enabled)

    def get_masked_twitter_keys(self):
        """Get masked version of Twitter keys for display"""

        def mask_key(key):
            if not key or len(key) < 8:
                return "Not configured"
            return key[:4] + "..." + key[-4:]

        return {
            "api_key": mask_key(self.twitter_api_key),
            "api_secret": mask_key(self.twitter_api_secret),
            "access_token": mask_key(self.twitter_access_token),
            "access_token_secret": mask_key(self.twitter_access_token_secret),
            "bearer_token": mask_key(self.twitter_bearer_token),
        }

    def get_masked_instagram_keys(self):
        """Get masked version of Instagram keys for display"""

        def mask_key(key):
            if not key or len(key) < 8:
                return "Not configured"
            return key[:4] + "..." + key[-4:]

        return {
            "access_token": mask_key(self.instagram_access_token),
            "user_token": mask_key(self.instagram_user_token),
            "app_token": mask_key(self.instagram_app_token),
            "user_id": mask_key(self.instagram_user_id),
            "app_id": mask_key(self.instagram_app_id),
            "app_secret": mask_key(self.instagram_app_secret),
        }

    def send_slack_notification(self, message, urgent=False):
        """Send a Slack notification for this brand"""
        if not self.has_slack_config:
            return False

        try:
            import requests
            import logging

            logger = logging.getLogger(__name__)

            # Prepare payload
            payload = {
                "text": message,
                "username": f"Gemnar Bot - {self.name}",
                "icon_emoji": ":warning:" if urgent else ":robot_face:",
            }

            # Add channel if specified
            if self.slack_channel:
                payload["channel"] = self.slack_channel

            # Send notification
            response = requests.post(self.slack_webhook_url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"Slack notification sent for brand {self.name}")
                return True
            else:
                logger.error(
                    f"Failed to send Slack notification for brand {self.name}: "
                    f"{response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Error sending Slack notification for brand {self.name}: {str(e)}"
            )
            return False

    def delete_tweet_from_twitter(self, twitter_id):
        """Delete a tweet from Twitter using this brand's API credentials"""
        import tweepy
        import logging

        logger = logging.getLogger(__name__)

        if not self.has_twitter_config:
            return {
                "success": False,
                "error": "Twitter API configuration is incomplete for this brand",
            }

        try:
            # Create Twitter API client
            client = tweepy.Client(
                bearer_token=self.twitter_bearer_token,
                consumer_key=self.twitter_api_key,
                consumer_secret=self.twitter_api_secret,
                access_token=self.twitter_access_token,
                access_token_secret=self.twitter_access_token_secret,
                wait_on_rate_limit=True,
            )

            # Delete the tweet
            response = client.delete_tweet(twitter_id)

            if response.data and response.data.get("deleted"):
                logger.info(
                    f"Successfully deleted tweet {twitter_id} for brand {self.name}"
                )
                return {
                    "success": True,
                    "message": "Tweet deleted successfully from Twitter",
                }
            else:
                logger.error(
                    f"Failed to delete tweet {twitter_id} for brand {self.name}: {response}"
                )
                return {
                    "success": False,
                    "error": "Tweet deletion failed - Twitter API returned unexpected response",
                }

        except tweepy.Forbidden as e:
            logger.error(
                f"Twitter API Forbidden error deleting tweet {twitter_id} for brand {self.name}: {str(e)}"
            )
            return {
                "success": False,
                "error": "Permission denied - you may not have permission to delete this tweet",
            }
        except tweepy.NotFound as e:
            logger.error(
                f"Tweet {twitter_id} not found for brand {self.name}: {str(e)}"
            )
            return {
                "success": False,
                "error": "Tweet not found - it may have already been deleted",
            }
        except tweepy.TooManyRequests as e:
            logger.error(
                f"Twitter API rate limit exceeded for brand {self.name}: {str(e)}"
            )
            return {
                "success": False,
                "error": "Rate limit exceeded - please try again later",
            }
        except Exception as e:
            logger.error(
                f"Unexpected error deleting tweet {twitter_id} for brand {self.name}: {str(e)}"
            )
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def get_subscription_plan(self):
        """Get the current subscription plan based on Stripe price ID"""
        if not self.stripe_subscription_status == "active":
            return None

        # Get environment variables for price IDs
        import os

        price_99 = os.environ.get("STRIPE_PRICE_99")
        price_199 = os.environ.get("STRIPE_PRICE_199")
        price_299 = os.environ.get("STRIPE_PRICE_299")

        # Get the subscription from Stripe to check price ID
        if self.stripe_subscription_id:
            try:
                import stripe

                subscription = stripe.Subscription.retrieve(self.stripe_subscription_id)
                if subscription.items and subscription.items.data:
                    price_id = subscription.items.data[0].price.id

                    if price_id == price_99:
                        return "starter"  # $99 plan
                    elif price_id == price_199:
                        return "professional"  # $199 plan
                    elif price_id == price_299:
                        return "enterprise"  # $299 plan
            except Exception:
                pass

        return None

    def get_daily_tweet_limit(self):
        """Get daily tweet limit based on subscription plan"""
        plan = self.get_subscription_plan()
        if plan == "starter":
            return 1  # $99 plan: 1 tweet per day
        elif plan == "professional":
            return 5  # $199 plan: 5 tweets per day
        elif plan == "enterprise":
            return 25  # $299 plan: 25 tweets per day
        else:
            return 0  # No active subscription

    def get_tweets_scheduled_today(self):
        """Get count of tweets scheduled for today"""
        from django.utils import timezone

        today = timezone.now().date()

        return self.brand_tweets.filter(
            scheduled_for__date=today, status__in=["draft", "approved"]
        ).count()

    def can_schedule_more_tweets_today(self):
        """Check if brand can schedule more tweets today based on plan"""
        daily_limit = self.get_daily_tweet_limit()
        if daily_limit == 0:
            return False

        scheduled_today = self.get_tweets_scheduled_today()
        return scheduled_today < daily_limit

    def get_next_available_time_slot(self):
        """Get the next available time slot for scheduling a tweet"""
        from django.utils import timezone
        import datetime

        daily_limit = self.get_daily_tweet_limit()
        if daily_limit == 0:
            return None

        now = timezone.now()

        # Check today first
        today = now.date()
        scheduled_today = self.get_tweets_scheduled_today()

        if scheduled_today < daily_limit:
            # Find next available hour today (9 AM to 8 PM)
            current_hour = now.hour
            for hour in range(max(9, current_hour + 1), 21):  # 9 AM to 8 PM
                potential_time = now.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
                if potential_time > now:
                    # Check if this time slot is already taken
                    existing_tweets = self.brand_tweets.filter(
                        scheduled_for__hour=hour,
                        scheduled_for__date=today,
                        status__in=["draft", "approved"],
                    ).count()

                    if existing_tweets == 0:
                        return potential_time

        # If no slots today, find next day with available slots
        for days_ahead in range(1, 30):  # Check next 30 days
            check_date = today + datetime.timedelta(days=days_ahead)
            scheduled_that_day = self.brand_tweets.filter(
                scheduled_for__date=check_date, status__in=["draft", "approved"]
            ).count()

            if scheduled_that_day < daily_limit:
                # Return 9 AM on that day
                return timezone.make_aware(
                    datetime.datetime.combine(check_date, datetime.time(9, 0))
                )

        return None

    def has_sufficient_credits(self, amount):
        """Check if brand has sufficient credits for a transaction"""
        return self.credits_balance >= amount

    def deduct_credits(self, amount, description="", transaction_type="usage"):
        """Deduct credits from brand balance with transaction record"""
        from decimal import Decimal

        amount = Decimal(str(amount))
        if not self.has_sufficient_credits(amount):
            return False, "Insufficient credits"

        # Deduct credits
        self.credits_balance -= amount
        self.save(update_fields=["credits_balance"])

        # Create transaction record
        CreditTransaction.objects.create(
            brand=self,
            transaction_type=transaction_type,
            amount=-amount,  # Negative for deduction
            description=description,
            balance_after=self.credits_balance,
        )

        return True, "Credits deducted successfully"

    def add_credits(self, amount, description="", transaction_type="purchase"):
        """Add credits to brand balance with transaction record"""
        from decimal import Decimal

        amount = Decimal(str(amount))

        # Add credits
        self.credits_balance += amount
        self.save(update_fields=["credits_balance"])

        # Create transaction record
        CreditTransaction.objects.create(
            brand=self,
            transaction_type=transaction_type,
            amount=amount,  # Positive for addition
            description=description,
            balance_after=self.credits_balance,
        )

        return True, "Credits added successfully"

    def get_credit_history(self, limit=50):
        """Get recent credit transaction history"""
        return self.credit_transactions.all()[:limit]

    class Meta:
        verbose_name_plural = "brands"


class Image(models.Model):
    """Generic image model for brands, users, or other entities"""

    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="images/")
    alt_text = models.CharField(
        max_length=255, blank=True, help_text="Alternative text for accessibility"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="images", null=True, blank=True
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="images", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Image {self.id}"

    class Meta:
        ordering = ["-created_at"]


class BrandAsset(models.Model):
    """Custom assets for brands to use in their social media posts"""

    ASSET_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("gif", "GIF"),
        ("logo", "Logo"),
        ("graphic", "Graphic"),
        ("template", "Template"),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="assets")
    name = models.CharField(max_length=200, help_text="Descriptive name for this asset")
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, default="image")
    file = models.FileField(
        upload_to="brand_assets/", help_text="The asset file (image, video, etc.)"
    )
    thumbnail = models.ImageField(
        upload_to="brand_assets/thumbnails/",
        blank=True,
        null=True,
        help_text="Thumbnail for video assets or custom thumbnails",
    )
    description = models.TextField(
        blank=True, help_text="Optional description or usage notes"
    )
    tags = models.JSONField(
        default=list,
        help_text="Tags for organizing assets (e.g., ['product', 'summer', 'promo'])",
    )
    file_size = models.PositiveIntegerField(
        null=True, blank=True, help_text="File size in bytes"
    )
    width = models.PositiveIntegerField(
        null=True, blank=True, help_text="Image/video width in pixels"
    )
    height = models.PositiveIntegerField(
        null=True, blank=True, help_text="Image/video height in pixels"
    )
    duration = models.FloatField(
        null=True, blank=True, help_text="Video duration in seconds"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether this asset is available for use"
    )
    usage_count = models.PositiveIntegerField(
        default=0, help_text="Number of times this asset has been used in posts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["brand", "name"]

    def __str__(self):
        return f"{self.brand.name} - {self.name}"

    def get_file_url(self):
        """Get the full URL to the asset file"""
        if self.file:
            return self.file.url
        return None

    def get_thumbnail_url(self):
        """Get thumbnail URL, generate one if needed for images"""
        if self.thumbnail:
            return self.thumbnail.url
        elif self.asset_type == "image" and self.file:
            return self.file.url  # Use the image itself as thumbnail
        return None

    def increment_usage(self):
        """Increment usage count when asset is used in a post"""
        self.usage_count += 1
        self.save(update_fields=["usage_count"])

    @property
    def file_extension(self):
        """Get file extension"""
        if self.file:
            import os

            return os.path.splitext(self.file.name)[1].lower()
        return ""

    @property
    def is_image(self):
        """Check if asset is an image"""
        return self.asset_type in [
            "image",
            "logo",
            "graphic",
        ] or self.file_extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]

    @property
    def is_video(self):
        """Check if asset is a video"""
        return self.asset_type == "video" or self.file_extension in [
            ".mp4",
            ".mov",
            ".avi",
            ".webm",
        ]

    def save(self, *args, **kwargs):
        """Override save to extract file metadata"""
        if self.file and not self.file_size:
            self.file_size = self.file.size

            # Extract dimensions for images
            if self.is_image:
                try:
                    from PIL import Image

                    image = Image.open(self.file)
                    self.width, self.height = image.size
                except Exception:
                    pass

            # Extract metadata for videos (optional - requires additional libraries)
            # You can add video metadata extraction here if needed

        super().save(*args, **kwargs)


class Link(models.Model):
    """Generic link model for brands, users, or other entities"""

    LINK_TYPES = [
        ("website", "Website"),
        ("social", "Social Media"),
        ("portfolio", "Portfolio"),
        ("blog", "Blog"),
        ("store", "Store"),
        ("other", "Other"),
    ]

    PLATFORMS = [
        ("website", "Website"),
        ("instagram", "Instagram"),
        ("twitter", "Twitter"),
        ("facebook", "Facebook"),
        ("linkedin", "LinkedIn"),
        ("youtube", "YouTube"),
        ("tiktok", "TikTok"),
        ("pinterest", "Pinterest"),
        ("behance", "Behance"),
        ("dribbble", "Dribbble"),
        ("github", "GitHub"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    url = models.URLField()
    link_type = models.CharField(max_length=20, choices=LINK_TYPES, default="other")
    platform = models.CharField(max_length=20, choices=PLATFORMS, default="other")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="links", null=True, blank=True
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="links", null=True, blank=True
    )
    order = models.PositiveIntegerField(default=0, help_text="Order for display")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.platform}"

    class Meta:
        ordering = ["order", "-created_at"]


# CustomSession model removed - replaced by Django's default sessions and analytics service


class PageView(models.Model):
    """Track page views for analytics"""

    # session field removed - replaced by analytics service
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Page info
    url = models.URLField()
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, default="GET")

    # Request metadata
    referrer = models.URLField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField(null=True, blank=True)  # in milliseconds
    status_code = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["path", "-timestamp"]),
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self):
        user_info = f"by {self.user.username}" if self.user else "anonymous"
        return f"{self.path} - {user_info} at {self.timestamp}"


class WhoisRecord(models.Model):
    """Store WHOIS lookup results for IP addresses"""

    ip_address = models.GenericIPAddressField(unique=True, db_index=True)
    raw_whois_data = models.TextField(blank=True)

    # Parsed WHOIS fields
    organization = models.CharField(max_length=500, blank=True)
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    network_name = models.CharField(max_length=200, blank=True)
    network_range = models.CharField(max_length=100, blank=True)
    asn = models.CharField(max_length=50, blank=True)
    asn_description = models.CharField(max_length=500, blank=True)

    # Metadata
    lookup_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    lookup_successful = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-lookup_date"]
        indexes = [
            models.Index(fields=["ip_address"]),
            models.Index(fields=["country_code", "-lookup_date"]),
            models.Index(fields=["organization", "-lookup_date"]),
            models.Index(fields=["lookup_successful", "-lookup_date"]),
        ]

    def __str__(self):
        return f"WHOIS: {self.ip_address} - {self.organization or 'Unknown'}"

    @classmethod
    def lookup_ip(cls, ip_address):
        """
        Perform WHOIS lookup for an IP address
        Returns existing record if found, otherwise creates new one
        """
        import subprocess
        from django.utils import timezone

        # Check if we already have a recent record (less than 24 hours old)
        try:
            existing = cls.objects.get(ip_address=ip_address)
            if (timezone.now() - existing.last_updated).days < 1:
                return existing
        except cls.DoesNotExist:
            pass

        # Perform WHOIS lookup
        try:
            result = subprocess.run(
                ["whois", ip_address], capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                raw_data = result.stdout

                # Parse common WHOIS fields
                parsed_data = cls._parse_whois_data(raw_data)

                # Create or update record
                record, created = cls.objects.update_or_create(
                    ip_address=ip_address,
                    defaults={
                        "raw_whois_data": raw_data,
                        "lookup_successful": True,
                        "error_message": "",
                        **parsed_data,
                    },
                )
                return record
            else:
                # WHOIS command failed
                record, created = cls.objects.update_or_create(
                    ip_address=ip_address,
                    defaults={
                        "raw_whois_data": result.stderr,
                        "lookup_successful": False,
                        "error_message": result.stderr,
                    },
                )
                return record

        except subprocess.TimeoutExpired:
            record, created = cls.objects.update_or_create(
                ip_address=ip_address,
                defaults={
                    "lookup_successful": False,
                    "error_message": "WHOIS lookup timed out",
                },
            )
            return record
        except Exception as e:
            record, created = cls.objects.update_or_create(
                ip_address=ip_address,
                defaults={
                    "lookup_successful": False,
                    "error_message": str(e),
                },
            )
            return record

    @staticmethod
    def _parse_whois_data(raw_data):
        """Parse raw WHOIS data to extract common fields"""
        import re

        parsed = {}
        lines = raw_data.lower().split("\n")

        # Common patterns for different WHOIS servers
        patterns = {
            "organization": [
                r"org(?:anization)?:\s*(.+)",
                r"orgname:\s*(.+)",
                r"owner:\s*(.+)",
                r"netname:\s*(.+)",
            ],
            "country": [
                r"country:\s*(.+)",
                r"country-code:\s*(.+)",
            ],
            "city": [
                r"city:\s*(.+)",
                r"address:\s*.*,\s*([^,]+),\s*[a-z]{2}",
            ],
            "region": [
                r"state(?:prov)?:\s*(.+)",
                r"region:\s*(.+)",
            ],
            "network_range": [
                r"inetnum:\s*(.+)",
                r"netrange:\s*(.+)",
                r"cidr:\s*(.+)",
            ],
            "asn": [
                r"origin(?:as)?:\s*(as\d+)",
                r"asn:\s*(as\d+)",
            ],
        }

        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                for line in lines:
                    match = re.search(pattern, line.strip())
                    if match:
                        value = match.group(1).strip()
                        if value and value != "-":
                            parsed[field] = value[:500]  # Limit length
                            break
                if field in parsed:
                    break

        # Extract country code if we have country
        if "country" in parsed:
            country_text = parsed["country"]
            # Look for 2-letter country codes
            country_code_match = re.search(r"\b([A-Z]{2})\b", country_text.upper())
            if country_code_match:
                parsed["country_code"] = country_code_match.group(1)

        return parsed


class IPLookupLog(models.Model):
    """Log all IP lookup attempts for monitoring and analytics"""

    ip_address = models.GenericIPAddressField(db_index=True)
    whois_record = models.ForeignKey(
        WhoisRecord, on_delete=models.SET_NULL, null=True, blank=True
    )
    # session field removed - replaced by analytics service
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Lookup metadata
    lookup_timestamp = models.DateTimeField(auto_now_add=True)
    lookup_source = models.CharField(
        max_length=50,
        choices=[
            ("session_tracking", "Session Tracking"),
            ("manual_lookup", "Manual Lookup"),
            ("admin_dashboard", "Admin Dashboard"),
            ("api_request", "API Request"),
        ],
        default="session_tracking",
    )
    lookup_successful = models.BooleanField(default=False)

    class Meta:
        ordering = ["-lookup_timestamp"]
        indexes = [
            models.Index(fields=["ip_address", "-lookup_timestamp"]),
            models.Index(fields=["lookup_source", "-lookup_timestamp"]),
            models.Index(fields=["lookup_successful", "-lookup_timestamp"]),
        ]

    def __str__(self):
        return f"Lookup: {self.ip_address} at {self.lookup_timestamp}"


class TweetConfiguration(models.Model):
    """Configuration for automated tweets"""

    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="tweet_configs"
    )
    name = models.CharField(
        max_length=100, help_text="Name of this tweet configuration"
    )
    prompt_template = models.TextField(
        help_text="Template for generating tweets. Use {topic}, {tone}, {keywords} as placeholders."
    )
    topics = models.JSONField(default=list, help_text="List of topics to tweet about")
    tones = models.JSONField(
        default=list,
        help_text="List of tones to use (e.g., professional, casual, humorous)",
    )
    keywords = models.JSONField(default=list, help_text="List of keywords to include")
    hashtags = models.JSONField(default=list, help_text="List of hashtags to use")
    schedule = models.JSONField(
        default=dict,
        help_text="Schedule configuration (e.g., {'frequency': 'daily', 'time': '09:00', 'days': ['Mon', 'Wed', 'Fri']})",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    class Meta:
        ordering = ["-created_at"]


class Tweet(models.Model):
    """Record of generated and posted tweets"""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("posted", "Posted"),
        ("failed", "Failed"),
    ]

    configuration = models.ForeignKey(
        TweetConfiguration, on_delete=models.CASCADE, related_name="tweets"
    )
    content = models.TextField()
    prompt_used = models.TextField(
        help_text="The actual prompt used to generate this tweet"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    tweet_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Twitter's tweet ID after posting",
    )
    scheduled_for = models.DateTimeField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tweet by {self.configuration.user.username} - {self.status}"

    class Meta:
        ordering = ["-created_at"]

    def post_to_twitter(self):
        """Post the tweet to Twitter using Tweepy"""
        try:
            import tweepy
            from django.utils import timezone

            # Get user from configuration
            user = self.configuration.user

            # Check if user has Twitter API configuration
            if not user.has_twitter_config:
                error_msg = "User does not have Twitter API keys configured"
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg

            # Get Twitter API credentials from user
            auth = tweepy.OAuthHandler(user.twitter_api_key, user.twitter_api_secret)
            auth.set_access_token(
                user.twitter_access_token, user.twitter_access_token_secret
            )

            # Create API object
            api = tweepy.API(auth)

            # Post tweet
            tweet = api.update_status(self.content)

            # Update tweet record
            self.tweet_id = tweet.id_str
            self.status = "posted"
            self.posted_at = timezone.now()
            self.save()

            # Send Slack notification for successful tweet
            self._send_slack_notification()

            return True, None

        except Exception as e:
            self.status = "failed"
            self.error_message = str(e)
            self.save()
            return False, str(e)

    def generate_content(self):
        """Generate tweet content using OpenAI"""
        logger = logging.getLogger(__name__)

        logger.info(f"Starting content generation for Tweet {self.id}")

        try:
            # Import get_openai_client with detailed error handling
            try:
                from website.utils import get_openai_client

                logger.info("Successfully imported get_openai_client in models")
            except ImportError as e:
                logger.error(f"Failed to import get_openai_client in models: {e}")
                raise Exception(f"Import error: {str(e)}. Please contact support.")
            except Exception as e:
                logger.error(
                    f"Unexpected error importing get_openai_client in models: {e}"
                )
                raise Exception(f"Import error: {str(e)}. Please contact support.")

            # Configure OpenAI with detailed logging
            try:
                client = get_openai_client()
                if not client:
                    logger.error(
                        "OpenAI client returned None in models - key not configured"
                    )
                    raise Exception("OpenAI API key is not configured")
                logger.info("OpenAI client created successfully in models")
            except Exception as e:
                if "OpenAI API key" in str(e):
                    raise e  # Re-raise if it's already our custom message
                logger.error(f"Error creating OpenAI client in models: {e}")
                raise Exception(f"Failed to create OpenAI client: {str(e)}")

            # Prepare the prompt
            topic = random.choice(self.configuration.topics)
            tone = random.choice(self.configuration.tones)
            keywords = (
                random.sample(
                    self.configuration.keywords,
                    min(3, len(self.configuration.keywords)),
                )
                if self.configuration.keywords
                else []
            )

            prompt = self.configuration.prompt_template.format(
                topic=topic, tone=tone, keywords=", ".join(keywords)
            )

            # Store the prompt used
            self.prompt_used = prompt

            logger.info(f"Models generating tweet with prompt: {prompt[:100]}...")

            # Generate tweet content
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional social media manager crafting engaging tweets.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.7,
            )

            # Get the generated tweet
            tweet_content = response.choices[0].message.content.strip()
            logger.info(f"Models successfully generated: {tweet_content[:50]}...")

            # Add hashtags
            if self.configuration.hashtags:
                hashtags = random.sample(
                    self.configuration.hashtags,
                    min(3, len(self.configuration.hashtags)),
                )
                tweet_content += "\n\n" + " ".join(hashtags)

            # Update content
            self.content = tweet_content
            self.save()

            logger.info(f"Tweet {self.id} content updated successfully")

            return True, None

        except Exception as e:
            logger.error(f"Failed to generate content for Tweet {self.id}: {str(e)}")
            return False, str(e)

    def _send_slack_notification(self):
        """Send a Slack notification for this tweet using the general notification system"""
        try:
            from .utils.slack_notifications import SlackNotifier

            # Create notification message
            username = self.configuration.user.username
            self.content[:100] + "..." if len(self.content) > 100 else self.content

            # Send to general notification channel
            return SlackNotifier.send_custom_notification(
                title="Tweet Posted",
                details=f"User {username} posted a new tweet",
                severity="info",
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error sending Slack notification for user tweet: {str(e)}")
            return False


class BrandTweet(models.Model):
    """Brand-specific tweets with AI generation and image support"""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("posted", "Posted"),
        ("failed", "Failed"),
    ]

    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="brand_tweets"
    )
    content = models.TextField(blank=True, help_text="Tweet content")
    image = models.ImageField(
        upload_to="brand_tweets/",
        blank=True,
        null=True,
        help_text="Optional image for the tweet",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    tweet_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Twitter's tweet ID after posting",
    )
    tweet_url = models.URLField(
        blank=True,
        null=True,
        help_text="Direct URL to the tweet on Twitter",
    )
    clicks = models.PositiveIntegerField(
        default=0, help_text="Number of clicks/engagement for this tweet"
    )
    # Twitter public metrics
    like_count = models.PositiveIntegerField(
        default=0, help_text="Number of likes on this tweet"
    )
    retweet_count = models.PositiveIntegerField(
        default=0, help_text="Number of retweets of this tweet"
    )
    reply_count = models.PositiveIntegerField(
        default=0, help_text="Number of replies to this tweet"
    )
    quote_count = models.PositiveIntegerField(
        default=0, help_text="Number of quote tweets of this tweet"
    )
    bookmark_count = models.PositiveIntegerField(
        default=0, help_text="Number of bookmarks of this tweet (only for own tweets)"
    )
    metrics_last_updated = models.DateTimeField(
        null=True, blank=True, help_text="Last time metrics were fetched from Twitter"
    )
    scheduled_for = models.DateTimeField(
        null=True, blank=True, help_text="When this tweet should be posted"
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    ai_prompt = models.TextField(
        blank=True, help_text="AI prompt used to generate content"
    )

    # Strategy tracking
    strategy = models.ForeignKey(
        "TweetStrategy",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tweets",
        help_text="Tweet strategy used to generate this tweet",
    )

    # Link tracking
    tracking_link = models.URLField(
        blank=True, null=True, help_text="Unique tracking link for this tweet"
    )
    tracking_token = models.CharField(
        max_length=32,
        blank=True,
        unique=True,
        help_text="Unique token for tracking link clicks",
    )
    link_clicks = models.PositiveIntegerField(
        default=0, help_text="Number of tracking link clicks"
    )

    # Asset management - allows using custom brand assets
    assets = models.ManyToManyField(
        BrandAsset,
        blank=True,
        related_name="tweets",
        help_text="Custom brand assets to include with this tweet",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_for", "-created_at"]

    def __str__(self):
        return f"{self.brand.name} - {self.content[:50]}..."

    def save(self, *args, **kwargs):
        """Override save to ensure unique tracking token is generated"""
        if not self.tracking_token:
            import secrets

            # Generate a unique token that doesn't exist in the database
            max_attempts = 10
            for _ in range(max_attempts):
                token = secrets.token_urlsafe(24)
                if not BrandTweet.objects.filter(tracking_token=token).exists():
                    self.tracking_token = token
                    break
            else:
                # Fallback: use a longer token with timestamp for uniqueness
                import time

                timestamp = str(int(time.time() * 1000))  # milliseconds
                self.tracking_token = f"{secrets.token_urlsafe(16)}_{timestamp}"

        super().save(*args, **kwargs)

    def generate_tracking_token(self):
        """Get or generate a unique tracking token for this tweet"""
        if not self.tracking_token:
            # Token will be auto-generated in save() method
            self.save()
        return self.tracking_token

    def get_tracking_url(self):
        """Get the tracking URL for this tweet"""
        if not self.tracking_token:
            self.generate_tracking_token()
        from django.urls import reverse, NoReverseMatch
        from django.conf import settings
        from .utils.slack_notifications import SlackNotifier
        import logging

        logger = logging.getLogger(__name__)
        base_url = getattr(settings, "SITE_URL", "https://gemnar.com")
        tracking_path = None
        try:
            # Primary attempt (non-namespaced include)
            tracking_path = reverse("track_link", kwargs={"token": self.tracking_token})
        except NoReverseMatch as e1:
            try:
                # Fallback if namespaced
                tracking_path = reverse(
                    "website:track_link", kwargs={"token": self.tracking_token}
                )
            except Exception as e2:
                err_msg = (
                    f"Failed to reverse tracking link for token={self.tracking_token}: "
                    f"primary={e1}; fallback={e2}"
                )
                logger.error(err_msg)
                # Notify Slack (non-fatal: we still return None)
                SlackNotifier.send_error_notification(
                    error_type="TrackingLinkReverseError",
                    error_message=err_msg,
                    request_info=None,
                    user_info=None,
                )
                return None

        if not tracking_path:
            return None
        return f"{base_url}{tracking_path}"

    def increment_link_clicks(self):
        """Increment the link click counter"""
        self.link_clicks += 1
        self.save(update_fields=["link_clicks"])

    def get_thumbnail_url(self):
        """Get thumbnail URL for the image"""
        if self.image:
            return self.image.url
        return None

    def can_be_posted(self):
        """Check if tweet can be posted"""
        return (
            self.status == "approved"
            and self.brand.has_twitter_config
            and bool(self.content.strip())
        )

    @classmethod
    def has_posted_tweets(cls, brand=None):
        """Check if there are any posted tweets for the brand"""
        queryset = cls.objects.filter(status="posted", tweet_id__isnull=False)
        if brand:
            queryset = queryset.filter(brand=brand)
        return queryset.exists()

    def post_to_twitter(self):
        """Post the tweet to Twitter using the brand's API keys"""
        try:
            import tweepy
            from django.utils import timezone

            # Check if tweet can be posted
            if not self.can_be_posted():
                error_msg = "Tweet cannot be posted - missing requirements"
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg

            # Get brand's Twitter configuration
            brand = self.brand

            # Initialize Twitter API client
            client = tweepy.Client(
                bearer_token=brand.twitter_bearer_token,
                consumer_key=brand.twitter_api_key,
                consumer_secret=brand.twitter_api_secret,
                access_token=brand.twitter_access_token,
                access_token_secret=brand.twitter_access_token_secret,
                wait_on_rate_limit=True,
            )

            # Handle media upload if image is present
            media_ids = None
            if self.image:
                try:
                    # Create API v1.1 client for media upload (required for v2 media uploads)
                    api = tweepy.API(
                        tweepy.OAuth1UserHandler(
                            consumer_key=self.brand.twitter_api_key,
                            consumer_secret=self.brand.twitter_api_secret,
                            access_token=self.brand.twitter_access_token,
                            access_token_secret=self.brand.twitter_access_token_secret,
                        ),
                        wait_on_rate_limit=True,
                    )

                    # Upload media using API v1.1
                    media = api.media_upload(filename=self.image.path)
                    media_ids = [media.media_id]
                except Exception as e:
                    self.status = "failed"
                    self.error_message = f"Failed to upload image: {str(e)}"
                    self.save()
                    return False, f"Failed to upload image: {str(e)}"

            try:
                # Post tweet using API v2 with media if present
                response = client.create_tweet(text=self.content, media_ids=media_ids)

                # Update tweet record with success details
                self.tweet_id = response.data["id"]
                self.status = "posted"
                self.posted_at = timezone.now()
                self.save()

                # Send Slack notification if brand has Slack configured
                self._send_slack_notification()

                # Send WebSocket notification for successful post
                self._send_websocket_notification(
                    "tweet_posted",
                    {
                        "tweet_id": self.id,
                        "posted_at": self.posted_at.isoformat(),
                        "tweet_url": self.get_twitter_url(),
                    },
                )

                return True, None
            except tweepy.Unauthorized:
                error_msg = "Twitter API authentication failed"
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg
            except tweepy.Forbidden:
                error_msg = "Twitter API access forbidden"
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg
            except tweepy.TooManyRequests:
                error_msg = "Twitter API rate limit exceeded"
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg
            except Exception as api_error:
                error_msg = f"Twitter API error: {str(api_error)}"
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg

        except Exception as e:
            error_msg = f"Error posting tweet: {str(e)}"
            self.status = "failed"
            self.error_message = error_msg
            self.save()
            return False, error_msg

    def get_twitter_url(self):
        """Generate Twitter URL for this tweet"""
        if self.tweet_id and self.brand.twitter_username:
            return f"https://twitter.com/{self.brand.twitter_username}/status/{self.tweet_id}"
        return None

    def refresh_metrics(self):
        """Refresh Twitter metrics from the API"""
        try:
            import tweepy
            from django.utils import timezone

            # Only refresh metrics for posted tweets with a tweet_id
            if self.status != "posted" or not self.tweet_id:
                return False, "Tweet must be posted and have a tweet_id"

            # Initialize Twitter API client
            client = tweepy.Client(
                bearer_token=self.brand.twitter_bearer_token,
                consumer_key=self.brand.twitter_api_key,
                consumer_secret=self.brand.twitter_api_secret,
                access_token=self.brand.twitter_access_token,
                access_token_secret=self.brand.twitter_access_token_secret,
                wait_on_rate_limit=True,
            )

            # Get tweet metrics
            tweet = client.get_tweet(
                self.tweet_id,
                tweet_fields=["public_metrics", "created_at"],
            )

            if tweet.data:
                metrics = tweet.data.public_metrics
                self.like_count = metrics.get("like_count", 0)
                self.retweet_count = metrics.get("retweet_count", 0)
                self.reply_count = metrics.get("reply_count", 0)
                self.quote_count = metrics.get("quote_count", 0)
                self.bookmark_count = metrics.get("bookmark_count", 0)
                self.metrics_last_updated = timezone.now()
                self.save()
                return True, "Metrics updated successfully"
            else:
                return False, "No metrics data available"

        except Exception as e:
            return False, f"Error fetching metrics: {str(e)}"

    def _send_slack_notification(self):
        """Send a Slack notification for this brand"""
        if not self.brand.has_slack_config:
            return False

        try:
            import requests
            import logging

            logger = logging.getLogger(__name__)

            webhook_url = self.brand.slack_webhook_url
            if not webhook_url:
                return False

            message = {
                "text": f"🐦 New tweet posted for {self.brand.name}!",
                "attachments": [
                    {
                        "color": "good",
                        "fields": [
                            {"title": "Content", "value": self.content, "short": False},
                            {
                                "title": "Posted at",
                                "value": (
                                    self.posted_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                                    if self.posted_at
                                    else "Unknown"
                                ),
                                "short": True,
                            },
                        ],
                    }
                ],
            }

            if self.get_twitter_url():
                message["attachments"][0]["fields"].append(
                    {
                        "title": "Twitter URL",
                        "value": self.get_twitter_url(),
                        "short": True,
                    }
                )

            response = requests.post(webhook_url, json=message, timeout=10)

            if response.status_code == 200:
                logger.info(f"Slack notification sent for brand {self.brand.name}")
                return True
            else:
                logger.error(
                    f"Failed to send Slack notification for brand {self.brand.name}: "
                    f"{response.status_code} - {response.text}"
                )
                return False
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Error sending Slack notification for brand {self.brand.name}: {str(e)}"
            )
            return False


class TweetStrategy(models.Model):
    """Predefined tweet strategies with prompts for content generation"""

    CATEGORY_CHOICES = [
        ("news_trend", "News & Trends"),
        ("product_feature", "Product Features"),
        ("brand_values", "Brand Values"),
        ("engagement", "Engagement"),
        ("educational", "Educational"),
        ("promotional", "Promotional"),
        ("community", "Community Building"),
        ("behind_scenes", "Behind the Scenes"),
        ("user_generated", "User Generated Content"),
        ("industry_insight", "Industry Insights"),
        ("seasonal", "Seasonal/Timely"),
        ("storytelling", "Storytelling"),
    ]

    name = models.CharField(max_length=100, help_text="Name of the tweet strategy")
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        help_text="Category of the tweet strategy",
    )
    description = models.TextField(
        help_text="Description of what this strategy accomplishes"
    )
    prompt_template = models.TextField(
        help_text="AI prompt template for generating tweets using this strategy. Use placeholders like {brand_name}, {brand_values}, {topic}, {competitor}, etc."
    )
    example_output = models.TextField(
        blank=True,
        help_text="Example of what a tweet generated with this strategy might look like",
    )

    # Strategy configuration
    tone_suggestions = models.JSONField(
        default=list,
        help_text="Suggested tones for this strategy (e.g., professional, casual, humorous)",
    )
    hashtag_suggestions = models.JSONField(
        default=list, help_text="Suggested hashtags for this strategy"
    )
    timing_suggestions = models.JSONField(
        default=dict,
        help_text="Suggested timing for this strategy (best times, frequency, etc.)",
    )

    # Meta information
    is_active = models.BooleanField(
        default=True, help_text="Whether this strategy is available for use"
    )
    usage_count = models.PositiveIntegerField(
        default=0, help_text="Number of times this strategy has been used"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]
        verbose_name = "Tweet Strategy"
        verbose_name_plural = "Tweet Strategies"

    def __str__(self):
        return f"{self.get_category_display()}: {self.name}"

    def generate_tweet_for_brand(self, brand, **kwargs):
        """Generate a tweet using this strategy for a specific brand"""
        from django.core.exceptions import ValidationError
        from website.utils import get_openai_client

        formatted_prompt = ""  # Initialize to avoid UnboundLocalError

        try:
            # Get OpenAI client from utils (handles database and fallback logic)
            client = get_openai_client()
            if not client:
                raise ValidationError(
                    "OpenAI API key is missing. Please configure OPENAI_API_KEY in the encrypted variables table."
                )

            # Prepare context variables
            context = {
                "brand_name": brand.name,
                "brand_description": brand.description if brand.description else "",
                **kwargs,  # Additional context passed in
            }

            # Format the prompt template with context
            formatted_prompt = self.prompt_template.format(**context)

            # Generate tweet content using OpenAI
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert social media manager. Generate engaging, authentic tweets that align with the brand's voice and values. Keep tweets under 280 characters and make them actionable and engaging.",
                    },
                    {"role": "user", "content": formatted_prompt},
                ],
                max_tokens=100,
                temperature=0.7,
            )

            tweet_content = response.choices[0].message.content.strip()

            # Update usage count
            self.usage_count += 1
            self.save(update_fields=["usage_count"])

            return {
                "content": tweet_content,
                "strategy_used": self.name,
                "prompt_used": formatted_prompt,
                "success": True,
            }

        except Exception as e:
            return {
                "content": "",
                "strategy_used": self.name,
                "prompt_used": formatted_prompt,
                "success": False,
                "error": str(e),
            }

    def refresh_metrics(self):
        """Refresh Twitter metrics from the API"""
        try:
            import tweepy
            from django.utils import timezone

            # Simple rate limiting: prevent multiple simultaneous calls
            if hasattr(self, "_refreshing_metrics") and self._refreshing_metrics:
                return False, "Metrics refresh already in progress"

            self._refreshing_metrics = True

            try:
                # Only refresh metrics for posted tweets with a tweet_id
                if self.status != "posted" or not self.tweet_id:
                    return False, "Tweet must be posted and have a tweet_id"

                # Check if brand has Twitter configuration
                if not self.brand.has_twitter_config:
                    return False, "Brand does not have Twitter API configuration"

                # Rate limiting: Only refresh if last update was more than 5 minutes ago
                if self.metrics_last_updated:
                    time_since_last_update = timezone.now() - self.metrics_last_updated
                    if time_since_last_update.total_seconds() < 300:  # 5 minutes
                        return False, "Metrics were recently updated, skipping refresh"

                # Create Twitter API v2 client
                client = tweepy.Client(
                    bearer_token=self.brand.twitter_bearer_token,
                    consumer_key=self.brand.twitter_api_key,
                    consumer_secret=self.brand.twitter_api_secret,
                    access_token=self.brand.twitter_access_token,
                    access_token_secret=self.brand.twitter_access_token_secret,
                    wait_on_rate_limit=True,
                )

                # Fetch tweet with public metrics
                tweet = client.get_tweet(
                    id=self.tweet_id, tweet_fields=["public_metrics"]
                )

                if tweet.data and hasattr(tweet.data, "public_metrics"):
                    metrics = tweet.data.public_metrics

                    # Update metrics fields
                    self.like_count = metrics.get("like_count", 0)
                    self.retweet_count = metrics.get("retweet_count", 0)
                    self.reply_count = metrics.get("reply_count", 0)
                    self.quote_count = metrics.get("quote_count", 0)
                    # bookmark_count is only available for your own tweets
                    self.bookmark_count = metrics.get("bookmark_count", 0)
                    self.metrics_last_updated = timezone.now()

                    self.save()
                    return True, "Metrics updated successfully"
                else:
                    return False, "No metrics data available"

            finally:
                # Always clear the flag
                self._refreshing_metrics = False

        except Exception as e:
            # Clear the flag in case of exception
            if hasattr(self, "_refreshing_metrics"):
                self._refreshing_metrics = False
            return False, f"Error fetching metrics: {str(e)}"

    def _send_slack_notification(self):
        """Send a Slack notification for this brand"""
        if not self.brand.has_slack_config:
            return False

        try:
            import requests
            import logging

            logger = logging.getLogger(__name__)

            # Create detailed notification message
            tweet_content = (
                self.content[:150] + "..." if len(self.content) > 150 else self.content
            )
            tweet_url = self.get_twitter_url() or "URL not available"

            message = (
                f"🐦 *New Tweet Posted for {self.brand.name}*\n"
                f"Content: {tweet_content}\n"
                f"Tweet URL: {tweet_url}\n"
                f"Posted at: {self.posted_at.strftime('%Y-%m-%d %H:%M:%S UTC') if self.posted_at else 'Unknown'}"
            )

            # Prepare payload
            payload = {
                "text": message,
                "username": f"Gemnar Bot - {self.brand.name}",
                "icon_emoji": ":bird:",
            }

            # Add channel if specified
            if self.brand.slack_channel:
                payload["channel"] = self.brand.slack_channel

            # Send notification
            response = requests.post(
                self.brand.slack_webhook_url, json=payload, timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Slack notification sent for brand {self.brand.name}")
                return True
            else:
                logger.error(
                    f"Failed to send Slack notification for brand {self.brand.name}: "
                    f"{response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Error sending Slack notification for brand {self.brand.name}: {str(e)}"
            )
            return False


class BrandInstagramPost(models.Model):
    """Brand-specific Instagram posts with AI generation and image support"""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("posted", "Posted"),
        ("failed", "Failed"),
    ]

    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="brand_instagram_posts"
    )
    content = models.TextField(blank=True, help_text="Instagram post caption")
    image = models.ImageField(
        upload_to="brand_instagram_posts/",
        blank=True,
        null=True,
        help_text="Image for the Instagram post",
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Cloudinary URL for the image",
    )
    video = models.FileField(
        upload_to="brand_instagram_posts/videos/",
        blank=True,
        null=True,
        help_text="Video for the Instagram post",
    )
    video_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Cloudinary URL for the video",
    )
    video_thumbnail = models.ImageField(
        upload_to="brand_instagram_posts/video_thumbnails/",
        blank=True,
        null=True,
        help_text="Thumbnail image for the video",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    instagram_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Instagram's post ID after posting",
    )
    instagram_url = models.URLField(
        blank=True,
        null=True,
        help_text="Direct URL to the post on Instagram",
    )
    scheduled_for = models.DateTimeField(
        null=True, blank=True, help_text="When this post should be posted"
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    ai_prompt = models.TextField(
        blank=True, help_text="AI prompt used to generate content"
    )
    video_prompt = models.TextField(
        blank=True, help_text="AI prompt used to generate video content"
    )
    is_video_post = models.BooleanField(
        default=False, help_text="Whether this is a video post"
    )
    video_duration = models.FloatField(
        null=True, blank=True, help_text="Video duration in seconds"
    )
    video_quality = models.CharField(
        max_length=20,
        choices=[("low", "Low"), ("high", "High")],
        default="low",
        help_text="Quality setting for video generation",
    )

    # Video generation async tracking
    video_generation_task_uuid = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="UUID of the video generation task for async processing",
    )
    video_generation_status = models.CharField(
        max_length=20,
        choices=[
            ("none", "None"),
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="none",
        help_text="Status of video generation task",
    )

    # Asset management - allows using custom brand assets
    assets = models.ManyToManyField(
        BrandAsset,
        blank=True,
        related_name="instagram_posts",
        help_text="Custom brand assets to include with this Instagram post",
    )

    # Instagram public metrics
    like_count = models.PositiveIntegerField(
        default=0, help_text="Number of likes on this Instagram post"
    )
    comment_count = models.PositiveIntegerField(
        default=0, help_text="Number of comments on this Instagram post"
    )
    share_count = models.PositiveIntegerField(
        default=0, help_text="Number of shares of this Instagram post"
    )
    reach = models.PositiveIntegerField(
        default=0, help_text="Number of unique accounts that saw this post"
    )
    impressions = models.PositiveIntegerField(
        default=0, help_text="Total number of times this post was seen"
    )
    saved_count = models.PositiveIntegerField(
        default=0, help_text="Number of times this post was saved"
    )
    video_views = models.PositiveIntegerField(
        default=0, help_text="Number of video views (for video posts only)"
    )
    metrics_last_updated = models.DateTimeField(
        null=True, blank=True, help_text="Last time metrics were fetched from Instagram"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_for", "-created_at"]

    def __str__(self):
        return f"{self.brand.name} - {self.content[:50]}..."

    def get_thumbnail_url(self):
        """Get thumbnail URL for the image or video"""
        if self.is_video_post and self.video_thumbnail:
            return self.video_thumbnail.url
        elif self.image:
            return self.image.url
        return None

    def get_media_url(self):
        """Get media URL (video or image)"""
        if self.is_video_post and self.video:
            return self.video.url
        elif self.image:
            return self.image.url
        return None

    def has_media(self):
        """Check if post has media content"""
        if self.is_video_post or self.video or self.video_url:
            return bool(self.video or self.video_url)
        else:
            return bool(self.image or self.image_url)

    def can_be_posted(self):
        """Check if Instagram post can be posted"""
        from django.conf import settings

        # Allow posting if in debug mode or development environment
        is_development = (
            getattr(settings, "DEBUG", False)
            or getattr(settings, "ENVIRONMENT", "") == "development"
        )

        # Check subscription requirement (skip in development)
        has_subscription = is_development or self.brand.stripe_subscription_status in [
            "active",
            "trialing",
        ]

        return (
            self.status == "approved"
            and self.brand.has_instagram_config
            and bool(self.content.strip() or self.has_media())
            and has_subscription
        )

    def post_to_instagram(self):
        """Post this to Instagram using brand's credentials"""
        try:
            import requests
            from django.utils import timezone

            if not self.can_be_posted():
                reasons = []
                if self.status != "approved":
                    reasons.append(f"status is '{self.status}' (needs 'approved')")
                if not self.brand.has_instagram_config:
                    reasons.append("brand missing Instagram configuration")
                if not bool(self.content.strip() or self.has_media()):
                    reasons.append("content and media are both empty")

                error_msg = f"Instagram post cannot be posted: {', '.join(reasons)}"
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg

            # Select the best available access token.
            # Prefer explicit long-lived user token if present; fall back
            # to legacy access token.
            access_token = (
                self.brand.instagram_user_token
                if (
                    self.brand.instagram_user_token
                    and self.brand.instagram_user_token.strip()
                )
                else self.brand.instagram_access_token
            )
            user_id = self.brand.instagram_user_id

            # Validate Instagram credentials before making API calls
            if not access_token or access_token.strip() == "":
                error_msg = (
                    "Instagram access token is missing or empty. "
                    "Please reconnect your Instagram account."
                )
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg

            if not user_id or user_id.strip() == "":
                error_msg = (
                    "Instagram user ID is missing or empty. Please check your "
                    "Instagram account configuration."
                )
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg

            # Detect likely Basic Display API tokens. IGQV tokens are classic Basic Display long-lived tokens.
            # IGAA prefixes are sometimes seen in valid Graph tokens; don't hard fail on IGAA, just note.
            if access_token.startswith("IGQV"):
                # Instead of hard failing, warn (still attempt so user can see detailed 190 error if truly invalid)
                import logging as _logging

                _logging.getLogger(__name__).warning(
                    "Attempting publish with token starting IGQV (likely Basic Display, may fail)."
                )

            # Additional validation for video posts
            if self.is_video_post and self.video:
                # Check video file format and size
                video_name = self.video.name.lower() if self.video.name else ""
                if not (video_name.endswith(".mp4") or video_name.endswith(".mov")):
                    error_msg = (
                        "Unsupported video format. Instagram only supports "
                        f"MP4 and MOV files. Your file: {video_name}"
                    )
                    self.status = "failed"
                    self.error_message = error_msg
                    self.save()
                    return False, error_msg

                # Check video file size (Instagram REELS limit is 300MB)
                if (
                    hasattr(self.video, "size") and self.video.size > 300 * 1024 * 1024
                ):  # 300MB for REELS
                    error_msg = (
                        "Video file too large ("
                        f"{self.video.size / (1024 * 1024):.1f}MB). Instagram "
                        "REELS must be under 300MB."
                    )
                    self.status = "failed"
                    self.error_message = error_msg
                    self.save()
                    return False, error_msg

            # Debug logging for user_id and brand
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                "Instagram posting - Brand: %s (ID: %s)",
                self.brand.name,
                self.brand.id,
            )
            logger.info("Instagram posting - User ID: %s", user_id)
            logger.info(
                "Instagram posting - Access token exists: %s",
                bool(access_token),
            )
            print(
                "DEBUG: Instagram posting - Brand:",
                f"{self.brand.name} (ID: {self.brand.id})",
            )
            print("DEBUG: Instagram posting - User ID:", user_id)
            print(
                "DEBUG: Instagram posting - Access token exists:",
                bool(access_token),
            )

            # Track which token field we are using (explicit user token
            # preferred)
            token_field = (
                "instagram_user_token"
                if self.brand.instagram_user_token
                else "instagram_access_token"
            )

            # Prepare post data
            post_data = {
                "access_token": access_token,
            }

            if self.has_media():
                # For posts with media (image or video), use media endpoint
                # Instagram needs a full absolute URL that it can download
                from django.contrib.sites.models import Site
                from django.conf import settings

                # Build absolute URL for the media
                if self.is_video_post and (self.video or self.video_url):
                    # Prefer Cloudinary URL if available
                    media_url = self.video_url if self.video_url else self.video.url
                    media_type = "video"
                    post_data[
                        "media_type"
                    ] = "REELS"  # Instagram now requires REELS for video
                    # content
                else:
                    # Prefer Cloudinary URL if available
                    media_url = self.image_url if self.image_url else self.image.url
                    media_type = "image"
                    # Do NOT set media_type=IMAGE (Graph infers it). Adding
                    # that param has previously produced generic 100 errors.

                if media_url.startswith("/"):
                    # It's a relative URL, make it absolute
                    try:
                        current_site = Site.objects.get_current()
                        protocol = (
                            "https" if getattr(settings, "USE_TLS", True) else "http"
                        )
                        media_url = f"{protocol}://{current_site.domain}{media_url}"
                    except Exception:
                        # Fallback to manual domain construction
                        domain = getattr(settings, "SITE_DOMAIN", "gemnar.com")
                        media_url = f"https://{domain}{media_url}"

                if self.is_video_post:
                    post_data["video_url"] = media_url
                else:
                    post_data["image_url"] = media_url
                if self.content:
                    post_data["caption"] = self.content

                # Add debugging for the media URL
                import logging

                logger = logging.getLogger(__name__)
                logger.info("Instagram posting - Media URL: %s", media_url)
                logger.info("Instagram posting - Media type: %s", media_type)
                logger.info(
                    "Instagram posting - Post data keys: %s",
                    list(post_data.keys()),
                )
                logger.info(
                    "Instagram posting - Brand: %s (ID: %s)",
                    self.brand.name,
                    self.brand.id,
                )
                logger.info(
                    "Instagram posting - Content length: %s",
                    len(self.content),
                )

                # Test if Instagram can access the media
                try:
                    # Use a User-Agent that Instagram accepts
                    headers = {
                        "User-Agent": (
                            "Mozilla/5.0 (compatible; InstagramBot/1.0; "
                            "+http://www.instagram.com/)"
                        ),
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate",
                        "Connection": "keep-alive",
                    }
                    test_response = requests.head(
                        media_url,
                        timeout=15,
                        headers=headers,
                        allow_redirects=True,
                    )
                    print(
                        "DEBUG: Media URL test - Status:",
                        test_response.status_code,
                    )
                    print(
                        "DEBUG: Media URL test - Headers:",
                        dict(test_response.headers),
                    )

                    # Accept 200, 301, 302 as valid responses
                    if test_response.status_code not in [200, 301, 302]:
                        # Try with GET request if HEAD fails
                        try:
                            test_response = requests.get(
                                media_url,
                                timeout=15,
                                headers=headers,
                                allow_redirects=True,
                                stream=True,
                            )
                            # Read only first 1KB to check if it's accessible
                            next(test_response.iter_content(1024), None)
                            test_response.close()
                            print(
                                "DEBUG: Media URL GET test - Status:",
                                test_response.status_code,
                            )

                            if test_response.status_code not in [
                                200,
                                301,
                                302,
                            ]:
                                error_msg = (
                                    "Media URL not accessible (status "
                                    f"{test_response.status_code}): {media_url}"
                                )
                                self.status = "failed"
                                self.error_message = error_msg
                                self.save()
                                return False, error_msg
                        except Exception as get_error:
                            error_msg = (
                                "Media URL not accessible (HEAD: "
                                f"{test_response.status_code}, GET failed: "
                                f"{get_error}): {media_url}"
                            )
                            self.status = "failed"
                            self.error_message = error_msg
                            self.save()
                            return False, error_msg

                    # Check content type
                    content_type = test_response.headers.get("content-type", "")

                    if self.is_video_post:
                        if not content_type.startswith("video/"):
                            error_msg = (
                                "Video URL doesn't return video content type "
                                f"(got {content_type}): {media_url}"
                            )
                            self.status = "failed"
                            self.error_message = error_msg
                            self.save()
                            return False, error_msg

                        # Check if it's a supported video format for Instagram
                        supported_types = [
                            "video/mp4",
                            "video/quicktime",
                            "video/avi",
                        ]
                        if content_type not in supported_types:
                            error_msg = (
                                "Video format not supported by Instagram (got "
                                f"{content_type}, need MP4/MOV): {media_url}"
                            )
                            self.status = "failed"
                            self.error_message = error_msg
                            self.save()
                            return False, error_msg
                    else:
                        if not content_type.startswith("image/"):
                            error_msg = (
                                "Image URL doesn't return image content type "
                                f"(got {content_type}): {media_url}"
                            )
                            self.status = "failed"
                            self.error_message = error_msg
                            self.save()
                            return False, error_msg

                        # Check if it's a supported image format for Instagram
                        supported_types = [
                            "image/jpeg",
                            "image/jpg",
                            "image/png",
                        ]
                        if content_type not in supported_types:
                            error_msg = (
                                "Image format not supported by Instagram (got "
                                f"{content_type}, need JPEG/PNG): {media_url}"
                            )
                            self.status = "failed"
                            self.error_message = error_msg
                            self.save()
                            return False, error_msg

                except requests.exceptions.RequestException as e:
                    error_msg = f"Cannot access media URL {media_url}: {str(e)}"
                    self.status = "failed"
                    self.error_message = error_msg
                    self.save()
                    return False, error_msg

                # Create media container. Use graph.instagram.com first
                # (previously working configuration for this project),
                # fallback to graph.facebook.com only if we hit token /
                # parameter style errors.
                api_version = "v18.0"
                graph_bases = [
                    "https://graph.instagram.com",  # primary
                    "https://graph.facebook.com",  # fallback
                ]
                chosen_base = graph_bases[0]
                container_url = f"{chosen_base}/{api_version}/{user_id}/media"

                # -----------------------------------------------------------
                # Preflight: Validate the Instagram Business Account ID before
                # attempting container creation. Error 100/33 often means the
                # ID is not an IG Business Account ID or token lacks access.
                # -----------------------------------------------------------
                try:
                    preflight_url = f"{chosen_base}/{api_version}/{user_id}"
                    preflight_params = {
                        "fields": "id,username,account_type",
                        "access_token": access_token,
                    }
                    pre_resp = requests.get(
                        preflight_url, params=preflight_params, timeout=10
                    )
                    print(
                        "DEBUG: Preflight user validation status:", pre_resp.status_code
                    )
                    if pre_resp.status_code != 200:
                        # Previously this was a HARD FAILURE that stopped posting.
                        # That created regressions for accounts that could
                        # create media containers despite this lookup failing
                        # (transient perms, propagation delay, partial perms).
                        # We now LOG & WARN only.
                        diag = []
                        try:
                            pj = pre_resp.json()
                            diag.append(f"Graph error: {pj}")
                            if isinstance(pj, dict) and "error" in pj:
                                errd = pj["error"]
                                diag.append(
                                    "Code:{c} Sub:{s} Msg:{m}".format(
                                        c=errd.get("code"),
                                        s=errd.get("error_subcode"),
                                        m=errd.get("message"),
                                    )
                                )
                        except Exception:
                            diag.append(f"Raw body: {pre_resp.text[:400]}")

                        suggestions = [
                            "(Preflight warn) instagram_user_id must be IG Business "
                            "Acct ID (numeric from FB Page).",
                            "(Preflight warn) Do NOT use Page ID, personal FB user ID "
                            "or IG username.",
                            "(Preflight warn) Token needs instagram_basic + "
                            "instagram_content_publish perms.",
                            "(Preflight warn) If perms just granted re-gen the token.",
                            "(Preflight warn) Ensure app is Live for prod accounts.",
                        ]
                        warning_msg = (
                            "WARN: Preflight IG user validation failed (continuing). "
                            + " | ".join(diag)
                            + "\n"
                            + "\n".join([f"- {s}" for s in suggestions])
                        )
                        # Do NOT change status here; stash warning for later use.
                        print(warning_msg)
                        # Append to existing error_message so final failure shows it.
                        if not getattr(self, "error_message", None):
                            self.error_message = warning_msg
                        else:
                            if warning_msg not in self.error_message:
                                self.error_message += "\n\n" + warning_msg
                        # No early return – proceed to container creation.
                except Exception as preflight_exc:
                    print(f"DEBUG: Preflight validation exception: {preflight_exc}")
                    # Continue; container creation may still reveal info

                # Add extra debugging for video posts
                if self.is_video_post:
                    print("DEBUG: VIDEO POST - Comprehensive debugging info:")
                    print(f"  Instagram API URL: {container_url}")
                    print(f"  User ID: {user_id}")
                    print(f"  Post data keys: {list(post_data.keys())}")
                    print(f"  Post data: {post_data}")

                    # Video file details
                    if self.video:
                        print(f"  Video file name: {self.video.name}")
                        print(
                            "  Video file size: "
                            f"{self.video.size} bytes ("
                            f"{self.video.size / (1024 * 1024):.2f} MB)"
                        )
                        print(f"  Video URL: {self.video.url}")
                        print(
                            "  Video field content type: "
                            f"{getattr(self.video, 'content_type', 'Unknown')}"
                        )

                        # Check if we can get more file info
                        try:
                            import os

                            video_path = (
                                self.video.path if hasattr(self.video, "path") else None
                            )
                            if video_path and os.path.exists(video_path):
                                print("  Video file exists on disk: Yes")
                                print(
                                    "  Actual file size on disk: "
                                    f"{os.path.getsize(video_path)} bytes"
                                )
                            else:
                                print(
                                    "  Video file exists on disk: No or path "
                                    "not available"
                                )
                        except Exception as e:
                            print(f"  Could not check video file on disk: {e}")
                    else:
                        print("  Video file: None")

                    # Media URL details
                    print(f"  Absolute media URL: {media_url}")
                    print(f"  Media URL length: {len(media_url)}")

                    # Brand details
                    print(f"  Brand: {self.brand.name} (ID: {self.brand.id})")
                    print(
                        "  Brand has Instagram config: "
                        f"{self.brand.has_instagram_config}"
                    )

                    # Post configuration
                    print(
                        f"  Content length: {len(self.content) if self.content else 0}"
                    )
                    print(f"  is_video_post flag: {self.is_video_post}")
                    print(f"  has_media(): {self.has_media()}")
                    print(f"  can_be_posted(): {self.can_be_posted()}")

                container_response = requests.post(container_url, data=post_data)

                # If first attempt failed with likely domain-related error, try fallback base
                if (
                    container_response.status_code != 200
                    and chosen_base == graph_bases[0]
                    and len(graph_bases) > 1
                ):
                    try:
                        err_json = container_response.json()
                        err_code = (
                            err_json.get("error", {}).get("code")
                            if isinstance(err_json, dict)
                            else None
                        )
                    except Exception:  # noqa: BLE001
                        err_code = None
                    # Retry for generic parameter (100) or token (190) errors
                    if err_code in [100, 190, None]:
                        fallback_base = graph_bases[1]
                        fallback_url = f"{fallback_base}/{api_version}/{user_id}/media"
                        print(
                            f"DEBUG: Retrying container creation with fallback domain {fallback_base}"
                        )
                        fb_resp = requests.post(fallback_url, data=post_data)
                        if fb_resp.status_code == 200:
                            container_response = fb_resp
                            chosen_base = fallback_base
                            container_url = fallback_url
                            print(f"DEBUG: Fallback domain succeeded ({fallback_base})")
                        else:
                            print(
                                f"DEBUG: Fallback domain failed ({fallback_base}) status {fb_resp.status_code}"
                            )

                print(
                    "DEBUG: Container response status:",
                    container_response.status_code,
                )
                print(
                    "DEBUG: Container response text:",
                    container_response.text,
                )

                # Additional debugging for failed responses
                if container_response.status_code != 200:
                    print("DEBUG: DETAILED ERROR ANALYSIS:")
                    try:
                        error_data = container_response.json()
                        print(f"  Full error response: {error_data}")
                        if "error" in error_data:
                            error_detail = error_data["error"]
                            print(
                                f"  Error code: {error_detail.get('code', 'unknown')}"
                            )
                            print(
                                "  Error subcode: "
                                f"{error_detail.get('error_subcode', 'unknown')}"
                            )
                            print(
                                "  Error message: "
                                f"{error_detail.get('message', 'unknown')}"
                            )
                            print(
                                f"  Error type: {error_detail.get('type', 'unknown')}"
                            )
                            print(
                                "  Error user title: "
                                f"{error_detail.get('error_user_title', 'unknown')}"
                            )
                            print(
                                "  Error user msg: "
                                f"{error_detail.get('error_user_msg', 'unknown')}"
                            )
                            print(
                                "  Facebook trace ID: "
                                f"{error_detail.get('fbtrace_id', 'unknown')}"
                            )
                    except Exception as e:
                        print(f"  Could not parse error response as JSON: {e}")
                        print(
                            "  Raw response headers: "
                            f"{dict(container_response.headers)}"
                        )
                        print(
                            "  Raw response content: "
                            f"{container_response.content[:500]}..."
                        )

                retry_attempted = False
                original_token_used = access_token
                if container_response.status_code != 200:
                    # Enhanced error handling for Instagram API errors
                    error_msg = "Failed to create media container"
                    try:
                        error_data = container_response.json()
                        if "error" in error_data:
                            error_detail = error_data["error"]
                            error_code = error_detail.get("code", "unknown")
                            error_subcode = error_detail.get("error_subcode", "unknown")
                            error_message = error_detail.get(
                                "message", "Unknown Instagram API error"
                            )
                            error_user_msg = error_detail.get("error_user_msg", "")

                            # Provide specific guidance based on error codes
                            if error_code == 190:
                                error_msg = (
                                    "Access token is invalid or expired. "
                                    "Please refresh your Instagram "
                                    "connection."
                                )
                                # Verbose diagnostics for token issues
                                try:
                                    import json as _json

                                    debug_payload = dict(post_data)
                                    # Avoid duplicating huge token in both places
                                    # Keep original in token_value field below
                                    debug_payload["access_token"] = "<omitted>"
                                    debug_info = {
                                        "token_field": token_field,
                                        "token_value": access_token,
                                        "api_endpoint": container_url,
                                        "http_status": container_response.status_code,
                                        "request_payload": debug_payload,
                                        "response_json": error_detail,
                                        "response_raw": container_response.text,
                                    }
                                    error_msg += (
                                        "\n\n[DEBUG TOKEN INFO]\n"
                                        + _json.dumps(debug_info, indent=2)[:4000]
                                    )
                                except Exception as _e:  # noqa: BLE001
                                    error_msg += (
                                        "\n\n[DEBUG TOKEN INFO] Failed to build "
                                        f"debug info: {_e}"
                                    )
                                # Attempt retry with alternate token if available and not yet tried
                                alt_token = None
                                if (
                                    token_field == "instagram_user_token"
                                    and self.brand.instagram_access_token
                                    and self.brand.instagram_access_token.strip()
                                ):
                                    alt_token = self.brand.instagram_access_token
                                elif (
                                    token_field == "instagram_access_token"
                                    and self.brand.instagram_user_token
                                    and self.brand.instagram_user_token.strip()
                                ):
                                    alt_token = self.brand.instagram_user_token
                                if alt_token and alt_token != access_token:
                                    retry_attempted = True
                                    access_token = alt_token
                                    token_field = (
                                        "instagram_user_token"
                                        if token_field == "instagram_access_token"
                                        else "instagram_access_token"
                                    )
                                    post_data["access_token"] = access_token
                                    import logging as _logging

                                    _logging.getLogger(__name__).warning(
                                        f"Retrying container creation with alternate token field {token_field}."
                                    )
                                    container_response = requests.post(
                                        container_url, data=post_data
                                    )
                                    print(
                                        "DEBUG: Container response (retry) status: "
                                        f"{container_response.status_code}"
                                    )
                                    print(
                                        "DEBUG: Container response (retry) text: "
                                        f"{container_response.text}"
                                    )
                                    if container_response.status_code == 200:
                                        # Clear previous failure context
                                        error_msg = None
                                    else:
                                        # Reparse error details for retry attempt
                                        try:
                                            error_data = container_response.json()
                                            if "error" in error_data:
                                                error_detail = error_data["error"]
                                                error_code = error_detail.get(
                                                    "code", "unknown"
                                                )
                                                error_subcode = error_detail.get(
                                                    "error_subcode", "unknown"
                                                )
                                                error_message = error_detail.get(
                                                    "message",
                                                    "Unknown Instagram API error",
                                                )
                                        except Exception:
                                            pass
                            elif error_code == 100:
                                # Error code 100 = invalid parameter. Provide nuanced guidance.
                                if self.is_video_post:
                                    # Provide detailed analysis for video Error 100
                                    video_size = self.video.size if self.video else 0
                                    video_name = (
                                        self.video.name if self.video else "No video"
                                    )

                                    # Create detailed error message with subcode analysis
                                    subcode_analysis = ""
                                    if error_subcode != "unknown":
                                        subcode_meanings = {
                                            "2207023": "Unknown media type - media_type field issue (VIDEO deprecated, use REELS)",
                                            "2207026": "Unsupported video format - must be MOV or MP4 with proper encoding",
                                            "2207052": "Media could not be fetched from URL - URL accessibility issue",
                                            "2207004": "File too large - must be under 8MB for images, 300MB for REELS",
                                            "2207027": "Media not ready for publishing - video still processing, try again later",
                                            "2207053": "Unknown upload error - video encoding or format issue",
                                            "100": "Invalid parameter - often caused by deprecated VIDEO media_type",
                                        }
                                        subcode_analysis = subcode_meanings.get(
                                            str(error_subcode),
                                            f"Unknown subcode: {error_subcode}",
                                        )

                                    error_details = [
                                        f"Instagram video upload failed (Error {error_code})",
                                        (
                                            f"Subcode: {error_subcode} - {subcode_analysis}"
                                            if subcode_analysis
                                            else f"Subcode: {error_subcode}"
                                        ),
                                        f"User ID: {user_id}",
                                        f"Video file: {video_name}",
                                        (
                                            f"Video size: {video_size / (1024 * 1024):.2f} MB"
                                            if video_size
                                            else "Unknown size"
                                        ),
                                        f"Media URL: {media_url if 'media_url' in locals() else 'Not available'}",
                                        f"Instagram error message: {error_message}",
                                        (
                                            f"Instagram user message: {error_user_msg}"
                                            if error_user_msg
                                            else ""
                                        ),
                                        "",
                                        "Common causes for Error 100 with video uploads (REELS):",
                                        "1. Video format not supported (must be MP4 or MOV)",
                                        "2. Video encoding not compatible (must be H.264/AAC)",
                                        "3. Video too large (must be under 300MB for REELS)",
                                        "4. Video duration invalid (3 seconds to 15 minutes for REELS)",
                                        "5. Media URL not accessible by Instagram servers",
                                        "6. Video file corrupted or incomplete",
                                        "7. Invalid video specifications (framerate >60fps, wrong aspect ratio)",
                                        "8. Video bitrate too high (max 25Mbps)",
                                        "9. REELS-specific requirements not met (9:16 aspect ratio recommended)",
                                    ]
                                    error_msg = "\n".join(error_details)
                                else:
                                    # Inspect message to tailor advice
                                    lower_msg = (
                                        error_message.lower()
                                        if isinstance(error_message, str)
                                        else ""
                                    )
                                    hints = [
                                        "Parameter issue (Error 100). Common causes:",
                                        "1. Using Instagram USERNAME instead of Business Account ID.",
                                        "2. Token lacks instagram_content_publish permission.",
                                        "3. media_type param not expected (removed now).",
                                        "4. Media URL inaccessible or not publicly resolvable.",
                                        "5. Caption contains disallowed characters or too long.",
                                        "6. Wrong type of token (Basic Display vs Graph).",
                                    ]
                                    # Attempt token permission introspection if app credentials available
                                    try:
                                        if (
                                            getattr(
                                                self.brand, "instagram_app_id", None
                                            )
                                            and getattr(
                                                self.brand, "instagram_app_secret", None
                                            )
                                            and access_token
                                        ):
                                            app_token = f"{self.brand.instagram_app_id}|{self.brand.instagram_app_secret}"
                                            debug_url = (
                                                "https://graph.facebook.com/debug_token"
                                            )
                                            dbg_params = {
                                                "input_token": access_token,
                                                "access_token": app_token,
                                            }
                                            dbg_resp = requests.get(
                                                debug_url, params=dbg_params, timeout=10
                                            )
                                            if dbg_resp.status_code == 200:
                                                dbg_json = dbg_resp.json()
                                                data = dbg_json.get("data", {})
                                                scopes = data.get("scopes", [])
                                                if (
                                                    "instagram_content_publish"
                                                    not in scopes
                                                ):
                                                    hints.append(
                                                        "(Token introspection) instagram_content_publish missing from token scopes."
                                                    )
                                                else:
                                                    hints.append(
                                                        "(Token introspection) instagram_content_publish present in token scopes."
                                                    )
                                                hints.append(
                                                    f"(Token introspection) scopes: {', '.join(scopes)[:300]}"
                                                )
                                            else:
                                                hints.append(
                                                    "Could not introspect token (debug_token call failed)"
                                                )
                                    except Exception as dbg_e:  # noqa: BLE001
                                        hints.append(
                                            f"Token introspection exception: {dbg_e}"
                                        )
                                    if "user id" in lower_msg or "user" in lower_msg:
                                        hints.insert(1, f"User ID provided: {user_id}")
                                    error_msg = (
                                        f"Instagram API parameter error (100/{error_subcode}): {error_message}\n"
                                        + "\n".join(hints)
                                    )
                            elif error_code == 104:
                                error_msg = "Instagram API rate limit exceeded. Please try again later."
                            elif error_code == 9007:
                                error_msg = f"Instagram media not ready for publishing (Error {error_code}). The video is still being processed. Please wait a few minutes and try again."
                            elif error_code == 1:
                                error_msg = "Instagram API error. Please check your app permissions and configuration."
                            elif error_code == 10:
                                error_msg = "Instagram API permissions error. Your app may not have the required permissions."
                            else:
                                error_msg = (
                                    f"Instagram API error {error_code}: {error_message}"
                                )
                    except (ValueError, KeyError):
                        error_msg = f"Failed to create media container: {container_response.text}"

                    if error_msg:  # Only fail if still an error after possible retry
                        # Attach debug block summarizing both attempts if retry happened
                        try:
                            if retry_attempted:
                                import json as _json

                                debug_block = {
                                    "initial_token_field": (
                                        "instagram_user_token"
                                        if original_token_used
                                        == self.brand.instagram_user_token
                                        else "instagram_access_token"
                                    ),
                                    "retried_with": token_field,
                                    "initial_token_prefix": (
                                        original_token_used[:8]
                                        if original_token_used
                                        else None
                                    ),
                                    "retry_token_prefix": (
                                        access_token[:8] if access_token else None
                                    ),
                                    "container_status": container_response.status_code,
                                }
                                error_msg += "\n\n[RETRY DEBUG]\n" + _json.dumps(
                                    debug_block, indent=2
                                )
                        except Exception:
                            pass
                        self.status = "failed"
                        self.error_message = error_msg
                        self.save()
                        return False, error_msg

                # Parse JSON response safely
                try:
                    container_data = container_response.json()
                except ValueError:
                    error_msg = f"Invalid JSON response from Instagram API: {container_response.text}"
                    self.status = "failed"
                    self.error_message = error_msg
                    self.save()
                    return False, error_msg
                creation_id = container_data.get("id")

                # For video posts, we need to wait for Instagram to finish processing
                if self.is_video_post:
                    print(f"DEBUG: Video container created with ID: {creation_id}")
                    print("DEBUG: Checking container status before publishing...")

                    # Check container status until it's ready
                    max_attempts = 30  # Wait up to 5 minutes (30 attempts * 10 seconds)
                    attempt = 0
                    container_ready = False

                    while attempt < max_attempts and not container_ready:
                        # Check container status
                        status_url = f"{chosen_base}/{api_version}/{creation_id}"
                        status_params = {
                            "fields": "status_code",
                            "access_token": access_token,
                        }

                        try:
                            status_response = requests.get(
                                status_url, params=status_params
                            )
                            print(
                                f"DEBUG: Status check attempt {attempt + 1}: HTTP {status_response.status_code}"
                            )

                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                container_status = status_data.get(
                                    "status_code", "unknown"
                                )
                                print(f"DEBUG: Container status: {container_status}")

                                if container_status == "FINISHED":
                                    container_ready = True
                                    print("DEBUG: Container is ready for publishing!")
                                    break
                                elif container_status == "ERROR":
                                    error_msg = "Instagram video processing failed. Container status: ERROR"
                                    self.status = "failed"
                                    self.error_message = error_msg
                                    self.save()
                                    return False, error_msg
                                else:
                                    # Status is IN_PROGRESS or similar, wait and retry
                                    print(
                                        f"DEBUG: Container still processing (status: {container_status}), waiting 10 seconds..."
                                    )
                                    import time

                                    time.sleep(10)
                            else:
                                print(
                                    f"DEBUG: Status check failed: {status_response.text}"
                                )
                                import time

                                time.sleep(10)

                        except Exception as e:
                            print(f"DEBUG: Status check error: {e}")
                            import time

                            time.sleep(10)

                        attempt += 1

                    if not container_ready:
                        error_msg = f"Instagram video processing timeout. Container not ready after {max_attempts} attempts (5 minutes). This may be due to large file size or Instagram server issues."
                        self.status = "failed"
                        self.error_message = error_msg
                        self.save()
                        return False, error_msg

                # Publish the media (container is ready)
                print(f"DEBUG: Publishing media with container ID: {creation_id}")
                publish_data = {
                    "creation_id": creation_id,
                    "access_token": access_token,
                }
                publish_url = f"{chosen_base}/{api_version}/{user_id}/media_publish"
                publish_response = requests.post(publish_url, data=publish_data)

                print(f"DEBUG: Publish response status: {publish_response.status_code}")
                print(f"DEBUG: Publish response text: {publish_response.text}")

                if publish_response.status_code == 200:
                    try:
                        publish_data = publish_response.json()
                    except ValueError:
                        error_msg = f"Instagram API returned invalid JSON: {publish_response.text}"
                        print(f"ERROR: {error_msg}")
                        self.status = "failed"
                        self.error_message = error_msg
                        self.save()
                        return False, error_msg

                    print(f"DEBUG: Publish response JSON: {publish_data}")

                    # Check for Instagram API errors even with 200 status
                    if "error" in publish_data:
                        error_detail = publish_data["error"]
                        error_msg = f"Instagram API error: {error_detail.get('message', 'Unknown error')}"
                        print(f"ERROR: {error_msg}")
                        self.status = "failed"
                        self.error_message = error_msg
                        self.save()
                        return False, error_msg

                    instagram_id = publish_data.get("id")
                    print(f"DEBUG: Instagram ID from response: {instagram_id}")

                    # Validate Instagram ID before proceeding
                    if not instagram_id:
                        error_msg = f"Instagram API returned success but no media ID. Response: {publish_data}"
                        print(f"ERROR: {error_msg}")
                        self.status = "failed"
                        self.error_message = error_msg
                        self.save()
                        return False, error_msg

                    # Validate Instagram ID format (should be numeric)
                    try:
                        int(instagram_id)
                    except (ValueError, TypeError):
                        error_msg = f"Instagram API returned invalid media ID format: {instagram_id}"
                        print(f"ERROR: {error_msg}")
                        self.status = "failed"
                        self.error_message = error_msg
                        self.save()
                        return False, error_msg

                    # Ensure Instagram ID is a string
                    instagram_id = str(instagram_id)

                    # Verify the post actually exists by fetching it back from Instagram
                    verify_url = f"{chosen_base}/{api_version}/{instagram_id}"
                    verify_params = {
                        "fields": "id,permalink,media_type",
                        "access_token": access_token,
                    }

                    print(
                        f"DEBUG: Verifying Instagram post exists for ID: {instagram_id}"
                    )
                    verify_response = requests.get(
                        verify_url, params=verify_params, timeout=10
                    )

                    if verify_response.status_code != 200:
                        try:
                            verify_error = verify_response.json()
                            error_msg = f"Instagram post verification failed: {verify_error.get('error', {}).get('message', 'Post not found after creation')}"
                        except (ValueError, KeyError, TypeError):
                            error_msg = f"Instagram post verification failed (status {verify_response.status_code}): Post may not have been created successfully"

                        print(f"ERROR: {error_msg}")
                        self.status = "failed"
                        self.error_message = error_msg
                        self.save()
                        return False, error_msg

                    verify_data = verify_response.json()
                    print(f"DEBUG: Post verification successful: {verify_data}")

                    # Get the permalink from Instagram API
                    permalink_url = f"{chosen_base}/{api_version}/{instagram_id}"
                    permalink_params = {
                        "fields": "permalink",
                        "access_token": access_token,
                    }

                    print(f"DEBUG: Fetching permalink for Instagram ID: {instagram_id}")
                    permalink_response = requests.get(
                        permalink_url, params=permalink_params
                    )

                    instagram_url = None
                    if permalink_response.status_code == 200:
                        permalink_data = permalink_response.json()
                        instagram_url = permalink_data.get("permalink")
                        print(f"DEBUG: Got Instagram URL: {instagram_url}")
                    else:
                        print(
                            f"DEBUG: Failed to get permalink: {permalink_response.status_code} - {permalink_response.text}"
                        )
                        # Don't fail the whole process if permalink fails, but log it
                        instagram_url = f"https://www.instagram.com/p/{instagram_id}/"

                    # Update post record with actual data
                    self.instagram_id = instagram_id
                    self.instagram_url = instagram_url
                    self.status = "posted"
                    self.posted_at = timezone.now()

                    print(
                        f"DEBUG: About to save post {self.id} with instagram_id='{instagram_id}' and instagram_url='{instagram_url}'"
                    )

                    try:
                        self.save()
                        print(f"DEBUG: Successfully saved post {self.id}")
                        print(
                            f"DEBUG: Saved values - instagram_id='{self.instagram_id}', instagram_url='{self.instagram_url}', status='{self.status}'"
                        )
                    except Exception as save_error:
                        error_msg = f"Failed to save Instagram post to database: {str(save_error)}"
                        print(f"ERROR: {error_msg}")
                        # Try to save at least the error
                        self.status = "failed"
                        self.error_message = error_msg
                        try:
                            self.save()
                        except Exception as final_error:
                            print(
                                f"ERROR: Could not even save error message: {final_error}"
                            )
                        return False, error_msg

                    # Send WebSocket notification for successful post
                    self._send_websocket_notification(
                        "instagram_post_posted",
                        {
                            "post_id": self.id,
                            "posted_at": self.posted_at.isoformat(),
                            "instagram_url": self.instagram_url,
                            "instagram_id": self.instagram_id,
                        },
                    )

                    return True, None
                else:
                    # Enhanced error handling for publish failures
                    error_msg = f"Failed to publish media: {publish_response.text}"
                    try:
                        error_data = publish_response.json()
                        if "error" in error_data:
                            error_detail = error_data["error"]
                            error_code = error_detail.get("code", "unknown")
                            error_subcode = error_detail.get("error_subcode", "unknown")
                            error_message = error_detail.get("message", "Unknown error")

                            if error_code == 9007 and error_subcode == 2207027:
                                error_msg = f"Instagram media not ready for publishing (Error {error_code}/{error_subcode}). The video may still be processing. Please try again in a few minutes."
                            else:
                                error_msg = f"Instagram publish failed (Error {error_code}/{error_subcode}): {error_message}"
                    except (ValueError, KeyError, TypeError):
                        pass  # Use the original error message

                    # Attempt to enrich publish failure with token info if token error
                    try:
                        if "error" in publish_data:
                            err_d = publish_data["error"]
                            if err_d.get("code") == 190:
                                import json as _json

                                debug_info_pub = {
                                    "token_field": token_field,
                                    "token_value": access_token,
                                    "publish_endpoint": publish_url,
                                    "http_status": publish_response.status_code,
                                    "request_payload": {
                                        "creation_id": publish_data.get("id"),
                                        "access_token": "<omitted>",
                                    },
                                    "response_json": err_d,
                                    "response_raw": publish_response.text,
                                }
                                error_msg += (
                                    "\n\n[DEBUG TOKEN INFO]\n"
                                    + _json.dumps(debug_info_pub, indent=2)[:4000]
                                )
                    except Exception as _e:  # noqa: BLE001
                        error_msg += (
                            f"\n[DEBUG TOKEN INFO] Failed to append publish debug: {_e}"
                        )

                    self.status = "failed"
                    self.error_message = error_msg
                    self.save()
                    return False, error_msg
            else:
                # Text-only posts (stories or reels might be needed)
                error_msg = "Text-only Instagram posts are not supported. Please add an image or video."
                self.status = "failed"
                self.error_message = error_msg
                self.save()
                return False, error_msg

        except Exception as e:
            self.status = "failed"
            self.error_message = str(e)
            self.save()

            # Send WebSocket notification for failed post
            self._send_websocket_notification(
                "instagram_post_failed",
                {
                    "post_id": self.id,
                    "error_message": str(e),
                },
            )

            return False, str(e)

    def _send_websocket_notification(self, event_type, data):
        """Send WebSocket notification to all connected clients"""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                room_group_name = (
                    f"instagram_queue_{self.brand.organization.pk}_{self.brand.pk}"
                )

                # Send real-time update to all connected clients
                async_to_sync(channel_layer.group_send)(
                    room_group_name, {"type": event_type, **data}
                )
        except Exception as e:
            # Don't fail the main operation if WebSocket fails
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send WebSocket notification: {e}")

    def get_instagram_url(self):
        """Get the Instagram URL for this post"""
        # Return stored URL if available
        if self.instagram_url:
            return self.instagram_url
        # Instagram URLs cannot be reliably constructed from media ID alone
        # The media ID is not the same as the URL shortcode
        # We should fetch the permalink from Instagram API or store it during posting
        return None

    def refresh_metrics(self):
        """Refresh Instagram metrics from the API"""
        try:
            import requests
            from django.utils import timezone

            # Detailed validation with specific error messages
            if self.status != "posted":
                return (
                    False,
                    f"Post status is '{self.status}' but must be 'posted' to refresh metrics",
                )

            if not self.instagram_id:
                return (
                    False,
                    f"Post {self.id} does not have an Instagram ID. This may be due to a posting failure or data corruption.",
                )

            # Validate instagram_id format (should be numeric string)
            if not str(self.instagram_id).isdigit():
                return (
                    False,
                    f"Invalid Instagram ID format: '{self.instagram_id}'. Instagram IDs should be numeric.",
                )

            # Check if brand has Instagram configuration
            if not self.brand.has_instagram_config:
                return (
                    False,
                    f"Brand '{self.brand.name}' does not have Instagram API configuration. Please connect Instagram account first.",
                )

            # Validate brand Instagram configuration details
            if not self.brand.instagram_access_token:
                return (
                    False,
                    f"Brand '{self.brand.name}' missing Instagram access token. Please reconnect Instagram account.",
                )

            if not self.brand.instagram_user_id:
                return (
                    False,
                    f"Brand '{self.brand.name}' missing Instagram user ID. Please reconnect Instagram account.",
                )

            print(f"DEBUG: Refreshing metrics for Instagram post {self.id}")
            print(f"DEBUG: Instagram ID: {self.instagram_id}")
            print(f"DEBUG: Brand: {self.brand.name}")
            print(f"DEBUG: Is video post: {self.is_video_post}")

            access_token = self.brand.instagram_access_token

            # First, check if the account has proper permissions by checking account info
            account_info_url = (
                f"https://graph.instagram.com/v18.0/{self.brand.instagram_user_id}"
            )
            account_params = {
                "fields": "account_type,name,username",
                "access_token": access_token,
            }

            try:
                account_response = requests.get(account_info_url, params=account_params)
                print(f"DEBUG: Account info response: {account_response.status_code}")

                if account_response.status_code == 200:
                    account_data = account_response.json()
                    account_type = account_data.get("account_type", "UNKNOWN")
                    print(f"DEBUG: Account type: {account_type}")

                    if account_type not in ["BUSINESS", "CREATOR"]:
                        return (
                            False,
                            f"Instagram account type '{account_type}' cannot access insights. Only Business and Creator accounts can view metrics. Please convert your account in Instagram settings.",
                        )
                else:
                    print(f"DEBUG: Account info failed: {account_response.text}")
            except Exception as e:
                print(f"DEBUG: Account info check failed: {e}")
                # Continue anyway, let the insights API call handle the error

            # Get Instagram media insights
            insights_url = (
                f"https://graph.instagram.com/v18.0/{self.instagram_id}/insights"
            )

            # Check if this is a reel by looking at multiple indicators
            is_reel = False
            instagram_url = self.get_instagram_url()

            # Method 1: Check Instagram URL for /reel/ path
            if instagram_url and "/reel/" in instagram_url:
                is_reel = True
                print(f"DEBUG: Detected Instagram Reel via URL: {instagram_url}")

            # Method 2: Check if this is a video post that was posted as REELS media_type
            # (The posting logic uses media_type="REELS" for videos)
            elif self.is_video_post and hasattr(self, "media_type_used"):
                # If we stored the media_type during posting
                if getattr(self, "media_type_used", None) == "REELS":
                    is_reel = True
                    print("DEBUG: Detected Instagram Reel via media_type: REELS")

            # Method 3: For video posts without clear reel indicators,
            # assume newer video posts are likely reels (Instagram's current default)
            elif self.is_video_post and self.created_at:
                from django.utils import timezone
                from datetime import datetime
                import zoneinfo

                reel_era_start = datetime(
                    2022, 6, 28, tzinfo=zoneinfo.ZoneInfo("UTC")
                )  # When Reels API launched
                if self.created_at >= reel_era_start:
                    is_reel = True
                    print(
                        f"DEBUG: Assuming video post is Reel based on creation date: {self.created_at}"
                    )

            print(
                f"DEBUG: Final reel detection result: {is_reel}, video_post: {self.is_video_post}, url: {instagram_url}"
            )

            # Define metrics to fetch based on post type
            if is_reel:
                # Reel-specific metrics (avoiding deprecated ones like video_views)
                metric_fields = [
                    "likes",
                    "comments",
                    "shares",
                    "reach",
                    "saved",
                    "views",  # New metric for reels
                    "total_interactions",  # Reel-specific metric
                ]
            elif self.is_video_post:
                # Regular video metrics (non-reel)
                metric_fields = [
                    "likes",
                    "comments",
                    "shares",
                    "reach",
                    "saved",
                    "views",  # Use views instead of deprecated video_views
                ]
            else:
                # Image post metrics
                metric_fields = [
                    "likes",
                    "comments",
                    "shares",
                    "reach",
                    "saved",
                ]

            # Remove impressions for newer posts (deprecated after July 2, 2024)
            from django.utils import timezone
            from datetime import datetime
            import zoneinfo

            july_2024 = datetime(2024, 7, 2, tzinfo=zoneinfo.ZoneInfo("UTC"))
            if not is_reel and (not self.created_at or self.created_at > july_2024):
                # For newer non-reel posts, impressions might not be available
                pass  # impressions already not included above
            elif not is_reel:
                # For older posts, we can still try to get impressions
                metric_fields.append("impressions")

            params = {
                "metric": ",".join(metric_fields),
                "access_token": access_token,
            }

            response = requests.get(insights_url, params=params)

            print("DEBUG: Instagram Insights API call:")
            print(f"DEBUG: URL: {insights_url}")
            # Mask access token for security
            debug_params = params.copy()
            if "access_token" in debug_params:
                debug_params["access_token"] = debug_params["access_token"][:10] + "..."
            print(f"DEBUG: Params: {debug_params}")
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response text: {response.text}")

            if response.status_code == 200:
                data = response.json()

                if "data" in data:
                    # Process insights data
                    for metric in data["data"]:
                        metric_name = metric.get("name")
                        metric_value = metric.get("values", [{}])[0].get("value", 0)

                        # Map Instagram metric names to model fields
                        if metric_name == "likes":
                            self.like_count = metric_value
                        elif metric_name == "comments":
                            self.comment_count = metric_value
                        elif metric_name == "shares":
                            self.share_count = metric_value
                        elif metric_name == "reach":
                            self.reach = metric_value
                        elif metric_name == "impressions":
                            self.impressions = metric_value
                        elif metric_name == "saved":
                            self.saved_count = metric_value
                        elif metric_name == "video_views":
                            # Handle deprecated metric for backward compatibility
                            self.video_views = metric_value
                        elif metric_name == "views":
                            # New views metric for reels and videos
                            self.video_views = metric_value  # Map to existing field
                        elif metric_name == "total_interactions":
                            # Reel-specific metric - store in a field if it exists
                            # For now, we'll use reach as a proxy since total_interactions
                            # is likes + saves + comments + shares - unlikes - unsaves - deleted comments
                            pass  # Could add a new field for this in the future

                    self.metrics_last_updated = timezone.now()
                    self.save()
                    return True, "Metrics updated successfully"
                else:
                    return False, "No insights data available"
            else:
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_detail = error_data["error"]
                        error_code = error_detail.get("code", "unknown")
                        error_message = error_detail.get("message", "Unknown error")

                        # Handle specific Instagram API errors
                        if error_code == 190:
                            return (
                                False,
                                "Access token is invalid or expired. Please reconnect your Instagram account.",
                            )
                        elif error_code == 100:
                            # Check if this is a reel-specific issue
                            instagram_url = self.get_instagram_url()
                            if instagram_url and "/reel/" in instagram_url:
                                return (
                                    False,
                                    f"Unable to fetch metrics for Instagram Reel. Post ID: '{self.instagram_id}', User ID: '{self.brand.instagram_user_id}'. This may be due to reel-specific API limitations, the reel being deleted, or insufficient permissions. Reel URL: {instagram_url}",
                                )
                            else:
                                return (
                                    False,
                                    f"Invalid Instagram user ID or post ID. Post ID: '{self.instagram_id}', User ID: '{self.brand.instagram_user_id}'. This may indicate the post was deleted on Instagram or the IDs are corrupted.",
                                )
                        elif error_code == 104:
                            return (
                                False,
                                "Instagram API rate limit exceeded. Please try again later.",
                            )
                        elif error_code == 200:
                            return (
                                False,
                                "Permissions error: Your Instagram account must be a Business or Creator account with proper permissions to access insights. Personal accounts cannot access metrics.",
                            )
                        elif error_code == 10:
                            return (
                                False,
                                "API permissions error: Missing required permissions (instagram_basic, instagram_manage_insights). Please reconnect your Instagram account.",
                            )
                        else:
                            return (
                                False,
                                f"Instagram API error {error_code}: {error_message}",
                            )
                except (ValueError, KeyError):
                    # Handle specific HTTP status codes
                    if response.status_code == 403:
                        return (
                            False,
                            "Access forbidden: Your Instagram account must be a Business or Creator account to access insights. Personal accounts cannot view metrics. Please convert your account to Business/Creator in Instagram settings.",
                        )
                    elif response.status_code == 401:
                        return (
                            False,
                            "Authentication failed: Instagram access token is invalid or expired. Please reconnect your Instagram account.",
                        )
                    else:
                        return (
                            False,
                            f"Failed to fetch metrics: HTTP {response.status_code}. Response: {response.text[:200]}{'...' if len(response.text) > 200 else ''}. Post ID: {self.instagram_id}, Brand: {self.brand.name}",
                        )

        except Exception as e:
            import traceback

            error_details = f"Error fetching metrics for post {self.id} (Instagram ID: {self.instagram_id}): {str(e)}"
            print(f"DEBUG: Exception in refresh_metrics: {error_details}")
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return False, error_details


class BlogPost(models.Model):
    """Blog post model for user-generated content"""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    CATEGORY_CHOICES = [
        ("ai_analytics", "AI & Analytics"),
        ("lead_generation", "Lead Generation"),
        ("automation", "Automation"),
        ("case_studies", "Case Studies"),
        ("marketing_tips", "Marketing Tips"),
        ("industry_news", "Industry News"),
        ("tutorials", "Tutorials"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_posts"
    )
    content = models.TextField()
    excerpt = models.TextField(
        max_length=500,
        blank=True,
        help_text="Brief description of the post (auto-generated if empty)",
    )
    featured_image = models.ImageField(
        upload_to="blog_images/",
        blank=True,
        null=True,
        help_text="Featured image for the blog post",
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="other"
    )
    tags = models.JSONField(default=list, help_text="List of tags for categorization")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_featured = models.BooleanField(
        default=False, help_text="Mark as featured to display prominently"
    )

    # SEO fields
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="SEO meta description"
    )
    meta_keywords = models.CharField(
        max_length=255, blank=True, help_text="SEO keywords (comma-separated)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["category", "-published_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)

        # Ensure slug is unique
        original_slug = self.slug
        counter = 1
        while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1

        # Auto-generate excerpt if not provided
        if not self.excerpt and self.content:
            # Extract first 200 characters from content, clean HTML if needed
            import re

            clean_content = re.sub(r"<[^>]+>", "", self.content)
            self.excerpt = (
                clean_content[:200] + "..."
                if len(clean_content) > 200
                else clean_content
            )

        # Set published_at when status changes to published
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("website:blog_detail", kwargs={"slug": self.slug})

    @property
    def is_published(self):
        return self.status == "published"

    @property
    def reading_time(self):
        """Estimate reading time in minutes"""
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))  # Assume 200 words per minute

    def get_related_posts(self, limit=3):
        """Get related posts by same category or tags"""
        related = BlogPost.objects.filter(
            status="published", category=self.category
        ).exclude(pk=self.pk)

        if related.count() < limit:
            # If not enough in same category, get by tags
            tag_related = BlogPost.objects.filter(
                status="published", tags__overlap=self.tags
            ).exclude(pk=self.pk)
            related = related.union(tag_related)

        return related.distinct()[:limit]

    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=["view_count"])


class BlogComment(models.Model):
    """Comments on blog posts"""

    post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_comments"
    )
    content = models.TextField()
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    @property
    def is_reply(self):
        return self.parent is not None


# Referral System Models
class ReferralCode(models.Model):
    """Model for tracking user referral codes"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="referral_code"
    )
    code = models.CharField(max_length=20, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Gamification fields
    total_points = models.IntegerField(default=0)
    total_clicks = models.IntegerField(default=0)
    total_signups = models.IntegerField(default=0)
    total_subscriptions = models.IntegerField(default=0)

    # Rewards tracking
    total_rewards_earned = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )

    class Meta:
        verbose_name = "Referral Code"
        verbose_name_plural = "Referral Codes"
        ordering = ["-total_points", "-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.code}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        """Generate a unique referral code"""
        import string
        import random

        # Use username + random string
        base = self.user.username[:4].upper()
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"{base}{suffix}"

        # Ensure uniqueness
        while ReferralCode.objects.filter(code=code).exists():
            suffix = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=6)
            )
            code = f"{base}{suffix}"

        return code

    def get_referral_url(self):
        """Get the full referral URL"""
        from django.urls import reverse
        from django.conf import settings

        base_url = getattr(settings, "SITE_URL", "https://gemnar.com")
        path = reverse("website:referral_signup", kwargs={"code": self.code})
        return f"{base_url}{path}"

    def calculate_points(self):
        """Calculate total points based on referral activities"""
        # Points system:
        # - 1 point per click
        # - 10 points per signup
        # - 50 points per subscription
        points = (
            (self.total_clicks * 1)
            + (self.total_signups * 10)
            + (self.total_subscriptions * 50)
        )
        self.total_points = points
        self.save()
        return points


class ReferralClick(models.Model):
    """Model for tracking referral clicks"""

    referral_code = models.ForeignKey(
        ReferralCode, on_delete=models.CASCADE, related_name="clicks"
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.URLField(
        blank=True, null=True, help_text="URL where the click originated from"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    # Location data (if available)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Referral Click"
        verbose_name_plural = "Referral Clicks"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["referral_code", "-timestamp"]),
            models.Index(fields=["ip_address", "-timestamp"]),
        ]
        # Prevent duplicate clicks from the same IP for the same referral code
        unique_together = [("referral_code", "ip_address")]

    def __str__(self):
        return f"Click on {self.referral_code.code} at {self.timestamp}"


class ReferralSignup(models.Model):
    """Model for tracking successful referral signups"""

    referral_code = models.ForeignKey(
        ReferralCode, on_delete=models.CASCADE, related_name="signups"
    )
    referred_user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="referral_signup"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    # Reward tracking
    reward_given = models.BooleanField(default=False)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Referral Signup"
        verbose_name_plural = "Referral Signups"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.referred_user.username} signed up via {self.referral_code.code}"


class ReferralSubscription(models.Model):
    """Model for tracking referral subscriptions/payments"""

    referral_code = models.ForeignKey(
        ReferralCode, on_delete=models.CASCADE, related_name="subscriptions"
    )
    referred_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referral_subscriptions"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    # Subscription details
    subscription_type = models.CharField(max_length=50)
    subscription_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Reward tracking
    reward_given = models.BooleanField(default=False)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reward_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00
    )  # Default 10% commission

    class Meta:
        verbose_name = "Referral Subscription"
        verbose_name_plural = "Referral Subscriptions"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.referred_user.username} subscribed via {self.referral_code.code}"

    def save(self, *args, **kwargs):
        if not self.reward_amount:
            self.reward_amount = self.subscription_amount * self.reward_percentage / 100
        super().save(*args, **kwargs)


class ReferralBadge(models.Model):
    """Model for gamification badges"""

    BADGE_TYPES = [
        ("first_referral", "First Referral"),
        ("bronze_referrer", "Bronze Referrer (5 signups)"),
        ("silver_referrer", "Silver Referrer (25 signups)"),
        ("gold_referrer", "Gold Referrer (100 signups)"),
        ("platinum_referrer", "Platinum Referrer (500 signups)"),
        ("click_master", "Click Master (1000 clicks)"),
        ("subscription_ace", "Subscription Ace (50 subscriptions)"),
        ("top_earner", "Top Earner (monthly)"),
        ("leaderboard_king", "Leaderboard King (weekly #1)"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referral_badges"
    )
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPES)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Referral Badge"
        verbose_name_plural = "Referral Badges"
        unique_together = ["user", "badge_type"]
        ordering = ["-earned_at"]

    def __str__(self):
        return f"{self.user.username} - {self.get_badge_type_display()}"


class ReferralLeaderboard(models.Model):
    """Model for tracking leaderboard periods"""

    PERIOD_TYPES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("all_time", "All Time"),
    ]

    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    # Top performers
    winner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="leaderboard_wins"
    )
    runner_up = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="leaderboard_seconds",
        null=True,
        blank=True,
    )
    third_place = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="leaderboard_thirds",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Referral Leaderboard"
        verbose_name_plural = "Referral Leaderboards"
        ordering = ["-period_start"]

    def __str__(self):
        return (
            f"{self.get_period_type_display()} Leaderboard - {self.period_start.date()}"
        )


class Task(models.Model):
    """Model for tasks that brands can create for creators"""

    CATEGORY_CHOICES = [
        ("POST", "Instagram Post"),
        ("REEL", "Instagram Reel"),
        ("STORY", "Instagram Story"),
        ("VIDEO", "Video Content"),
        ("BLOG", "Blog Article"),
        ("REVIEW", "Product Review"),
        ("UNBOXING", "Unboxing Video"),
        ("TUTORIAL", "Tutorial"),
        ("COLLABORATION", "Brand Collaboration"),
        ("UGC", "User Generated Content"),
        ("TESTIMONIAL", "Testimonial"),
        ("LIVESTREAM", "Live Stream"),
    ]

    GENRE_CHOICES = [
        ("BEAUTY", "Beauty & Cosmetics"),
        ("FASHION", "Fashion & Style"),
        ("FOOD", "Food & Beverage"),
        ("FITNESS", "Fitness & Health"),
        ("TECH", "Technology"),
        ("TRAVEL", "Travel & Lifestyle"),
        ("HOME", "Home & Decor"),
        ("AUTOMOTIVE", "Automotive"),
        ("GAMING", "Gaming"),
        ("FINANCE", "Finance & Business"),
        ("EDUCATION", "Education"),
        ("ENTERTAINMENT", "Entertainment"),
        ("SPORTS", "Sports & Recreation"),
        ("PETS", "Pets & Animals"),
        ("PARENTING", "Parenting & Family"),
        ("SUSTAINABLE", "Sustainability & Eco-friendly"),
        ("LUXURY", "Luxury Goods"),
        ("B2B", "Business to Business"),
        ("OTHER", "Other"),
    ]

    INCENTIVE_CHOICES = [
        ("NONE", "No Compensation"),
        ("BARTER", "Product Exchange"),
        ("PAY", "Monetary Payment"),
        ("COMMISSION", "Commission Based"),
        ("EXPOSURE", "Exposure & Credits"),
        ("GIFT_CARD", "Gift Card"),
        ("EXPERIENCE", "Experience/Event Access"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    genre = models.CharField(max_length=15, choices=GENRE_CHOICES)
    incentive_type = models.CharField(max_length=15, choices=INCENTIVE_CHOICES)
    barter_details = models.TextField(blank=True, null=True)
    pay_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Commission percentage for commission-based tasks",
    )
    gift_card_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Gift card amount for gift card incentives",
    )
    experience_details = models.TextField(
        blank=True,
        null=True,
        help_text="Details about the experience or event access offered",
    )
    deadline = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    brand = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["brand", "-created_at"]),
            models.Index(fields=["category", "-created_at"]),
            models.Index(fields=["genre", "-created_at"]),
            models.Index(fields=["incentive_type", "-created_at"]),
            models.Index(fields=["is_active", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.brand.username}"

    @property
    def application_count(self):
        return self.applications.count()

    @property
    def accepted_applications_count(self):
        return self.applications.filter(status="ACCEPTED").count()


class TaskApplication(models.Model):
    """Model for creator applications to tasks"""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("REJECTED", "Rejected"),
        ("COMPLETED", "Completed"),
    ]

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="applications"
    )
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="task_applications"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    message = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]
        unique_together = ["task", "creator"]
        indexes = [
            models.Index(fields=["task", "-applied_at"]),
            models.Index(fields=["creator", "-applied_at"]),
            models.Index(fields=["status", "-applied_at"]),
        ]

    def __str__(self):
        return f"{self.creator.username} -> {self.task.title} ({self.status})"


class EncryptedVariable(models.Model):
    """
    Model for storing encrypted key-value pairs that can be managed through
    Django admin. Uses the same encryption system as chat messages for
    consistency.
    """

    key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique identifier for this variable",
    )
    value = models.TextField(
        help_text="The encrypted value. This will be automatically encrypted/decrypted."
    )
    description = models.TextField(
        blank=True, help_text="Optional description of what this variable is used for"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether this variable is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_variables",
        help_text="User who created this variable",
    )
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modified_variables",
        help_text="User who last modified this variable",
    )

    class Meta:
        verbose_name = "Encrypted Variable"
        verbose_name_plural = "Encrypted Variables"
        ordering = ["key"]
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["is_active", "key"]),
        ]

    def __str__(self):
        return f"{self.key} ({'Active' if self.is_active else 'Inactive'})"

    def save(self, *args, **kwargs):
        """Override save to automatically encrypt the value if it's not
        already encrypted."""
        if self.value:
            from chat.encryption import ChatEncryption

            try:
                # Try to decrypt first to see if it's already encrypted
                ChatEncryption.decrypt_message(self.value)
            except Exception:
                # If decryption fails, it's plain text, so encrypt it
                self.value = ChatEncryption.encrypt_message(self.value)

        super().save(*args, **kwargs)

    def get_decrypted_value(self):
        """
        Get the decrypted value of this variable.
        Returns the decrypted value or the original value if decryption fails.
        """
        try:
            from chat.encryption import ChatEncryption

            return ChatEncryption.decrypt_message(self.value)
        except Exception:
            # If decryption fails, assume it's plain text
            return self.value

    @classmethod
    def get_value(cls, key, default=None):
        """
        Get a decrypted variable value by key.

        Args:
            key (str): The variable key to retrieve
            default: Default value if variable doesn't exist or is inactive

        Returns:
            The decrypted value or default
        """
        try:
            var = cls.objects.get(key=key, is_active=True)
            return var.get_decrypted_value()
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value, description="", user=None):
        """
        Set a variable value, creating it if it doesn't exist.

        Args:
            key (str): The variable key
            value (str): The value to store (will be encrypted)
            description (str): Optional description
            user (User): User making the change

        Returns:
            The EncryptedVariable instance
        """
        var, created = cls.objects.get_or_create(
            key=key,
            defaults={
                "description": description,
                "created_by": user,
                "last_modified_by": user,
            },
        )

        if not created:
            var.last_modified_by = user
            var.description = description

        var.value = value  # Will be encrypted in save()
        var.save()
        return var

    @classmethod
    def delete_value(cls, key):
        """
        Delete a variable by key.

        Args:
            key (str): The variable key to delete

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            var = cls.objects.get(key=key)
            var.delete()
            return True
        except cls.DoesNotExist:
            return False


class ServicePrompt(models.Model):
    """Model for storing AI prompts sent to various services"""

    SERVICE_CHOICES = [
        ("twitter", "Twitter"),
        ("instagram", "Instagram"),
        ("reddit", "Reddit"),
        ("blog", "Blog"),
        ("gemnar_feed", "Gemnar Feed"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("scheduled", "Scheduled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Generated content
    generated_content = models.TextField(blank=True, null=True)
    generated_image = models.ImageField(
        upload_to="generated_images/", blank=True, null=True
    )

    # Posting details
    posted_at = models.DateTimeField(blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)
    external_id = models.CharField(max_length=100, blank=True, null=True)

    # Engagement metrics
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.service} - {self.prompt[:50]}..."


class ServiceStats(models.Model):
    """Model for storing service statistics"""

    SERVICE_CHOICES = [
        ("twitter", "Twitter"),
        ("instagram", "Instagram"),
        ("reddit", "Reddit"),
        ("blog", "Blog"),
        ("gemnar_feed", "Gemnar Feed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)

    # Stats
    total_prompts = models.IntegerField(default=0)
    successful_posts = models.IntegerField(default=0)
    failed_posts = models.IntegerField(default=0)
    pending_posts = models.IntegerField(default=0)

    # Engagement
    total_likes = models.IntegerField(default=0)
    total_shares = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)

    # Last updated
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "service"]

    def __str__(self):
        return f"{self.user.username} - {self.service}"


class ServiceConnection(models.Model):
    """Model for storing service connection details"""

    SERVICE_CHOICES = [
        ("twitter", "Twitter"),
        ("instagram", "Instagram"),
        ("reddit", "Reddit"),
        ("blog", "Blog"),
        ("gemnar_feed", "Gemnar Feed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    is_connected = models.BooleanField(default=False)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    # Service-specific details
    username = models.CharField(max_length=100, blank=True, null=True)
    service_user_id = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "service"]

    def __str__(self):
        return f"{self.user.username} - {self.service}"


class AIServiceUsage(models.Model):
    """Track daily AI service usage per brand"""

    SERVICE_CHOICES = [
        ("openai_text", "OpenAI Text Generation"),
        ("openai_image", "OpenAI Image Generation"),
        ("runware_image", "Runware Image Generation"),
    ]

    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="ai_service_usage"
    )
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    usage_date = models.DateField(auto_now_add=True)
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["brand", "service", "usage_date"]
        ordering = ["-usage_date", "brand", "service"]
        indexes = [
            models.Index(fields=["brand", "service", "usage_date"]),
            models.Index(fields=["usage_date"]),
        ]

    def __str__(self):
        return f"{self.brand.name} - {self.get_service_display()} - {self.usage_date}: {self.usage_count}"

    @classmethod
    def get_daily_usage(cls, brand, service, date=None):
        """Get daily usage count for a brand and service"""
        if date is None:
            date = timezone.now().date()

        usage, created = cls.objects.get_or_create(
            brand=brand, service=service, usage_date=date, defaults={"usage_count": 0}
        )
        return usage.usage_count

    @classmethod
    def increment_usage(cls, brand, service, date=None):
        """Increment usage count for a brand and service"""
        if date is None:
            date = timezone.now().date()

        usage, created = cls.objects.get_or_create(
            brand=brand, service=service, usage_date=date, defaults={"usage_count": 0}
        )
        usage.usage_count += 1
        usage.save()
        return usage.usage_count

    @classmethod
    def check_limit(cls, brand, service, date=None):
        """Check if usage is within limits for a brand and service"""
        if date is None:
            date = timezone.now().date()

        current_usage = cls.get_daily_usage(brand, service, date)
        limit = AIServiceLimit.get_limit(service)

        return current_usage < limit, current_usage, limit


class AIServiceLimit(models.Model):
    """Configure limits for AI services"""

    SERVICE_CHOICES = [
        ("openai_text", "OpenAI Text Generation"),
        ("openai_image", "OpenAI Image Generation"),
        ("runware_image", "Runware Image Generation"),
    ]

    service = models.CharField(max_length=20, choices=SERVICE_CHOICES, unique=True)
    daily_limit = models.PositiveIntegerField(default=10)
    description = models.TextField(
        blank=True, help_text="Description of this service limit"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["service"]
        verbose_name = "AI Service Limit"
        verbose_name_plural = "AI Service Limits"

    def __str__(self):
        return f"{self.service}: {self.daily_limit}/day"

    @classmethod
    def get_limit(cls, service):
        """Get the daily limit for a service"""
        try:
            limit = cls.objects.get(service=service, is_active=True)
            return limit.daily_limit
        except cls.DoesNotExist:
            return 10  # Default limit

    @classmethod
    def set_limit(cls, service, daily_limit, description=""):
        """Set or update a service limit"""
        limit, created = cls.objects.get_or_create(
            service=service,
            defaults={
                "daily_limit": daily_limit,
                "description": description,
                "is_active": True,
            },
        )
        if not created:
            limit.daily_limit = daily_limit
            limit.description = description
            limit.is_active = True
            limit.save()
        return limit


class WebLog(models.Model):
    """Model for logging web activities including minute tasks, deployments, and system events"""

    ACTIVITY_TYPES = [
        ("minute_task", "Minute Task"),
        ("deployment", "Deployment"),
        ("system_event", "System Event"),
        ("user_action", "User Action"),
        ("error", "Error"),
        ("debug", "Debug"),
    ]

    STATUS_CHOICES = [
        ("started", "Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    # Basic log fields
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    activity_name = models.CharField(max_length=200, help_text="Name of the activity")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="started")

    # Description and details
    description = models.TextField(blank=True, help_text="Human-readable description")
    details = models.JSONField(
        default=dict, help_text="Structured data about the activity"
    )

    # Metrics and counts
    items_processed = models.IntegerField(
        default=0, help_text="Number of items processed"
    )
    items_succeeded = models.IntegerField(
        default=0, help_text="Number of items that succeeded"
    )
    items_failed = models.IntegerField(
        default=0, help_text="Number of items that failed"
    )

    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(
        null=True, blank=True, help_text="Duration in seconds"
    )

    # Error handling
    error_message = models.TextField(blank=True, help_text="Error message if failed")
    error_traceback = models.TextField(blank=True, help_text="Full error traceback")

    # Optional associations
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Web Log"
        verbose_name_plural = "Web Logs"
        indexes = [
            models.Index(fields=["activity_type", "-started_at"]),
            models.Index(fields=["status", "-started_at"]),
            models.Index(fields=["activity_name", "-started_at"]),
            models.Index(fields=["-started_at"]),
        ]

    def __str__(self):
        return f"{self.activity_name} - {self.status} ({self.started_at})"

    def mark_completed(self, items_succeeded=None, items_failed=None, details=None):
        """Mark the log entry as completed with optional metrics"""
        from django.utils import timezone

        self.status = "completed"
        self.completed_at = timezone.now()

        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = duration

        if items_succeeded is not None:
            self.items_succeeded = items_succeeded
        if items_failed is not None:
            self.items_failed = items_failed
        if details:
            self.details.update(details)

        self.save()

    def mark_failed(self, error_message="", error_traceback="", details=None):
        """Mark the log entry as failed with error information"""
        from django.utils import timezone

        self.status = "failed"
        self.completed_at = timezone.now()

        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = duration

        self.error_message = error_message
        self.error_traceback = error_traceback

        if details:
            self.details.update(details)

        self.save()

    def update_progress(
        self,
        items_processed=None,
        items_succeeded=None,
        items_failed=None,
        details=None,
    ):
        """Update progress while the activity is running"""
        self.status = "in_progress"

        if items_processed is not None:
            self.items_processed = items_processed
        if items_succeeded is not None:
            self.items_succeeded = items_succeeded
        if items_failed is not None:
            self.items_failed = items_failed
        if details:
            self.details.update(details)

        self.save()

    @classmethod
    def log_minute_task(cls, task_name, description="", details=None):
        """Create a log entry for a minute task"""
        return cls.objects.create(
            activity_type="minute_task",
            activity_name=task_name,
            description=description,
            details=details or {},
            status="started",
        )

    @classmethod
    def log_deployment(cls, deployment_type, description="", details=None):
        """Create a log entry for a deployment"""
        return cls.objects.create(
            activity_type="deployment",
            activity_name=deployment_type,
            description=description,
            details=details or {},
            status="started",
        )

    @classmethod
    def log_system_event(cls, event_name, description="", details=None, user=None):
        """Create a log entry for a system event"""
        return cls.objects.create(
            activity_type="system_event",
            activity_name=event_name,
            description=description,
            details=details or {},
            user=user,
            status="started",
        )

    @classmethod
    def log_user_action(
        cls, action_name, description="", details=None, user=None, brand=None
    ):
        """Create a log entry for a user action"""
        return cls.objects.create(
            activity_type="user_action",
            activity_name=action_name,
            description=description,
            details=details or {},
            user=user,
            brand=brand,
            status="started",
        )

    @classmethod
    def log_error(
        cls,
        error_name,
        description="",
        error_message="",
        error_traceback="",
        details=None,
        user=None,
    ):
        """Create a log entry for an error"""
        return cls.objects.create(
            activity_type="error",
            activity_name=error_name,
            description=description,
            error_message=error_message,
            error_traceback=error_traceback,
            details=details or {},
            user=user,
            status="failed",
        )

    @property
    def success_rate(self):
        """Calculate success rate as a percentage"""
        if self.items_processed == 0:
            return 0
        return (self.items_succeeded / self.items_processed) * 100

    @property
    def is_running(self):
        """Check if the activity is currently running"""
        return self.status in ["started", "in_progress"]

    @property
    def is_finished(self):
        """Check if the activity has finished (completed or failed)"""
        return self.status in ["completed", "failed", "cancelled"]


# Import analytics models at the end to avoid circular imports


# =====================================
# CRM MODELS
# =====================================


class CRMContact(models.Model):
    """CRM Contact model for managing customer/prospect information"""

    CONTACT_TYPES = [
        ("lead", "Lead"),
        ("customer", "Customer"),
        ("partner", "Partner"),
        ("vendor", "Vendor"),
        ("other", "Other"),
    ]

    LEAD_SOURCES = [
        ("website", "Website"),
        ("referral", "Referral"),
        ("social_media", "Social Media"),
        ("email_marketing", "Email Marketing"),
        ("cold_outreach", "Cold Outreach"),
        ("event", "Event"),
        ("partner", "Partner"),
        ("advertising", "Advertising"),
        ("other", "Other"),
    ]

    # Organization association
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="crm_contacts",
    )

    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True)

    # Contact Details
    contact_type = models.CharField(
        max_length=20, choices=CONTACT_TYPES, default="lead"
    )
    lead_source = models.CharField(max_length=20, choices=LEAD_SOURCES, blank=True)

    # Address Information
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Social Media
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    # Relationship
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_contacts",
    )
    tags = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated tags"
    )
    description = models.TextField(blank=True)

    # Status and tracking
    is_active = models.BooleanField(default=True)
    last_contact_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_contacts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["organization", "email"]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "contact_type"]),
            models.Index(fields=["assigned_to", "-created_at"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]


class CRMCompany(models.Model):
    """CRM Company model for managing business organizations"""

    # Organization association
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="crm_companies",
    )

    # Required Information
    name = models.CharField(max_length=200)
    website = models.URLField()
    email = models.EmailField()

    # Optional Social Media
    twitter_handle = models.CharField(
        max_length=100, blank=True, help_text="Twitter handle without @"
    )
    instagram_handle = models.CharField(
        max_length=100, blank=True, help_text="Instagram handle without @"
    )
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn company page URL")

    # Additional Information
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    industry = models.CharField(max_length=100, blank=True)

    # Address Information
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Relationship
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_companies",
    )
    tags = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated tags"
    )

    # Status and tracking
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_companies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "CRM Companies"
        unique_together = ["organization", "name"]
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "name"]),
            models.Index(fields=["assigned_to", "-created_at"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return self.name

    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    @property
    def twitter_url(self):
        if self.twitter_handle:
            return f"https://twitter.com/{self.twitter_handle.lstrip('@')}"
        return ""

    @property
    def instagram_url(self):
        if self.instagram_handle:
            return f"https://instagram.com/{self.instagram_handle.lstrip('@')}"
        return ""

    @property
    def linkedin_company_url(self):
        """Return the formatted LinkedIn URL or the stored URL if it exists"""
        if self.linkedin_url:
            return self.linkedin_url
        return ""


class CRMDeal(models.Model):
    """CRM Deal/Opportunity model for tracking sales pipeline"""

    DEAL_STAGES = [
        ("prospecting", "Prospecting"),
        ("qualification", "Qualification"),
        ("proposal", "Proposal"),
        ("negotiation", "Negotiation"),
        ("closed_won", "Closed Won"),
        ("closed_lost", "Closed Lost"),
    ]

    CURRENCIES = [
        ("USD", "US Dollar"),
        ("EUR", "Euro"),
        ("GBP", "British Pound"),
        ("CAD", "Canadian Dollar"),
        ("AUD", "Australian Dollar"),
        ("INR", "Indian Rupee"),
    ]

    # Organization and Contact
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="crm_deals"
    )
    contact = models.ForeignKey(
        CRMContact, on_delete=models.CASCADE, related_name="deals"
    )

    # Deal Information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    stage = models.CharField(max_length=20, choices=DEAL_STAGES, default="prospecting")

    # Financial
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default="USD")
    probability = models.PositiveIntegerField(
        default=10, help_text="Probability of closing (0-100%)"
    )

    # Dates
    expected_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)

    # Assignment and tracking
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_deals",
    )

    # Status
    is_active = models.BooleanField(default=True)
    lost_reason = models.TextField(blank=True, help_text="Reason if deal was lost")

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_deals"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "stage"]),
            models.Index(fields=["assigned_to", "-created_at"]),
            models.Index(fields=["expected_close_date"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.contact.full_name} ({self.get_stage_display()})"

    @property
    def is_won(self):
        return self.stage == "closed_won"

    @property
    def is_lost(self):
        return self.stage == "closed_lost"

    @property
    def is_closed(self):
        return self.stage in ["closed_won", "closed_lost"]

    @property
    def weighted_value(self):
        """Calculate weighted value based on probability"""
        return self.value * (self.probability / 100)


class CRMActivity(models.Model):
    """CRM Activity model for tracking interactions and tasks"""

    ACTIVITY_TYPES = [
        ("call", "Phone Call"),
        ("email", "Email"),
        ("meeting", "Meeting"),
        ("task", "Task"),
        ("note", "Note"),
        ("proposal", "Proposal Sent"),
        ("demo", "Demo/Presentation"),
        ("follow_up", "Follow Up"),
        ("other", "Other"),
    ]

    ACTIVITY_STATUS = [
        ("planned", "Planned"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("overdue", "Overdue"),
    ]

    # Organization and relationships
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="crm_activities",
    )
    contact = models.ForeignKey(
        CRMContact, on_delete=models.CASCADE, related_name="activities"
    )
    deal = models.ForeignKey(
        CRMDeal,
        on_delete=models.CASCADE,
        related_name="activities",
        null=True,
        blank=True,
    )

    # Activity Details
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    subject = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ACTIVITY_STATUS, default="planned")

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_activities",
    )

    # Outcome
    outcome = models.TextField(
        blank=True, help_text="Result or notes from the activity"
    )
    next_action = models.CharField(
        max_length=200, blank=True, help_text="Planned next step"
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_activities"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_at", "-created_at"]
        verbose_name_plural = "CRM Activities"
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["assigned_to", "scheduled_at"]),
            models.Index(fields=["contact", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.subject}"

    @property
    def is_overdue(self):
        if self.scheduled_at and self.status == "planned":
            from django.utils import timezone

            return self.scheduled_at < timezone.now()
        return False


class CRMNote(models.Model):
    """CRM Note model for storing notes about contacts and deals"""

    # Organization and relationships
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="crm_notes"
    )
    contact = models.ForeignKey(
        CRMContact,
        on_delete=models.CASCADE,
        related_name="crm_notes",
        null=True,
        blank=True,
    )
    deal = models.ForeignKey(
        CRMDeal,
        on_delete=models.CASCADE,
        related_name="crm_notes",
        null=True,
        blank=True,
    )

    # Note Content
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    is_private = models.BooleanField(default=False, help_text="Only visible to creator")

    # Metadata
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["contact", "-created_at"]),
            models.Index(fields=["deal", "-created_at"]),
        ]

    def __str__(self):
        return f"Note: {self.title or self.content[:50]}"


class CRMPipeline(models.Model):
    """CRM Pipeline model for custom sales pipelines"""

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="crm_pipelines",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_pipelines"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["organization", "name"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class CRMPipelineStage(models.Model):
    """CRM Pipeline Stage model for custom pipeline stages"""

    pipeline = models.ForeignKey(
        CRMPipeline, on_delete=models.CASCADE, related_name="stages"
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    probability = models.PositiveIntegerField(
        default=10, help_text="Default probability for this stage (0-100%)"
    )

    # Stage behavior
    is_active = models.BooleanField(default=True)
    is_closed_won = models.BooleanField(default=False)
    is_closed_lost = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["pipeline", "name"]
        ordering = ["pipeline", "order"]

    def __str__(self):
        return f"{self.pipeline.name}: {self.name}"


class CRMTask(models.Model):
    """CRM Task model for managing follow-ups and to-dos"""

    TASK_PRIORITIES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    TASK_STATUS = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    # Organization and relationships
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="crm_tasks"
    )
    contact = models.ForeignKey(
        CRMContact,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    deal = models.ForeignKey(
        CRMDeal, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True
    )

    # Task Details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10, choices=TASK_PRIORITIES, default="medium"
    )
    status = models.CharField(max_length=20, choices=TASK_STATUS, default="pending")

    # Scheduling
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_crm_tasks",
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_crm_tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["assigned_to", "due_date"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_priority_display()}"

    @property
    def is_overdue(self):
        if self.due_date and self.status in ["pending", "in_progress"]:
            from django.utils import timezone

            return self.due_date < timezone.now()
        return False


class BetaTester(models.Model):
    """Model to store beta tester email addresses for TestFlight invitations"""

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    invited_to_testflight = models.BooleanField(default=False)
    testflight_invitation_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional fields for better user experience
    user_agent = models.TextField(blank=True, help_text="Browser/device info")
    referral_source = models.CharField(
        max_length=100, blank=True, help_text="How they found us"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["invited_to_testflight"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.email} ({'Invited' if self.invited_to_testflight else 'Pending'})"
        )

    def mark_as_invited(self):
        """Mark this beta tester as invited to TestFlight"""
        from django.utils import timezone

        self.invited_to_testflight = True
        self.testflight_invitation_sent_at = timezone.now()
        self.save()


class TwitterMention(models.Model):
    """Track Twitter usernames mentioned in tweets and link to CRM records"""

    MENTION_TYPES = [
        ("company", "Company"),
        ("contact", "Contact"),
        ("unlinked", "Unlinked"),
    ]

    # Core fields
    twitter_handle = models.CharField(
        max_length=100, help_text="Twitter handle without @ symbol"
    )
    mention_type = models.CharField(
        max_length=20, choices=MENTION_TYPES, default="unlinked"
    )

    # Organization association
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="twitter_mentions",
    )

    # Links to CRM records
    crm_company = models.ForeignKey(
        CRMCompany,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="twitter_mentions",
        help_text="Linked CRM company if this is a company handle",
    )
    crm_contact = models.ForeignKey(
        CRMContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="twitter_mentions",
        help_text="Linked CRM contact if this is an individual handle",
    )

    # Tracking information
    first_mentioned_in = models.ForeignKey(
        BrandTweet,
        on_delete=models.CASCADE,
        related_name="mentioned_handles",
        help_text="The tweet where this handle was first mentioned",
    )
    times_mentioned = models.PositiveIntegerField(
        default=1, help_text="Number of times this handle has been mentioned"
    )
    last_mentioned_at = models.DateTimeField(auto_now=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_twitter_mentions",
    )

    class Meta:
        unique_together = ["organization", "twitter_handle"]
        ordering = ["-last_mentioned_at"]
        indexes = [
            models.Index(fields=["organization", "mention_type"]),
            models.Index(fields=["twitter_handle"]),
            models.Index(fields=["last_mentioned_at"]),
        ]

    def __str__(self):
        return f"@{self.twitter_handle} ({self.get_mention_type_display()})"

    def link_to_company(self, company):
        """Link this mention to a CRM company"""
        self.crm_company = company
        self.crm_contact = None  # Clear contact link
        self.mention_type = "company"
        self.save()

    def link_to_contact(self, contact):
        """Link this mention to a CRM contact"""
        self.crm_contact = contact
        self.crm_company = None  # Clear company link
        self.mention_type = "contact"
        self.save()

    def increment_mentions(self, tweet):
        """Increment mention count and update last mentioned info"""
        self.times_mentioned += 1
        self.last_mentioned_at = timezone.now()
        self.save()

        # Create a record linking this specific tweet to the mention
        TweetMention.objects.create(
            twitter_mention=self,
            brand_tweet=tweet,
            created_by=tweet.created_by if hasattr(tweet, "created_by") else None,
        )


class TweetMention(models.Model):
    """Junction table tracking specific tweet-mention relationships"""

    twitter_mention = models.ForeignKey(
        TwitterMention, on_delete=models.CASCADE, related_name="tweet_mentions"
    )
    brand_tweet = models.ForeignKey(
        BrandTweet, on_delete=models.CASCADE, related_name="twitter_mentions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ["twitter_mention", "brand_tweet"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"@{self.twitter_mention.twitter_handle} in tweet {self.brand_tweet.id}"


class TwitterConfig(models.Model):
    """Twitter API configuration for brands"""
    
    brand = models.OneToOneField(
        Brand, 
        on_delete=models.CASCADE, 
        related_name="twitter_config"
    )
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    access_token_secret = models.CharField(max_length=255)
    bearer_token = models.CharField(max_length=255, blank=True)
    
    # Account info
    twitter_username = models.CharField(max_length=100, blank=True)
    twitter_user_id = models.CharField(max_length=50, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_verified = models.DateTimeField(blank=True, null=True)
    verification_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Twitter Configuration"
        verbose_name_plural = "Twitter Configurations"

    def __str__(self):
        return f"Twitter Config for {self.brand.name} (@{self.twitter_username or 'unverified'})"


class QueuedTweet(models.Model):
    """Tweets in the queue for posting"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('scheduled', 'Scheduled'),
        ('posted', 'Posted'),
        ('failed', 'Failed'),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='queued_tweets')
    content = models.TextField(max_length=280)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    media_urls = models.JSONField(default=list, blank=True)
    twitter_id = models.CharField(max_length=50, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'website_queuedtweet'
        ordering = ['-created_at']
        verbose_name = "Queued Tweet"
        verbose_name_plural = "Queued Tweets"

    def __str__(self):
        return f"Tweet for {self.brand.name}: {self.content[:50]}..."


class TwitterAnalytics(models.Model):
    """Twitter analytics data for brands"""
    
    brand = models.ForeignKey(
        Brand, 
        on_delete=models.CASCADE, 
        related_name="twitter_analytics"
    )
    
    # Date range for this analytics record
    date = models.DateField()
    
    # Core metrics
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    tweets_count = models.IntegerField(default=0)
    likes_count = models.IntegerField(default=0)
    
    # Daily metrics
    daily_impressions = models.IntegerField(default=0)
    daily_engagements = models.IntegerField(default=0)
    daily_retweets = models.IntegerField(default=0)
    daily_likes = models.IntegerField(default=0)
    daily_replies = models.IntegerField(default=0)
    
    # Engagement rate (calculated)
    engagement_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['brand', 'date']
        verbose_name = "Twitter Analytics"
        verbose_name_plural = "Twitter Analytics"

    def __str__(self):
        return f"Analytics for {self.brand.name} - {self.date}"


class SystemStats(models.Model):
    """Model to store system statistics snapshots"""

    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # Memory Stats (in MB)
    memory_total = models.FloatField(help_text="Total memory in MB")
    memory_used = models.FloatField(help_text="Used memory in MB")
    memory_available = models.FloatField(help_text="Available memory in MB")
    memory_percent = models.FloatField(help_text="Memory usage percentage")

    # CPU Stats
    cpu_percent = models.FloatField(help_text="CPU usage percentage")
    cpu_count = models.IntegerField(help_text="Number of CPU cores")

    # Disk Stats (in GB)
    disk_total = models.FloatField(help_text="Total disk space in GB")
    disk_used = models.FloatField(help_text="Used disk space in GB")
    disk_free = models.FloatField(help_text="Free disk space in GB")
    disk_percent = models.FloatField(help_text="Disk usage percentage")

    # Database Stats
    user_count = models.IntegerField(default=0, help_text="Total number of users")
    organization_count = models.IntegerField(
        default=0, help_text="Total number of organizations"
    )
    brand_count = models.IntegerField(default=0, help_text="Total number of brands")
    post_count = models.IntegerField(
        default=0, help_text="Total number of posts/tweets"
    )

    # Application Stats
    active_sessions = models.IntegerField(
        default=0, help_text="Number of active user sessions"
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "System Statistics"
        verbose_name_plural = "System Statistics"
        indexes = [
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self):
        return f"System Stats - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def capture_current_stats(cls):
        """Capture current system statistics and save to database"""
        import psutil
        import shutil
        from django.contrib.sessions.models import Session

        # Get memory stats
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024 * 1024)  # Convert to MB
        memory_used = memory.used / (1024 * 1024)
        memory_available = memory.available / (1024 * 1024)
        memory_percent = memory.percent

        # Get CPU stats
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # Get disk stats
        disk_usage = shutil.disk_usage("/")
        disk_total = disk_usage.total / (1024 * 1024 * 1024)  # Convert to GB
        disk_used = (disk_usage.total - disk_usage.free) / (1024 * 1024 * 1024)
        disk_free = disk_usage.free / (1024 * 1024 * 1024)
        disk_percent = (disk_used / disk_total) * 100

        # Get database counts safely
        user_count = User.objects.count()

        try:
            from organizations.models import Organization

            organization_count = Organization.objects.count()
        except ImportError:
            organization_count = 0

        brand_count = Brand.objects.count()

        # Count posts from available models
        post_count = 0
        try:
            post_count += Tweet.objects.count()
        except Exception:
            pass

        try:
            post_count += BrandTweet.objects.count()
        except Exception:
            pass

        try:
            post_count += BrandInstagramPost.objects.count()
        except Exception:
            pass

        # Get active sessions
        active_sessions = Session.objects.filter(expire_date__gt=timezone.now()).count()

        # Create and save the stats record
        stats = cls.objects.create(
            memory_total=memory_total,
            memory_used=memory_used,
            memory_available=memory_available,
            memory_percent=memory_percent,
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            disk_total=disk_total,
            disk_used=disk_used,
            disk_free=disk_free,
            disk_percent=disk_percent,
            user_count=user_count,
            organization_count=organization_count,
            brand_count=brand_count,
            post_count=post_count,
            active_sessions=active_sessions,
        )

        return stats

    @classmethod
    def cleanup_old_stats(cls, days_to_keep=7):
        """Remove stats older than specified days"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
        deleted_count = cls.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        return deleted_count

    @classmethod
    def get_last_24_hours(cls):
        """Get stats from the last 24 hours"""
        cutoff_time = timezone.now() - timezone.timedelta(hours=24)
        return cls.objects.filter(timestamp__gte=cutoff_time).order_by("timestamp")

    @classmethod
    def get_stats_by_timespan(cls, timespan):
        """Get stats for different time spans"""
        now = timezone.now()

        if timespan == "1h":
            cutoff_time = now - timezone.timedelta(hours=1)
        elif timespan == "12h":
            cutoff_time = now - timezone.timedelta(hours=12)
        elif timespan == "24h":
            cutoff_time = now - timezone.timedelta(hours=24)
        elif timespan == "2d":
            cutoff_time = now - timezone.timedelta(days=2)
        elif timespan == "5d":
            cutoff_time = now - timezone.timedelta(days=5)
        else:
            # Default to 24h
            cutoff_time = now - timezone.timedelta(hours=24)

        return cls.objects.filter(timestamp__gte=cutoff_time).order_by("timestamp")

    @classmethod
    def get_hourly_averages(cls, hours=24):
        """Get hourly averages for the specified number of hours"""
        from django.db.models import Avg

        cutoff_time = timezone.now() - timezone.timedelta(hours=hours)

        # Group by hour and calculate averages
        stats = (
            cls.objects.filter(timestamp__gte=cutoff_time)
            .extra(select={"hour": "date_trunc('hour', timestamp)"})
            .values("hour")
            .annotate(
                avg_memory_percent=Avg("memory_percent"),
                avg_cpu_percent=Avg("cpu_percent"),
                avg_disk_percent=Avg("disk_percent"),
                avg_active_sessions=Avg("active_sessions"),
            )
            .order_by("hour")
        )

        return stats


class RunwarePricingData(models.Model):
    """
    Model to store Runware pricing data with Gemnar markup
    """

    service_name = models.CharField(max_length=255, unique=True)
    service_description = models.TextField(blank=True)
    runware_price = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )
    runware_unit = models.CharField(
        max_length=100, blank=True
    )  # e.g., "per image", "per request"
    gemnar_price = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )
    markup_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.00
    )  # Default 50% markup
    is_active = models.BooleanField(default=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Runware Pricing Data"
        verbose_name_plural = "Runware Pricing Data"
        ordering = ["service_name"]

    def __str__(self):
        return f"{self.service_name} - Runware: ${self.runware_price} | Gemnar: ${self.gemnar_price}"

    def calculate_gemnar_price(self):
        """Calculate Gemnar price based on Runware price and markup"""
        if self.runware_price:
            markup_multiplier = 1 + (self.markup_percentage / 100)
            self.gemnar_price = self.runware_price * markup_multiplier
            return self.gemnar_price
        return None

    def save(self, *args, **kwargs):
        """Override save to automatically calculate Gemnar price"""
        self.calculate_gemnar_price()
        super().save(*args, **kwargs)


class PricingPageConfig(models.Model):
    """
    Configuration for the pricing page
    """

    page_title = models.CharField(max_length=255, default="Gemnar AI Services Pricing")
    page_description = models.TextField(
        default="Transparent pricing for AI-powered marketing services. No hidden fees, pay as you go."
    )
    featured_services = models.ManyToManyField("RunwarePricingData", blank=True)
    default_markup_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.00
    )
    show_comparison = models.BooleanField(
        default=True
    )  # Show Runware vs Gemnar comparison
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Pricing Page Configuration"
        verbose_name_plural = "Pricing Page Configurations"

    def __str__(self):
        return f"Pricing Config - {self.page_title}"

    @classmethod
    def get_active_config(cls):
        """Get the active pricing configuration"""
        return cls.objects.filter(is_active=True).first()


class PricingScrapingLog(models.Model):
    """
    Log entries for pricing scraping activities
    """

    STATUS_CHOICES = [
        ("success", "Success"),
        ("error", "Error"),
        ("partial", "Partial Success"),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    services_updated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    scraped_data = models.JSONField(default=dict, blank=True)  # Store raw scraped data

    class Meta:
        verbose_name = "Pricing Scraping Log"
        verbose_name_plural = "Pricing Scraping Logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Scraping {self.status} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class CreditTransaction(models.Model):
    """Model to track AI credit transactions (purchases, usage, refunds, etc.)"""

    TRANSACTION_TYPES = [
        ("purchase", "Credit Purchase"),
        ("usage", "Credit Usage"),
        ("refund", "Credit Refund"),
        ("bonus", "Bonus Credits"),
        ("adjustment", "Manual Adjustment"),
    ]

    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="credit_transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount of credits (positive for additions, negative for deductions)",
    )
    description = models.TextField(
        blank=True, help_text="Description of the transaction"
    )
    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Credit balance after this transaction",
    )

    # Reference fields for linking to related objects
    payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe/Cashfree payment intent ID for purchases",
    )
    service_used = models.CharField(
        max_length=100,
        blank=True,
        help_text="AI service used (e.g., 'runware_image_generation')",
    )
    api_request_id = models.CharField(
        max_length=255, blank=True, help_text="API request ID for usage tracking"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_credit_transactions",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Credit Transaction"
        verbose_name_plural = "Credit Transactions"
        indexes = [
            models.Index(fields=["brand", "-created_at"]),
            models.Index(fields=["transaction_type", "-created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        sign = "+" if self.amount >= 0 else ""
        return f"{self.brand.name}: {sign}{self.amount} credits ({self.get_transaction_type_display()})"

    @property
    def is_credit(self):
        """Check if this transaction added credits"""
        return self.amount > 0

    @property
    def is_debit(self):
        """Check if this transaction deducted credits"""
        return self.amount < 0


class CreditPackage(models.Model):
    """Model for predefined credit packages that brands can purchase"""

    name = models.CharField(
        max_length=100, help_text="Package name (e.g., 'Starter Pack')"
    )
    description = models.TextField(
        blank=True, help_text="Description of what's included in this package"
    )
    credits_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Number of credits included in this package",
    )
    price_usd = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price in USD"
    )
    price_inr = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price in INR (optional)",
    )

    # Stripe product/price IDs
    stripe_price_id_usd = models.CharField(
        max_length=255, blank=True, help_text="Stripe price ID for USD pricing"
    )
    stripe_price_id_inr = models.CharField(
        max_length=255, blank=True, help_text="Stripe price ID for INR pricing"
    )

    # Cashfree pricing (if using Cashfree for INR)
    cashfree_product_id = models.CharField(
        max_length=255, blank=True, help_text="Cashfree product ID"
    )

    # Package settings
    is_active = models.BooleanField(
        default=True, help_text="Whether this package is available for purchase"
    )
    is_featured = models.BooleanField(
        default=False, help_text="Featured packages are highlighted in the UI"
    )
    sort_order = models.PositiveIntegerField(
        default=0, help_text="Order for displaying packages (lower numbers first)"
    )

    # Bonus features
    bonus_credits = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Extra bonus credits included (shown separately)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "price_usd"]
        verbose_name = "Credit Package"
        verbose_name_plural = "Credit Packages"

    def __str__(self):
        return f"{self.name} - {self.credits_amount} credits (${self.price_usd})"

    @property
    def total_credits(self):
        """Get total credits including bonus"""
        return self.credits_amount + self.bonus_credits

    @property
    def credits_per_dollar(self):
        """Calculate credits per dollar ratio"""
        if self.price_usd > 0:
            return self.total_credits / self.price_usd
        return 0

    def get_price_for_currency(self, currency="USD"):
        """Get price for specified currency"""
        if currency.upper() == "INR" and self.price_inr:
            return self.price_inr
        return self.price_usd

    def get_stripe_price_id(self, currency="USD"):
        """Get appropriate Stripe price ID for currency"""
        if currency.upper() == "INR" and self.stripe_price_id_inr:
            return self.stripe_price_id_inr
        return self.stripe_price_id_usd


# Import Flow Workspace model
from .workspace_models import FlowWorkspace
from .cloud_storage_models import CloudinaryUpload, UserStorageQuota
