#!/usr/bin/env python3
"""
Simple test script to send a tweet using Twitter API v2
Make sure to fill in your actual API credentials below
"""

import tweepy
from datetime import datetime

# Twitter API credentials - REPLACE WITH YOUR ACTUAL CREDENTIALS
TWITTER_API_KEY = "ekRTd5mqUpVkV9kNkr1tRV5yD"
TWITTER_API_SECRET = "CYnbBzV1mXMahySnzsfsUCNpg8DYH4o5Zf0FERm0I78voz4UxS"
TWITTER_ACCESS_TOKEN = "1941603294322851840-fpsVfnHeKRsD0qMRV4026YCwNE0tQO"
TWITTER_ACCESS_TOKEN_SECRET = "SRyOUXNQ3e1B57vJqR2qzl6M4hO1Q60yTw7ouWEnBHm9l"
TWITTER_BEARER_TOKEN = (
    "AAAAAAAAAAAAAAAAAAAAAP%2Bz2wEAAAAABEQF0PJzDybsA3bPQ4kAzcbCRB4%3D"
    "rqqwPe0isM328A7B9ELPVv1fFw4M5Reg2Mj5qHw5Wf2aJln6P9"
)


def send_test_tweet():
    """Send a simple test tweet"""

    # Initialize Twitter API client
    try:
        # For Twitter API v2
        client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True,
        )

        # Create tweet text
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tweet_text = f"Test tweet from Gemnar - {current_time} 🚀"

        print(f"Sending tweet: {tweet_text}")

        # Send the tweet
        response = client.create_tweet(text=tweet_text)

        if response.data:
            print("✅ Tweet sent successfully!")
            print(f"Tweet ID: {response.data['id']}")
            tweet_url = f"https://twitter.com/user/status/{response.data['id']}"
            print(f"Tweet URL: {tweet_url}")
        else:
            print("❌ Failed to send tweet - no response data")

    except tweepy.Unauthorized:
        print("❌ Authentication failed - check your API credentials")
    except tweepy.Forbidden:
        print("❌ Forbidden - check your API access level and permissions")
    except tweepy.TooManyRequests:
        print("❌ Rate limit exceeded - wait and try again later")
    except Exception as e:
        print(f"❌ Error sending tweet: {str(e)}")


def verify_credentials():
    """Verify that API credentials are working"""
    try:
        client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True,
        )

        # Get current user info
        me = client.get_me()
        if me.data:
            print("✅ Authentication successful!")
            print(f"Logged in as: @{me.data.username}")
            print(f"User ID: {me.data.id}")
            return True
        else:
            print("❌ Authentication failed - no user data returned")
            return False

    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("Twitter API Test Script")
    print("=" * 50)

    # Check if credentials are still placeholder values
    if TWITTER_API_KEY == "your_api_key_here":
        print("❌ Please update the API credentials in this file before running")
        print("You need to replace:")
        print("- TWITTER_API_KEY")
        print("- TWITTER_API_SECRET")
        print("- TWITTER_ACCESS_TOKEN")
        print("- TWITTER_ACCESS_TOKEN_SECRET")
        print("- TWITTER_BEARER_TOKEN")
        exit(1)

    # Verify credentials first
    print("1. Verifying API credentials...")
    if verify_credentials():
        print("\n2. Sending test tweet...")
        send_test_tweet()
    else:
        print("❌ Cannot send tweet - authentication failed")
