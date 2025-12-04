#!/usr/bin/env python3
"""
Test Reddit Posting Script

This script demonstrates how to post to Reddit using the PRAW (Python Reddit API Wrapper) library.
It includes hardcoded credentials (placeholders) and detailed instructions on how to obtain them.

Requirements:
    pip install praw

Usage:
    python test_post_to_reddit.py
"""

import praw
from datetime import datetime


# =============================================================================
# REDDIT API CREDENTIALS - REPLACE WITH YOUR ACTUAL VALUES
# =============================================================================

# How to get Reddit API credentials:
# 1. Go to https://www.reddit.com/prefs/apps
# 2. Click "Create App" or "Create Another App"
# 3. Fill out the form:
#    - Name: Your app name (e.g., "My Bot App")
#    - App type: Select "script"
#    - Description: Brief description of your app
#    - About URL: Can be blank or your website
#    - Redirect URI: For scripts, use http://localhost:8080
# 4. Click "Create app"
# 5. After creation, you'll see:
#    - client_id: The string under your app name (14 characters)
#    - client_secret: The "secret" field (27 characters)
# 6. You'll also need your Reddit username and password

REDDIT_CONFIG = {
    # Replace these with your actual Reddit API credentials
    "client_id": "client_id",  # 14-character string under app name
    "client_secret": "client_secret",  # 27-character secret key
    "username": "username",  # Your Reddit username
    "password": "password",  # Your Reddit password
    "user_agent": "TestBot/1.0 by YourUsername",  # Format: "AppName/Version by Username"
}

# Test configuration
TEST_CONFIG = {
    "subreddit": "test",  # Use 'test' subreddit for testing (safe subreddit for bots)
    "title": f"Test Post from Python Script - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "content": """
This is a test post created using Python and the PRAW library.

**Features tested:**
- Reddit API authentication
- Text post submission
- Markdown formatting

**Technical details:**
- Posted via Python script
- Using PRAW (Python Reddit API Wrapper)
- Timestamp: {timestamp}

**Note:** This is a test post and can be safely ignored.
    """.strip().format(timestamp=datetime.now().isoformat()),
}


def validate_credentials():
    """Validate that credentials are not placeholder values"""
    required_fields = ["client_id", "client_secret", "username", "password"]

    for field in required_fields:
        value = REDDIT_CONFIG.get(field, "")
        if not value or "YOUR_" in value.upper() or "HERE" in value.upper():
            print(f"❌ Error: {field} is not configured properly")
            print(f"   Current value: {value}")
            return False

    return True


def create_reddit_instance():
    """Create and return authenticated Reddit instance"""
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CONFIG["client_id"],
            client_secret=REDDIT_CONFIG["client_secret"],
            username=REDDIT_CONFIG["username"],
            password=REDDIT_CONFIG["password"],
            user_agent=REDDIT_CONFIG["user_agent"],
        )

        # Test authentication by getting user info
        user = reddit.user.me()
        print(f"✅ Successfully authenticated as: {user.name}")
        return reddit

    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None


def test_reddit_posting():
    """Test posting to Reddit"""
    print("🚀 Testing Reddit API Posting")
    print("=" * 50)

    # Validate credentials
    print("1. Validating credentials...")
    if not validate_credentials():
        print("\n📋 To get Reddit API credentials:")
        print("   1. Go to https://www.reddit.com/prefs/apps")
        print("   2. Click 'Create App' or 'Create Another App'")
        print("   3. Choose 'script' as app type")
        print("   4. Fill in the form and create the app")
        print("   5. Copy the client_id and client_secret to this script")
        print("   6. Add your Reddit username and password")
        return False

    # Create Reddit instance
    print("2. Authenticating with Reddit...")
    reddit = create_reddit_instance()
    if not reddit:
        return False

    # Get subreddit
    print(f"3. Accessing subreddit: r/{TEST_CONFIG['subreddit']}")
    try:
        subreddit = reddit.subreddit(TEST_CONFIG["subreddit"])
        print(f"   Subreddit: {subreddit.display_name}")
        print(f"   Subscribers: {subreddit.subscribers:,}")
    except Exception as e:
        print(f"❌ Error accessing subreddit: {str(e)}")
        return False

    # Test post submission
    print("4. Submitting test post...")
    try:
        submission = subreddit.submit(
            title=TEST_CONFIG["title"], selftext=TEST_CONFIG["content"]
        )

        print("✅ Post submitted successfully!")
        print(f"   Post ID: {submission.id}")
        print(f"   Post URL: https://reddit.com{submission.permalink}")
        print(
            f"   Direct link: https://reddit.com/r/{TEST_CONFIG['subreddit']}/comments/{submission.id}/"
        )

        return True

    except Exception as e:
        print(f"❌ Error submitting post: {str(e)}")
        return False


def test_reddit_read_only():
    """Test read-only Reddit operations (doesn't require authentication)"""
    print("\n🔍 Testing Read-Only Operations")
    print("=" * 50)

    try:
        # Create read-only Reddit instance
        reddit = praw.Reddit(
            client_id=REDDIT_CONFIG["client_id"],
            client_secret=REDDIT_CONFIG["client_secret"],
            user_agent=REDDIT_CONFIG["user_agent"],
        )

        # Get hot posts from a popular subreddit
        subreddit = reddit.subreddit("python")
        hot_posts = list(subreddit.hot(limit=5))

        print(f"✅ Successfully retrieved {len(hot_posts)} hot posts from r/python:")
        for i, post in enumerate(hot_posts, 1):
            print(f"   {i}. {post.title[:60]}{'...' if len(post.title) > 60 else ''}")
            print(f"      Score: {post.score}, Comments: {post.num_comments}")

        return True

    except Exception as e:
        print(f"❌ Error in read-only operations: {str(e)}")
        return False


def main():
    """Main function to run Reddit API tests"""
    print("Reddit API Test Script")
    print("=" * 50)
    print()

    # Check if PRAW is installed
    try:
        import praw

        print(f"✅ PRAW version: {praw.__version__}")
    except ImportError:
        print("❌ PRAW not installed. Run: pip install praw")
        return

    print()

    # Test read-only operations first (less sensitive)
    read_success = test_reddit_read_only()

    # Test posting (requires full authentication)
    post_success = test_reddit_posting()

    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    print(f"Read-only operations: {'✅ PASS' if read_success else '❌ FAIL'}")
    print(f"Post submission: {'✅ PASS' if post_success else '❌ FAIL'}")

    if post_success:
        print("\n🎉 All tests passed! Reddit API integration is working.")
        print("💡 You can now integrate Reddit posting into your application.")
    elif read_success:
        print("\n⚠️  Read-only operations work, but posting failed.")
        print("💡 Check your credentials and ensure your account can post.")
    else:
        print("\n❌ Tests failed. Please check your configuration.")

    print("\n📚 Useful Resources:")
    print("   - PRAW Documentation: https://praw.readthedocs.io/")
    print("   - Reddit API: https://www.reddit.com/dev/api/")
    print("   - Reddit Apps: https://www.reddit.com/prefs/apps")


if __name__ == "__main__":
    main()
