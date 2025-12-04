#!/usr/bin/env python3
"""
Instagram API Test Script (Python Version)
This script provides comprehensive testing of Instagram API connectivity
with detailed debugging and validation procedures.
"""

import requests
import json
import sys
from datetime import datetime

# ============================================================================
# HARDCODED CREDENTIALS - UPDATE THESE WITH YOUR ACTUAL VALUES
# ============================================================================

# STEP 1: UPDATE THESE CREDENTIALS WITH YOUR ACTUAL VALUES
INSTAGRAM_ACCESS_TOKEN = "YOUR_LONG_LIVED_ACCESS_TOKEN_HERE"
INSTAGRAM_USER_ID = "YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID_HERE"
INSTAGRAM_APP_ID = "YOUR_FACEBOOK_APP_ID_HERE"
INSTAGRAM_APP_SECRET = "YOUR_FACEBOOK_APP_SECRET_HERE"
INSTAGRAM_USERNAME = "YOUR_INSTAGRAM_USERNAME_HERE"

# Test content for posting
TEST_CAPTION = f"🚀 Testing Instagram API integration from Gemnar! #automated #testing {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
TEST_IMAGE_URL = "https://picsum.photos/1080/1080"  # Sample test image

# ============================================================================
# COLOR CODES AND UTILITIES
# ============================================================================


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


def print_header(text):
    print(f"\n{Colors.PURPLE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.PURPLE}{text}{Colors.NC}")
    print(f"{Colors.PURPLE}{'=' * 80}{Colors.NC}\n")


def print_step(step_num, text):
    print(f"\n{Colors.BLUE}📋 STEP {step_num}: {text}{Colors.NC}")


def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")


def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.NC}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")


def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.NC}")


def format_json(data):
    """Pretty print JSON data"""
    return json.dumps(data, indent=2, ensure_ascii=False)


def mask_token(token, show_chars=10):
    """Mask sensitive token for display"""
    if len(token) <= show_chars * 2:
        return f"{token[:3]}...{token[-3:]}"
    return f"{token[:show_chars]}...{token[-show_chars:]}"


# ============================================================================
# TEST FUNCTIONS
# ============================================================================


def validate_credentials():
    """Validate that all required credentials are set"""
    print_step(1, "Validating Credentials")

    credentials = {
        "INSTAGRAM_ACCESS_TOKEN": INSTAGRAM_ACCESS_TOKEN,
        "INSTAGRAM_USER_ID": INSTAGRAM_USER_ID,
        "INSTAGRAM_APP_ID": INSTAGRAM_APP_ID,
        "INSTAGRAM_APP_SECRET": INSTAGRAM_APP_SECRET,
    }

    missing = []
    for name, value in credentials.items():
        if value.startswith("YOUR_") and value.endswith("_HERE"):
            missing.append(name)

    if missing:
        print_error(f"Missing credentials: {', '.join(missing)}")
        print_setup_instructions()
        return False

    print_success("All credentials are set")

    # Print masked credentials for verification
    print(f"\n{Colors.CYAN}Current Credentials (masked):{Colors.NC}")
    print(f"  Access Token: {mask_token(INSTAGRAM_ACCESS_TOKEN)}")
    print(f"  User ID: {INSTAGRAM_USER_ID}")
    print(f"  App ID: {INSTAGRAM_APP_ID}")
    print(f"  App Secret: {mask_token(INSTAGRAM_APP_SECRET, 5)}")
    print(f"  Username: {INSTAGRAM_USERNAME}")

    return True


def debug_access_token():
    """Debug and validate the access token"""
    print_step(2, "Debugging Access Token")

    print_info("Testing access token validity...")

    try:
        # Debug access token
        debug_url = "https://graph.facebook.com/debug_token"
        params = {
            "input_token": INSTAGRAM_ACCESS_TOKEN,
            "access_token": f"{INSTAGRAM_APP_ID}|{INSTAGRAM_APP_SECRET}",
        }

        response = requests.get(debug_url, params=params)
        debug_data = response.json()

        print(f"\n{Colors.CYAN}Access Token Debug Response:{Colors.NC}")
        print(format_json(debug_data))

        if debug_data.get("data", {}).get("is_valid"):
            print_success("Access token is valid")

            # Extract token info
            token_data = debug_data["data"]
            expires_at = token_data.get("expires_at", "Never")
            app_id = token_data.get("app_id", "Unknown")
            user_id = token_data.get("user_id", "Unknown")
            scopes = token_data.get("scopes", [])

            print(f"\n{Colors.CYAN}Token Details:{Colors.NC}")
            print(f"  App ID: {app_id}")
            print(f"  User ID: {user_id}")
            print(f"  Expires: {expires_at}")
            print(f"  Scopes: {', '.join(scopes)}")

            # Check required scopes
            required_scopes = [
                "instagram_basic",
                "instagram_content_publish",
                "pages_show_list",
            ]
            for scope in required_scopes:
                if scope in scopes:
                    print_success(f"Has required scope: {scope}")
                else:
                    print_warning(f"Missing scope: {scope}")

            return True
        else:
            print_error("Access token is invalid or expired")
            error = debug_data.get("data", {}).get("error", {})
            if error:
                print_error(f"Error: {error.get('message', 'Unknown error')}")

            print(f"\n{Colors.RED}Common issues:{Colors.NC}")
            print("1. Token has expired (Instagram tokens expire after 60 days)")
            print("2. Token was revoked")
            print("3. App permissions changed")
            print("4. Incorrect token format")
            return False

    except requests.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def test_instagram_account():
    """Test Instagram Business Account access"""
    print_step(3, "Testing Instagram Business Account Access")

    try:
        # Test Instagram Business Account endpoint
        account_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_USER_ID}"
        params = {
            "fields": "id,username,followers_count,follows_count,media_count,name,profile_picture_url,website",
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        }

        response = requests.get(account_url, params=params)
        account_data = response.json()

        print(f"\n{Colors.CYAN}Instagram Account Response:{Colors.NC}")
        print(format_json(account_data))

        if "error" in account_data:
            print_error("Failed to access Instagram Business Account")
            error = account_data["error"]

            # Check for common errors
            if "Tried accessing nonexisting field" in error.get("message", ""):
                print_error(
                    "The User ID appears to be a Facebook User ID, not an Instagram Business Account ID"
                )
                print_info(
                    "You need to use the Instagram Business Account ID, not the Facebook User ID"
                )
            elif "Invalid user id" in error.get("message", ""):
                print_error("Invalid Instagram User ID")
            elif "Invalid OAuth access token" in error.get("message", ""):
                print_error("Invalid or expired access token")

            print_error(f"Error {error.get('code')}: {error.get('message')}")
            return False
        else:
            print_success("Successfully accessed Instagram Business Account")

            username = account_data.get("username", "Unknown")
            followers = account_data.get("followers_count", "Unknown")
            following = account_data.get("follows_count", "Unknown")
            media_count = account_data.get("media_count", "Unknown")

            print(f"\n{Colors.CYAN}Account Details:{Colors.NC}")
            print(f"  Username: @{username}")
            print(
                f"  Followers: {followers:,}"
                if isinstance(followers, int)
                else f"  Followers: {followers}"
            )
            print(
                f"  Following: {following:,}"
                if isinstance(following, int)
                else f"  Following: {following}"
            )
            print(
                f"  Posts: {media_count:,}"
                if isinstance(media_count, int)
                else f"  Posts: {media_count}"
            )

            if (
                INSTAGRAM_USERNAME != "YOUR_INSTAGRAM_USERNAME_HERE"
                and username != INSTAGRAM_USERNAME
            ):
                print_warning(
                    f"Username mismatch: Expected @{INSTAGRAM_USERNAME}, got @{username}"
                )

            return True

    except requests.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def test_media_permissions():
    """Test media upload permissions"""
    print_step(4, "Testing Media Upload Permissions")

    try:
        # Test media endpoint access
        media_url = f"https://graph.instagram.com/v18.0/{INSTAGRAM_USER_ID}/media"
        params = {"limit": 1, "access_token": INSTAGRAM_ACCESS_TOKEN}

        response = requests.get(media_url, params=params)
        media_data = response.json()

        print(f"\n{Colors.CYAN}Media Access Response:{Colors.NC}")
        print(format_json(media_data))

        if "error" in media_data:
            print_error("Cannot access media endpoint")
            error = media_data["error"]

            if "Insufficient permissions" in error.get("message", ""):
                print_error("Missing instagram_content_publish permission")
                print_info(
                    "Make sure your app has the instagram_content_publish scope approved"
                )

            print_error(f"Error {error.get('code')}: {error.get('message')}")
            return False
        else:
            print_success("Media endpoint accessible")
            return True

    except requests.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def create_test_post():
    """Create a test Instagram post"""
    print_step(5, "Creating Test Instagram Post")

    try:
        print_info("Creating media container...")

        # Create media container
        container_url = f"https://graph.instagram.com/v18.0/{INSTAGRAM_USER_ID}/media"
        container_data = {
            "image_url": TEST_IMAGE_URL,
            "caption": TEST_CAPTION,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        }

        response = requests.post(container_url, data=container_data)
        container_result = response.json()

        print(f"\n{Colors.CYAN}Media Container Response:{Colors.NC}")
        print(format_json(container_result))

        if "error" in container_result:
            print_error("Failed to create media container")
            error = container_result["error"]

            if "Invalid image URL" in error.get("message", ""):
                print_error("Image URL is invalid or inaccessible")
            elif "Insufficient permissions" in error.get("message", ""):
                print_error("Missing content publishing permissions")

            print_error(f"Error {error.get('code')}: {error.get('message')}")
            return False

        creation_id = container_result.get("id")
        if not creation_id:
            print_error("Failed to get creation ID from container response")
            return False

        print_success(f"Media container created with ID: {creation_id}")

        print_info("Publishing media container...")

        # Publish the media
        publish_url = (
            f"https://graph.instagram.com/v18.0/{INSTAGRAM_USER_ID}/media_publish"
        )
        publish_data = {
            "creation_id": creation_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        }

        response = requests.post(publish_url, data=publish_data)
        publish_result = response.json()

        print(f"\n{Colors.CYAN}Publish Response:{Colors.NC}")
        print(format_json(publish_result))

        if "error" in publish_result:
            print_error("Failed to publish media")
            error = publish_result["error"]
            print_error(f"Error {error.get('code')}: {error.get('message')}")
            return False
        else:
            post_id = publish_result.get("id")
            print_success("✨ Post published successfully!")
            print_success(f"Instagram Post ID: {post_id}")
            print_success(
                f"Check your Instagram account @{INSTAGRAM_USERNAME} for the new post!"
            )

            print(
                f"\n{Colors.GREEN}🎉 SUCCESS! Your Instagram API integration is working correctly!{Colors.NC}"
            )
            return True

    except requests.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def print_setup_instructions():
    """Print detailed setup instructions"""
    print_header("INSTAGRAM API SETUP INSTRUCTIONS")

    print(
        f"{Colors.YELLOW}If this script failed, follow these steps to set up Instagram API correctly:{Colors.NC}\n"
    )

    instructions = [
        (
            "1. CREATE FACEBOOK APP",
            [
                "• Go to https://developers.facebook.com/apps/",
                "• Create a new app (Business type)",
                "• Note your App ID and App Secret",
            ],
        ),
        (
            "2. ADD INSTAGRAM PRODUCT",
            [
                "• In your app dashboard, add the Instagram product",
                "• Choose 'API setup with Instagram login'",
            ],
        ),
        (
            "3. CONNECT INSTAGRAM BUSINESS ACCOUNT",
            [
                "• Your Instagram account must be a Business or Creator account",
                "• It must be linked to a Facebook Page",
                "• Add your Instagram account as a test user in App Roles",
            ],
        ),
        (
            "4. GET ACCESS TOKEN",
            [
                "• Go to Graph API Explorer: https://developers.facebook.com/tools/explorer/",
                "• Select your app",
                "• Get User Access Token with these permissions:",
                "  - instagram_basic",
                "  - instagram_content_publish",
                "  - pages_show_list",
                "• Exchange for long-lived token (60 days)",
            ],
        ),
        (
            "5. GET INSTAGRAM BUSINESS ACCOUNT ID",
            [
                "• Use Graph API Explorer to call: me/accounts",
                "• Look for 'instagram_business_account' in the response",
                "• Use that ID, NOT your Facebook User ID",
            ],
        ),
        (
            "6. UPDATE SCRIPT CREDENTIALS",
            [
                "• Edit this script and replace the placeholder values:",
                "• INSTAGRAM_ACCESS_TOKEN: Your long-lived access token",
                "• INSTAGRAM_USER_ID: Your Instagram Business Account ID",
                "• INSTAGRAM_APP_ID: Your Facebook App ID",
                "• INSTAGRAM_APP_SECRET: Your Facebook App Secret",
                "• INSTAGRAM_USERNAME: Your Instagram username",
            ],
        ),
        (
            "7. COMMON ISSUES",
            [
                "• Error 100: Using Facebook User ID instead of Instagram Business Account ID",
                "• Error 190: Invalid/expired access token",
                "• Error 10: Missing permissions or app not approved",
                "• Make sure your app is in Live mode for production posting",
            ],
        ),
        (
            "8. HELPFUL LINKS",
            [
                f"• App Dashboard: https://developers.facebook.com/apps/{INSTAGRAM_APP_ID}/",
                "• Token Debugger: https://developers.facebook.com/tools/debug/accesstoken/",
                "• Graph API Explorer: https://developers.facebook.com/tools/explorer/",
                "• Instagram API Docs: https://developers.facebook.com/docs/instagram-api/",
            ],
        ),
    ]

    for title, items in instructions:
        print(f"{Colors.CYAN}{title}{Colors.NC}")
        for item in items:
            print(f"   {item}")
        print()


def run_tests():
    """Run the complete test suite"""
    print_header("INSTAGRAM API TEST SUITE")

    if not validate_credentials():
        return False

    tests_passed = []
    tests_passed.append(debug_access_token())
    tests_passed.append(test_instagram_account())
    tests_passed.append(test_media_permissions())

    if all(tests_passed):
        print(
            f"\n{Colors.GREEN}🎯 All validation tests passed! Ready to create test post...{Colors.NC}"
        )

        # Ask for confirmation before posting
        print(
            f"\n{Colors.YELLOW}⚠️  This will create an actual post on your Instagram account.{Colors.NC}"
        )
        print(f"{Colors.YELLOW}Caption: {TEST_CAPTION}{Colors.NC}")
        print(f"{Colors.YELLOW}Image: {TEST_IMAGE_URL}{Colors.NC}")

        try:
            response = input("Continue with test post? (y/N): ").lower().strip()
            if response in ["y", "yes"]:
                create_test_post()
            else:
                print_info("Skipping test post creation.")
                print(
                    f"\n{Colors.GREEN}✅ Validation complete! Your Instagram API is configured correctly.{Colors.NC}"
                )
        except KeyboardInterrupt:
            print_info("\nSkipping test post creation.")
            print(
                f"\n{Colors.GREEN}✅ Validation complete! Your Instagram API is configured correctly.{Colors.NC}"
            )
    else:
        print_error("Some tests failed. Please check the setup instructions above.")
        return False

    return True


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print_setup_instructions()
        return

    try:
        success = run_tests()

        print_header("Instagram API Test Complete")

        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user.{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
