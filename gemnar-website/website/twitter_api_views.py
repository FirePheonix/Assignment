from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.conf import settings

import tweepy
import logging
import traceback
from datetime import datetime, timezone
import requests
import os
from openai import OpenAI
import cloudinary
import cloudinary.uploader

from .models import Brand, QueuedTweet
from .twitter_serializers import QueuedTweetSerializer

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

logger = logging.getLogger(__name__)

def has_twitter_credentials(brand):
    """
    Check if a brand has valid Twitter API credentials configured.
    
    Args:
        brand: Brand instance
        
    Returns:
        bool: True if credentials exist and are complete, False otherwise
    """
    # Check that all required credentials are present on the Brand model
    return all([
        brand.twitter_api_key,
        brand.twitter_api_secret, 
        brand.twitter_access_token,
        brand.twitter_access_token_secret
    ])


def get_twitter_client(brand):
    """
    Create and return a Tweepy client for the given brand.
    
    Args:
        brand: Brand instance with Twitter credentials
        
    Returns:
        tweepy.Client: Authenticated Twitter API client
    """
    if not has_twitter_credentials(brand):
        raise ValueError("Twitter credentials not configured for this brand")
    
    return tweepy.Client(
        consumer_key=brand.twitter_api_key,
        consumer_secret=brand.twitter_api_secret,
        access_token=brand.twitter_access_token,
        access_token_secret=brand.twitter_access_token_secret,
        bearer_token=brand.twitter_bearer_token
    )


def get_twitter_api(brand):
    """
    Create and return Tweepy API v1.1 for media upload.
    
    Args:
        brand: Brand instance with Twitter credentials
        
    Returns:
        tweepy.API: Authenticated Twitter API v1.1 client
    """
    if not has_twitter_credentials(brand):
        raise ValueError("Twitter credentials not configured for this brand")
    
    auth = tweepy.OAuth1UserHandler(
        brand.twitter_api_key,
        brand.twitter_api_secret,
        brand.twitter_access_token,
        brand.twitter_access_token_secret
    )
    return tweepy.API(auth)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def twitter_config(request, brand_id):
    """Get or update Twitter configuration for a brand"""
    brand = get_object_or_404(Brand, id=brand_id)
    
    # Check if user owns this brand
    if brand.owner != request.user:
        raise PermissionDenied("You don't have access to this brand")
    
    if request.method == 'GET':
        # Return configuration from Brand model
        return Response({
            'id': brand.id,
            'api_key': brand.twitter_api_key or '',
            'api_secret': '*' * 20 if brand.twitter_api_secret else '',
            'access_token': brand.twitter_access_token or '',
            'access_token_secret': '*' * 20 if brand.twitter_access_token_secret else '',
            'bearer_token': brand.twitter_bearer_token or '',
            'username': brand.twitter_username or '',
            'is_active': has_twitter_credentials(brand),
        })
    
    elif request.method == 'POST':
        # Only owner can modify config
        if brand.owner != request.user:
            raise PermissionDenied("Only the brand owner can modify Twitter configuration")
        
        # Update fields on Brand model
        if 'api_key' in request.data:
            brand.twitter_api_key = request.data['api_key']
        if 'api_secret' in request.data:
            brand.twitter_api_secret = request.data['api_secret']
        if 'access_token' in request.data:
            brand.twitter_access_token = request.data['access_token']
        if 'access_token_secret' in request.data:
            brand.twitter_access_token_secret = request.data['access_token_secret']
        if 'bearer_token' in request.data:
            brand.twitter_bearer_token = request.data['bearer_token']
        
        # Validate the configuration by testing connection
        if brand.twitter_api_key and brand.twitter_api_secret:
            try:
                # Test the credentials
                client = get_twitter_client(brand)
                
                # Try to get user info
                me = client.get_me()
                brand.twitter_username = me.data.username if me.data else None
                
            except Exception as e:
                logger.error(f"Twitter API validation failed: {e}")
                brand.twitter_username = None
        
        brand.save()
        
        return Response({
            'id': brand.id,
            'api_key': brand.twitter_api_key or '',
            'api_secret': '*' * 20 if brand.twitter_api_secret else '',
            'access_token': brand.twitter_access_token or '',
            'access_token_secret': '*' * 20 if brand.twitter_access_token_secret else '',
            'bearer_token': brand.twitter_bearer_token or '',
            'username': brand.twitter_username or '',
            'is_active': has_twitter_credentials(brand),
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_twitter_connection(request, brand_id):
    """Test Twitter API connection"""
    brand = get_object_or_404(Brand, id=brand_id)
    
    # Check if user owns this brand
    if brand.owner != request.user:
        raise PermissionDenied("You don't have access to this brand")
    
    if not has_twitter_credentials(brand):
        return Response({
            'success': False,
            'error': 'Twitter configuration not found'
        })
    
    try:
        # Test connection
        client = get_twitter_client(brand)
        
        me = client.get_me()
        if me.data:
            return Response({
                'success': True,
                'username': me.data.username
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to authenticate with Twitter'
            })
            
    except Exception as e:
        logger.error(f"Twitter connection test failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_tweet(request, brand_id):
    """Send a test tweet"""
    brand = get_object_or_404(Brand, id=brand_id)
    
    # Check if user owns this brand
    if brand.owner != request.user:
        raise PermissionDenied("You don't have access to this brand")
    
    # Check if Twitter credentials are configured
    if not has_twitter_credentials(brand):
        return Response({
            'success': False,
            'error': 'Twitter API credentials not configured. Please configure your Twitter API keys first.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    content = request.data.get('content', '')
    if not content or len(content) > 280:
        return Response({
            'success': False,
            'error': 'Invalid tweet content'
        })
    
    try:
        # Send tweet
        client = get_twitter_client(brand)
        
        response = client.create_tweet(text=content)
        
        if response.data:
            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/{brand.twitter_username}/status/{tweet_id}"
            
            return Response({
                'success': True,
                'tweet_id': tweet_id,
                'tweet_url': tweet_url
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to send tweet'
            })
            
    except tweepy.Unauthorized:
        return Response({
            'success': False,
            'error': 'Twitter API authorization failed',
            'error_type': 'authorization'
        })
    except tweepy.Forbidden:
        return Response({
            'success': False,
            'error': 'Twitter API access level insufficient. Upgrade to Basic access.',
            'error_type': 'access_level'
        })
    except Exception as e:
        logger.error(f"Tweet sending failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_twitter(request, brand_id):
    """Disconnect Twitter from brand"""
    brand = get_object_or_404(Brand, id=brand_id)
    
    # Check if user is admin
    if not brand.organization.is_user_admin(request.user):
        raise PermissionDenied("Only admins can disconnect Twitter")
    
    # Clear Twitter credentials from Brand model
    brand.twitter_api_key = None
    brand.twitter_api_secret = None
    brand.twitter_access_token = None
    brand.twitter_access_token_secret = None
    brand.twitter_bearer_token = None
    brand.twitter_username = None
    brand.save()
    
    return Response({'success': True})

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def twitter_queue(request, brand_id=None):
    """Get or create tweets in queue"""
    
    if request.method == 'GET':
        # If no brand_id provided, get all tweets from all brands user owns
        if brand_id is None:
            # Get all brands user owns
            brands = Brand.objects.filter(owner=request.user)
            tweets = QueuedTweet.objects.filter(brand__in=brands).select_related('brand').order_by('-created_at')
        else:
            brand = get_object_or_404(Brand, id=brand_id)
            
            # Check if user owns this brand
            if brand.owner != request.user:
                raise PermissionDenied("You don't have access to this brand")
            
            # Get all tweets for this brand
            tweets = QueuedTweet.objects.filter(brand=brand).order_by('-created_at')
        
        # Calculate stats
        stats = {
            'total_queued': tweets.filter(status='queued').count(),
            'total_scheduled': tweets.filter(status='scheduled').count(),
            'total_drafts': tweets.filter(status='draft').count(),
            'total_posted': tweets.filter(status='posted').count(),
        }
        
        serializer = QueuedTweetSerializer(tweets, many=True)
        return Response({
            'tweets': serializer.data,
            'stats': stats
        })
    
    elif request.method == 'POST':
        brand_id = request.data.get('brand_id')
        if not brand_id:
            return Response({
                'error': 'brand_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        brand = get_object_or_404(Brand, id=brand_id)
        
        # Check if user owns this brand
        if brand.owner != request.user:
            raise PermissionDenied("You don't have access to this brand")
        
        # Check if Twitter credentials are configured before allowing tweet creation
        if not has_twitter_credentials(brand):
            return Response({
                'error': 'Twitter API credentials not configured. Please configure your Twitter API keys first.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Create new tweet
        content = request.data.get('content', '').strip()
        scheduled_at = request.data.get('scheduled_at')
        media_urls = request.data.get('media_urls', [])
        
        if not content or len(content) > 280:
            return Response({
                'error': 'Invalid tweet content (must be 1-280 characters)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine status based on scheduled_at
        tweet_status = 'scheduled' if scheduled_at else 'draft'
        
        # Parse scheduled_at if provided
        scheduled_datetime = None
        if scheduled_at:
            try:
                scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            except ValueError:
                return Response({
                    'error': 'Invalid scheduled_at format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        tweet = QueuedTweet.objects.create(
            brand=brand,
            content=content,
            status=tweet_status,
            scheduled_at=scheduled_datetime,
            media_urls=media_urls,
            created_by=request.user
        )
        
        serializer = QueuedTweetSerializer(tweet)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_queued_tweet(request, tweet_id):
    """Update a queued tweet"""
    tweet = get_object_or_404(QueuedTweet, id=tweet_id)
    
    # Check if user owns this brand
    if tweet.brand.owner != request.user:
        raise PermissionDenied("You don't have access to this tweet")
    
    # Don't allow editing of posted tweets
    if tweet.status == 'posted':
        return Response({
            'error': 'Cannot edit posted tweets'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update fields
    if 'content' in request.data:
        content = request.data['content'].strip()
        if not content or len(content) > 280:
            return Response({
                'error': 'Invalid tweet content (must be 1-280 characters)'
            }, status=status.HTTP_400_BAD_REQUEST)
        tweet.content = content
    
    if 'scheduled_at' in request.data:
        scheduled_at = request.data['scheduled_at']
        if scheduled_at:
            try:
                tweet.scheduled_at = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
                tweet.status = 'scheduled'
            except ValueError:
                return Response({
                    'error': 'Invalid scheduled_at format'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            tweet.scheduled_at = None
            tweet.status = 'draft'
    
    if 'media_urls' in request.data:
        tweet.media_urls = request.data['media_urls']
    
    tweet.save()
    
    serializer = QueuedTweetSerializer(tweet)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_queued_tweet(request, tweet_id):
    """Delete a queued tweet"""
    tweet = get_object_or_404(QueuedTweet, id=tweet_id)
    
    # Check if user owns this brand
    if tweet.brand.owner != request.user:
        raise PermissionDenied("You don't have access to this tweet")
    
    # Don't allow deletion of posted tweets
    if tweet.status == 'posted':
        return Response({
            'error': 'Cannot delete posted tweets'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    tweet.delete()
    return Response({'success': True})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_tweet_now(request, tweet_id):
    """Post a queued tweet immediately with media support"""
    tweet = get_object_or_404(QueuedTweet, id=tweet_id)
    
    # Check if user owns this brand
    if tweet.brand.owner != request.user:
        raise PermissionDenied("You don't have access to this tweet")
    
    # Check if Twitter credentials are configured
    if not has_twitter_credentials(tweet.brand):
        return Response({
            'success': False,
            'error': 'Twitter API credentials not configured. Please configure your Twitter API keys first.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if tweet.status == 'posted':
        return Response({
            'success': False,
            'error': 'Tweet already posted'
        })
    
    try:
        # Get clients
        client = get_twitter_client(tweet.brand)
        api = get_twitter_api(tweet.brand)
        
        # Handle media uploads if present
        media_ids = []
        if tweet.media_urls and len(tweet.media_urls) > 0:
            for media_url in tweet.media_urls:
                try:
                    # Download media from URL
                    response = requests.get(media_url, timeout=30)
                    response.raise_for_status()
                    
                    # Create temp file
                    import tempfile
                    suffix = os.path.splitext(media_url)[1] or '.jpg'
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name
                    
                    try:
                        # Upload media to Twitter
                        media = api.media_upload(tmp_path)
                        media_ids.append(media.media_id)
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                            
                except Exception as media_error:
                    logger.error(f"Media upload failed for {media_url}: {media_error}")
                    # Continue without this media
        
        # Post tweet with or without media
        if media_ids:
            response = client.create_tweet(text=tweet.content, media_ids=media_ids)
        else:
            response = client.create_tweet(text=tweet.content)
        
        if response.data:
            tweet_id_twitter = response.data['id']
            tweet.twitter_id = tweet_id_twitter
            tweet.status = 'posted'
            tweet.posted_at = datetime.now(timezone.utc)
            tweet.save()
            
            tweet_url = f"https://twitter.com/{tweet.brand.twitter_username}/status/{tweet_id_twitter}"
            
            return Response({
                'success': True,
                'tweet_id': tweet_id_twitter,
                'tweet_url': tweet_url
            })
        else:
            tweet.status = 'failed'
            tweet.error_message = 'Failed to send tweet'
            tweet.save()
            return Response({
                'success': False,
                'error': 'Failed to send tweet'
            })
            
    except Exception as e:
        logger.error(f"Tweet posting failed: {e}")
        tweet.status = 'failed'
        tweet.error_message = str(e)
        tweet.save()
        
        return Response({
            'success': False,
            'error': str(e)
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_ai_tweets(request, brand_id):
    """Generate AI tweets for a brand using OpenAI"""
    brand = get_object_or_404(Brand, id=brand_id)
    
    # Check if user owns this brand
    if brand.owner != request.user:
        raise PermissionDenied("You don't have access to this brand")
    
    # Get parameters from request
    prompt = request.data.get('prompt', '')
    count = min(int(request.data.get('count', 3)), 10)  # Max 10 tweets
    tone = request.data.get('tone', 'professional')  # professional, casual, funny, inspirational
    
    if not prompt:
        return Response({
            'error': 'Prompt is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Initialize OpenAI client
        openai_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))
        if not openai_key:
            return Response({
                'error': 'OpenAI API key not configured'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        client_openai = OpenAI(api_key=openai_key)
        
        # Create system prompt based on brand and tone
        system_prompt = f"""You are a professional social media manager for {brand.name}. 
Generate engaging tweets that are {tone} in tone.
Each tweet must be under 280 characters.
Make them engaging, authentic, and relevant to the prompt.
Do not use hashtags unless specifically requested.
Return ONLY the tweet text, one per line, no numbering or extra formatting."""

        # Generate tweets with OpenAI
        response = client_openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate {count} unique tweets about: {prompt}"}
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        # Parse response
        generated_text = response.choices[0].message.content.strip()
        tweets = [t.strip() for t in generated_text.split('\n') if t.strip() and len(t.strip()) <= 280]
        
        # Create draft tweets
        created_tweets = []
        for content in tweets[:count]:
            if content:
                tweet = QueuedTweet.objects.create(
                    brand=brand,
                    content=content,
                    status='draft',
                    created_by=request.user
                )
                created_tweets.append(QueuedTweetSerializer(tweet).data)
        
        return Response({
            'success': True,
            'count': len(created_tweets),
            'tweets': created_tweets
        })
        
    except Exception as e:
        logger.error(f"AI tweet generation failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_twitter_media(request):
    """Upload media (images/videos) to Cloudinary for tweets"""
    try:
        if 'file' not in request.FILES:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'video/mp4', 'video/mov']
        if file.content_type not in allowed_types:
            return Response({
                'error': 'Invalid file type. Allowed: images (JPEG, PNG, GIF, WebP) and videos (MP4, MOV)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (Twitter limits: 5MB for images, 512MB for videos)
        max_size = 512 * 1024 * 1024 if file.content_type.startswith('video/') else 5 * 1024 * 1024
        if file.size > max_size:
            return Response({
                'error': f'File too large. Max size: {max_size / (1024*1024)}MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine resource type
        resource_type = 'video' if file.content_type.startswith('video/') else 'image'
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            folder='twitter_media',
            resource_type=resource_type,
            transformation=[
                {'quality': 'auto'},
                {'fetch_format': 'auto'}
            ]
        )
        
        return Response({
            'success': True,
            'url': upload_result['secure_url'],
            'public_id': upload_result['public_id'],
            'resource_type': resource_type,
            'format': upload_result['format'],
            'width': upload_result.get('width'),
            'height': upload_result.get('height'),
        })
        
    except Exception as e:
        logger.error(f"Media upload failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def twitter_analytics(request, brand_id=None):
    """
    Get Twitter analytics data from actual Twitter API for user's brands
    Uses accessible API endpoints to fetch public metrics: likes, retweets, replies, quotes
    """
    try:
        # Get brand_id from URL parameter or query string
        if brand_id is None:
            brand_id = request.GET.get('brand_id')
        
        # Get user's brands with Twitter configured
        if brand_id:
            brands = Brand.objects.filter(id=brand_id, owner=request.user)
            if not brands.exists():
                return Response({
                    'error': 'Brand not found or you do not have access'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            brands = Brand.objects.filter(owner=request.user)
        
        # Filter brands with Twitter credentials
        brands_with_twitter = [b for b in brands if has_twitter_credentials(b)]
        
        if not brands_with_twitter:
            return Response({
                'total_tweets': 0,
                'total_followers': 0,
                'total_likes': 0,
                'total_retweets': 0,
                'total_replies': 0,
                'total_quotes': 0,
                'engagement_rate': 0.0,
                'tweets': [],
                'brands': [],
                'message': 'No brands with Twitter configured'
            })
        
        # Aggregate data across all brands
        all_tweets_data = []
        total_followers = 0
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        total_quotes = 0
        brands_data = []
        
        for brand in brands_with_twitter:
            try:
                client = get_twitter_client(brand)
                
                # Step 1: Get authenticated user info (follower count, etc.)
                me = None
                brand_followers = 0
                brand_following = 0
                brand_tweet_count = 0
                user_id = None
                
                try:
                    me = client.get_me(user_fields=['public_metrics', 'username', 'name'])
                    if me.data:
                        user_metrics = me.data.public_metrics or {}
                        brand_followers = user_metrics.get('followers_count', 0)
                        brand_following = user_metrics.get('following_count', 0)
                        brand_tweet_count = user_metrics.get('tweet_count', 0)
                        user_id = me.data.id
                        
                        # Update brand username if not set
                        if not brand.twitter_username and me.data.username:
                            brand.twitter_username = me.data.username
                            brand.save()
                except Exception as e:
                    logger.warning(f"Failed to fetch user info for brand {brand.id}: {e}")
                
                total_followers += brand_followers
                
                # Step 2: Get user's tweets with public_metrics
                # Fetch from Twitter API to get latest metrics
                brand_tweets = []
                brand_likes = 0
                brand_retweets = 0
                brand_replies = 0
                brand_quotes = 0
                
                try:
                    # Get user ID (needed for fetching tweets)
                    if user_id:
                        
                        # Fetch user's tweets with metrics
                        tweets_response = client.get_users_tweets(
                            id=user_id,
                            max_results=100,  # Get last 100 tweets
                            tweet_fields=['created_at', 'public_metrics'],
                            exclude=['retweets', 'replies']  # Only original tweets
                        )
                        
                        if tweets_response.data:
                            for tweet in tweets_response.data:
                                metrics = tweet.public_metrics or {}
                                likes = metrics.get('like_count', 0)
                                retweets = metrics.get('retweet_count', 0)
                                replies = metrics.get('reply_count', 0)
                                quotes = metrics.get('quote_count', 0)
                                
                                # Get detailed liking users count (verifies actual likes)
                                actual_likes_count = 0
                                try:
                                    liking_users = client.get_liking_users(
                                        id=tweet.id,
                                        max_results=100  # Get up to 100 liking users
                                    )
                                    if liking_users.data:
                                        actual_likes_count = len(liking_users.data)
                                    # Note: If tweet has > 100 likes, we'd need pagination
                                    # For now, we'll use the public_metrics like_count as primary
                                except Exception as e:
                                    logger.debug(f"Could not fetch liking users for tweet {tweet.id}: {e}")
                                    actual_likes_count = likes  # Fallback to public metric
                                
                                brand_likes += likes
                                brand_retweets += retweets
                                brand_replies += replies
                                brand_quotes += quotes
                                
                                # Calculate engagement
                                total_interactions = likes + retweets + replies + quotes
                                engagement_rate = round((total_interactions / max(brand_followers, 1)) * 100, 2) if brand_followers > 0 else 0
                                
                                # Match with our database tweets if possible
                                db_tweet = QueuedTweet.objects.filter(
                                    brand=brand,
                                    twitter_id=tweet.id
                                ).first()
                                
                                tweet_data = {
                                    'id': db_tweet.id if db_tweet else None,
                                    'twitter_id': tweet.id,
                                    'content': tweet.text,
                                    'posted_at': tweet.created_at.isoformat() if tweet.created_at else None,
                                    'twitter_url': f"https://twitter.com/{brand.twitter_username}/status/{tweet.id}" if brand.twitter_username else None,
                                    'brand_id': brand.id,
                                    'brand_name': brand.name,
                                    'metrics': {
                                        'likes': likes,
                                        'verified_likes': actual_likes_count,  # Actual count from liking_users
                                        'retweets': retweets,
                                        'replies': replies,
                                        'quotes': quotes,
                                        'engagement': total_interactions,
                                        'engagement_rate': engagement_rate
                                    }
                                }
                                brand_tweets.append(tweet_data)
                                all_tweets_data.append(tweet_data)
                                
                except tweepy.TweepyException as e:
                    logger.warning(f"Failed to fetch tweets for brand {brand.id}: {e}")
                except Exception as e:
                    logger.warning(f"Error fetching tweets for brand {brand.id}: {e}")
                
                # Aggregate totals
                total_likes += brand_likes
                total_retweets += brand_retweets
                total_replies += brand_replies
                total_quotes += brand_quotes
                
                # Calculate brand engagement rate based on followers
                brand_total_engagement = brand_likes + brand_retweets + brand_replies + brand_quotes
                brand_engagement_rate = round(brand_total_engagement / max(brand_followers, 1) * 100, 2) if brand_followers > 0 else 0
                
                brands_data.append({
                    'id': brand.id,
                    'name': brand.name,
                    'slug': brand.slug,
                    'username': brand.twitter_username or 'N/A',
                    'followers': brand_followers,
                    'following': brand_following,
                    'total_tweets': len(brand_tweets),
                    'total_likes': brand_likes,
                    'total_retweets': brand_retweets,
                    'total_replies': brand_replies,
                    'total_quotes': brand_quotes,
                    'engagement_rate': brand_engagement_rate
                })
                
            except tweepy.TweepyException as e:
                logger.error(f"Twitter API error for brand {brand.id}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error fetching analytics for brand {brand.id}: {e}")
                continue
        
        # Calculate overall engagement rate based on total followers
        total_engagement = total_likes + total_retweets + total_replies + total_quotes
        overall_engagement_rate = round(total_engagement / max(total_followers, 1) * 100, 2) if total_followers > 0 else 0
        
        # Sort tweets by engagement
        all_tweets_data.sort(key=lambda x: x['metrics']['engagement'], reverse=True)
        
        return Response({
            'success': True,
            'total_tweets': len(all_tweets_data),
            'total_followers': total_followers,
            'total_likes': total_likes,
            'total_retweets': total_retweets,
            'total_replies': total_replies,
            'total_quotes': total_quotes,
            'total_engagement': total_engagement,
            'engagement_rate': overall_engagement_rate,
            'tweets': all_tweets_data,
            'brands': brands_data,
            'top_performing': all_tweets_data[:10],  # Top 10 by engagement
        })
        
    except Exception as e:
        logger.error(f"Analytics fetch failed: {e}")
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e),
            'details': 'Check server logs for full traceback'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)