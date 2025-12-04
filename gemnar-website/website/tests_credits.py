"""
Tests for AI credit system
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationUser
from website.models import Brand, CreditTransaction, CreditPackage
from website.utils.credit_manager import CreditManager

User = get_user_model()


class CreditSystemTestCase(TestCase):
    """Test cases for the AI credit system"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create test organization
        self.organization = Organization.objects.create(name="Test Organization")

        # Add user to organization
        OrganizationUser.objects.create(
            user=self.user, organization=self.organization, is_admin=True
        )

        # Create test brand
        self.brand = Brand.objects.create(
            name="Test Brand",
            url="https://testbrand.com",
            owner=self.user,
            organization=self.organization,
            credits_balance=Decimal("10.00"),  # Start with 10 credits
        )

        # Create test credit package
        self.credit_package = CreditPackage.objects.create(
            name="Test Package",
            credits_amount=Decimal("100.00"),
            price_usd=Decimal("20.00"),
            bonus_credits=Decimal("10.00"),
            is_active=True,
        )

    def test_brand_has_credits_balance(self):
        """Test that brand starts with correct credit balance"""
        self.assertEqual(self.brand.credits_balance, Decimal("10.00"))

    def test_has_sufficient_credits(self):
        """Test credit balance checking"""
        # Should have sufficient credits for small amount
        self.assertTrue(self.brand.has_sufficient_credits(Decimal("5.00")))

        # Should not have sufficient credits for large amount
        self.assertFalse(self.brand.has_sufficient_credits(Decimal("15.00")))

    def test_deduct_credits(self):
        """Test credit deduction"""
        initial_balance = self.brand.credits_balance
        deduction_amount = Decimal("3.00")

        success, message = self.brand.deduct_credits(
            deduction_amount, "Test deduction", "usage"
        )

        self.assertTrue(success)
        self.assertEqual(message, "Credits deducted successfully")

        # Check new balance
        self.brand.refresh_from_db()
        expected_balance = initial_balance - deduction_amount
        self.assertEqual(self.brand.credits_balance, expected_balance)

        # Check transaction was created
        transaction = CreditTransaction.objects.filter(brand=self.brand).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, -deduction_amount)
        self.assertEqual(transaction.transaction_type, "usage")
        self.assertEqual(transaction.balance_after, expected_balance)

    def test_deduct_insufficient_credits(self):
        """Test deduction when insufficient credits"""
        deduction_amount = Decimal("15.00")  # More than available

        success, message = self.brand.deduct_credits(
            deduction_amount, "Test deduction", "usage"
        )

        self.assertFalse(success)
        self.assertIn("Insufficient credits", message)

        # Balance should not change
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.credits_balance, Decimal("10.00"))

    def test_add_credits(self):
        """Test credit addition"""
        initial_balance = self.brand.credits_balance
        addition_amount = Decimal("5.00")

        success, message = self.brand.add_credits(
            addition_amount, "Test addition", "purchase"
        )

        self.assertTrue(success)
        self.assertEqual(message, "Credits added successfully")

        # Check new balance
        self.brand.refresh_from_db()
        expected_balance = initial_balance + addition_amount
        self.assertEqual(self.brand.credits_balance, expected_balance)

        # Check transaction was created
        transaction = CreditTransaction.objects.filter(brand=self.brand).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, addition_amount)
        self.assertEqual(transaction.transaction_type, "purchase")
        self.assertEqual(transaction.balance_after, expected_balance)

    def test_credit_manager_service_cost(self):
        """Test CreditManager service cost calculation"""
        cost = CreditManager.get_service_cost("Image Generation")
        self.assertIsInstance(cost, Decimal)
        self.assertGreater(cost, Decimal("0"))

    def test_credit_manager_deduct(self):
        """Test CreditManager deduction"""
        initial_balance = self.brand.credits_balance
        amount = Decimal("2.00")

        success, message = CreditManager.deduct_credits(
            brand=self.brand,
            amount=amount,
            description="Test API call",
            service_used="runware_image_generation",
            api_request_id="test_123",
        )

        self.assertTrue(success)

        # Check balance
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.credits_balance, initial_balance - amount)

        # Check transaction details
        transaction = CreditTransaction.objects.filter(brand=self.brand).first()
        self.assertEqual(transaction.service_used, "runware_image_generation")
        self.assertEqual(transaction.api_request_id, "test_123")

    def test_credit_manager_add(self):
        """Test CreditManager addition"""
        initial_balance = self.brand.credits_balance
        amount = Decimal("7.50")

        success, message = CreditManager.add_credits(
            brand=self.brand,
            amount=amount,
            description="Test purchase",
            payment_intent_id="pi_test_123",
        )

        self.assertTrue(success)

        # Check balance
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.credits_balance, initial_balance + amount)

        # Check transaction details
        transaction = CreditTransaction.objects.filter(brand=self.brand).first()
        self.assertEqual(transaction.payment_intent_id, "pi_test_123")

    def test_credit_package_total_credits(self):
        """Test credit package calculations"""
        total = self.credit_package.total_credits
        expected = (
            self.credit_package.credits_amount + self.credit_package.bonus_credits
        )
        self.assertEqual(total, expected)

        ratio = self.credit_package.credits_per_dollar
        expected_ratio = total / self.credit_package.price_usd
        self.assertEqual(ratio, expected_ratio)

    def test_purchase_credits_from_package(self):
        """Test purchasing credits from package"""
        initial_balance = self.brand.credits_balance

        success, message = CreditManager.purchase_credits(
            brand=self.brand,
            package_id=self.credit_package.id,
            payment_intent_id="pi_purchase_123",
        )

        self.assertTrue(success)

        # Check balance increased by total credits (including bonus)
        self.brand.refresh_from_db()
        expected_balance = initial_balance + self.credit_package.total_credits
        self.assertEqual(self.brand.credits_balance, expected_balance)

        # Check transaction
        transaction = CreditTransaction.objects.filter(brand=self.brand).first()
        self.assertEqual(transaction.amount, self.credit_package.total_credits)
        self.assertEqual(transaction.payment_intent_id, "pi_purchase_123")
        self.assertEqual(transaction.transaction_type, "purchase")

    def test_get_credit_stats(self):
        """Test credit statistics calculation"""
        # Add some transactions
        self.brand.add_credits(Decimal("50.00"), "Purchase", "purchase")
        self.brand.deduct_credits(Decimal("15.00"), "Usage", "usage")
        self.brand.add_credits(Decimal("5.00"), "Bonus", "bonus")

        stats = CreditManager.get_credit_stats(self.brand)

        self.assertIn("current_balance", stats)
        self.assertIn("total_purchased", stats)
        self.assertIn("total_used", stats)
        self.assertIn("transaction_count", stats)

        # Check some calculations
        self.assertEqual(stats["current_balance"], self.brand.credits_balance)
        self.assertGreater(stats["transaction_count"], 0)
        self.assertGreater(stats["total_purchased"], Decimal("0"))
        self.assertGreater(stats["total_used"], Decimal("0"))
