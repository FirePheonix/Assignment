from rest_framework import serializers
from .models import QueuedTweet


class QueuedTweetSerializer(serializers.ModelSerializer):
    brand = serializers.SerializerMethodField()
    twitter_url = serializers.SerializerMethodField()
    
    class Meta:
        model = QueuedTweet
        fields = ['id', 'content', 'status', 'scheduled_at', 'posted_at', 'media_urls',
                 'twitter_id', 'twitter_url', 'error_message', 'brand', 'created_at', 'updated_at']
        read_only_fields = ['id', 'posted_at', 'twitter_id', 'twitter_url', 'error_message', 'created_at', 'updated_at']
    
    def get_brand(self, obj):
        return {
            'id': obj.brand.id,
            'name': obj.brand.name,
            'slug': obj.brand.slug,
        }
    
    def get_twitter_url(self, obj):
        if obj.twitter_id and obj.brand.twitter_username:
            return f"https://twitter.com/{obj.brand.twitter_username}/status/{obj.twitter_id}"
        return None