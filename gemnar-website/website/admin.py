from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.utils.html import format_html
from .models import (
    User,
    Brand,
    BrandAsset,
    Image,
    Link,
    PageView,
    ProfileImpression,
    OrganizationInvitation,
    WhoisRecord,
    IPLookupLog,
    TweetConfiguration,
    Tweet,
    BrandTweet,
    TweetStrategy,
    BlogPost,
    BlogComment,
    ReferralCode,
    ReferralClick,
    ReferralSignup,
    ReferralSubscription,
    ReferralBadge,
    ReferralLeaderboard,
    Task,
    TaskApplication,
    EncryptedVariable,
    ServicePrompt,
    ServiceStats,
    ServiceConnection,
    AIServiceUsage,
    AIServiceLimit,
    WebLog,
    # CRM Models
    CRMContact,
    CRMCompany,
    CRMDeal,
    CRMActivity,
    CRMNote,
    CRMPipeline,
    CRMPipelineStage,
    CRMTask,
    BetaTester,
    TwitterMention,
    TweetMention,
    BrandInstagramPost,
    SystemStats,
    CreditTransaction,
    CreditPackage,
)


# Custom list filters for Brand model
class TwitterConfigFilter(admin.SimpleListFilter):
    title = "Twitter Configuration"
    parameter_name = "twitter_config"

    def lookups(self, request, model_admin):
        return (
            ("configured", "Configured"),
            ("not_configured", "Not Configured"),
        )

    def queryset(self, request, queryset):
        if self.value() == "configured":
            return (
                queryset.exclude(twitter_api_key__isnull=True)
                .exclude(twitter_api_key__exact="")
                .exclude(twitter_access_token__isnull=True)
                .exclude(twitter_access_token__exact="")
            )
        elif self.value() == "not_configured":
            return (
                queryset.filter(twitter_api_key__isnull=True)
                .union(queryset.filter(twitter_api_key__exact=""))
                .union(queryset.filter(twitter_access_token__isnull=True))
                .union(queryset.filter(twitter_access_token__exact=""))
            )


class InstagramConfigFilter(admin.SimpleListFilter):
    title = "Instagram Configuration"
    parameter_name = "instagram_config"

    def lookups(self, request, model_admin):
        return (
            ("configured", "Configured"),
            ("not_configured", "Not Configured"),
        )

    def queryset(self, request, queryset):
        if self.value() == "configured":
            return (
                queryset.exclude(instagram_access_token__isnull=True)
                .exclude(instagram_access_token__exact="")
                .exclude(instagram_user_id__isnull=True)
                .exclude(instagram_user_id__exact="")
            )
        elif self.value() == "not_configured":
            return (
                queryset.filter(instagram_access_token__isnull=True)
                .union(queryset.filter(instagram_access_token__exact=""))
                .union(queryset.filter(instagram_user_id__isnull=True))
                .union(queryset.filter(instagram_user_id__exact=""))
            )


class SlackConfigFilter(admin.SimpleListFilter):
    title = "Slack Configuration"
    parameter_name = "slack_config"

    def lookups(self, request, model_admin):
        return (
            ("configured", "Configured"),
            ("not_configured", "Not Configured"),
        )

    def queryset(self, request, queryset):
        if self.value() == "configured":
            return queryset.exclude(slack_webhook_url__isnull=True).exclude(
                slack_webhook_url__exact=""
            )
        elif self.value() == "not_configured":
            return queryset.filter(slack_webhook_url__isnull=True).union(
                queryset.filter(slack_webhook_url__exact="")
            )


def send_welcome_email(modeladmin, request, queryset):
    """Sends a welcome email to the selected users."""
    success_count = 0
    error_count = 0

    for user in queryset:
        try:
            subject = "Welcome to Gemnar!"
            # Simple text email, can be replaced with an HTML template
            message = (
                f"Hi {user.username},\n\nWelcome to our platform. "
                f"We're excited to have you on board!"
            )
            # In a real app, you'd use an HTML template:
            # html_message = render_to_string(
            #     'emails/welcome.html', {'user': user}
            # )
            send_mail(
                subject,
                message,
                "support@gemnar.com",  # From email
                [user.email],
                # html_message=html_message,
                fail_silently=False,
            )
            success_count += 1
        except Exception as e:
            # Log the error, you can use logging module here
            print(f"Failed to send email to {user.email}: {e}")
            error_count += 1

    if success_count > 0:
        modeladmin.message_user(
            request,
            f"Successfully sent welcome emails to {success_count} user(s).",
            messages.SUCCESS,
        )
    if error_count > 0:
        modeladmin.message_user(
            request,
            f"Failed to send welcome emails to {error_count} user(s). "
            f"Check logs for details.",
            messages.ERROR,
        )


send_welcome_email.short_description = "Send welcome email to selected users"


# Register your models here.


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Add custom fields to the User admin
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Info",
            {"fields": ("bio", "profile_image", "created_at", "updated_at")},
        ),
    )
    readonly_fields = ("created_at", "updated_at")
    # Show all user fields in the list view (may be very wide). Consider trimming later for usability.
    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
        "last_login",
        "date_joined",
        # Custom fields
        "bio",
        "age",
        "instagram_handle",
        "profile_image",
        "banner_image",
        "additional_image1",
        "additional_image2",
        "story_price",
        "post_price",
        "reel_price",
        "impressions_count",
        "twitter_api_key",
        "twitter_api_secret",
        "twitter_access_token",
        "twitter_access_token_secret",
        "twitter_bearer_token",
        "twitter_username",
        "name",
        "description",
        "instagram_url",
        "photo1",
        "photo2",
        "photo3",
        "photo4",
        "photo5",
        "photo6",
        "brand1",
        "brand2",
        "brand3",
        "brand4",
        "brand5",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "created_at")
    actions = [send_welcome_email]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "owner",
        "organization",
        "credits_balance",
        "is_default",
        "has_twitter_config",
        "twitter_username",
        "has_instagram_config",
        "instagram_username",
        "has_slack_config",
        "total_posts_display",
        "recent_activity_display",
        "subscription_status_display",
        "subscription_plan_display",
        "preferred_payment_method",
        "created_at",
    )
    list_filter = (
        "created_at",
        "updated_at",
        "is_default",
        "stripe_subscription_status",
        "preferred_payment_method",
        TwitterConfigFilter,
        InstagramConfigFilter,
        SlackConfigFilter,
        "slack_notifications_enabled",
        "organization",
        "owner",
    )
    search_fields = (
        "name",
        "slug",
        "description",
        "url",
        "owner__username",
        "owner__email",
        "organization__name",
        "stripe_customer_id",
        "stripe_subscription_id",
        "cashfree_customer_id",
        "twitter_username",
        "twitter_api_key",
        "instagram_user_id",
        "instagram_username",
        "instagram_app_id",
        "slack_channel",
    )
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "slug",
                    "owner",
                    "organization",
                    "is_default",
                    "url",
                    "description",
                    "logo",
                )
            },
        ),
        (
            "AI Credits",
            {
                "fields": ("credits_balance",),
                "description": "Current AI credits balance for this brand",
            },
        ),
        (
            "Instagram API Configuration",
            {
                "fields": (
                    "instagram_access_token",
                    "instagram_user_id",
                    "instagram_username",
                    "instagram_app_id",
                    "instagram_app_secret",
                ),
                "classes": ("collapse",),
                "description": "Instagram API credentials for posting content",
            },
        ),
        (
            "Twitter API Configuration",
            {
                "fields": (
                    "twitter_api_key",
                    "twitter_api_secret",
                    "twitter_access_token",
                    "twitter_access_token_secret",
                    "twitter_bearer_token",
                    "twitter_username",
                ),
                "classes": ("collapse",),
                "description": "Twitter API credentials for posting content",
            },
        ),
        (
            "Payment & Subscription",
            {
                "fields": (
                    "stripe_customer_id",
                    "stripe_subscription_id",
                    "stripe_subscription_status",
                    "last_payment_date",
                    "cashfree_customer_id",
                    "cashfree_order_id",
                    "cashfree_payment_status",
                    "preferred_payment_method",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Slack Integration",
            {
                "fields": (
                    "slack_webhook_url",
                    "slack_channel",
                    "slack_notifications_enabled",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def subscription_status_display(self, obj):
        """Display subscription status with color coding"""
        if not obj.stripe_subscription_status:
            return "No Subscription"

        status_colors = {
            "active": "🟢",
            "trialing": "🟡",
            "past_due": "🟠",
            "canceled": "🔴",
            "unpaid": "🔴",
            "incomplete": "🟡",
        }

        icon = status_colors.get(obj.stripe_subscription_status, "⚪")
        return f"{icon} {obj.stripe_subscription_status.title()}"

    subscription_status_display.short_description = "Subscription Status"

    def subscription_plan_display(self, obj):
        """Display subscription plan"""
        plan = obj.get_subscription_plan()
        if plan:
            plan_emojis = {
                "starter": "🥉 Starter ($99)",
                "professional": "🥈 Professional ($199)",
                "enterprise": "🥇 Enterprise ($299)",
            }
            return plan_emojis.get(plan, f"📋 {plan.title()}")
        return "No Plan"

    subscription_plan_display.short_description = "Plan"

    def twitter_config_display(self, obj):
        """Display Twitter configuration status"""
        if obj.has_twitter_config:
            return f"✅ @{obj.twitter_username or 'username_missing'}"
        return "❌ Not Configured"

    twitter_config_display.short_description = "Twitter Config"

    def instagram_config_display(self, obj):
        """Display Instagram configuration status"""
        if obj.has_instagram_config:
            return f"✅ @{obj.instagram_username or obj.instagram_user_id or 'username_missing'}"
        return "❌ Not Configured"

    instagram_config_display.short_description = "Instagram Config"

    def slack_config_display(self, obj):
        """Display Slack configuration status"""
        if obj.has_slack_config:
            status = "🔔" if obj.slack_notifications_enabled else "🔕"
            channel = obj.slack_channel or "default"
            return f"{status} #{channel}"
        return "❌ Not Configured"

    slack_config_display.short_description = "Slack Config"

    def payment_info_display(self, obj):
        """Display payment information summary"""
        method = obj.preferred_payment_method.title()
        if obj.stripe_customer_id or obj.cashfree_customer_id:
            customer_id = obj.stripe_customer_id or obj.cashfree_customer_id
            return (
                f"{method}: {customer_id[:15]}..."
                if len(customer_id) > 15
                else f"{method}: {customer_id}"
            )
        return f"{method}: No Customer ID"

    payment_info_display.short_description = "Payment Info"

    def total_posts_display(self, obj):
        """Display total number of posts for this brand"""
        tweet_count = obj.brand_tweets.count()
        instagram_count = obj.brand_instagram_posts.count()
        asset_count = obj.assets.count()  # BrandAsset.brand related_name='assets'
        return f"🐦 {tweet_count} | 📷 {instagram_count} | 📁 {asset_count}"

    total_posts_display.short_description = "Posts & Assets"

    def recent_activity_display(self, obj):
        """Show recent activity summary"""
        from django.utils import timezone
        from datetime import timedelta

        last_week = timezone.now() - timedelta(days=7)

        recent_tweets = obj.brand_tweets.filter(created_at__gte=last_week).count()
        recent_instagram = obj.brand_instagram_posts.filter(
            created_at__gte=last_week
        ).count()

        if recent_tweets + recent_instagram == 0:
            return "No recent activity"

        return f"📊 {recent_tweets + recent_instagram} posts (7 days)"

    recent_activity_display.short_description = "Recent Activity"

    # Add inlines to show related objects
    class BrandTweetInline(admin.TabularInline):
        model = BrandTweet
        extra = 0
        max_num = 5
        fields = ("content", "status", "scheduled_for", "posted_at")
        readonly_fields = ("posted_at",)

    class BrandInstagramPostInline(admin.TabularInline):
        model = BrandInstagramPost
        extra = 0
        max_num = 5
        fields = ("content", "status", "scheduled_for", "posted_at")
        readonly_fields = ("posted_at",)

    class BrandAssetInline(admin.TabularInline):
        model = BrandAsset
        extra = 0
        max_num = 3
        fields = ("name", "asset_type", "is_active")

    inlines = [BrandTweetInline, BrandInstagramPostInline, BrandAssetInline]


@admin.register(BrandAsset)
class BrandAssetAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "brand",
        "asset_type",
        "file_size_display",
        "is_active",
        "created_at",
    ]
    list_filter = ["asset_type", "is_active", "created_at", "brand"]
    search_fields = ["name", "brand__name", "description"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "brand",
                    "name",
                    "description",
                    "asset_type",
                    "is_active",
                ]
            },
        ),
        (
            "File",
            {
                "fields": [
                    "file",
                ]
            },
        ),
        (
            "Metadata",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    def file_size_display(self, obj):
        """Display file size in MB"""
        if obj.file and hasattr(obj.file, "size"):
            return f"{obj.file.size / (1024 * 1024):.2f} MB"
        return "N/A"

    file_size_display.short_description = "File Size"


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "brand", "created_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("title", "alt_text", "user__username", "brand__name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Image Information", {"fields": ("title", "image", "alt_text")}),
        ("Associations", {"fields": ("user", "brand")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "platform",
        "link_type",
        "user",
        "brand",
        "is_active",
        "order",
    )
    list_filter = ("platform", "link_type", "is_active", "created_at")
    search_fields = ("title", "url", "user__username", "brand__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("order", "-created_at")

    fieldsets = (
        ("Link Information", {"fields": ("title", "url", "link_type", "platform")}),
        ("Associations", {"fields": ("user", "brand")}),
        ("Display Settings", {"fields": ("order", "is_active")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# CustomSession admin removed - replaced by analytics service


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = (
        "path_display",
        "method",
        "user_display",
        "status_code_display",
        "response_time_display",
        "timestamp",
    )
    list_filter = (
        "method",
        "status_code",
        "timestamp",
        "user",
    )
    search_fields = ("url", "path", "user__username", "user__email", "referrer")
    readonly_fields = ("timestamp",)
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"

    fieldsets = (
        ("Page Information", {"fields": ("url", "path", "method", "referrer")}),
        ("User Context", {"fields": ("user",)}),
        ("Response Details", {"fields": ("status_code", "response_time")}),
        ("Metadata", {"fields": ("timestamp",), "classes": ("collapse",)}),
    )

    def path_display(self, obj):
        """Show a shortened path"""
        if len(obj.path) > 40:
            return obj.path[:37] + "..."
        return obj.path

    path_display.short_description = "Path"

    def user_display(self, obj):
        """Show user with better formatting"""
        if obj.user:
            return f"👤 {obj.user.username}"
        return "👤 Anonymous"

    user_display.short_description = "User"

    def status_code_display(self, obj):
        """Show status code with color coding"""
        if obj.status_code:
            if obj.status_code < 300:
                icon = "✅"
            elif obj.status_code < 400:
                icon = "🔄"
            elif obj.status_code < 500:
                icon = "⚠️"
            else:
                icon = "❌"
            return f"{icon} {obj.status_code}"
        return "❓"

    status_code_display.short_description = "Status"

    def response_time_display(self, obj):
        """Show response time with formatting"""
        if obj.response_time is not None:
            if obj.response_time > 2000:
                icon = "🐌"
            elif obj.response_time > 1000:
                icon = "⚠️"
            else:
                icon = "⚡"
            return f"{icon} {obj.response_time}ms"
        return "❓"

    response_time_display.short_description = "Response Time"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(ProfileImpression)
class ProfileImpressionAdmin(admin.ModelAdmin):
    list_display = (
        "profile_user",
        "viewer",
        "ip_address",
        "timestamp",
        "country",
        "city",
    )
    list_filter = ("timestamp", "country")
    search_fields = (
        "profile_user__username",
        "viewer__username",
        "ip_address",
        "country",
        "city",
    )
    readonly_fields = ("timestamp",)
    ordering = ("-timestamp",)

    fieldsets = (
        (
            "Profile View Information",
            {"fields": ("profile_user", "viewer", "ip_address", "user_agent")},
        ),
        ("Location", {"fields": ("country", "city", "referrer")}),
        ("Context", {"fields": ("session",)}),
        ("Metadata", {"fields": ("timestamp",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("profile_user", "viewer", "session")
        )


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "organization",
        "invited_by",
        "status",
        "is_admin",
        "created_at",
        "expires_at",
    ]
    list_filter = ["status", "is_admin", "created_at", "expires_at"]
    search_fields = ["email", "organization__name", "invited_by__username"]
    readonly_fields = ["created_at", "accepted_at", "token"]

    fieldsets = [
        (
            "Invitation Details",
            {
                "fields": [
                    "organization",
                    "email",
                    "invited_by",
                    "is_admin",
                    "status",
                ]
            },
        ),
        (
            "Dates",
            {
                "fields": [
                    "created_at",
                    "expires_at",
                    "accepted_at",
                ]
            },
        ),
        (
            "Technical",
            {
                "fields": [
                    "token",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["resend_invitations", "expire_invitations"]

    def resend_invitations(self, request, queryset):
        """Resend selected invitations"""
        count = 0
        for invitation in queryset.filter(status="pending"):
            # Here you would implement the resend logic
            count += 1
        self.message_user(
            request,
            f"Resent {count} invitations.",
            messages.SUCCESS,
        )

    resend_invitations.short_description = "Resend selected invitations"

    def expire_invitations(self, request, queryset):
        """Expire selected pending invitations"""
        count = queryset.filter(status="pending").update(status="expired")
        self.message_user(
            request,
            f"Expired {count} invitations.",
            messages.SUCCESS,
        )

    expire_invitations.short_description = "Expire selected invitations"


@admin.register(WhoisRecord)
class WhoisRecordAdmin(admin.ModelAdmin):
    list_display = (
        "ip_address",
        "organization",
        "country",
        "lookup_successful",
        "lookup_date",
    )
    list_filter = ("lookup_successful", "country_code", "lookup_date")
    search_fields = ("ip_address", "organization", "country", "city", "asn")
    readonly_fields = ("lookup_date", "last_updated")
    ordering = ("-lookup_date",)

    fieldsets = (
        (
            "IP Information",
            {"fields": ("ip_address", "lookup_successful", "error_message")},
        ),
        (
            "Organization Details",
            {
                "fields": (
                    "organization",
                    "network_name",
                    "asn",
                    "asn_description",
                )
            },
        ),
        (
            "Location",
            {"fields": ("country", "country_code", "region", "city", "network_range")},
        ),
        ("Raw Data", {"fields": ("raw_whois_data",), "classes": ("collapse",)}),
        (
            "Metadata",
            {"fields": ("lookup_date", "last_updated"), "classes": ("collapse",)},
        ),
    )


@admin.register(IPLookupLog)
class IPLookupLogAdmin(admin.ModelAdmin):
    list_display = (
        "ip_address",
        "lookup_source",
        "lookup_successful",
        "user",
        "lookup_timestamp",
    )
    list_filter = ("lookup_source", "lookup_successful", "lookup_timestamp")
    search_fields = ("ip_address", "user__username")
    readonly_fields = ("lookup_timestamp",)
    ordering = ("-lookup_timestamp",)

    fieldsets = (
        (
            "Lookup Information",
            {
                "fields": (
                    "ip_address",
                    "whois_record",
                    "lookup_source",
                    "lookup_successful",
                )
            },
        ),
        ("Context", {"fields": ("user", "session")}),
        ("Metadata", {"fields": ("lookup_timestamp",), "classes": ("collapse",)}),
    )


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "user",
        "total_points",
        "total_clicks",
        "total_signups",
        "total_subscriptions",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["code", "user__username", "user__email"]
    readonly_fields = [
        "code",
        "total_points",
        "total_clicks",
        "total_signups",
        "total_subscriptions",
        "created_at",
    ]
    ordering = ["-total_points", "-created_at"]

    fieldsets = (
        (
            "Code Information",
            {"fields": ("code", "user", "is_active", "created_at")},
        ),
        (
            "Statistics",
            {
                "fields": (
                    "total_points",
                    "total_clicks",
                    "total_signups",
                    "total_subscriptions",
                    "total_rewards_earned",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ReferralClick)
class ReferralClickAdmin(admin.ModelAdmin):
    list_display = [
        "referral_code",
        "ip_address",
        "timestamp",
        "country",
        "city",
    ]
    list_filter = ["timestamp", "country"]
    search_fields = ["referral_code__code", "ip_address"]
    readonly_fields = ["timestamp"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("referral_code__user")


@admin.register(ReferralSignup)
class ReferralSignupAdmin(admin.ModelAdmin):
    list_display = [
        "referral_code",
        "referred_user",
        "timestamp",
        "reward_given",
        "reward_amount",
    ]
    list_filter = ["timestamp", "reward_given"]
    search_fields = ["referral_code__code", "referred_user__username"]
    readonly_fields = ["timestamp"]
    ordering = ["-timestamp"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("referral_code__user", "referred_user")
        )


@admin.register(ReferralSubscription)
class ReferralSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "referral_code",
        "referred_user",
        "subscription_type",
        "subscription_amount",
        "reward_amount",
        "timestamp",
    ]
    list_filter = ["timestamp", "subscription_type", "reward_given"]
    search_fields = ["referral_code__code", "referred_user__username"]
    readonly_fields = ["timestamp", "reward_amount"]
    ordering = ["-timestamp"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("referral_code__user", "referred_user")
        )


@admin.register(ReferralBadge)
class ReferralBadgeAdmin(admin.ModelAdmin):
    list_display = ["user", "badge_type", "earned_at"]
    list_filter = ["badge_type", "earned_at"]
    search_fields = ["user__username", "badge_type"]
    readonly_fields = ["earned_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(ReferralLeaderboard)
class ReferralLeaderboardAdmin(admin.ModelAdmin):
    list_display = [
        "period_type",
        "period_start",
        "period_end",
        "winner",
        "runner_up",
        "third_place",
    ]
    list_filter = ["period_type", "period_start"]
    search_fields = [
        "winner__username",
        "runner_up__username",
        "third_place__username",
    ]
    readonly_fields = ["created_at"]
    ordering = ["-period_start"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("winner", "runner_up", "third_place")
        )


# Custom admin actions
def recalculate_referral_points(modeladmin, request, queryset):
    """Recalculate points for selected referral codes"""
    updated_count = 0
    for referral_code in queryset:
        old_points = referral_code.total_points
        new_points = referral_code.calculate_points()
        if old_points != new_points:
            updated_count += 1

    modeladmin.message_user(
        request,
        f"Recalculated points for {updated_count} referral codes.",
        messages.SUCCESS,
    )


recalculate_referral_points.short_description = (
    "Recalculate points for selected referral codes"
)

# Add the action to ReferralCodeAdmin
ReferralCodeAdmin.actions = ["recalculate_referral_points"]
ReferralCodeAdmin.actions.append(recalculate_referral_points)


@admin.register(TweetConfiguration)
class TweetConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active", "created_at", "updated_at"]
    search_fields = ["name", "user__username", "topics"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "user", "is_active")},
        ),
        (
            "Tweet Content",
            {
                "fields": (
                    "prompt_template",
                    "topics",
                    "tones",
                    "keywords",
                    "hashtags",
                ),
                "classes": ("wide",),
            },
        ),
        (
            "Schedule",
            {"fields": ("schedule",), "classes": ("collapse",)},
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = [
        "content_preview",
        "configuration",
        "status",
        "scheduled_for",
        "posted_at",
        "created_at",
    ]
    list_filter = ["status", "scheduled_for", "posted_at", "created_at"]
    search_fields = [
        "content",
        "configuration__name",
        "configuration__user__username",
    ]
    readonly_fields = ["created_at", "updated_at", "tweet_id", "posted_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Tweet Information",
            {
                "fields": (
                    "configuration",
                    "content",
                    "status",
                    "tweet_id",
                )
            },
        ),
        (
            "Scheduling",
            {"fields": ("scheduled_for", "posted_at")},
        ),
        (
            "Generation Details",
            {
                "fields": ("prompt_used", "error_message"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content Preview"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("configuration__user")


@admin.register(BrandTweet)
class BrandTweetAdmin(admin.ModelAdmin):
    list_display = [
        "content_preview",
        "brand",
        "status",
        "scheduled_for",
        "posted_at",
        "created_at",
    ]
    list_filter = [
        "status",
        "scheduled_for",
        "posted_at",
        "created_at",
        "brand__organization",
    ]
    search_fields = [
        "content",
        "brand__name",
        "brand__organization__name",
        "ai_prompt",
    ]
    readonly_fields = ["created_at", "updated_at", "tweet_id", "posted_at"]
    ordering = ["-scheduled_for", "-created_at"]

    fieldsets = (
        (
            "Tweet Information",
            {
                "fields": (
                    "brand",
                    "content",
                    "status",
                    "scheduled_for",
                    "posted_at",
                )
            },
        ),
        (
            "Media & AI",
            {
                "fields": (
                    "image",
                    "ai_prompt",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Technical Details",
            {
                "fields": (
                    "tweet_id",
                    "error_message",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content"

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("brand", "brand__organization")
        )

    def get_list_display(self, request):
        """Show different columns based on status filter"""
        list_display = list(super().get_list_display(request))

        # If filtering by status, show relevant columns
        status_filter = request.GET.get("status__exact")
        if status_filter == "approved":
            # For approved tweets, emphasize scheduled time
            list_display.insert(3, "time_until_posted")
        elif status_filter == "posted":
            # For posted tweets, emphasize post time
            list_display.insert(4, "time_since_posted")

        return list_display

    def time_until_posted(self, obj):
        """Show time until scheduled post for approved tweets"""
        if obj.status == "approved" and obj.scheduled_for:
            from django.utils import timezone

            now = timezone.now()
            if obj.scheduled_for > now:
                delta = obj.scheduled_for - now
                if delta.days > 0:
                    return f"In {delta.days} days"
                elif delta.seconds > 3600:
                    hours = delta.seconds // 3600
                    return f"In {hours} hours"
                else:
                    minutes = delta.seconds // 60
                    return f"In {minutes} minutes"
            else:
                return "Overdue"
        return "-"

    time_until_posted.short_description = "Time Until Posted"

    def time_since_posted(self, obj):
        """Show time since posted for posted tweets"""
        if obj.status == "posted" and obj.posted_at:
            from django.utils import timezone

            now = timezone.now()
            delta = now - obj.posted_at
            if delta.days > 0:
                return f"{delta.days} days ago"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} hours ago"
            else:
                minutes = delta.seconds // 60
                return f"{minutes} minutes ago"
        return "-"

    time_since_posted.short_description = "Time Since Posted"

    actions = ["approve_tweets", "mark_as_draft", "post_tweets_now"]

    def approve_tweets(self, request, queryset):
        """Approve selected tweets for posting"""
        updated = queryset.update(status="approved")
        self.message_user(
            request,
            f"Successfully approved {updated} tweet(s) for posting.",
            messages.SUCCESS,
        )

    approve_tweets.short_description = "Approve selected tweets"

    def mark_as_draft(self, request, queryset):
        """Mark selected tweets as draft"""
        updated = queryset.update(status="draft")
        self.message_user(
            request,
            f"Successfully marked {updated} tweet(s) as draft.",
            messages.SUCCESS,
        )

    mark_as_draft.short_description = "Mark selected tweets as draft"

    def post_tweets_now(self, request, queryset):
        """Post approved tweets immediately"""
        approved_tweets = queryset.filter(status="approved")
        success_count = 0
        error_count = 0

        for tweet in approved_tweets:
            try:
                success, error = tweet.post_to_twitter()
                if success:
                    success_count += 1
                else:
                    error_count += 1
            except Exception:
                error_count += 1

        if success_count > 0:
            self.message_user(
                request,
                f"Successfully posted {success_count} tweet(s).",
                messages.SUCCESS,
            )
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to post {error_count} tweet(s). Check error messages.",
                messages.ERROR,
            )

    post_tweets_now.short_description = "Post approved tweets now"


@admin.register(BrandInstagramPost)
class BrandInstagramPostAdmin(admin.ModelAdmin):
    list_display = [
        "brand",
        "content_preview",
        "is_video_post",
        "status",
        "scheduled_for",
        "posted_at",
        "created_at",
    ]
    list_filter = [
        "status",
        "is_video_post",
        "brand",
        "created_at",
        "scheduled_for",
        "posted_at",
    ]
    search_fields = ["content", "brand__name", "ai_prompt", "video_prompt"]
    readonly_fields = [
        "instagram_id",
        "instagram_url",
        "posted_at",
        "created_at",
        "updated_at",
        "video_duration",
    ]

    fieldsets = [
        (
            "Content",
            {
                "fields": [
                    "brand",
                    "content",
                    "is_video_post",
                ]
            },
        ),
        (
            "Media",
            {
                "fields": [
                    "image",
                    "video",
                    "video_thumbnail",
                    "video_duration",
                    "video_quality",
                ]
            },
        ),
        (
            "AI Generation",
            {
                "fields": [
                    "ai_prompt",
                    "video_prompt",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Scheduling",
            {
                "fields": [
                    "status",
                    "scheduled_for",
                ]
            },
        ),
        (
            "Instagram",
            {
                "fields": [
                    "instagram_id",
                    "instagram_url",
                    "posted_at",
                    "error_message",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Metadata",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    def content_preview(self, obj):
        """Show a preview of the content"""
        if obj.content:
            return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return "(No content)"

    content_preview.short_description = "Content Preview"

    def has_media_display(self, obj):
        """Show if post has media"""
        if obj.is_video_post:
            return "📹 Video" if obj.video else "📹 No Video"
        else:
            return "🖼️ Image" if obj.image else "🖼️ No Image"

    has_media_display.short_description = "Media"

    actions = ["approve_posts", "schedule_posts_now", "generate_video"]

    def approve_posts(self, request, queryset):
        """Approve selected posts"""
        count = queryset.filter(status="draft").update(status="approved")
        self.message_user(
            request,
            f"Approved {count} Instagram posts.",
            messages.SUCCESS,
        )

    approve_posts.short_description = "Approve selected posts"

    def schedule_posts_now(self, request, queryset):
        """Schedule selected posts to post now"""
        from django.utils import timezone

        count = queryset.filter(status="approved").update(scheduled_for=timezone.now())
        self.message_user(
            request,
            f"Scheduled {count} Instagram posts to post now.",
            messages.SUCCESS,
        )

    schedule_posts_now.short_description = "Schedule selected posts to post now"

    def generate_video(self, request, queryset):
        """Generate videos for selected posts"""
        from website.video_utils import generate_video_for_brand_post

        success_count = 0
        for post in queryset.filter(is_video_post=True, video__isnull=True):
            if post.video_prompt:
                success = generate_video_for_brand_post(
                    post, post.video_prompt, quality=post.video_quality, duration=5.0
                )
                if success:
                    success_count += 1

        self.message_user(
            request,
            f"Generated videos for {success_count} Instagram posts.",
            messages.SUCCESS if success_count > 0 else messages.WARNING,
        )

    generate_video.short_description = "Generate videos for selected posts"


@admin.register(TweetStrategy)
class TweetStrategyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "is_active",
        "usage_count",
        "created_at",
    ]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["name", "description", "prompt_template"]
    readonly_fields = ["usage_count", "created_at", "updated_at"]

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "name",
                    "category",
                    "description",
                    "is_active",
                ]
            },
        ),
        (
            "Prompt Configuration",
            {
                "fields": [
                    "prompt_template",
                    "example_output",
                ]
            },
        ),
        (
            "Strategy Settings",
            {
                "fields": [
                    "tone_suggestions",
                    "hashtag_suggestions",
                    "timing_suggestions",
                ]
            },
        ),
        (
            "Analytics",
            {
                "fields": ["usage_count"],
                "classes": ["collapse"],
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ["collapse"],
            },
        ),
    ]

    def get_form(self, request, obj=None, **kwargs):
        """Customize the form to show helpful text for JSON fields"""
        form = super().get_form(request, obj, **kwargs)

        # Add help text for JSON fields
        if "tone_suggestions" in form.base_fields:
            form.base_fields[
                "tone_suggestions"
            ].help_text = 'JSON array of suggested tones, e.g., ["professional", "casual", "humorous"]'

        if "hashtag_suggestions" in form.base_fields:
            form.base_fields[
                "hashtag_suggestions"
            ].help_text = (
                'JSON array of hashtags, e.g., ["#marketing", "#business", "#tips"]'
            )

        if "timing_suggestions" in form.base_fields:
            form.base_fields[
                "timing_suggestions"
            ].help_text = 'JSON object with timing info, e.g., {"best_time": "9AM-11AM", "frequency": "daily", "days": ["Monday", "Wednesday", "Friday"]}'

        return form


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author",
        "category",
        "status_display",
        "is_featured",
        "comments_count",
        "word_count_display",
        "created_at",
        "published_at",
    ]
    list_filter = [
        "status",
        "category",
        "is_featured",
        "author",
        "created_at",
        "published_at",
    ]
    search_fields = [
        "title",
        "content",
        "excerpt",
        "author__username",
        "author__email",
        "tags",
        "meta_description",
        "meta_keywords",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "published_at",
        "slug",
    ]
    prepopulated_fields = {"slug": ("title",)}
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    def status_display(self, obj):
        """Show status with icons"""
        status_icons = {
            "draft": "📝",
            "published": "✅",
            "archived": "📦",
        }
        icon = status_icons.get(obj.status, "❓")
        featured = " ⭐" if obj.is_featured else ""
        return f"{icon} {obj.status.title()}{featured}"

    status_display.short_description = "Status"

    def comments_count(self, obj):
        """Show comment count"""
        count = obj.comments.count()
        approved_count = obj.comments.filter(is_approved=True).count()
        if count == 0:
            return "No comments"
        return f"💬 {approved_count}/{count}"

    comments_count.short_description = "Comments"

    def word_count_display(self, obj):
        """Show approximate word count"""
        if obj.content:
            word_count = len(obj.content.split())
            if word_count > 1000:
                return f"📄 {word_count} words (long)"
            elif word_count > 500:
                return f"📄 {word_count} words (medium)"
            else:
                return f"📄 {word_count} words (short)"
        return "📄 No content"

    word_count_display.short_description = "Length"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "title",
                    "slug",
                    "author",
                    "category",
                    "status",
                    "is_featured",
                )
            },
        ),
        (
            "Content",
            {
                "fields": (
                    "excerpt",
                    "content",
                    "featured_image",
                    "tags",
                ),
                "classes": ("wide",),
            },
        ),
        (
            "SEO",
            {
                "fields": ("meta_description", "meta_keywords"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at", "published_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author")


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = [
        "content_preview",
        "author",
        "post",
        "is_approved",
        "created_at",
    ]
    list_filter = ["is_approved", "created_at"]
    search_fields = ["content", "author__username", "post__title"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Comment Information",
            {"fields": ("post", "author", "content", "is_approved")},
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content Preview"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author", "post")


@admin.register(EncryptedVariable)
class EncryptedVariableAdmin(admin.ModelAdmin):
    list_display = [
        "key",
        "value_preview",
        "is_active",
        "created_by",
        "last_modified_by",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active", "created_at", "updated_at"]
    search_fields = ["key", "description"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "created_by",
        "last_modified_by",
        "decrypted_value_display",
    ]
    ordering = ["key"]

    fieldsets = (
        (
            "Variable Information",
            {"fields": ("key", "value", "description", "is_active")},
        ),
        (
            "Audit Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "created_by",
                    "last_modified_by",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Decrypted Value Preview",
            {"fields": ("decrypted_value_display",), "classes": ("collapse",)},
        ),
    )

    def value_preview(self, obj):
        """Show a preview of the encrypted value"""
        if obj.value:
            return f"{obj.value[:50]}..." if len(obj.value) > 50 else obj.value
        return "No value"

    value_preview.short_description = "Value Preview"

    def decrypted_value_display(self, obj):
        """Display the decrypted value for admin viewing"""
        try:
            decrypted = obj.get_decrypted_value()
            return decrypted
        except Exception as e:
            return f"Error decrypting: {str(e)}"

    decrypted_value_display.short_description = "Decrypted Value"

    def save_model(self, request, obj, form, change):
        """Override save to track who made the change"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("created_by", "last_modified_by")
        )


@admin.register(ServicePrompt)
class ServicePromptAdmin(admin.ModelAdmin):
    list_display = ["user", "service", "status", "created_at", "posted_at"]
    list_filter = ["service", "status", "created_at"]
    search_fields = ["user__username", "user__email", "prompt"]
    readonly_fields = ["created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(ServiceStats)
class ServiceStatsAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "service",
        "total_prompts",
        "successful_posts",
        "pending_posts",
        "failed_posts",
    ]
    list_filter = ["service", "last_updated"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["last_updated"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(ServiceConnection)
class ServiceConnectionAdmin(admin.ModelAdmin):
    list_display = ["user", "service", "is_connected", "username", "created_at"]
    list_filter = ["service", "is_connected", "created_at"]
    search_fields = ["user__username", "user__email", "username"]
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


@admin.register(AIServiceUsage)
class AIServiceUsageAdmin(admin.ModelAdmin):
    list_display = [
        "brand",
        "service",
        "usage_date",
        "usage_count",
        "last_used",
    ]
    list_filter = ["service", "usage_date", "brand__organization"]
    search_fields = ["brand__name", "brand__organization__name"]
    readonly_fields = ["usage_date", "last_used"]
    ordering = ["-usage_date", "brand", "service"]

    fieldsets = (
        (
            "Usage Information",
            {
                "fields": (
                    "brand",
                    "service",
                    "usage_date",
                    "usage_count",
                    "last_used",
                )
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(brand__owner=request.user)

    def has_add_permission(self, request):
        # Usage should be automatically tracked, not manually added
        return False


@admin.register(AIServiceLimit)
class AIServiceLimitAdmin(admin.ModelAdmin):
    list_display = [
        "service",
        "daily_limit",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["service", "is_active", "created_at"]
    search_fields = ["service", "description"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["service"]

    fieldsets = (
        (
            "Limit Configuration",
            {
                "fields": (
                    "service",
                    "daily_limit",
                    "description",
                    "is_active",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only superusers can manage service limits
        if request.user.is_superuser:
            return qs
        return qs.none()

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(WebLog)
class WebLogAdmin(admin.ModelAdmin):
    list_display = [
        "activity_name",
        "activity_type",
        "status",
        "items_processed",
        "items_succeeded",
        "items_failed",
        "started_at",
        "completed_at",
        "duration_seconds",
        "user",
        "brand",
    ]
    list_filter = [
        "activity_type",
        "status",
        "started_at",
        "completed_at",
    ]
    search_fields = [
        "activity_name",
        "description",
        "error_message",
    ]
    readonly_fields = [
        "started_at",
        "completed_at",
        "duration_seconds",
    ]
    raw_id_fields = ["user", "brand"]
    ordering = ["-started_at"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "activity_type",
                    "activity_name",
                    "status",
                    "description",
                )
            },
        ),
        (
            "Metrics",
            {
                "fields": (
                    "items_processed",
                    "items_succeeded",
                    "items_failed",
                )
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    "started_at",
                    "completed_at",
                    "duration_seconds",
                )
            },
        ),
        (
            "Error Information",
            {
                "fields": (
                    "error_message",
                    "error_traceback",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Associations",
            {
                "fields": (
                    "user",
                    "brand",
                )
            },
        ),
        ("Details", {"fields": ("details",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "brand")


# Unregister and re-register Site admin to ensure it's visible
admin.site.unregister(Site)
admin.site.register(Site, SiteAdmin)


# =====================================
# CRM ADMIN CLASSES
# =====================================


@admin.register(CRMContact)
class CRMContactAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "email",
        "company",
        "contact_type",
        "assigned_to",
        "organization",
        "created_at",
    ]
    list_filter = [
        "contact_type",
        "lead_source",
        "organization",
        "assigned_to",
        "is_active",
        "created_at",
    ]
    search_fields = [
        "first_name",
        "last_name",
        "email",
        "company",
        "job_title",
        "phone",
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 50

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "company",
                    "job_title",
                )
            },
        ),
        ("Contact Details", {"fields": ("contact_type", "lead_source", "assigned_to")}),
        (
            "Address",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Social Media",
            {
                "fields": ("linkedin_url", "twitter_handle", "website"),
                "classes": ("collapse",),
            },
        ),
        ("Notes & Tags", {"fields": ("description", "tags")}),
        (
            "Organization & Status",
            {
                "fields": (
                    "organization",
                    "is_active",
                    "last_contact_date",
                    "created_by",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("organization", "assigned_to", "created_by")
        )


@admin.register(CRMCompany)
class CRMCompanyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "website",
        "email",
        "industry",
        "assigned_to",
        "organization",
        "created_at",
    ]
    list_filter = [
        "industry",
        "organization",
        "assigned_to",
        "is_active",
        "created_at",
    ]
    search_fields = [
        "name",
        "email",
        "website",
        "industry",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 50

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "website",
                    "email",
                    "phone",
                    "industry",
                )
            },
        ),
        (
            "Social Media",
            {
                "fields": ("twitter_handle", "instagram_handle"),
                "classes": ("collapse",),
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Notes & Tags", {"fields": ("description", "tags")}),
        (
            "Organization & Status",
            {
                "fields": (
                    "organization",
                    "assigned_to",
                    "is_active",
                    "created_by",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("organization", "assigned_to", "created_by")
        )


@admin.register(CRMDeal)
class CRMDealAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "contact",
        "stage",
        "value",
        "currency",
        "probability",
        "expected_close_date",
        "assigned_to",
    ]
    list_filter = [
        "stage",
        "currency",
        "organization",
        "assigned_to",
        "is_active",
        "created_at",
    ]
    search_fields = ["name", "description", "contact__email"]
    readonly_fields = ["created_at", "updated_at", "weighted_value"]
    date_hierarchy = "expected_close_date"
    list_per_page = 50

    fieldsets = (
        (
            "Deal Information",
            {"fields": ("name", "description", "contact", "organization")},
        ),
        ("Sales Pipeline", {"fields": ("stage", "probability", "assigned_to")}),
        ("Financial", {"fields": ("value", "currency", "weighted_value")}),
        ("Timeline", {"fields": ("expected_close_date", "actual_close_date")}),
        ("Status", {"fields": ("is_active", "lost_reason", "created_by")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("contact", "organization", "assigned_to", "created_by")
        )


@admin.register(CRMActivity)
class CRMActivityAdmin(admin.ModelAdmin):
    list_display = [
        "subject",
        "activity_type",
        "contact",
        "status",
        "scheduled_at",
        "assigned_to",
    ]
    list_filter = [
        "activity_type",
        "status",
        "organization",
        "assigned_to",
        "scheduled_at",
    ]
    search_fields = ["subject", "description", "contact__email"]
    readonly_fields = ["created_at", "updated_at", "is_overdue"]
    date_hierarchy = "scheduled_at"
    list_per_page = 50

    fieldsets = (
        (
            "Activity Details",
            {"fields": ("activity_type", "subject", "description", "contact", "deal")},
        ),
        (
            "Schedule",
            {"fields": ("status", "scheduled_at", "completed_at", "duration_minutes")},
        ),
        ("Assignment", {"fields": ("assigned_to", "organization")}),
        ("Outcome", {"fields": ("outcome", "next_action")}),
        (
            "Metadata",
            {"fields": ("created_by", "is_overdue"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "contact", "deal", "organization", "assigned_to", "created_by"
            )
        )


@admin.register(CRMNote)
class CRMNoteAdmin(admin.ModelAdmin):
    list_display = ["title_or_content", "contact", "deal", "created_by", "created_at"]
    list_filter = ["is_private", "organization", "created_by", "created_at"]
    search_fields = ["title", "content", "contact__email"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    list_per_page = 50

    fieldsets = (
        ("Note Content", {"fields": ("title", "content", "is_private")}),
        ("Associations", {"fields": ("contact", "deal", "organization")}),
        ("Metadata", {"fields": ("created_by",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def title_or_content(self, obj):
        return obj.title or obj.content[:50] + "..."

    title_or_content.short_description = "Note"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("contact", "deal", "organization", "created_by")
        )


class CRMPipelineStageInline(admin.TabularInline):
    model = CRMPipelineStage
    extra = 3
    fields = ["name", "order", "probability", "is_active"]
    ordering = ["order"]


@admin.register(CRMPipeline)
class CRMPipelineAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "is_default", "is_active", "created_at"]
    list_filter = ["is_default", "is_active", "organization", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [CRMPipelineStageInline]

    fieldsets = (
        ("Pipeline Information", {"fields": ("name", "description", "organization")}),
        ("Settings", {"fields": ("is_default", "is_active", "created_by")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(CRMPipelineStage)
class CRMPipelineStageAdmin(admin.ModelAdmin):
    list_display = ["name", "pipeline", "order", "probability", "is_active"]
    list_filter = ["pipeline", "is_active", "is_closed_won", "is_closed_lost"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["pipeline", "order"]


@admin.register(CRMTask)
class CRMTaskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "priority",
        "status",
        "due_date",
        "assigned_to",
        "contact",
        "deal",
    ]
    list_filter = ["priority", "status", "organization", "assigned_to", "due_date"]
    search_fields = ["title", "description", "contact__email"]
    readonly_fields = ["created_at", "updated_at", "is_overdue"]
    date_hierarchy = "due_date"
    list_per_page = 50

    fieldsets = (
        (
            "Task Information",
            {"fields": ("title", "description", "priority", "status")},
        ),
        ("Associations", {"fields": ("contact", "deal", "organization")}),
        ("Schedule", {"fields": ("due_date", "completed_at")}),
        ("Assignment", {"fields": ("assigned_to", "created_by")}),
        ("Status Info", {"fields": ("is_overdue",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "contact", "deal", "organization", "assigned_to", "created_by"
            )
        )


@admin.register(BetaTester)
class BetaTesterAdmin(admin.ModelAdmin):
    """Admin interface for BetaTester model"""

    list_display = (
        "email",
        "name",
        "invited_to_testflight",
        "testflight_invitation_sent_at",
        "created_at",
    )
    list_filter = (
        "invited_to_testflight",
        "created_at",
        "testflight_invitation_sent_at",
    )
    search_fields = ("email", "name", "referral_source")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "name")}),
        (
            "TestFlight Status",
            {
                "fields": (
                    "invited_to_testflight",
                    "testflight_invitation_sent_at",
                )
            },
        ),
        (
            "Additional Info",
            {
                "fields": ("referral_source", "user_agent"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_invited", "export_emails"]

    def mark_as_invited(self, request, queryset):
        """Mark selected beta testers as invited to TestFlight"""
        from django.utils import timezone

        count = queryset.filter(invited_to_testflight=False).update(
            invited_to_testflight=True,
            testflight_invitation_sent_at=timezone.now(),
        )

        if count == 1:
            message = "1 beta tester was marked as invited."
        else:
            message = f"{count} beta testers were marked as invited."

        self.message_user(request, message, messages.SUCCESS)

    mark_as_invited.short_description = "Mark as invited to TestFlight"

    def export_emails(self, request, queryset):
        """Export email addresses for easy copying"""
        emails = list(queryset.values_list("email", flat=True))
        email_list = ", ".join(emails)

        self.message_user(
            request,
            f"Email addresses: {email_list}",
            messages.INFO,
        )

    export_emails.short_description = "Export email addresses"


@admin.register(TwitterMention)
class TwitterMentionAdmin(admin.ModelAdmin):
    list_display = [
        "twitter_handle",
        "mention_type",
        "organization",
        "times_mentioned",
        "last_mentioned_at",
        "crm_company",
        "crm_contact",
    ]
    list_filter = [
        "mention_type",
        "organization",
        "last_mentioned_at",
        "created_at",
    ]
    search_fields = [
        "twitter_handle",
        "crm_company__name",
        "crm_contact__first_name",
        "crm_contact__last_name",
        "crm_contact__email",
    ]
    readonly_fields = [
        "first_mentioned_in",
        "times_mentioned",
        "created_at",
        "last_mentioned_at",
    ]
    raw_id_fields = [
        "organization",
        "crm_company",
        "crm_contact",
        "first_mentioned_in",
        "created_by",
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "organization",
                "crm_company",
                "crm_contact",
                "first_mentioned_in",
                "created_by",
            )
        )

    actions = ["link_to_company", "link_to_contact", "mark_as_unlinked"]

    def link_to_company(self, request, queryset):
        # This would need a custom form to select the company
        self.message_user(
            request,
            "Use the change form to link mentions to companies.",
            messages.INFO,
        )

    link_to_company.short_description = "Link to company"

    def link_to_contact(self, request, queryset):
        # This would need a custom form to select the contact
        self.message_user(
            request,
            "Use the change form to link mentions to contacts.",
            messages.INFO,
        )

    link_to_contact.short_description = "Link to contact"

    def mark_as_unlinked(self, request, queryset):
        updated = queryset.update(
            mention_type="unlinked", crm_company=None, crm_contact=None
        )
        self.message_user(
            request,
            f"Marked {updated} mentions as unlinked.",
            messages.SUCCESS,
        )

    mark_as_unlinked.short_description = "Mark as unlinked"


@admin.register(TweetMention)
class TweetMentionAdmin(admin.ModelAdmin):
    list_display = [
        "twitter_mention",
        "brand_tweet",
        "created_at",
        "created_by",
    ]
    list_filter = [
        "created_at",
        "twitter_mention__mention_type",
        "twitter_mention__organization",
    ]
    search_fields = [
        "twitter_mention__twitter_handle",
        "brand_tweet__content",
    ]
    readonly_fields = [
        "created_at",
    ]
    raw_id_fields = [
        "twitter_mention",
        "brand_tweet",
        "created_by",
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "twitter_mention", "brand_tweet", "brand_tweet__brand", "created_by"
            )
        )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "genre",
        "incentive_type",
        "pay_amount",
        "is_active",
        "created_at",
    ]
    list_filter = ["category", "genre", "incentive_type", "is_active", "created_at"]
    search_fields = ["title", "description", "barter_details"]
    readonly_fields = ["created_at"]

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "title",
                    "description",
                    "category",
                    "genre",
                    "is_active",
                ]
            },
        ),
        (
            "Incentive Details",
            {
                "fields": [
                    "incentive_type",
                    "barter_details",
                    "pay_amount",
                ]
            },
        ),
        (
            "Requirements",
            {
                "fields": [
                    "minimum_followers",
                    "requirements",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Metadata",
            {
                "fields": [
                    "created_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["activate_tasks", "deactivate_tasks"]

    def activate_tasks(self, request, queryset):
        """Activate selected tasks"""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f"Activated {count} tasks.",
            messages.SUCCESS,
        )

    activate_tasks.short_description = "Activate selected tasks"

    def deactivate_tasks(self, request, queryset):
        """Deactivate selected tasks"""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f"Deactivated {count} tasks.",
            messages.SUCCESS,
        )

    deactivate_tasks.short_description = "Deactivate selected tasks"


@admin.register(TaskApplication)
class TaskApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "task",
        "creator",
        "status",
        "applied_at",
        "updated_at",
    ]
    list_filter = ["status", "applied_at", "updated_at"]
    search_fields = ["task__title", "creator__username", "message"]
    readonly_fields = ["applied_at", "updated_at"]

    fieldsets = [
        (
            "Application Details",
            {
                "fields": [
                    "task",
                    "creator",
                    "status",
                    "message",
                ]
            },
        ),
        (
            "Dates",
            {
                "fields": [
                    "applied_at",
                    "updated_at",
                ]
            },
        ),
    ]

    actions = ["accept_applications", "reject_applications"]

    def accept_applications(self, request, queryset):
        """Accept selected applications"""
        count = queryset.filter(status="PENDING").update(status="ACCEPTED")
        self.message_user(
            request,
            f"Accepted {count} applications.",
            messages.SUCCESS,
        )

    accept_applications.short_description = "Accept selected applications"

    def reject_applications(self, request, queryset):
        """Reject selected applications"""
        count = queryset.filter(status="PENDING").update(status="REJECTED")
        self.message_user(
            request,
            f"Rejected {count} applications.",
            messages.SUCCESS,
        )

    reject_applications.short_description = "Reject selected applications"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("task", "creator")


@admin.register(SystemStats)
class SystemStatsAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "memory_display",
        "cpu_display",
        "disk_display",
        "database_display",
        "active_sessions",
    ]
    list_filter = ["timestamp"]
    readonly_fields = [
        "timestamp",
        "memory_total",
        "memory_used",
        "memory_available",
        "memory_percent",
        "cpu_percent",
        "cpu_count",
        "disk_total",
        "disk_used",
        "disk_free",
        "disk_percent",
        "user_count",
        "organization_count",
        "brand_count",
        "post_count",
        "active_sessions",
    ]

    def memory_display(self, obj):
        if not obj.memory_percent:
            return "N/A"

        if obj.memory_percent > 80:
            color = "red"
        elif obj.memory_percent > 60:
            color = "orange"
        else:
            color = "green"

        percentage_str = f"{obj.memory_percent:.1f}%"
        return format_html('<span style="color: {};">{}</span>', color, percentage_str)

    memory_display.short_description = "Memory"

    def cpu_display(self, obj):
        if not obj.cpu_percent:
            return "N/A"

        if obj.cpu_percent > 80:
            color = "red"
        elif obj.cpu_percent > 60:
            color = "orange"
        else:
            color = "green"

        percentage_str = f"{obj.cpu_percent:.1f}%"
        return format_html('<span style="color: {};">{}</span>', color, percentage_str)

    cpu_display.short_description = "CPU"

    def disk_display(self, obj):
        if not obj.disk_percent:
            return "N/A"

        if obj.disk_percent > 90:
            color = "red"
        elif obj.disk_percent > 80:
            color = "orange"
        else:
            color = "green"

        percentage_str = f"{obj.disk_percent:.1f}%"
        return format_html('<span style="color: {};">{}</span>', color, percentage_str)

    disk_display.short_description = "Disk"

    def database_display(self, obj):
        return format_html(
            "Users: {} | Orgs: {} | Brands: {} | Posts: {}",
            obj.user_count,
            obj.organization_count,
            obj.brand_count,
            obj.post_count,
        )

    database_display.short_description = "Database"


# Credit System Admin Classes


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "brand",
        "transaction_type",
        "amount",
        "balance_after",
        "description",
        "created_at",
    ]
    list_filter = ["transaction_type", "created_at", "brand"]
    search_fields = ["brand__name", "description", "service_used"]
    readonly_fields = ["created_at", "balance_after"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("brand", "transaction_type", "amount", "description")}),
        (
            "Service Details",
            {
                "fields": ("service_used", "api_request_id", "payment_intent_id"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("balance_after", "created_at", "created_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ["brand", "transaction_type", "amount"]
        return self.readonly_fields


@admin.register(CreditPackage)
class CreditPackageAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "credits_amount",
        "bonus_credits",
        "total_credits",
        "price_usd",
        "credits_per_dollar",
        "is_active",
        "is_featured",
    ]
    list_filter = ["is_active", "is_featured", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["sort_order", "price_usd"]

    fieldsets = (
        (None, {"fields": ("name", "description", "credits_amount", "bonus_credits")}),
        ("Pricing", {"fields": ("price_usd", "price_inr")}),
        (
            "Payment Integration",
            {
                "fields": (
                    "stripe_price_id_usd",
                    "stripe_price_id_inr",
                    "cashfree_product_id",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Display Settings", {"fields": ("is_active", "is_featured", "sort_order")}),
    )

    def total_credits(self, obj):
        return obj.total_credits

    total_credits.short_description = "Total Credits"

    def credits_per_dollar(self, obj):
        return f"{obj.credits_per_dollar:.2f}"

    credits_per_dollar.short_description = "Credits/$"
