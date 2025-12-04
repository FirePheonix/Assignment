"""
API views for credit management
"""

from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
import json
import logging

from website.models import Brand
from website.utils.credit_manager import CreditManager
from organizations.models import Organization

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def brand_credit_info(request, organization_pk, brand_pk):
    """Get credit information for a brand"""
    try:
        organization = get_object_or_404(Organization, pk=organization_pk)
        brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

        # Check if user has access to this brand
        if not organization.users.filter(id=request.user.id).exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": "You do not have access to this organization",
                },
                status=403,
            )

        # Get credit statistics
        stats = CreditManager.get_credit_stats(brand)

        # Get recent transactions
        recent_transactions = []
        for transaction in brand.credit_transactions.all()[:10]:
            recent_transactions.append(
                {
                    "id": transaction.id,
                    "type": transaction.transaction_type,
                    "amount": str(transaction.amount),
                    "description": transaction.description,
                    "balance_after": str(transaction.balance_after),
                    "created_at": transaction.created_at.isoformat(),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "credits": {
                    "current_balance": str(brand.credits_balance),
                    "total_purchased": str(stats["total_purchased"]),
                    "total_used": str(stats["total_used"]),
                    "recent_usage_30d": str(stats["recent_usage_30d"]),
                    "transaction_count": stats["transaction_count"],
                },
                "recent_transactions": recent_transactions,
            }
        )

    except Exception as e:
        logger.error(f"Error getting credit info for brand {brand_pk}: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Error retrieving credit information"},
            status=500,
        )


@login_required
@require_http_methods(["GET"])
def credit_packages(request):
    """Get available credit packages"""
    try:
        packages = []
        for package in CreditManager.get_available_packages():
            packages.append(
                {
                    "id": package.id,
                    "name": package.name,
                    "description": package.description,
                    "credits_amount": str(package.credits_amount),
                    "bonus_credits": str(package.bonus_credits),
                    "total_credits": str(package.total_credits),
                    "price_usd": str(package.price_usd),
                    "price_inr": (
                        str(package.price_inr) if package.price_inr else None
                    ),
                    "credits_per_dollar": (f"{package.credits_per_dollar:.2f}"),
                    "is_featured": package.is_featured,
                    "stripe_price_id_usd": package.stripe_price_id_usd,
                    "stripe_price_id_inr": package.stripe_price_id_inr,
                }
            )

        return JsonResponse({"success": True, "packages": packages})

    except Exception as e:
        logger.error(f"Error getting credit packages: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Error retrieving credit packages"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def simulate_credit_usage(request, organization_pk, brand_pk):
    """Simulate credit usage (for testing purposes)"""
    try:
        organization = get_object_or_404(Organization, pk=organization_pk)
        brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

        # Check if user has access to this brand
        if not organization.users.filter(id=request.user.id).exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": "You do not have access to this organization",
                },
                status=403,
            )

        # Parse request data
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON in request body"}, status=400
            )

        service_name = data.get("service", "Image Generation")
        amount = data.get("amount")

        if amount is None:
            # Get cost from service
            amount = CreditManager.get_service_cost(service_name)
        else:
            amount = Decimal(str(amount))

        # Simulate the usage
        success, message = CreditManager.deduct_credits(
            brand=brand,
            amount=amount,
            description=f"Test usage of {service_name}",
            service_used=service_name.lower().replace(" ", "_"),
            api_request_id=f"test_{request.user.id}",
        )

        if success:
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Deducted {amount} credits for {service_name}",
                    "credits_used": str(amount),
                    "credits_remaining": str(brand.credits_balance),
                }
            )
        else:
            return JsonResponse({"success": False, "error": message}, status=400)

    except Exception as e:
        logger.error(f"Error simulating credit usage: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Error processing credit usage"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def add_test_credits(request, organization_pk, brand_pk):
    """Add test credits to a brand (for development/testing)"""
    try:
        organization = get_object_or_404(Organization, pk=organization_pk)
        brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

        # Check if user has admin access to this brand
        org_user = organization.organization_users.filter(user=request.user).first()
        if not org_user or not org_user.is_admin:
            return JsonResponse(
                {"success": False, "error": "Admin access required"}, status=403
            )

        # Parse request data
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON in request body"}, status=400
            )

        amount = data.get("amount", 5.0)  # Default 5 credits
        amount = Decimal(str(amount))

        # Add test credits
        success, message = CreditManager.add_credits(
            brand=brand,
            amount=amount,
            description=f"Test credits added by {request.user.username}",
            transaction_type="bonus",
        )

        if success:
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Added {amount} test credits",
                    "credits_added": str(amount),
                    "credits_balance": str(brand.credits_balance),
                }
            )
        else:
            return JsonResponse({"success": False, "error": message}, status=400)

    except Exception as e:
        logger.error(f"Error adding test credits: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Error adding test credits"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def apply_coupon(request, organization_pk, brand_pk):
    """Apply a coupon code to add credits. Includes a $1 superuser-only code.

    Request JSON: { "code": "..." }
    - SUPER1: superuser-only, grants small credit bonus (e.g., 1.00 credits)
    - Other codes: stub for future; currently returns 400
    """
    try:
        organization = get_object_or_404(Organization, pk=organization_pk)
        brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

        if not organization.users.filter(id=request.user.id).exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": "You do not have access to this organization",
                },
                status=403,
            )

        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON"},
                status=400,
            )

        code = (data.get("code") or "").strip().upper()
        if not code:
            return JsonResponse(
                {"success": False, "error": "Coupon code required"},
                status=400,
            )

        if code == "SUPER1":
            if not request.user.is_superuser:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Not authorized for this coupon",
                    },
                    status=403,
                )
            # Grant a nominal 1.00 credits for $1 superuser-only code
            success, message = CreditManager.add_credits(
                brand=brand,
                amount=Decimal("1.00"),
                description="Applied SUPER1 coupon",
                transaction_type="bonus",
            )
            if success:
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Coupon applied. 1.00 credits added.",
                        "credits_balance": str(brand.credits_balance),
                    }
                )
            return JsonResponse(
                {"success": False, "error": message},
                status=400,
            )

        return JsonResponse(
            {"success": False, "error": "Unknown coupon code"},
            status=400,
        )
    except Exception as e:
        logger.error(f"Error applying coupon: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Error applying coupon"},
            status=500,
        )
