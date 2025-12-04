from django.urls import path
from . import twitter_api_views

urlpatterns = [
    # Twitter Configuration
    path('brands/<int:brand_id>/twitter/config/', twitter_api_views.twitter_config, name='twitter_config'),
    path('brands/<int:brand_id>/twitter/test/', twitter_api_views.test_twitter_connection, name='test_twitter_connection'),
    path('brands/<int:brand_id>/twitter/test-tweet/', twitter_api_views.send_test_tweet, name='send_test_tweet'),
    path('brands/<int:brand_id>/twitter/disconnect/', twitter_api_views.disconnect_twitter, name='disconnect_twitter'),
    
    # Tweet Queue (brand-specific and global)
    path('twitter/queue/', twitter_api_views.twitter_queue, name='twitter_queue_all'),  # Get all tweets
    path('brands/<int:brand_id>/twitter/queue/', twitter_api_views.twitter_queue, name='twitter_queue'),  # Brand-specific
    path('twitter/queue/<int:tweet_id>/', twitter_api_views.delete_queued_tweet, name='delete_queued_tweet'),
    path('twitter/queue/<int:tweet_id>/post/', twitter_api_views.post_tweet_now, name='post_tweet_now'),
    path('twitter/queue/<int:tweet_id>/update/', twitter_api_views.update_queued_tweet, name='update_queued_tweet'),
    
    # AI Generation
    path('brands/<int:brand_id>/twitter/generate/', twitter_api_views.generate_ai_tweets, name='generate_ai_tweets'),
    
    # Media Upload
    path('twitter/upload-media/', twitter_api_views.upload_twitter_media, name='upload_twitter_media'),
    
    # Analytics
    path('twitter/analytics/', twitter_api_views.twitter_analytics, name='twitter_analytics'),
    path('brands/<int:brand_id>/twitter/analytics/', twitter_api_views.twitter_analytics, name='twitter_analytics_brand'),
]