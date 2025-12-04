from django.urls import path, include
from django.conf import settings
from . import views
from . import api_views
from . import analytics_views
from . import analytics_api

app_name = "website"

admin_url = getattr(settings, "ADMIN_URL", "admin-lkj234234ljk8c8")

urlpatterns = [
    # Main Site Pages
    # TEMP (2025-09-28): Use new marketing landing page.
    # Revert: change `views.landing_new` back to `views.index`.
    path("", views.landing_new, name="landing_page"),
    path("index/", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
    path("contact/", views.contact, name="contact"),
    path("services/", views.services, name="services"),
    path("pricing/", views.pricing, name="pricing"),
    path("help/", views.help_page, name="help"),
    path("status/", views.status, name="status"),
    path("feed/", views.feed, name="feed"),
    path("landing/", views.landing, name="landing"),
    path("landing_new/", views.landing_new, name="landing_new"),
    path("landing_new", views.landing_new),  # alias without trailing slash
    path("waitlist/", views.waitlist_signup, name="waitlist"),
    path("waitlist", views.waitlist_signup),
    path("report-issue/", views.report_issue, name="report_issue"),
    path("submit-feedback/", views.submit_feedback, name="submit_feedback"),
    path("agency/", views.agency, name="agency"),
    # Signup & Authentication Flows
    path("signup/", views.signup_choice, name="signup"),
    path("signup/brand/", views.brand_signup, name="brand_signup"),
    path("signup/user/", views.user_signup, name="user_signup"),
    path("beta-signup/", views.beta_signup, name="beta_signup"),
    path("process-payment/", views.process_payment, name="process_payment"),
    # Blog
    path("blog/", views.blog, name="blog"),
    path("blog/create/", views.blog_create, name="blog_create"),
    path("blog/my-posts/", views.blog_my_posts, name="blog_my_posts"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("blog/<slug:slug>/edit/", views.blog_edit, name="blog_edit"),
    path("blog/<slug:slug>/delete/", views.blog_delete, name="blog_delete"),
    path("blog/<slug:slug>/comment/", views.blog_comment, name="blog_comment"),
    # Marketing Tools
    path(
        "marketing-grade/processing/",
        views.marketing_grade_processing,
        name="marketing_grade_processing",
    ),
    path(
        "marketing-grade/result/",
        views.marketing_grade_result,
        name="marketing_grade_result",
    ),
    # Tweet Automation URLs
    path("tweet-dashboard/", views.tweet_dashboard, name="tweet_dashboard"),
    path(
        "tweet-config/create/",
        views.tweet_config_create,
        name="tweet_config_create",
    ),
    path(
        "tweet-config/<int:config_id>/edit/",
        views.tweet_config_edit,
        name="tweet_config_edit",
    ),
    path(
        "tweet-config/<int:config_id>/delete/",
        views.tweet_config_delete,
        name="tweet_config_delete",
    ),
    path(
        "tweet-config/<int:config_id>/debug/",
        views.tweet_config_debug,
        name="tweet_config_debug",
    ),
    path("tweet-history/", views.tweet_history, name="tweet_history"),
    path(
        "tweet/<int:tweet_id>/preview/",
        views.tweet_preview,
        name="tweet_preview",
    ),
    path("tweet-analytics/", views.tweet_analytics, name="tweet_analytics"),
    path("send-test-tweet/", views.send_test_tweet, name="send_test_tweet"),
    path(
        "update-twitter-api-keys/",
        views.update_twitter_api_keys,
        name="update_twitter_api_keys",
    ),
    path(
        "twitter-api-diagnostic/",
        views.twitter_api_diagnostic,
        name="twitter_api_diagnostic",
    ),
    path(
        "check-twitter-api-access-level/",
        views.check_twitter_api_access_level,
        name="check_twitter_api_access_level",
    ),
    # Creator flow URLs
    path("creator/step1/", views.creator_step1, name="creator_step1"),
    path(
        "creator/step2/<int:creator_id>/",
        views.creator_step2,
        name="creator_step2",
    ),
    path(
        "creator/step3/<int:creator_id>/",
        views.creator_step3,
        name="creator_step3",
    ),
    path(
        "creator/success/<int:creator_id>/",
        views.creator_success,
        name="creator_success",
    ),
    path(
        "creator/<int:creator_id>/profile/",
        views.creator_profile,
        name="creator_profile",
    ),
    path(
        "creator/<int:creator_id>/update/",
        views.update_creator_profile,
        name="update_creator_profile",
    ),
    # Business URLs
    path("business/step1/", views.business_step1, name="business_step1"),
    path(
        "business/success/<int:brand_id>/",
        views.brand_success,
        name="brand_success",
    ),
    path(
        "business/<int:business_id>/profile/",
        views.business_profile,
        name="business_profile",
    ),
    # Text to Image
    path("text-to-image/", views.text_to_image, name="text_to_image"),
    # Referral System URLs
    path("ref/<str:code>/", views.referral_signup, name="referral_signup"),
    path(
        "referral/dashboard/",
        views.referral_dashboard,
        name="referral_dashboard",
    ),
    path(
        "referral/generate/",
        views.generate_referral_code,
        name="generate_referral_code",
    ),
    path(
        "referral/delete/<str:activity_type>/<int:activity_id>/",
        views.delete_referral_activity,
        name="delete_referral_activity",
    ),
    path(
        "company/invitation/",
        views.company_invitation,
        name="company_invitation",
    ),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    # Account Management URLs
    path("account/settings/", views.account_settings, name="account_settings"),
    path(
        "account/delete/preview/",
        views.account_deletion_preview,
        name="account_deletion_preview",
    ),
    path(
        "account/delete/confirm/",
        views.account_deletion_confirm,
        name="account_deletion_confirm",
    ),
    # API Authentication Endpoints - Token-based auth only
    path(
        "api/auth/me/",
        api_views.current_user,
        name="current_user",
    ),
    path(
        "api/auth/register/creator/",
        api_views.register_creator,
        name="register_creator",
    ),
    path(
        "api/auth/register/brand/",
        api_views.register_brand,
        name="register_brand",
    ),
    path(
        "api/auth/password/change/",
        api_views.change_password,
        name="change_password",
    ),
    path(
        "api/users/profile/",
        api_views.UserProfileView.as_view(),
        name="user_profile",
    ),
    path(
        "api/users/profile/update/",
        api_views.UserProfileView.as_view(),
        name="update_user_profile",
    ),
    path(
        "api/users/upload-image/",
        api_views.upload_image,
        name="upload_image",
    ),
    path(
        "api/users/upload-instagram-image/",
        api_views.upload_instagram_image,
        name="upload_instagram_image",
    ),
    path(
        "api/users/upload-instagram-image-production/",
        api_views.upload_instagram_image_to_production,
        name="upload_instagram_image_to_production",
    ),
    path(
        "api/users/my-uploads/",
        api_views.list_user_uploads,
        name="list_user_uploads",
    ),
    path(
        "api/users/my-uploads/<int:image_id>/",
        api_views.delete_user_upload,
        name="delete_user_upload",
    ),
    path("api/users/feed/", api_views.users_feed, name="users_feed"),
    path(
        "api/users/<int:user_id>/",
        api_views.user_detail,
        name="user_detail",
    ),
    path(
        "api/users/<int:user_id>/profile/",
        api_views.public_user_profile,
        name="public_user_profile",
    ),
    # Analytics API URLs
    path(
        "api/analytics/pageview",
        analytics_api.analytics_pageview,
        name="analytics_pageview",
    ),
    path(
        "api/analytics/event",
        analytics_api.analytics_event,
        name="analytics_event",
    ),
    path(
        "api/analytics/update-pageview",
        analytics_api.analytics_update_pageview,
        name="analytics_update_pageview",
    ),
    path(
        "api/analytics/recording",
        analytics_api.analytics_recording,
        name="analytics_recording",
    ),
    path(
        "api/analytics/metrics",
        analytics_api.analytics_metrics,
        name="analytics_metrics",
    ),
    path(
        "analytics/<str:tracking_code>/script.js",
        analytics_api.analytics_script,
        name="analytics_script",
    ),
    path(
        "api/users/<int:user_id>/impression/",
        api_views.track_profile_impression,
        name="track_profile_impression",
    ),
    path(
        "api/ai/generate-image/",
        api_views.generate_ai_image,
        name="generate_ai_image",
    ),
    path(
        "api/ai/generate-image-openai/",
        api_views.generate_ai_image_openai,
        name="generate_ai_image_openai",
    ),
    path(
        "api/ai/edit-image-openai/",
        api_views.generate_ai_image_edit_openai,
        name="edit_image_openai",
    ),
    # New GPT Image Advanced Endpoints
    path(
        "api/ai/gpt-image/multi-reference/",
        api_views.gpt_image_multi_reference,
        name="gpt_image_multi_reference",
    ),
    path(
        "api/ai/gpt-image/inpainting/",
        api_views.gpt_image_inpainting,
        name="gpt_image_inpainting",
    ),
    path(
        "api/ai/gpt-image/high-fidelity/",
        api_views.gpt_image_high_fidelity,
        name="gpt_image_high_fidelity",
    ),
    path(
        "api/ai/gpt-image/advanced/",
        api_views.gpt_image_generate_advanced,
        name="gpt_image_generate_advanced",
    ),
    path(
        "api/ai/gpt-image/transparent/",
        api_views.gpt_image_transparent_background,
        name="gpt_image_transparent_background",
    ),
    path(
        "api/ai/gpt-image/stream/",
        api_views.gpt_image_streaming,
        name="gpt_image_streaming",
    ),
    # Sora 2 Video Generation Endpoints (Essential only)
    path(
        "api/ai/sora/create/",
        api_views.sora_create_video,
        name="sora_create_video",
    ),
    path(
        "api/ai/sora/create-with-reference/",
        api_views.sora_create_video_with_reference,
        name="sora_create_video_with_reference",
    ),
    path(
        "api/ai/sora/status/<str:video_id>/",
        api_views.sora_get_video_status,
        name="sora_get_video_status",
    ),
    path(
        "api/ai/sora/download/<str:video_id>/",
        api_views.sora_download_video,
        name="sora_download_video",
    ),
    path(
        "api/ai/generate-video/",
        api_views.generate_ai_video,
        name="generate_ai_video",
    ),
    path(
        "api/ai/upload-reference-image/",
        api_views.upload_reference_image,
        name="upload_reference_image",
    ),
    path(
        "api/ai/upload-to-cloudinary/",
        api_views.upload_to_cloudinary,
        name="upload_to_cloudinary",
    ),
    path(
        "api/ai/kling/generate/",
        api_views.generate_kling_video,
        name="generate_kling_video",
    ),
    path(
        "api/ai/kling/status/<path:generation_id>/",
        api_views.get_kling_video_status,
        name="get_kling_video_status",
    ),
    path(
        "api/ai/veo/status/<str:task_id>/",
        api_views.get_veo_video_status,
        name="get_veo_video_status",
    ),
    path(
        "api/ai/veo/1080p/<str:task_id>/",
        api_views.get_veo_1080p_video,
        name="get_veo_1080p_video",
    ),
    path(
        "api/ai/generate-audio/",
        api_views.generate_ai_audio,
        name="generate_ai_audio",
    ),
    path(
        "api/ai/generate-instagram-video/",
        api_views.generate_instagram_video,
        name="generate_instagram_video",
    ),
    # Instagram video generation for Flutter app
    path(
        "api/instagram/generate-video/",
        api_views.generate_instagram_video,
        name="api_generate_instagram_video",
    ),
    # Video generation status check
    path(
        "api/instagram/video-status/<str:task_uuid>/",
        api_views.check_video_generation_status_by_task,
        name="api_check_video_generation_status",
    ),
    # Video upload endpoint
    path(
        "api/instagram/upload-video/",
        api_views.upload_instagram_video,
        name="api_upload_instagram_video",
    ),
    path(
        "api/referral/stats/",
        views.referral_api_stats,
        name="referral_api_stats",
    ),
    # New Referral API endpoints
    path(
        "api/referral/code/",
        api_views.referral_code,
        name="api_referral_code",
    ),
    path(
        "api/referral/dashboard/",
        api_views.referral_dashboard,
        name="api_referral_dashboard",
    ),
    path(
        "api/referral/leaderboard/",
        api_views.referral_leaderboard,
        name="api_referral_leaderboard",
    ),
    path(
        "api/referral/badges/",
        api_views.referral_badges,
        name="api_referral_badges",
    ),
    path(
        "api/referral/track-click/",
        api_views.track_referral_click,
        name="api_track_referral_click",
    ),
    # Stripe API endpoints
    path(
        "api/stripe/account-status/",
        api_views.stripe_account_status,
        name="api_stripe_account_status",
    ),
    path(
        "api/stripe/create-customer/",
        api_views.create_stripe_customer,
        name="api_create_stripe_customer",
    ),
    path(
        "api/stripe/create-subscription/",
        api_views.create_stripe_subscription,
        name="api_create_stripe_subscription",
    ),
    path(
        "api/stripe/subscription-status/<int:brand_id>/",
        api_views.stripe_subscription_status,
        name="api_stripe_subscription_status",
    ),
    path(
        "api/stripe/cancel-subscription/<int:brand_id>/",
        api_views.cancel_stripe_subscription,
        name="api_cancel_stripe_subscription",
    ),
    path(
        "api/stripe/payment-methods/<int:brand_id>/",
        api_views.stripe_payment_methods,
        name="api_stripe_payment_methods",
    ),
    path(
        "api/stripe/plans/",
        api_views.stripe_plans,
        name="api_stripe_plans",
    ),
    # Stripe webhook endpoint
    path(
        "api/stripe/webhook/",
        api_views.stripe_webhook,
        name="api_stripe_webhook",
    ),
    # Stripe webhook test endpoint
    path(
        "api/stripe/webhook/test/",
        api_views.stripe_webhook_test,
        name="api_stripe_webhook_test",
    ),
    # Task Management API endpoints
    path(
        "api/tasks/",
        api_views.tasks_list,
        name="api_tasks_list",
    ),
    path(
        "api/tasks/<int:task_id>/",
        api_views.task_detail,
        name="api_task_detail",
    ),
    path(
        "api/my-tasks/",
        api_views.my_tasks,
        name="api_my_tasks",
    ),
    path(
        "api/tasks/<int:task_id>/applications/",
        api_views.task_applications,
        name="api_task_applications",
    ),
    path(
        "api/applications/<int:application_id>/",
        api_views.application_detail,
        name="api_application_detail",
    ),
    path(
        "api/my-applications/",
        api_views.my_applications,
        name="api_my_applications",
    ),
    # Twitter API endpoints
    path("api/twitter/post/", api_views.post_tweet, name="api_post_tweet"),
    path(
        "api/twitter/check-credentials/",
        api_views.check_twitter_credentials,
        name="api_check_twitter_credentials",
    ),
    path("api/twitter/history/", api_views.get_tweet_history, name="api_tweet_history"),
    # Test endpoint
    path("api/test-auth/", api_views.test_auth_disabled, name="test_auth_disabled"),
    # Brand-specific Twitter configuration endpoints
    path(
        "api/brands/<int:brand_id>/twitter/config/save/",
        api_views.save_twitter_config,
        name="api_save_twitter_config",
    ),
    path(
        "api/brands/<int:brand_id>/twitter/config/",
        api_views.get_twitter_config,
        name="api_get_twitter_config",
    ),
    path(
        "api/brands/<int:brand_id>/twitter/test/",
        api_views.test_twitter_connection,
        name="api_test_twitter_connection",
    ),
    path(
        "api/brands/<int:brand_id>/twitter/test-tweet/",
        api_views.send_test_tweet,
        name="api_send_test_tweet",
    ),
    path(
        "api/brands/<int:brand_id>/twitter/disconnect/",
        api_views.disconnect_twitter,
        name="api_disconnect_twitter",
    ),
    # New Twitter automation endpoints
    path(
        "api/twitter/configurations/",
        api_views.tweet_configurations,
        name="api_tweet_configurations",
    ),
    # Legacy alias for backwards compatibility.
    # Older templates/code may still reverse 'api_configuration'.
    path(
        "api/twitter/configurations/legacy/",
        api_views.tweet_configurations,
        name="api_configuration",
    ),
    path("api/twitter/brand-tweets/", api_views.brand_tweets, name="api_brand_tweets"),
    path(
        "api/twitter/brand-tweets/<int:tweet_id>/",
        api_views.brand_tweet_detail,
        name="api_brand_tweet_detail",
    ),
    path(
        "api/twitter/brand-tweets/<int:tweet_id>/post-now/",
        api_views.post_tweet_now,
        name="api_post_tweet_now",
    ),
    path(
        "api/twitter/brand-tweets/<int:tweet_id>/refresh-metrics/",
        api_views.refresh_brand_tweet_metrics,
        name="api_refresh_brand_tweet_metrics",
    ),
    path(
        "api/twitter/generate-content/",
        api_views.generate_tweet_content,
        name="api_generate_tweet_content",
    ),
    # Tweet Strategy endpoints
    path(
        "api/twitter/strategies/",
        api_views.tweet_strategies,
        name="api_tweet_strategies",
    ),
    path(
        "api/twitter/strategies/by-category/",
        api_views.tweet_strategies_by_category,
        name="api_tweet_strategies_by_category",
    ),
    path(
        "api/twitter/strategies/<int:strategy_id>/",
        api_views.tweet_strategy_detail,
        name="api_tweet_strategy_detail",
    ),
    path(
        "api/twitter/generate-with-strategy/",
        api_views.generate_tweet_with_strategy,
        name="api_generate_tweet_with_strategy",
    ),
    path(
        "api/twitter/test-website-content/",
        api_views.test_website_content,
        name="api_test_website_content",
    ),
    path(
        "api/twitter/generate-from-prompt/",
        api_views.generate_from_prompt,
        name="api_generate_from_prompt",
    ),
    path(
        "track/<str:token>/",
        views.track_link_click,
        name="track_link",
    ),
    # Tweet Strategy Dashboard
    path(
        "tweet-strategies/",
        views.tweet_strategies_dashboard,
        name="tweet_strategies_dashboard",
    ),
    path(
        "tweet-strategies/analytics/",
        views.get_strategy_analytics,
        name="strategy_analytics",
    ),
    path(
        "tweet-strategies/generate/",
        views.generate_strategy_tweet,
        name="generate_strategy_tweet",
    ),
    path(
        "tweet-strategies/<int:strategy_id>/details/",
        views.get_strategy_details,
        name="strategy_details",
    ),
    # Priority 1: Core Missing Features - New Twitter endpoints
    path(
        "api/twitter/analytics/",
        api_views.tweet_analytics,
        name="api_tweet_analytics",
    ),
    path(
        "api/twitter/tweets/<int:tweet_id>/delete/",
        api_views.delete_tweet,
        name="api_delete_tweet",
    ),
    path(
        "api/twitter/tweets/<int:tweet_id>/schedule/",
        api_views.update_tweet_schedule,
        name="api_update_tweet_schedule",
    ),
    # Phase 2: AI Integration - New Twitter AI endpoints
    path(
        "api/twitter/tweets/<int:tweet_id>/generate-image/",
        api_views.generate_tweet_image,
        name="api_generate_tweet_image",
    ),
    # Slack integration endpoints
    path(
        "api/brands/<int:brand_id>/slack/",
        api_views.brand_slack_config,
        name="api_brand_slack_config",
    ),
    path(
        "api/brands/<int:brand_id>/slack/test/",
        api_views.test_slack_webhook,
        name="api_test_slack_webhook",
    ),
    path(
        "api/twitter/tweets/<int:tweet_id>/generate-text/",
        api_views.generate_tweet_text,
        name="api_generate_tweet_text",
    ),
    
    # Twitter Configuration & Queue Management API endpoints
    path('api/', include('website.twitter_urls')),
    
    # Organization Management API endpoints
    path("api/organizations/", api_views.organizations_list, name="api_organizations_list"),
    path("api/organizations/create/", api_views.create_organization, name="api_create_organization"),
    path("api/organizations/<int:organization_id>/", api_views.update_organization, name="api_update_organization"),
    path("api/organizations/<int:organization_id>/delete/", api_views.delete_organization, name="api_delete_organization"),
    # Brand Management API endpoints
    path("api/brands/", api_views.brands_list, name="api_brands_list"),
    path("api/brands/create/", api_views.create_brand, name="api_create_brand"),
    path("api/brands/<str:slug>/", api_views.get_brand_by_slug, name="api_get_brand_by_slug"),
    path("api/brands/<int:brand_id>/", api_views.update_brand, name="api_update_brand"),
    path("api/brands/<int:brand_id>/delete/", api_views.delete_brand, name="api_delete_brand"),
    path(
        "api/brands/<int:brand_id>/set-default/",
        api_views.set_brand_default,
        name="api_set_brand_default",
    ),
    # Phase 3: Brand Management - Brand Twitter endpoints
    path(
        "api/brands/<int:brand_id>/connect-twitter/",
        api_views.connect_brand_twitter,
        name="api_connect_brand_twitter",
    ),
    path(
        "api/brands/<int:brand_id>/test-twitter/",
        api_views.test_brand_twitter,
        name="api_test_brand_twitter",
    ),
    # Instagram API endpoints
    path("instagram-oauth/", views.instagram_oauth_page, name="instagram_oauth_page"),
    path("api/instagram/oauth-start/", views.instagram_oauth_start, name="instagram_oauth_start"),
    path("api/instagram/oauth-callback/", views.instagram_oauth_callback, name="instagram_oauth_callback"),
    path("api/instagram/oauth-disconnect/", views.instagram_oauth_disconnect, name="instagram_oauth_disconnect"),
    path("api/instagram/oauth-status/", views.instagram_oauth_status, name="instagram_oauth_status"),
    path("api/instagram/post/", api_views.post_instagram, name="api_post_instagram"),
    path(
        "api/instagram/check-credentials/",
        api_views.check_instagram_credentials,
        name="api_check_instagram_credentials",
    ),
    path(
        "api/test-auth/",
        api_views.test_auth,
        name="api_test_auth",
    ),
    path(
        "api/test-auth-debug/",
        api_views.test_auth_debug,
        name="api_test_auth_debug",
    ),
    path(
        "api/debug-instagram-config/",
        api_views.debug_instagram_config,
        name="api_debug_instagram_config",
    ),
    path(
        "api/instagram/history/",
        api_views.get_instagram_post_history,
        name="api_instagram_history",
    ),
    path(
        "api/instagram/brand-posts/",
        api_views.brand_instagram_posts,
        name="api_brand_instagram_posts",
    ),
    path(
        "api/instagram/brand-posts/<int:post_id>/",
        api_views.brand_instagram_post_detail,
        name="api_brand_instagram_post_detail",
    ),
    path(
        "api/instagram/brand-posts/<int:post_id>/post-now/",
        api_views.post_instagram_now,
        name="api_post_instagram_now",
    ),
    path(
        "api/instagram/generate-content/",
        api_views.generate_instagram_content,
        name="api_generate_instagram_content",
    ),
    # Brand Assets API endpoints
    path("api/brand-assets/", api_views.brand_assets, name="api_brand_assets"),
    path(
        "api/brand-assets/<int:asset_id>/",
        api_views.brand_asset_detail,
        name="api_brand_asset_detail",
    ),
    path(
        "api/brand-assets/upload/",
        api_views.brand_asset_upload,
        name="api_brand_asset_upload",
    ),
    path(
        "api/brand-assets/<int:asset_id>/usage/",
        api_views.brand_asset_usage,
        name="api_brand_asset_usage",
    ),
    # Enhanced Asset Management APIs
    path(
        "api/brands/<int:brand_id>/assets/analytics/",
        api_views.brand_asset_analytics,
        name="api_brand_asset_analytics",
    ),
    path(
        "api/brands/<int:brand_id>/assets/search/",
        api_views.brand_asset_search,
        name="api_brand_asset_search",
    ),
    path(
        "api/brands/<int:brand_id>/assets/bulk-operations/",
        api_views.brand_asset_bulk_operations,
        name="api_brand_asset_bulk_operations",
    ),
    # Instagram Analytics APIs
    path(
        "api/brands/<int:brand_id>/instagram/analytics/",
        api_views.instagram_analytics,
        name="api_instagram_analytics",
    ),
    path(
        "api/brands/<int:brand_id>/instagram/performance-metrics/",
        api_views.instagram_performance_metrics,
        name="api_instagram_performance_metrics",
    ),
    # Real-time Notifications APIs
    path(
        "api/brands/<int:brand_id>/instagram/notifications/",
        api_views.instagram_notifications,
        name="api_instagram_notifications",
    ),
    path(
        "api/notifications/<int:notification_id>/mark-read/",
        api_views.mark_notification_read,
        name="api_mark_notification_read",
    ),
    path(
        "api/brands/<int:brand_id>/instagram/webhook-status/",
        api_views.instagram_webhook_status,
        name="api_instagram_webhook_status",
    ),
    # Phase 4B: Background Task Status APIs
    path(
        "api/tasks/<str:task_id>/status/",
        api_views.get_task_status,
        name="api_get_task_status",
    ),
    path(
        "api/tasks/active/",
        api_views.get_user_active_tasks,
        name="api_get_user_active_tasks",
    ),
    # Video Generation Status API
    path(
        "api/instagram/posts/<int:post_id>/video-status/",
        api_views.check_video_generation_status,
        name="api_check_video_generation_status",
    ),
    # Phase 4C: Background Sync APIs
    path(
        "api/sync/force/",
        api_views.force_sync_user_data,
        name="api_force_sync_user_data",
    ),
    path(
        "api/sync/status/",
        api_views.get_sync_status,
        name="api_get_sync_status",
    ),
    # Analytics Frontend URLs
    path(
        "brand/<int:brand_id>/analytics/",
        analytics_views.analytics_dashboard,
        name="analytics_dashboard",
    ),
    path(
        "brand/<int:brand_id>/analytics/setup/",
        analytics_views.analytics_setup,
        name="analytics_setup",
    ),
    path(
        "brand/<int:brand_id>/analytics/sessions/",
        analytics_views.analytics_sessions,
        name="analytics_sessions",
    ),
    path(
        "brand/<int:brand_id>/analytics/sessions/<uuid:session_id>/replay/",
        analytics_views.analytics_session_replay,
        name="analytics_session_replay",
    ),
    path(
        "brand/<int:brand_id>/analytics/heatmaps/",
        analytics_views.analytics_heatmaps,
        name="analytics_heatmaps",
    ),
    path(
        "brand/<int:brand_id>/analytics/heatmaps/<uuid:heatmap_id>/view/",
        analytics_views.analytics_heatmap_view,
        name="analytics_heatmap_view",
    ),
    path(
        "brand/<int:brand_id>/analytics/settings/",
        analytics_views.analytics_settings,
        name="analytics_settings",
    ),
    path(
        "brand/<int:brand_id>/analytics/page/<path:path>/",
        analytics_views.page_detail_analytics,
        name="page_detail_analytics",
    ),
    path(
        "api/analytics/<int:brand_id>/data/",
        analytics_views.analytics_api_data,
        name="analytics_api_data",
    ),
    path(
        "api/analytics/recording/<uuid:pageview_id>/data/",
        analytics_views.analytics_recording_data,
        name="analytics_recording_data",
    ),
    path(
        "api/analytics/session/<uuid:session_id>/delete/",
        analytics_views.delete_session_recording,
        name="delete_session_recording",
    ),
    path(
        "api/analytics/<int:brand_id>/heatmap/generate/",
        analytics_views.generate_heatmap,
        name="generate_heatmap",
    ),
    path(
        "api/analytics/<int:brand_id>/heatmap/generate-all/",
        analytics_views.generate_all_heatmaps,
        name="generate_all_heatmaps",
    ),
    path(
        "brand/<int:brand_id>/analytics/pages/",
        analytics_views.analytics_all_pages,
        name="analytics_all_pages",
    ),
    path(
        "brand/<int:brand_id>/analytics/events/",
        analytics_views.analytics_all_events,
        name="analytics_all_events",
    ),
    path(
        "brand/<int:brand_id>/analytics/pages/stream/",
        analytics_views.analytics_pages_stream,
        name="analytics_pages_stream",
    ),
    path(
        "brand/<int:brand_id>/analytics/events/stream/",
        analytics_views.analytics_events_stream,
        name="analytics_events_stream",
    ),
    # Task Management Frontend URLs
    path(
        "tasks/active/",
        views.active_tasks_dashboard,
        name="active_tasks_dashboard",
    ),
    path(
        "tasks/create/",
        views.task_create,
        name="task_create",
    ),
    path(
        "tasks/<int:task_id>/manage/",
        views.task_detail_management,
        name="task_detail_management",
    ),
    path(
        "tasks/<int:task_id>/analytics/",
        views.task_analytics,
        name="task_analytics",
    ),
    path(
        "tasks/overview/",
        views.all_tasks_overview,
        name="all_tasks_overview",
    ),
    # Account Deletion API URLs
    path(
        "api/account/deletion/preview/",
        api_views.account_deletion_preview_api,
        name="api_account_deletion_preview",
    ),
    path(
        "api/account/delete/",
        api_views.delete_account_api,
        name="api_delete_account",
    ),
    # Brand profile URL - Must be last to avoid conflicts
    path("<slug:slug>/", views.brand_profile, name="brand_profile"),
    
    # Twitter Integration URLs
    path("api/twitter/", include("website.twitter_urls")),
]
