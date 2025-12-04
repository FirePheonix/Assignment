#!/usr/bin/env python3
"""
Test script for Stripe webhook endpoint
"""

import requests
import os


def test_webhook_endpoint():
    """Test the webhook endpoint configuration"""

    # Configuration
    BASE_URL = "http://localhost:8000"  # Change this to your domain
    WEBHOOK_URL = f"{BASE_URL}/api/stripe/webhook/"
    TEST_URL = f"{BASE_URL}/api/stripe/webhook/test/"

    print("🔧 Testing Stripe Webhook Configuration")
    print("=" * 50)

    # Test 1: Check if webhook test endpoint is accessible
    print("\n1. Testing webhook test endpoint...")
    try:
        # You'll need to authenticate this request in production
        response = requests.get(TEST_URL)
        if response.status_code == 200:
            print("✅ Webhook test endpoint is accessible")
            data = response.json()
            print(f"   Webhook URL: {data.get('webhook_url')}")
            print(f"   Secret configured: {data.get('webhook_secret_configured')}")
        else:
            print(f"❌ Webhook test endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error accessing webhook test endpoint: {e}")

    # Test 2: Check webhook endpoint accessibility (without signature)
    print("\n2. Testing webhook endpoint accessibility...")
    try:
        response = requests.post(WEBHOOK_URL, json={})
        if response.status_code == 400:
            print(
                "✅ Webhook endpoint is accessible (returns 400 for missing signature)"
            )
        else:
            print(f"⚠️  Webhook endpoint returned: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error accessing webhook endpoint: {e}")

    # Test 3: Check environment variables
    print("\n3. Checking environment variables...")
    required_vars = [
        "STRIPE_PUBLIC_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_STARTER_PRICE_ID",
        "STRIPE_PROFESSIONAL_PRICE_ID",
        "STRIPE_ENTERPRISE_PRICE_ID",
    ]

    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if "SECRET" in var or "KEY" in var:
                print(f"✅ {var}: {value[:10]}...")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")

    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Set missing environment variables")
    print("2. Configure Stripe webhook in dashboard")
    print(
        "3. Test with Stripe CLI: stripe listen --forward-to localhost:8000/api/stripe/webhook/"
    )
    print("4. Trigger test events: stripe trigger payment_intent.succeeded")


if __name__ == "__main__":
    test_webhook_endpoint()
