"""
Django management command to test Stripe webhook functionality
"""

import os
import json
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from website.api_views import stripe_webhook
from website.models import Brand, User


class Command(BaseCommand):
    help = "Test Stripe webhook functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--event-type",
            type=str,
            default="payment_intent.succeeded",
            help="Type of Stripe event to test",
        )
        parser.add_argument(
            "--customer-id", type=str, help="Stripe customer ID to use in test"
        )
        parser.add_argument(
            "--subscription-id", type=str, help="Stripe subscription ID to use in test"
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔧 Testing Stripe Webhook Functionality"))
        self.stdout.write("=" * 60)

        # Check environment variables
        self.stdout.write("\n📋 Environment Variables:")
        env_vars = [
            "STRIPE_PUBLIC_KEY",
            "STRIPE_SECRET_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "STRIPE_STARTER_PRICE_ID",
            "STRIPE_PROFESSIONAL_PRICE_ID",
            "STRIPE_ENTERPRISE_PRICE_ID",
        ]

        for var in env_vars:
            value = os.environ.get(var)
            if value:
                if "SECRET" in var or "KEY" in var:
                    self.stdout.write(f"  ✅ {var}: {value[:10]}...")
                else:
                    self.stdout.write(f"  ✅ {var}: {value}")
            else:
                self.stdout.write(f"  ❌ {var}: Not set")

        # Check database setup
        self.stdout.write("\n📊 Database Status:")
        try:
            user_count = User.objects.count()
            brand_count = Brand.objects.count()
            brands_with_stripe = Brand.objects.filter(
                stripe_customer_id__isnull=False
            ).count()

            self.stdout.write(f"  👥 Users: {user_count}")
            self.stdout.write(f"  🏢 Brands: {brand_count}")
            self.stdout.write(f"  💳 Brands with Stripe: {brands_with_stripe}")
        except Exception as e:
            self.stdout.write(f"  ❌ Database error: {e}")

        # Test webhook endpoint
        self.stdout.write("\n🔗 Testing Webhook Endpoint:")

        # Create test webhook payload
        test_payload = self.create_test_payload(
            options["event_type"],
            options.get("customer_id"),
            options.get("subscription_id"),
        )

        self.stdout.write(f"  📤 Testing event: {options['event_type']}")

        # Test without signature (should fail)
        factory = RequestFactory()
        request = factory.post(
            "/api/stripe/webhook/",
            data=json.dumps(test_payload),
            content_type="application/json",
        )

        try:
            response = stripe_webhook(request)
            self.stdout.write(
                f"  ⚠️  No signature test: {response.status_code} - {response.content.decode()}"
            )
        except Exception as e:
            self.stdout.write(f"  ❌ Webhook test error: {e}")

        # Instructions
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("🎯 Next Steps:"))
        self.stdout.write("1. Set up environment variables in .env file")
        self.stdout.write("2. Create Stripe products and get price IDs")
        self.stdout.write("3. Set up webhook endpoint in Stripe dashboard")
        self.stdout.write("4. Test with Stripe CLI:")
        self.stdout.write(
            "   stripe listen --forward-to localhost:8000/api/stripe/webhook/"
        )
        self.stdout.write("5. Trigger test events:")
        self.stdout.write("   stripe trigger payment_intent.succeeded")
        self.stdout.write("   stripe trigger customer.subscription.created")

    def create_test_payload(self, event_type, customer_id=None, subscription_id=None):
        """Create a test webhook payload"""

        # Use default test IDs if not provided
        customer_id = customer_id or "cus_test_customer_id"
        subscription_id = subscription_id or "sub_test_subscription_id"

        base_payload = {
            "id": "evt_test_webhook",
            "object": "event",
            "api_version": "2020-08-27",
            "created": 1234567890,
            "type": event_type,
            "livemode": False,
            "pending_webhooks": 1,
            "request": {"id": "req_test_request", "idempotency_key": None},
        }

        # Create event-specific data
        if event_type == "payment_intent.succeeded":
            base_payload["data"] = {
                "object": {
                    "id": "pi_test_payment_intent",
                    "object": "payment_intent",
                    "customer": customer_id,
                    "amount": 9900,
                    "currency": "usd",
                    "status": "succeeded",
                }
            }
        elif event_type == "customer.subscription.created":
            base_payload["data"] = {
                "object": {
                    "id": subscription_id,
                    "object": "subscription",
                    "customer": customer_id,
                    "status": "active",
                    "current_period_start": 1234567890,
                    "current_period_end": 1237159890,
                }
            }
        elif event_type == "invoice.payment_succeeded":
            base_payload["data"] = {
                "object": {
                    "id": "in_test_invoice",
                    "object": "invoice",
                    "customer": customer_id,
                    "subscription": subscription_id,
                    "amount_paid": 9900,
                    "currency": "usd",
                    "status": "paid",
                }
            }

        return base_payload
