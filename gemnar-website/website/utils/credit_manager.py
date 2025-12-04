"""
Credit management utilities for AI services
"""

from decimal import Decimal
from django.utils import timezone
from website.models import CreditTransaction, CreditPackage, RunwarePricingData
import logging

logger = logging.getLogger(__name__)


class CreditManager:
    """Utility class for managing AI credits"""

    @staticmethod
    def get_service_cost(service_name):
        """Get the cost for a specific AI service"""
        try:
            pricing = RunwarePricingData.objects.filter(
                service_name__icontains=service_name, is_active=True
            ).first()

            if pricing and pricing.gemnar_price:
                return pricing.gemnar_price

            # Default costs if no pricing data found
            default_costs = {
                "Image Generation": Decimal("0.02"),
                "Text Generation": Decimal("0.001"),
                "Image Upscaling": Decimal("0.005"),
                "Background Removal": Decimal("0.003"),
            }

            for key, value in default_costs.items():
                if key.lower() in service_name.lower():
                    return value

            return Decimal("0.01")  # Default fallback

        except Exception as e:
            logger.error(f"Error getting service cost for {service_name}: {str(e)}")
            return Decimal("0.01")

    @staticmethod
    def check_sufficient_credits(brand, amount):
        """Check if brand has sufficient credits"""
        try:
            amount = Decimal(str(amount))
            return brand.credits_balance >= amount
        except Exception as e:
            logger.error(f"Error checking credits for brand {brand.id}: {str(e)}")
            return False

    @staticmethod
    def deduct_credits(
        brand, amount, description="", service_used="", api_request_id=""
    ):
        """Deduct credits from brand with transaction record"""
        try:
            amount = Decimal(str(amount))

            if not CreditManager.check_sufficient_credits(brand, amount):
                return (
                    False,
                    f"Insufficient credits. Need {amount}, have {brand.credits_balance}",
                )

            # Deduct credits
            brand.credits_balance -= amount
            brand.save(update_fields=["credits_balance"])

            # Create transaction record
            CreditTransaction.objects.create(
                brand=brand,
                transaction_type="usage",
                amount=-amount,  # Negative for deduction
                description=description or f"Used {service_used or 'AI service'}",
                balance_after=brand.credits_balance,
                service_used=service_used,
                api_request_id=api_request_id,
            )

            logger.info(
                f"Deducted {amount} credits from brand {brand.id}. New balance: {brand.credits_balance}"
            )
            return True, "Credits deducted successfully"

        except Exception as e:
            logger.error(f"Error deducting credits from brand {brand.id}: {str(e)}")
            return False, f"Error processing credit deduction: {str(e)}"

    @staticmethod
    def add_credits(
        brand, amount, description="", payment_intent_id="", transaction_type="purchase"
    ):
        """Add credits to brand with transaction record"""
        try:
            amount = Decimal(str(amount))

            # Add credits
            brand.credits_balance += amount
            brand.save(update_fields=["credits_balance"])

            # Create transaction record
            CreditTransaction.objects.create(
                brand=brand,
                transaction_type=transaction_type,
                amount=amount,  # Positive for addition
                description=description or f"Credits added via {transaction_type}",
                balance_after=brand.credits_balance,
                payment_intent_id=payment_intent_id,
            )

            logger.info(
                f"Added {amount} credits to brand {brand.id}. New balance: {brand.credits_balance}"
            )
            return True, "Credits added successfully"

        except Exception as e:
            logger.error(f"Error adding credits to brand {brand.id}: {str(e)}")
            return False, f"Error processing credit addition: {str(e)}"

    @staticmethod
    def get_credit_history(brand, limit=50):
        """Get recent credit transaction history for a brand"""
        try:
            return brand.credit_transactions.all()[:limit]
        except Exception as e:
            logger.error(f"Error getting credit history for brand {brand.id}: {str(e)}")
            return []

    @staticmethod
    def get_available_packages():
        """Get all active credit packages"""
        try:
            return CreditPackage.objects.filter(is_active=True).order_by(
                "sort_order", "price_usd"
            )
        except Exception as e:
            logger.error(f"Error getting credit packages: {str(e)}")
            return []

    @staticmethod
    def purchase_credits(brand, package_id, payment_intent_id=""):
        """Process credit purchase from a package"""
        try:
            package = CreditPackage.objects.get(id=package_id, is_active=True)
            total_credits = package.total_credits

            success, message = CreditManager.add_credits(
                brand=brand,
                amount=total_credits,
                description=f"Purchased {package.name} - {package.credits_amount} credits + {package.bonus_credits} bonus",
                payment_intent_id=payment_intent_id,
                transaction_type="purchase",
            )

            if success:
                logger.info(
                    f"Successfully processed credit purchase for brand {brand.id}: {package.name}"
                )
                return (
                    True,
                    f"Successfully added {total_credits} credits to your account",
                )
            else:
                return False, message

        except CreditPackage.DoesNotExist:
            return False, "Credit package not found"
        except Exception as e:
            logger.error(f"Error processing credit purchase: {str(e)}")
            return False, f"Error processing purchase: {str(e)}"

    @staticmethod
    def get_credit_stats(brand):
        """Get credit usage statistics for a brand"""
        try:
            transactions = brand.credit_transactions.all()

            # Calculate totals
            total_purchased = sum(
                t.amount
                for t in transactions
                if t.transaction_type in ["purchase", "bonus"] and t.amount > 0
            )
            total_used = sum(
                abs(t.amount)
                for t in transactions
                if t.transaction_type == "usage" and t.amount < 0
            )

            # Recent usage (last 30 days)
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recent_usage = sum(
                abs(t.amount)
                for t in transactions
                if t.transaction_type == "usage"
                and t.amount < 0
                and t.created_at >= thirty_days_ago
            )

            return {
                "current_balance": brand.credits_balance,
                "total_purchased": total_purchased,
                "total_used": total_used,
                "recent_usage_30d": recent_usage,
                "transaction_count": transactions.count(),
            }

        except Exception as e:
            logger.error(f"Error getting credit stats for brand {brand.id}: {str(e)}")
            return {
                "current_balance": brand.credits_balance,
                "total_purchased": 0,
                "total_used": 0,
                "recent_usage_30d": 0,
                "transaction_count": 0,
            }
