from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import User, Brand


class BrandSignupAndPaymentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {
            "email": "testbrand@example.com",
            "password": "testpassword123",
        }
        self.brand_data = {
            "name": "Test Brand",
            "url": "http://testbrand.com",
        }

    @patch("stripe.Customer.create")
    @patch("stripe.Subscription.create")
    @patch("os.environ.get")
    def test_brand_signup_and_payment_flow(
        self, mock_env_get, mock_subscription_create, mock_customer_create
    ):
        # Mock environment variables
        mock_env_get.return_value = "price_12345"

        # Mock Stripe API responses
        mock_customer_create.return_value = MagicMock(id="cus_testcustomer")
        mock_subscription_create.return_value = MagicMock(
            id="sub_testsubscription", status="active"
        )

        # Simulate form submission to process_payment view
        response = self.client.post(
            reverse("website:process_payment"),
            {
                **self.user_data,
                **self.brand_data,
                "stripeToken": "tok_testtoken",
                "plan": "starter",
            },
        )

        # Debug: Print the actual response
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        print(f"Response JSON: {response.json()}")

        # Check for a successful JSON response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        # Check if user and brand are created
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())
        user = User.objects.get(email=self.user_data["email"])
        self.assertTrue(
            Brand.objects.filter(owner=user, name=self.brand_data["name"]).exists()
        )
        brand = Brand.objects.get(owner=user)

        # Check if Stripe customer and subscription were called
        mock_customer_create.assert_called_once()
        mock_subscription_create.assert_called_once()

        # Check for redirect URL in JSON response
        expected_redirect_url = reverse("website:brand_success", args=[brand.id])
        self.assertEqual(response.json()["redirect_url"], expected_redirect_url)
