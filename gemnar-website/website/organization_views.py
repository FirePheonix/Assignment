from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import (
    JsonResponse,
    HttpResponseRedirect,
    HttpResponseForbidden,
)
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from organizations.models import (
    Organization,
    OrganizationUser,
    OrganizationOwner,
)
from .models import User, Brand, OrganizationInvitation, BrandTweet
from website.forms import CustomOrganizationForm
import tweepy
from django.views.decorators.http import require_POST, require_http_methods
from website.utils.credit_manager import CreditManager
import json
import logging

logger = logging.getLogger(__name__)


@login_required
def organization_list(request):
    """List organizations for the current user"""
    organizations = Organization.objects.filter(users=request.user)
    return render(
        request,
        "organizations/organization_list.html",
        {"organization_list": organizations},
    )


@login_required
def organization_detail(request, organization_pk):
    """Show organization details"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    # Check if user is member of the organization
    if not organization.users.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this organization.")
        return redirect("organization_list")

    return render(
        request,
        "organizations/organization_detail.html",
        {"organization": organization},
    )


@login_required
def organization_brand_credits(request, organization_pk, brand_pk):
    """Credits overview page for a brand inside an organization."""
    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Access control: user must belong to org
    if not organization.users.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this brand.")
        return redirect("organization_detail", organization_pk=organization_pk)

    stats = CreditManager.get_credit_stats(brand)

    # Optional: finalize Stripe checkout return (success=1)
    session_id = request.GET.get("session_id")
    added_amount = None
    if session_id and request.GET.get("success") == "1":
        try:
            import os
            import stripe
            from decimal import Decimal

            stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
            if stripe.api_key:
                session = stripe.checkout.Session.retrieve(session_id)
                if getattr(session, "payment_status", "") == "paid":
                    from website.models import CreditTransaction

                    already = CreditTransaction.objects.filter(
                        payment_intent_id=session.id
                    ).exists()
                    if not already:
                        amount_dollars = Decimal(session.amount_total) / Decimal(100)
                        success_refill, _ = CreditManager.add_credits(
                            brand,
                            amount=amount_dollars,
                            description=(
                                "Stripe Checkout credits purchase ($%s)"
                                % amount_dollars
                            ),
                            payment_intent_id=session.id,
                            transaction_type="purchase",
                        )
                        if success_refill:
                            added_amount = amount_dollars
                            stats = CreditManager.get_credit_stats(brand)
        except Exception as e:
            logger.error("Finalize Stripe session %s err: %s", session_id, e)
    transactions = brand.credit_transactions.all()[:25]
    packages = CreditManager.get_available_packages()

    context = {
        "organization": organization,
        "brand": brand,
        "stats": stats,
        "transactions": transactions,
        "packages": packages,
        "added_amount": added_amount,
        # Quick purchase amounts (avoid template .split)
        "quick_amounts": [10, 25, 50, 100, 250, 500],
    }
    return render(request, "organizations/brand_credits.html", context)


@login_required
@require_POST
def brand_credit_create_checkout_session(request, organization_pk, brand_pk):
    """Create Stripe Checkout Session or instant refill if superuser.
    JSON body: { amount: <number> }  (1 credit = $1)
    """
    import json
    from decimal import Decimal
    from django.urls import reverse

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse(
            {"success": False, "error": "Permission denied"}, status=403
        )

    try:
        data = json.loads(request.body or "{}")
        amount_raw = data.get("amount")
        amount = Decimal(str(amount_raw))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    if amount <= 0:
        return JsonResponse(
            {"success": False, "error": "Amount must be greater than zero"},
            status=400,
        )

    # Superuser direct credit path
    if request.user.is_superuser:
        success, msg = CreditManager.add_credits(
            brand,
            amount=amount,
            description=f"Admin refill (${amount})",
            payment_intent_id=(f"admin-{timezone.now().timestamp()}-{request.user.id}"),
            transaction_type="bonus",
        )
        if success:
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Added ${amount} credits (admin refill)",
                    "new_balance": str(brand.credits_balance),
                    "superuser": True,
                }
            )
        else:
            return JsonResponse({"success": False, "error": msg}, status=500)

    # Stripe Checkout path
    try:
        import os
        import stripe

        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe_secret_key:
            return JsonResponse(
                {"success": False, "error": "Stripe not configured"},
                status=503,
            )
        stripe.api_key = stripe_secret_key

        amount_cents = int(amount * 100)
        success_url = (
            request.build_absolute_uri(
                reverse(
                    "organization_brand_credits",
                    args=[organization_pk, brand_pk],
                )
            )
            + "?success=1&session_id={CHECKOUT_SESSION_ID}"
        )
        cancel_url = request.build_absolute_uri(
            reverse("organization_brand_credits", args=[organization_pk, brand_pk])
        )

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": "AI Credits",
                            "description": "Gemnar AI Credits (1 credit = $1)",
                        },
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "brand_id": str(brand.id),
                "organization_id": str(organization.id),
                "credits_amount": str(amount),
            },
        )
        return JsonResponse(
            {
                "success": True,
                "checkout_url": session.url,
                "session_id": session.id,
            }
        )
    except Exception as e:
        logger.error(f"Error creating Stripe checkout session: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def organization_create(request):
    """Create a new organization"""
    if request.method == "POST":
        form = CustomOrganizationForm(request.POST, request=request)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create organization without saving to database yet
                    organization = form.save(commit=False)
                    # Save the organization first
                    organization.save()
                    # Add current user as owner
                    org_user = OrganizationUser.objects.create(
                        user=request.user, organization=organization, is_admin=True
                    )
                    # Set the organization owner
                    OrganizationOwner.objects.create(
                        organization=organization, organization_user=org_user
                    )
                messages.success(
                    request, f'Organization "{organization.name}" created successfully!'
                )
                return redirect("organization_detail", organization_pk=organization.pk)
            except Exception as e:
                messages.error(request, f"Error creating organization: {str(e)}")
    else:
        form = CustomOrganizationForm(request=request)

    return render(request, "organizations/organization_form.html", {"form": form})


@login_required
def organization_edit(request, organization_pk):
    """Edit an organization"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    # Check if user is admin of the organization
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        messages.error(request, "You don't have permission to edit this organization.")
        return redirect("organization_detail", organization_pk=organization_pk)

    if request.method == "POST":
        form = CustomOrganizationForm(
            request.POST, instance=organization, request=request
        )
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Organization "{organization.name}" updated successfully!'
            )
            return redirect("organization_detail", organization_pk=organization.pk)
    else:
        form = CustomOrganizationForm(instance=organization, request=request)

    return render(
        request,
        "organizations/organization_form.html",
        {"form": form, "object": organization},
    )


@login_required
def organization_delete(request, organization_pk):
    """Delete an organization"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    # Check if user is admin of the organization
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        messages.error(
            request, "You don't have permission to delete this organization."
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    if request.method == "POST":
        organization_name = organization.name
        organization.delete()
        messages.success(
            request, f'Organization "{organization_name}" deleted successfully!'
        )
        return redirect("organization_list")

    return render(
        request,
        "organizations/organization_confirm_delete.html",
        {"organization": organization},
    )


@login_required
def organization_user_add(request, organization_pk):
    """Add a user to an organization"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    # Check if user is admin of the organization
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        messages.error(
            request, "You don't have permission to add members to this organization."
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    if request.method == "POST":
        email_or_username = request.POST.get("email_or_username")
        is_admin = request.POST.get("is_admin") == "on"

        if not email_or_username:
            messages.error(request, "Please enter an email address or username.")
            return render(
                request,
                "organizations/organizationuser_form.html",
                {"organization": organization},
            )

        # Try to find user by email first (if input looks like an email)
        user = None
        if "@" in email_or_username:
            try:
                user = User.objects.get(email=email_or_username)
            except User.DoesNotExist:
                pass

        # If not found by email, try by username
        if not user:
            try:
                user = User.objects.get(username=email_or_username)
            except User.DoesNotExist:
                pass

        if user:
            # Check if user is already a member
            if organization.users.filter(id=user.id).exists():
                messages.error(
                    request,
                    f'User "{user.username}" is already a member of this organization.',
                )
            else:
                OrganizationUser.objects.create(
                    user=user, organization=organization, is_admin=is_admin
                )
                messages.success(
                    request,
                    f'User "{user.username}" ({user.email}) added to the '
                    f"organization successfully!",
                )
                return redirect("organization_detail", organization_pk=organization_pk)
        else:
            messages.error(
                request,
                f'User "{email_or_username}" not found. Please check the '
                f"email address or username and try again.",
            )

    return render(
        request,
        "organizations/organizationuser_form.html",
        {"organization": organization},
    )


@login_required
def organization_user_edit(request, organization_pk, pk):
    """Edit a user's role in an organization"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    org_user = get_object_or_404(OrganizationUser, pk=pk, organization=organization)

    # Check if current user is admin of the organization
    current_org_user = organization.organization_users.filter(user=request.user).first()
    if not current_org_user or not current_org_user.is_admin:
        messages.error(
            request, "You don't have permission to edit members in this organization."
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    if request.method == "POST":
        is_admin = request.POST.get("is_admin") == "on"
        org_user.is_admin = is_admin
        org_user.save()
        messages.success(
            request, f'User "{org_user.user.username}" updated successfully!'
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    return render(
        request,
        "organizations/organizationuser_form.html",
        {"organization": organization, "object": org_user},
    )


@login_required
def organization_user_delete(request, organization_pk, pk):
    """Remove a user from an organization"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    org_user = get_object_or_404(OrganizationUser, pk=pk, organization=organization)

    # Check if current user is admin of the organization
    current_org_user = organization.organization_users.filter(user=request.user).first()
    if not current_org_user or not current_org_user.is_admin:
        messages.error(
            request,
            "You don't have permission to remove members from this organization.",
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    if request.method == "POST":
        username = org_user.user.username
        org_user.delete()
        messages.success(
            request, f'User "{username}" removed from the organization successfully!'
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    return render(
        request,
        "organizations/organizationuser_confirm_delete.html",
        {"organization": organization, "object": org_user},
    )


# Brand Management Views for Organizations


@login_required
def organization_brand_list(request, organization_pk):
    """List brands for an organization"""
    organization = get_object_or_404(Organization, pk=organization_pk)

    # Check if user is member of the organization
    if not organization.users.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this organization.")
        return redirect("organization_list")

    brands = organization.brands.all()

    return render(
        request,
        "organizations/brand_list.html",
        {"organization": organization, "brands": brands},
    )


@login_required
def organization_brand_create(request, organization_pk):
    """Create a new brand for an organization"""
    organization = get_object_or_404(Organization, pk=organization_pk)

    # Check if user is admin of the organization
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        messages.error(
            request, "You don't have permission to create brands for this organization."
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    if request.method == "POST":
        name = request.POST.get("name")
        url = request.POST.get("url")
        description = request.POST.get("description", "")
        is_default = request.POST.get("is_default") == "on"

        if name and url:
            # Validate field lengths and URL format before creating
            errors = []
            if len(name) > 200:
                errors.append("Brand name cannot exceed 200 characters.")
            if len(description) > 1000:
                errors.append("Description cannot exceed 1000 characters.")

            # Validate URL format
            from django.core.validators import URLValidator
            from django.core.exceptions import ValidationError

            url_validator = URLValidator()
            try:
                url_validator(url)
            except ValidationError:
                errors.append("Please enter a valid URL.")

            if errors:
                for error in errors:
                    messages.error(request, f"Error creating brand: {error}")
            else:
                try:
                    brand = Brand.objects.create(
                        name=name,
                        url=url,
                        description=description,
                        owner=request.user,
                        organization=organization,
                        is_default=is_default,
                    )
                    messages.success(
                        request, f'Brand "{brand.name}" created successfully!'
                    )
                    return redirect(
                        "organization_brand_detail",
                        organization_pk=organization_pk,
                        brand_pk=brand.pk,
                    )
                except Exception as e:
                    messages.error(request, f"Error creating brand: {str(e)}")
        else:
            messages.error(request, "Brand name and URL are required.")

    return render(
        request,
        "organizations/brand_form.html",
        {"organization": organization},
    )


@login_required
def organization_brand_detail(request, organization_pk, brand_pk):
    """Show brand details and dashboard"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check if user is member of the organization
    if not organization.users.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this brand.")
        return redirect("organization_list")

    # Check if current user is admin for editing permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    is_admin = org_user and org_user.is_admin

    context = {
        "organization": organization,
        "brand": brand,
        "is_admin": is_admin,
        "twitter_keys_status": {
            "configured": brand.has_twitter_config,
            **brand.get_masked_twitter_keys(),
        },
    }

    return render(
        request,
        "organizations/brand_detail.html",
        context,
    )


@login_required
def organization_brand_connect_twitter(request, organization_pk, brand_pk):
    """Connect Twitter account to a brand"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check if user is admin of the organization
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        messages.error(
            request,
            "You don't have permission to manage Twitter connections for this brand.",
        )
        return redirect(
            "organization_brand_detail",
            organization_pk=organization_pk,
            brand_pk=brand_pk,
        )

    if request.method == "POST":
        api_key = request.POST.get("api_key")
        api_secret = request.POST.get("api_secret")
        access_token = request.POST.get("access_token")
        access_token_secret = request.POST.get("access_token_secret")
        bearer_token = request.POST.get("bearer_token")

        if all([api_key, api_secret, access_token, access_token_secret, bearer_token]):
            try:
                # Test Twitter connection
                auth = tweepy.OAuthHandler(api_key, api_secret)
                auth.set_access_token(access_token, access_token_secret)
                api = tweepy.API(auth)

                # Verify credentials and get username
                twitter_user = api.verify_credentials()

                # Save Twitter credentials to brand
                brand.twitter_api_key = api_key
                brand.twitter_api_secret = api_secret
                brand.twitter_access_token = access_token
                brand.twitter_access_token_secret = access_token_secret
                brand.twitter_bearer_token = bearer_token
                brand.twitter_username = twitter_user.screen_name
                brand.save()

                messages.success(
                    request,
                    f"Twitter account @{twitter_user.screen_name} connected successfully!",
                )
                return redirect(
                    "organization_brand_detail",
                    organization_pk=organization_pk,
                    brand_pk=brand_pk,
                )

            except tweepy.Unauthorized:
                messages.error(
                    request,
                    "Invalid Twitter credentials. Please check your API keys and tokens.",
                )
            except Exception as e:
                messages.error(request, f"Error connecting Twitter: {str(e)}")
        else:
            messages.error(
                request, "All Twitter API fields are required, including Bearer Token."
            )

    return render(
        request,
        "organizations/twitter_connect.html",
        {"organization": organization, "brand": brand},
    )


@login_required
def organization_brand_test_tweet(request, organization_pk, brand_pk):
    """Send a test tweet from a brand's Twitter account"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check if user is admin of the organization
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    if not brand.has_twitter_config:
        return JsonResponse(
            {"success": False, "error": "Twitter not configured for this brand"}
        )

    if request.method == "POST":
        tweet_content = request.POST.get(
            "content", f"Test tweet from {brand.name} via Gemnar! 🚀"
        )

        try:
            # Setup Twitter API v2 client
            client = tweepy.Client(
                bearer_token=brand.twitter_bearer_token,
                consumer_key=brand.twitter_api_key,
                consumer_secret=brand.twitter_api_secret,
                access_token=brand.twitter_access_token,
                access_token_secret=brand.twitter_access_token_secret,
                wait_on_rate_limit=True,
            )

            # First verify credentials
            try:
                me = client.get_me()
                if not me.data:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Unable to verify Twitter credentials. Please check your API keys.",
                        }
                    )
            except tweepy.Unauthorized:
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            "Twitter API credentials are invalid. Please check "
                            "your API keys and regenerate them if necessary."
                        ),
                    }
                )

            # Send tweet using API v2
            response = client.create_tweet(text=tweet_content)

            if response.data:
                tweet_id = response.data["id"]
                tweet_url = (
                    f"https://twitter.com/{brand.twitter_username}/status/{tweet_id}"
                )

                # Send Slack notification if brand has Slack configured
                if brand.has_slack_config:
                    try:
                        import requests

                        message = (
                            f"🧪 *Test Tweet Posted for {brand.name}*\n"
                            f"Content: {tweet_content}\n"
                            f"Tweet URL: {tweet_url}\n"
                            f"Posted by: {request.user.username}"
                        )

                        payload = {
                            "text": message,
                            "username": f"Gemnar Bot - {brand.name}",
                            "icon_emoji": ":test_tube:",
                        }

                        if brand.slack_channel:
                            payload["channel"] = brand.slack_channel

                        requests.post(brand.slack_webhook_url, json=payload, timeout=10)
                    except Exception:
                        pass  # Don't fail test tweet if Slack fails

                return JsonResponse(
                    {
                        "success": True,
                        "tweet_id": tweet_id,
                        "tweet_url": tweet_url,
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Failed to send tweet - no response data",
                    }
                )

        except tweepy.Unauthorized:
            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Twitter API authorization failed. Please check your API "
                        "keys and ensure your Twitter app has 'Read and Write' "
                        "permissions."
                    ),
                }
            )
        except tweepy.Forbidden as e:
            error_message = str(e)
            if "403" in error_message and (
                "subset of X API" in error_message
                or "limited v1.1 endpoints" in error_message
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            "Your Twitter API access level doesn't support posting "
                            "tweets. You need to upgrade to Twitter API v1.1 with "
                            "Elevated access or Twitter API v2 with Basic access or "
                            "higher. Please visit https://developer.twitter.com/en/"
                            "portal/petition/essential/basic-info to request "
                            "elevated access."
                        ),
                        "error_type": "access_level",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Twitter API access forbidden: {error_message}. This could mean your app doesn't have write permissions, your account is restricted, or you need elevated API access.",
                    }
                )
        except tweepy.TooManyRequests:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API rate limit exceeded. Please wait a few minutes before trying again.",
                }
            )
        except Exception as e:
            error_message = str(e)
            if "403" in error_message and (
                "subset of X API" in error_message
                or "limited v1.1 endpoints" in error_message
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Your Twitter API access level doesn't support posting tweets. You need Basic access or higher for Twitter API v2. Please visit https://developer.x.com/en/portal/dashboard to upgrade your access level.",
                        "error_type": "access_level",
                    }
                )
            else:
                return JsonResponse(
                    {"success": False, "error": f"Error sending tweet: {error_message}"}
                )

    return JsonResponse({"success": False, "error": "Invalid request method"})


# Instagram Connection Views


@login_required
def organization_brand_connect_instagram(request, organization_pk, brand_pk):
    """Connect Instagram account to a brand"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check if user is admin of the organization
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        messages.error(
            request,
            "You don't have permission to manage Instagram connections for this brand.",
        )
        return redirect(
            "organization_brand_detail",
            organization_pk=organization_pk,
            brand_pk=brand_pk,
        )

    # Initialize context with form data and errors
    context = {
        "organization": organization,
        "brand": brand,
        "form_data": {},
        "field_errors": {},
        "meta_api_response": None,
    }

    if request.method == "POST":
        access_token = request.POST.get("access_token", "").strip()
        user_id = request.POST.get("user_id", "").strip()
        username = request.POST.get("username", "").strip()
        app_id = request.POST.get("app_id", "").strip()
        app_secret = request.POST.get("app_secret", "").strip()
        business_id = request.POST.get("business_id", "").strip()

        # Preserve form data for redisplay
        context["form_data"] = {
            "access_token": access_token,
            "user_id": user_id,
            "username": username,
            "app_id": app_id,
            "app_secret": app_secret,
            "business_id": business_id,
        }

        # Validate required fields
        field_errors = {}
        if not access_token:
            field_errors["access_token"] = "Access token is required"
        if not user_id:
            field_errors["user_id"] = "User ID is required"
        if not app_id:
            field_errors["app_id"] = "App ID is required"
        if not app_secret:
            field_errors["app_secret"] = "App Secret is required"
        if business_id and not business_id.isdigit():
            field_errors["business_id"] = "Business ID should be numeric"

        # Additional format validation
        if access_token and len(access_token) < 20:
            field_errors[
                "access_token"
            ] = "Access Token appears to be too short (minimum 20 characters)"
        if user_id and not user_id.isdigit():
            field_errors["user_id"] = "User ID should be numeric"
        if app_id and not app_id.isdigit():
            field_errors["app_id"] = "App ID should be numeric"

        context["field_errors"] = field_errors

        if not field_errors:
            try:
                # Test Instagram connection with detailed error handling
                import requests
                import json

                # First, validate the token with Instagram API
                token_url = "https://graph.instagram.com/v18.0/me"
                # Determine which token to validate (single access token now)
                chosen_token = access_token
                token_params = {
                    "fields": "id,username,account_type,media_count",
                    "access_token": chosen_token,
                }

                token_response = requests.get(token_url, params=token_params)
                token_data = token_response.json()

                # Store the Instagram API response for user feedback
                context["meta_api_response"] = {
                    "status_code": token_response.status_code,
                    "raw_response": token_data,
                    "url": token_url,
                    "request_params": token_params,
                }

                # If token validation successful, get detailed account info
                if token_response.status_code == 200:
                    # Get the actual user ID from the token (more reliable)
                    actual_user_id = token_data.get("id")

                    # Now get detailed account info using the verified user ID
                    url = f"https://graph.instagram.com/v18.0/{actual_user_id}"
                    params = {
                        "fields": "id,username,account_type,followers_count,follows_count,media_count,name,profile_picture_url",
                        "access_token": chosen_token,
                    }

                    response = requests.get(url, params=params)
                    response_data = response.json()

                    # Update meta_api_response with detailed info
                    if response.status_code == 200:
                        context["meta_api_response"][
                            "detailed_response"
                        ] = response_data
                else:
                    # Use the token validation response as the main response
                    response = token_response
                    response_data = token_data

                if response.status_code == 200:
                    user_data = response_data

                    # Verify it's an Instagram account
                    if "username" not in user_data:
                        field_errors[
                            "user_id"
                        ] = "This User ID doesn't appear to be associated with an Instagram account"
                        context["field_errors"] = field_errors
                        messages.error(
                            request,
                            f"Meta API Response (Code {response.status_code}): User ID valid but no Instagram username found. Please verify this is an Instagram Business account.",
                        )
                    else:
                        # Test posting permissions by attempting to get media
                        test_url = (
                            f"https://graph.instagram.com/v18.0/{actual_user_id}/media"
                        )
                        test_params = {
                            "access_token": access_token,
                            "limit": 1,
                        }
                        test_response = requests.get(test_url, params=test_params)

                        # Save Instagram credentials to brand
                        # Persist tokens (store in new user token + legacy access token for compatibility)
                        if access_token:
                            brand.instagram_access_token = access_token
                            brand.instagram_user_token = access_token
                        brand.instagram_user_id = (
                            actual_user_id  # Use verified ID from token
                        )
                        brand.instagram_username = username or user_data.get("username")
                        brand.instagram_app_id = app_id
                        brand.instagram_app_secret = app_secret
                        if business_id:
                            brand.instagram_business_id = business_id
                        update_fields = [
                            "instagram_user_id",
                            "instagram_username",
                            "instagram_app_id",
                            "instagram_app_secret",
                        ]
                        if business_id:
                            update_fields.append("instagram_business_id")
                        if access_token:
                            update_fields.extend(
                                ["instagram_access_token", "instagram_user_token"]
                            )
                        brand.save(update_fields=update_fields)

                        # Create detailed success message with API details
                        success_msg = f"Instagram account @{brand.instagram_username} connected successfully!"
                        if "account_type" in user_data:
                            success_msg += f" Account Type: {user_data['account_type']}"
                        if "followers_count" in user_data:
                            success_msg += (
                                f" | Followers: {user_data['followers_count']:,}"
                            )

                        messages.success(request, success_msg)

                        # Add API response details as info message
                        messages.info(
                            request,
                            f"Meta API Connection Test Successful (HTTP {response.status_code}). "
                            f"User ID {user_data.get('id')} verified. "
                            f"Posting permissions: {'✓ Available' if test_response.status_code == 200 else '⚠ Limited'}.",
                        )

                        return redirect(
                            "organization_brand_detail",
                            organization_pk=organization_pk,
                            brand_pk=brand_pk,
                        )

                else:
                    # Handle specific Meta API errors
                    error_code = response_data.get("error", {}).get("code")
                    error_message = response_data.get("error", {}).get(
                        "message", "Unknown error"
                    )
                    error_type = response_data.get("error", {}).get("type", "Unknown")

                    if error_code == 190:  # Invalid access token
                        field_errors["access_token"] = "Invalid or expired access token"
                        messages.error(
                            request,
                            f"Meta API Error {error_code}: {error_message}. "
                            f"Please generate a new long-lived access token from your Facebook app settings.",
                        )
                    elif error_code == 100:  # Invalid parameter
                        if "user_id" in error_message.lower():
                            field_errors[
                                "user_id"
                            ] = "Invalid User ID format or account not found"
                        messages.error(
                            request,
                            f"Meta API Error {error_code}: {error_message}. "
                            f"Please verify your User ID and ensure it's associated with an Instagram account.",
                        )
                    elif error_code == 10:  # Permission error
                        messages.error(
                            request,
                            f"Meta API Error {error_code}: {error_message}. "
                            f"Your app doesn't have the required Instagram permissions. "
                            f"Please add Instagram Basic Display or Instagram Graph API to your Facebook app.",
                        )
                    elif response.status_code == 400:
                        field_errors[
                            "access_token"
                        ] = "Access token or User ID format is incorrect"
                        messages.error(
                            request,
                            f"Meta API Error (HTTP {response.status_code}): {error_message}. "
                            f"Please check your credentials format.",
                        )
                    elif response.status_code == 403:
                        messages.error(
                            request,
                            f"Meta API Error (HTTP {response.status_code}): {error_message}. "
                            f"Access forbidden. Check your app permissions and account status.",
                        )
                    else:
                        messages.error(
                            request,
                            f"Meta API Error (HTTP {response.status_code}, Code {error_code}): {error_message}. "
                            f"Error Type: {error_type}. Please check the Meta API response details below.",
                        )

                    context["field_errors"] = field_errors

            except requests.exceptions.RequestException as e:
                messages.error(
                    request,
                    f"Network Error: Unable to connect to Meta API. {str(e)}. "
                    f"Please check your internet connection and try again.",
                )
            except json.JSONDecodeError as e:
                messages.error(
                    request,
                    f"Meta API Response Error: Received invalid response format. {str(e)}. "
                    f"This may indicate a temporary API issue.",
                )
            except Exception as e:
                messages.error(
                    request,
                    f"Unexpected Error: {str(e)}. Please try again or contact support if the issue persists.",
                )
        else:
            messages.error(
                request,
                f"Please correct the highlighted fields: {', '.join(field_errors.keys())}",
            )

    return render(
        request,
        "organizations/instagram_connect.html",
        context,
    )


@login_required
def test_instagram_access_token(request, organization_pk, brand_pk):
    """Test (or ad-hoc validate) an Instagram user access token.

    Accepts optional JSON body with {"access_token": "..."}; falls back to the
    stored brand token. Returns structured error info including code, subcode,
    and remediation hints for session invalidation scenarios.
    """
    import json as _json
    import requests

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse(
            {"success": False, "error": "Permission denied"},
            status=403,
        )

    # Parse posted token if provided
    posted_token = None
    if request.method == "POST" and request.body:
        try:
            payload = _json.loads(request.body.decode("utf-8"))
            posted_token = (
                (payload.get("access_token") or "").strip()
                if isinstance(payload, dict)
                else None
            )
        except Exception:  # noqa: BLE001
            posted_token = None

    access_token = posted_token or getattr(brand, "instagram_access_token", None)
    if not access_token:
        return JsonResponse(
            {"success": False, "error": "No access token provided or stored."},
            status=400,
        )
    # Sanitize (remove accidental surrounding quotes / whitespace)
    access_token = access_token.strip().strip("'\"")

    # Decide endpoint: Basic Display style tokens usually start with IG* (long-lived IGQV... historically);
    # Graph API user tokens often start with 'EA'. The /graph.instagram.com/me endpoint rejects 'EA...' tokens.
    is_basic_display = access_token.upper().startswith("IG")
    if is_basic_display:
        url = "https://graph.instagram.com/me"
        params = {"fields": "id,username", "access_token": access_token}
    else:
        # Fallback to Facebook Graph /me which will parse generic user token. We can later attempt retrieval of IG account.
        url = "https://graph.facebook.com/v19.0/me"
        params = {"fields": "id,name", "access_token": access_token}

    debug_info = {}
    # Optionally call debug_token to produce richer diagnostics for non IG tokens if app creds available.
    if not is_basic_display and brand.instagram_app_id and brand.instagram_app_secret:
        import requests as _requests

        try:
            app_token = f"{brand.instagram_app_id}|{brand.instagram_app_secret}"
            dbg_resp = _requests.get(
                "https://graph.facebook.com/debug_token",
                params={
                    "input_token": access_token,
                    "access_token": app_token,
                },
                timeout=10,
            )
            try:
                debug_info = dbg_resp.json()
            except Exception:  # noqa: BLE001
                debug_info = {"raw_debug": dbg_resp.text[:500]}
        except Exception as _e:  # noqa: BLE001
            debug_info = {"debug_error": str(_e)}

    try:
        resp = requests.get(url, params=params, timeout=15)
    except requests.RequestException as e:
        return JsonResponse(
            {"success": False, "error": f"Network error: {e}"}, status=502
        )

    # Attempt parse
    try:
        data = resp.json()
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Non-JSON response from Instagram API",
                "raw": resp.text[:1000],
            },
            status=resp.status_code if resp.status_code >= 400 else 400,
        )

    if resp.status_code == 200 and data.get("id"):
        # Normalize username field when using /me on facebook graph (it returns name not username)
        username = data.get("username") or data.get("name")
        return JsonResponse(
            {
                "success": True,
                "user_id": data.get("id"),
                "username": username,
                "message": "Token valid",
                "token_type": "basic_display" if is_basic_display else "graph_user",
                "used_posted_token": bool(posted_token),
                "debug": debug_info if debug_info else None,
            }
        )

    # Failure path — extract error info
    error_info = data.get("error") if isinstance(data, dict) else None
    code = error_info.get("code") if isinstance(error_info, dict) else None
    subcode = error_info.get("error_subcode") if isinstance(error_info, dict) else None
    msg = error_info.get("message") if isinstance(error_info, dict) else None
    etype = error_info.get("type") if isinstance(error_info, dict) else None

    hints = []
    session_invalidated = False
    if code == 190:  # Generic OAuth token error
        # Password change / session invalidation (460, 463, 467, etc.)
        if subcode in {460, 463, 467} or (
            msg and "session has been invalidated" in msg.lower()
        ):
            session_invalidated = True
            hints.append(
                "Password/security event: new short-lived token, then exchange."  # noqa: E501
            )
            hints.append("Have the user log out and back in via the auth flow.")
            hints.append("If long-lived: re-create (short -> long-lived exchange).")
        else:
            if msg and "cannot parse access token" in msg.lower():
                hints.append(
                    "Token format not recognized by endpoint. If this is an EA* Graph token, use Graph endpoint not graph.instagram.com."
                )
                hints.append(
                    "Confirm you copied the full token (no extra quotes or truncation)."
                )
                if not is_basic_display:
                    hints.append(
                        "If you intended a Basic Display token, generate via OAuth exchange (short-lived -> long-lived)."
                    )
            else:
                hints.append("Access token expired or invalid. Regenerate the token.")
    else:
        hints.append("Verify scopes and IG account added as tester for the app.")

    return JsonResponse(
        {
            "success": False,
            "error": msg or "Token validation failed",
            "code": code,
            "subcode": subcode,
            "type": etype,
            "session_invalidated": session_invalidated,
            "hints": hints,
            "http_status": resp.status_code,
            "used_posted_token": bool(posted_token),
            "raw": data,
            "debug": debug_info if debug_info else None,
            "guessed_token_type": "basic_display" if is_basic_display else "graph_user",
        },
        status=resp.status_code if resp.status_code >= 400 else 400,
    )


@login_required
def test_instagram_business_id(request, organization_pk, brand_pk):
    """Validate an Instagram (Meta) Business ID.

    JSON body: {"business_id": "...", "access_token": "..."}
    Token precedence: posted token, else stored brand.instagram_access_token.
    Graph endpoint used:
        GET https://graph.facebook.com/v19.0/{business_id}
            ?fields=id,name,verification_status
    """
    import json as _json
    import requests

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse(
            {"success": False, "error": "Permission denied"}, status=403
        )

    business_id = None
    posted_token = None
    if request.method == "POST" and request.body:
        try:
            payload = _json.loads(request.body.decode("utf-8"))
            if isinstance(payload, dict):
                business_id = (payload.get("business_id") or "").strip()
                posted_token = (payload.get("access_token") or "").strip()
        except Exception:  # noqa: BLE001
            pass

    if not business_id or not business_id.isdigit():
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid or missing business_id (must be numeric).",
            },
            status=400,
        )

    access_token = posted_token or getattr(brand, "instagram_access_token", None)
    if not access_token:
        return JsonResponse(
            {"success": False, "error": "No access token provided or stored."},
            status=400,
        )

    url = f"https://graph.facebook.com/v19.0/{business_id}"
    params = {
        "fields": "id,name,verification_status",
        "access_token": access_token,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
    except requests.RequestException as e:  # Network issue
        return JsonResponse(
            {"success": False, "error": f"Network error: {e}"}, status=502
        )

    try:
        data = resp.json()
    except ValueError:
        return JsonResponse(
            {
                "success": False,
                "error": "Non-JSON response from Meta API",
                "raw": resp.text[:1000],
            },
            status=resp.status_code if resp.status_code >= 400 else 400,
        )

    if resp.status_code == 200 and data.get("id"):
        return JsonResponse(
            {
                "success": True,
                "business_id": data.get("id"),
                "name": data.get("name"),
                "verification_status": data.get("verification_status"),
                "used_posted_token": bool(posted_token),
            }
        )

    # Failure path
    error_info = data.get("error") if isinstance(data, dict) else None
    msg = error_info.get("message") if isinstance(error_info, dict) else None
    code = error_info.get("code") if isinstance(error_info, dict) else None
    subcode = error_info.get("error_subcode") if isinstance(error_info, dict) else None

    hints = []
    if code == 190:
        hints.append("Access token invalid/expired – generate a new user token.")
    elif code == 10:
        hints.append("Missing permission: ensure business_scoped permissions.")
    else:
        hints.append("Verify the Business ID exists and token has required scopes.")

    return JsonResponse(
        {
            "success": False,
            "error": msg or "Business ID validation failed",
            "code": code,
            "subcode": subcode,
            "http_status": resp.status_code,
            "hints": hints,
            "raw": data,
        },
        status=resp.status_code if resp.status_code >= 400 else 400,
    )


# ---- Instagram OAuth (Automatic Re-Auth / Recovery) ---- #
@login_required
def instagram_oauth_start(request, organization_pk, brand_pk):
    """Initiate Instagram Basic Display OAuth to recover a new user token.

    We rely on stored app_id/app_secret on the Brand. Builds authorization URL,
    sends user to consent, then callback exchanges code for short-lived token
    and attempts long-lived upgrade.
    """
    from django.urls import reverse
    from urllib.parse import urlencode

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return HttpResponseForbidden("Permission denied")

    if not (brand.instagram_app_id and brand.instagram_app_secret):
        messages.error(request, "App ID / Secret must be saved before re-auth.")
        return redirect(
            "organization_brand_connect_instagram",
            organization_pk=organization.pk,
            brand_pk=brand.pk,
        )

    # NOTE: Basic Display style endpoint used even for business scopes.
    client_id = brand.instagram_app_id.strip()
    redirect_uri = request.build_absolute_uri(
        reverse(
            "instagram_oauth_callback",
            kwargs={
                "organization_pk": organization.pk,
                "brand_pk": brand.pk,
            },
        )
    )

    # Updated 2025 business scopes (Meta may trim unsupported ones).
    scopes = [
        "instagram_business_basic",
        "instagram_business_content_publish",
        "instagram_business_manage_messages",
        "instagram_business_manage_comments",
        "public_profile",  # fallback
    ]
    import secrets

    state_token = secrets.token_urlsafe(16)
    request.session["ig_oauth_state"] = state_token
    request.session["ig_oauth_brand"] = brand.pk

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": ",".join(scopes),
        "response_type": "code",
        "state": state_token,
    }

    auth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"
    return HttpResponseRedirect(auth_url)


@login_required
def instagram_oauth_callback(request, organization_pk, brand_pk):
    """Handle OAuth redirect and store refreshed user access token.

    Simplified: we exchange code -> short-lived token and attempt long-lived
    upgrade; resulting token is stored in instagram_user_token and legacy
    instagram_access_token for backward compatibility. Deprecated short/long
    token fields are no longer updated.
    """
    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return HttpResponseForbidden("Permission denied")

    stored_state = request.session.get("ig_oauth_state")
    stored_brand = request.session.get("ig_oauth_brand")
    code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")
    error_desc = request.GET.get("error_description")

    if error:
        messages.error(request, f"Instagram auth error: {error_desc or error}")
        return redirect(
            "organization_brand_connect_instagram",
            organization_pk=organization.pk,
            brand_pk=brand.pk,
        )

    if not code or not state or state != stored_state or stored_brand != brand.pk:
        messages.error(request, "Invalid OAuth state / response.")
        return redirect(
            "organization_brand_connect_instagram",
            organization_pk=organization.pk,
            brand_pk=brand.pk,
        )

    # Clear session markers to prevent reuse
    request.session.pop("ig_oauth_state", None)
    request.session.pop("ig_oauth_brand", None)

    import requests
    from django.urls import reverse

    redirect_uri = request.build_absolute_uri(
        reverse(
            "instagram_oauth_callback",
            kwargs={
                "organization_pk": organization.pk,
                "brand_pk": brand.pk,
            },
        )
    )
    # Exchange code -> short-lived token (access_token & maybe user_id)
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": brand.instagram_app_id.strip(),
        "client_secret": brand.instagram_app_secret.strip(),
        "redirect_uri": redirect_uri,
        "code": code,
    }
    short_token = None
    user_id = None
    try:
        token_resp = requests.get(token_url, params=params, timeout=20)
        token_data = token_resp.json()
        if token_resp.status_code == 200 and "access_token" in token_data:
            short_token = token_data["access_token"]
            user_id = token_data.get("user_id")
        else:
            err_msg = token_data.get("error", {}).get("message", token_resp.text)
            messages.error(request, f"Failed to exchange code: {err_msg}")
            return redirect(
                "organization_brand_connect_instagram",
                organization_pk=organization.pk,
                brand_pk=brand.pk,
            )
    except Exception as e:  # noqa: BLE001
        messages.error(request, f"Network error exchanging code: {e}")
        return redirect(
            "organization_brand_connect_instagram",
            organization_pk=organization.pk,
            brand_pk=brand.pk,
        )

    # Exchange for long-lived token if possible (Basic Display style). Some business tokens may already be long-lived.
    long_token = None
    try:
        exchange_url = "https://graph.instagram.com/access_token"
        exchange_params = {
            "grant_type": "ig_exchange_token",
            "client_secret": brand.instagram_app_secret.strip(),
            "access_token": short_token,
        }
        exch_resp = requests.get(exchange_url, params=exchange_params, timeout=20)
        exch_data = exch_resp.json()
        if exch_resp.status_code == 200 and "access_token" in exch_data:
            long_token = exch_data["access_token"]
        else:
            # If exchange fails, fall back to short token
            long_token = short_token
    except Exception:  # noqa: BLE001
        long_token = short_token

    # Persist token info (new canonical field + legacy access token)
    final_token = long_token or short_token
    if final_token:
        brand.instagram_user_token = final_token
        brand.instagram_access_token = final_token  # legacy compatibility
    if user_id and not brand.instagram_user_id:
        brand.instagram_user_id = user_id
    brand.save(
        update_fields=[
            "instagram_user_token",
            "instagram_access_token",
            "instagram_user_id",
        ]
    )

    if long_token and long_token != short_token:
        msg = "Instagram user token refreshed and upgraded to long-lived token."
    else:
        msg = "Instagram user token refreshed."  # either short-lived or already long-lived
    messages.success(request, msg)
    return redirect(
        "organization_brand_connect_instagram",
        organization_pk=organization.pk,
        brand_pk=brand.pk,
    )


@login_required
def debug_instagram_token(request, organization_pk, brand_pk):
    """Introspect stored Instagram user/access token via Graph API /debug_token.

    Requirements:
      - Admin user
      - Stored app_id & app_secret
      - Stored user/access token
    Returns JSON with validation info, scopes, expiry, classification.
    """
    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Permission check (admin only for token introspection)
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse(
            {"success": False, "error": "Permission denied"}, status=403
        )

    access_token = brand.instagram_user_token or brand.instagram_access_token
    if not access_token:
        return JsonResponse(
            {"success": False, "error": "No Instagram token stored"},
            status=400,
        )
    if not (brand.instagram_app_id and brand.instagram_app_secret):
        return JsonResponse(
            {"success": False, "error": "App ID / Secret required"},
            status=400,
        )

    import requests

    debug_url = "https://graph.facebook.com/debug_token"
    params = {
        "input_token": access_token,
        "access_token": (f"{brand.instagram_app_id}|{brand.instagram_app_secret}"),
    }
    try:
        resp = requests.get(debug_url, params=params, timeout=15)
    except requests.RequestException as e:  # noqa: BLE001
        return JsonResponse(
            {"success": False, "error": f"Network error: {e}"},
            status=502,
        )

    try:
        payload = resp.json()
    except Exception:  # noqa: BLE001
        payload = {"raw": resp.text[:800]}

    if resp.status_code != 200:
        return JsonResponse(
            {
                "success": False,
                "http_status": resp.status_code,
                "data": payload,
            },
            status=resp.status_code,
        )

    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    scopes = data.get("scopes") or data.get("granular_scopes") or []
    token_len = len(access_token)
    if token_len > 150 and "." in access_token:
        classification = "graph_user_token"
    elif access_token.startswith("IGQV"):
        classification = "basic_display_style"
    else:
        classification = "unknown"

    recommended_scopes = [
        "instagram_business_basic",
        "instagram_business_content_publish",
        "instagram_business_manage_messages",
        "instagram_business_manage_comments",
    ]
    missing_recommended = [s for s in recommended_scopes if s not in scopes]

    result = {
        "success": True,
        "application": data.get("application"),
        "type": data.get("type"),
        "is_valid": data.get("is_valid"),
        "expires_at": data.get("expires_at"),
        "issued_at": data.get("issued_at"),
        "scopes": scopes,
        "classification": classification,
        "token_length": token_len,
        "prefix": access_token[:6],
        # Short helper booleans for UI consumption
        "has_publish_scope": any(
            s for s in scopes if "content_publish" in s or "manage_messages" in s
        ),
        "missing_recommended_scopes": missing_recommended,
    }
    if request.user.is_staff:
        result["raw_token"] = access_token
    else:
        result["masked_token"] = access_token[:6] + "…" + access_token[-6:]
    return JsonResponse(result)


@login_required
def organization_brand_test_instagram_post(request, organization_pk, brand_pk):
    """Send a test Instagram post from a brand's Instagram account"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check if user is admin of the organization
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    if not brand.has_instagram_config:
        return JsonResponse(
            {"success": False, "error": "Instagram not configured for this brand"}
        )

    if request.method == "POST":
        post_content = request.POST.get(
            "content", f"Test post from {brand.name} via Gemnar! 🚀"
        )
        image_file = request.FILES.get("image")

        if not image_file:
            return JsonResponse(
                {"success": False, "error": "Image is required for Instagram posts"}
            )

        try:
            # Create Instagram post record
            from .models import BrandInstagramPost

            instagram_post = BrandInstagramPost.objects.create(
                brand=brand, content=post_content, image=image_file, status="approved"
            )

            # Post to Instagram
            success, error = instagram_post.post_to_instagram()

            if success:
                return JsonResponse(
                    {
                        "success": True,
                        "instagram_id": instagram_post.instagram_id,
                        "instagram_url": instagram_post.instagram_url,
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Failed to post to Instagram: {error}",
                    }
                )

        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error posting to Instagram: {str(e)}"}
            )

    return JsonResponse({"success": False, "error": "Invalid request method"})


# --- AJAX granular Instagram field update --- #
@login_required
def update_instagram_field(request, organization_pk, brand_pk, field_name):
    """Update a single Instagram-related field on Brand via AJAX.

    Expects JSON body: {"value": "..."}
    Returns masked value for sensitive token/secret fields.
    """
    if request.method != "POST":  # Only allow POST
        return JsonResponse({"success": False, "error": "POST required"}, status=405)

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse(
            {"success": False, "error": "Permission denied"}, status=403
        )

    import json

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:  # noqa: BLE001
        data = {}
    raw_value = (data.get("value") or "").strip()

    allowed_fields = {
        "access_token": "instagram_access_token",
        "user_id": "instagram_user_id",
        "username": "instagram_username",
        "app_id": "instagram_app_id",
        "app_secret": "instagram_app_secret",
        "business_id": "instagram_business_id",
        "user_token": "instagram_user_token",
        "app_token": "instagram_app_token",
    }
    if field_name not in allowed_fields:
        return JsonResponse({"success": False, "error": "Invalid field"}, status=400)

    model_field = allowed_fields[field_name]

    # Validation rules
    if (
        field_name in {"user_id", "app_id", "business_id"}
        and raw_value
        and not raw_value.isdigit()
    ):
        return JsonResponse({"success": False, "error": "Must be numeric"}, status=400)
    if (
        field_name in {"access_token", "user_token", "app_token"}
        and raw_value
        and len(raw_value) < 20
    ):
        return JsonResponse({"success": False, "error": "Token too short"}, status=400)
    if field_name == "app_secret" and raw_value and len(raw_value) < 10:
        return JsonResponse({"success": False, "error": "Secret too short"}, status=400)

    setattr(brand, model_field, raw_value or None)
    brand.save(update_fields=[model_field, "updated_at"])

    masked = raw_value
    if (
        field_name in {"access_token", "user_token", "app_token", "app_secret"}
        and raw_value
    ):
        if len(raw_value) <= 8:
            masked = "*" * len(raw_value)
        else:
            masked = raw_value[:4] + ("*" * (len(raw_value) - 8)) + raw_value[-4:]

    return JsonResponse(
        {
            "success": True,
            "field": field_name,
            "masked_value": masked,
            "empty": not bool(raw_value),
        }
    )


@login_required
@require_POST
def generate_instagram_app_access_token(request, organization_pk, brand_pk):
    """
    Server-side generation of an app access token (client_credentials) so the
    app secret is never sent from the browser.

    NOTE:
    - App access tokens have limitations vs user tokens (reduced user data).
    - Use a user access token for user-specific data or posting on behalf of a user.
    - We do NOT persist the generated token; caller treats it as transient.
    """
    import json
    import requests
    import logging

    logger = logging.getLogger(__name__)

    organization = get_object_or_404(Organization, pk=organization_pk)
    # Ensure brand belongs to organization (also enforces existence)
    get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Verify admin permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse(
            {"success": False, "error": "Permission denied"}, status=403
        )

    try:
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON body"}, status=400
            )

        app_id = (data.get("app_id") or "").strip()
        app_secret = (data.get("app_secret") or "").strip()

        if not app_id or not app_secret:
            return JsonResponse(
                {
                    "success": False,
                    "error": "app_id and app_secret are required",
                },
                status=400,
            )

        # Call Meta Graph API securely from server
        url = "https://graph.facebook.com/oauth/access_token"
        params = {
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "client_credentials",
        }

        try:
            logger.debug(
                "Generating app access token via Graph API for app_id=%s org=%s brand=%s",  # noqa: E501
                app_id,
                organization_pk,
                brand_pk,
            )
            response = requests.get(url, params=params, timeout=15)
        except requests.RequestException as e:
            logger.warning(
                "Network error contacting Meta Graph API for app_id=%s: %s", app_id, e
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Network error contacting Meta Graph API: {e}",
                },
                status=502,
            )

        # Attempt to parse JSON regardless of status for better diagnostics
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}

        if response.status_code == 200 and "access_token" in payload:
            # Do NOT store secret or token; return to client
            logger.debug(
                "Successfully generated app access token (length=%d) for app_id=%s",
                len(payload["access_token"]),
                app_id,
            )
            return JsonResponse(
                {
                    "success": True,
                    "access_token": payload["access_token"],
                    "token_type": payload.get("token_type"),
                    "issued_via": "client_credentials",
                    "limitations": [
                        "Limited user data vs user access token",
                        "Not suitable for posting user media",
                        "Do not embed in distributed client apps",
                    ],
                }
            )
        else:
            # Meta style error envelope
            error_message = "Failed to generate app access token"
            if isinstance(payload, dict):
                meta_error = payload.get("error")
                if isinstance(meta_error, dict):
                    msg = meta_error.get("message")
                    code = meta_error.get("code")
                    type_ = meta_error.get("type")
                    error_message += (
                        f": {msg} (code={code}, type={type_})" if msg else ""
                    )
                    # Provide human-readable hints for common codes
                    hints = []
                    if code == 101:  # OAuthException - Error validating application
                        hints.append(
                            "Confirm the App ID is correct (numeric) and matches the App Secret you copied."
                        )
                        hints.append(
                            "Ensure you're not mixing a Test App secret with the main App ID (Meta creates test apps)."
                        )
                        hints.append(
                            "Open the App in Meta Developer Dashboard to verify it isn't in a locked or deleted state."
                        )
                        hints.append(
                            "If this persists, it can be a transient Meta platform issue — wait a few minutes and retry."
                        )
                        hints.append(
                            "Try specifying an explicit Graph API version (e.g. v19.0) if generic endpoint keeps failing."
                        )
                    else:
                        hints = []
                else:
                    hints = []
            else:
                hints = []
            logger.warning(
                "App token generation failed for app_id=%s status=%s body=%s",  # noqa: E501
                app_id,
                response.status_code,
                payload,
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": error_message,
                    "meta": payload,
                    "hints": hints,
                },
                status=(response.status_code if response.status_code >= 400 else 400),
            )
    except Exception as e:  # Broad catch to ensure no secret leakage
        logger.exception(
            "Unexpected error generating app access token for app_id=%s: %s", app_id, e
        )
        return JsonResponse(
            {"success": False, "error": f"Unexpected server error: {str(e)}"},
            status=500,
        )


@login_required
@require_POST
def validate_facebook_app_id(request, organization_pk, brand_pk):
    """Validate a Facebook App ID (optionally with secret) server-side.
    If an app secret is provided, attempt to obtain an app access token and
    then fetch basic app info, improving validation accuracy for non-public apps.
    """
    import json
    import logging
    import requests

    logger = logging.getLogger(__name__)

    organization = get_object_or_404(Organization, pk=organization_pk)
    get_object_or_404(Brand, pk=brand_pk, organization=organization)

    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse(
            {"success": False, "error": "Permission denied"}, status=403
        )

    try:
        try:
            body = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "error": "Invalid JSON body"}, status=400
            )

        app_id = (body.get("app_id") or "").strip()
        app_secret = (body.get("app_secret") or "").strip()

        if not app_id:
            return JsonResponse(
                {"success": False, "error": "app_id required"}, status=400
            )

        base_version = "v19.0"  # explicit versioning for stability

        app_token = None
        if app_secret:
            # Attempt to generate app token
            token_url = f"https://graph.facebook.com/{base_version}/oauth/access_token"
            params = {
                "client_id": app_id,
                "client_secret": app_secret,
                "grant_type": "client_credentials",
            }
            try:
                t_resp = requests.get(token_url, params=params, timeout=15)
                t_payload = (
                    t_resp.json()
                    if t_resp.headers.get("Content-Type", "").startswith(
                        "application/json"
                    )
                    else {}
                )
                if t_resp.status_code == 200 and "access_token" in t_payload:
                    app_token = t_payload["access_token"]
                else:
                    logger.debug(
                        "App token generation for validation failed status=%s body=%s",
                        t_resp.status_code,
                        t_payload,
                    )
            except requests.RequestException as e:
                logger.debug("App token generation request exception: %s", e)

        # Fetch app info
        info_url = f"https://graph.facebook.com/{base_version}/{app_id}"
        info_params = {"fields": "id,name"}
        if app_token:
            info_params["access_token"] = app_token

        try:
            resp = requests.get(info_url, params=info_params, timeout=15)
        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "error": f"Network error fetching app info: {e}"},
                status=502,
            )

        try:
            payload = resp.json()
        except ValueError:
            payload = {"raw": resp.text}

        if resp.status_code == 200 and payload.get("id") == app_id:
            return JsonResponse(
                {
                    "success": True,
                    "app_id": payload.get("id"),
                    "name": payload.get("name"),
                    "used_access_token": bool(app_token),
                }
            )

        # Build descriptive error
        error_msg = "App ID validation failed"
        hints = []
        if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
            err = payload["error"]
            msg = err.get("message")
            code = err.get("code")
            etype = err.get("type")
            error_msg += f": {msg} (code={code}, type={etype})" if msg else ""
            # Common codes: 803 = unknown object
            if code == 803:
                hints.append(
                    "Check that the App ID is correct and not a Test App ID mismatch."
                )
                hints.append(
                    "Open the Meta Developer Dashboard to confirm the app still exists."
                )
            if code == 190:
                hints.append(
                    "If using an access token, it may be invalid/expired; re-generate app token."
                )
        else:
            hints.append("Non-JSON response from Graph API; retry after a short delay.")

        return JsonResponse(
            {
                "success": False,
                "error": error_msg,
                "meta": payload,
                "hints": hints,
                "used_access_token": bool(app_token),
            },
            status=resp.status_code if resp.status_code >= 400 else 400,
        )

    except Exception as e:  # pylint: disable=broad-except
        return JsonResponse(
            {"success": False, "error": f"Unexpected server error: {e}"}, status=500
        )


@login_required
def brand_instagram_queue(request, organization_pk, brand_pk):
    """View and manage brand Instagram queue"""
    from django.utils import timezone
    from .models import BrandInstagramPost

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check if user is member of the organization
    if not organization.users.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this brand.")
        return redirect("organization_list")

    # Handle POST request for creating new Instagram posts
    if request.method == "POST":
        org_user = organization.organization_users.filter(user=request.user).first()
        if not org_user or not org_user.is_admin:
            return JsonResponse({"success": False, "error": "Permission denied"})

        content = request.POST.get("content", "")
        image_file = request.FILES.get("image")
        video_file = request.FILES.get("video")
        scheduled_for = request.POST.get("scheduled_for")
        status = request.POST.get("status", "draft")
        is_video_post = request.POST.get("is_video_post", "false").lower() == "true"

        # Video-specific fields
        video_prompt = request.POST.get("video_prompt", "")
        video_quality = request.POST.get("video_quality", "low")
        video_duration = request.POST.get("video_duration", "5")
        generated_video_url = request.POST.get("generated_video_url", "")

        # Validation
        if is_video_post:
            if not video_file and not generated_video_url:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Video file or generated video is required for video posts",
                    }
                )
        else:
            if not image_file:
                return JsonResponse(
                    {"success": False, "error": "Image is required for image posts"}
                )

        try:
            # Parse scheduled_for if provided
            scheduled_datetime = None
            if scheduled_for:
                from django.utils.dateparse import parse_datetime

                scheduled_datetime = parse_datetime(scheduled_for)

            # Create the Instagram post
            instagram_post = BrandInstagramPost.objects.create(
                brand=brand,
                content=content,
                image=image_file if not is_video_post else None,
                video=video_file if is_video_post else None,
                status=status,
                scheduled_for=scheduled_datetime,
                is_video_post=is_video_post,
                video_prompt=video_prompt if is_video_post else "",
                video_quality=video_quality if is_video_post else "low",
                video_duration=(
                    float(video_duration) if is_video_post and video_duration else None
                ),
            )

            # Handle generated video URL (download and save)
            if is_video_post and generated_video_url:
                try:
                    import requests
                    from django.core.files.base import ContentFile

                    response = requests.get(generated_video_url, timeout=120)
                    response.raise_for_status()

                    # Save the generated video
                    video_content = ContentFile(
                        response.content,
                        name=f"generated_video_{instagram_post.id}.mp4",
                    )
                    instagram_post.video.save(
                        f"generated_video_{instagram_post.id}.mp4",
                        video_content,
                        save=True,
                    )

                    # Generate thumbnail if needed
                    from website.video_utils import video_service

                    thumbnail = video_service.generate_video_thumbnail(
                        generated_video_url
                    )
                    if thumbnail:
                        instagram_post.video_thumbnail.save(
                            f"thumb_{instagram_post.id}.jpg", thumbnail, save=True
                        )

                except Exception as e:
                    # If video download fails, mark as failed
                    instagram_post.status = "failed"
                    instagram_post.error_message = (
                        f"Failed to download generated video: {str(e)}"
                    )
                    instagram_post.save()

            return JsonResponse({"success": True, "post_id": instagram_post.id})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    # Get all Instagram posts for this brand
    now = timezone.now()

    # Handle sorting
    sort_by = request.GET.get("sort", "created_at")  # Default to most recent
    sort_order = request.GET.get("order", "desc")  # Default to descending

    # Define available sort options
    sort_options = {
        "created_at": "created_at",
        "posted_at": "posted_at",
        "scheduled_for": "scheduled_for",
        "like_count": "like_count",
        "comment_count": "comment_count",
        "share_count": "share_count",
        "reach": "reach",
        "impressions": "impressions",
        "saved_count": "saved_count",
        "video_views": "video_views",
        "status": "status",
    }

    # Validate sort parameter
    if sort_by not in sort_options:
        sort_by = "created_at"

    # Build order_by string
    order_field = sort_options[sort_by]
    if sort_order == "desc":
        order_field = f"-{order_field}"

    posts = BrandInstagramPost.objects.filter(brand=brand).order_by(order_field)

    # Check if current user is admin for editing permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    is_admin = org_user and org_user.is_admin

    # Calculate counts for status display
    video_count = posts.filter(is_video_post=True).count()
    image_count = posts.filter(is_video_post=False).count()
    ready_count = posts.filter(status="approved").count()
    posted_count = posts.filter(status="posted").count()
    failed_count = posts.filter(status="failed").count()

    # Find next scheduled Instagram post
    next_scheduled_post = (
        posts.filter(status__in=["draft", "approved"], scheduled_for__gt=now)
        .order_by("scheduled_for")
        .first()
    )

    # Get subscription info
    subscription_plan = "Free"  # Default
    upgrade_url = "/upgrade/"  # Default upgrade URL

    # Check if brand has subscription info
    if (
        hasattr(brand, "stripe_subscription_status")
        and brand.stripe_subscription_status
    ):
        if brand.stripe_subscription_status in ["active", "trialing"]:
            subscription_plan = brand.stripe_subscription_status.title()
        elif brand.stripe_subscription_status == "canceled":
            subscription_plan = "Canceled"

    from django.conf import settings

    context = {
        "organization": organization,
        "brand": brand,
        "posts": posts,
        "is_admin": is_admin,
        "is_superuser": request.user.is_superuser,
        "current_time": now,
        "date_range": "All posts",
        "video_count": video_count,
        "image_count": image_count,
        "ready_count": ready_count,
        "posted_count": posted_count,
        "failed_count": failed_count,
        "next_scheduled_post": next_scheduled_post,
        "subscription_plan": subscription_plan,
        "upgrade_url": upgrade_url,
        "admin_url": settings.ADMIN_URL,
        "current_sort": sort_by,
        "current_order": sort_order,
        "sort_options": sort_options,
    }

    return render(request, "organizations/brand_instagram_queue.html", context)


# Organization Invitation Views


@login_required
def organization_invitation_send(request, organization_pk):
    """Send invitation to join organization"""
    organization = get_object_or_404(Organization, pk=organization_pk)

    # Check if user is admin of the organization
    if not organization.owners.filter(organization_user__user=request.user).exists():
        messages.error(
            request,
            "You don't have permission to send invitations for this organization.",
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    if request.method == "POST":
        email = request.POST.get("email")
        is_admin = request.POST.get("is_admin") == "on"

        if not email:
            messages.error(request, "Email is required.")
            return render(
                request,
                "organizations/invitation_send.html",
                {"organization": organization},
            )

        # Check if user is already a member
        if organization.users.filter(email=email).exists():
            messages.error(request, "User is already a member of this organization.")
            return render(
                request,
                "organizations/invitation_send.html",
                {"organization": organization},
            )

        # Check if invitation already exists
        existing_invitation = OrganizationInvitation.objects.filter(
            organization=organization, email=email, status="pending"
        ).first()

        if existing_invitation:
            messages.error(
                request, "An invitation has already been sent to this email address."
            )
            return render(
                request,
                "organizations/invitation_send.html",
                {"organization": organization},
            )

        # Create invitation
        invitation = OrganizationInvitation.objects.create(
            organization=organization,
            invited_by=request.user,
            email=email,
            is_admin=is_admin,
        )

        # Send email
        try:
            invitation_url = request.build_absolute_uri(
                reverse(
                    "organization_invitation_accept", kwargs={"token": invitation.token}
                )
            )

            subject = f"Invitation to join {organization.name} on Gemnar"
            html_message = render_to_string(
                "organizations/invitation_email.html",
                {
                    "organization": organization,
                    "invitation": invitation,
                    "invitation_url": invitation_url,
                    "inviter": request.user,
                },
            )

            send_mail(
                subject=subject,
                message=f"You've been invited to join {organization.name} on Gemnar. Visit: {invitation_url}",
                from_email="noreply@gemnar.com",
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )

            messages.success(request, f"Invitation sent to {email}")
            return redirect(
                "organization_invitation_list", organization_pk=organization_pk
            )

        except Exception as e:
            # If email fails, delete the invitation
            invitation.delete()
            messages.error(request, f"Failed to send invitation: {str(e)}")
            return render(
                request,
                "organizations/invitation_send.html",
                {"organization": organization},
            )

    return render(
        request, "organizations/invitation_send.html", {"organization": organization}
    )


@login_required
def organization_invitation_list(request, organization_pk):
    """List pending invitations for an organization"""
    organization = get_object_or_404(Organization, pk=organization_pk)

    # Check if user is admin of the organization
    if not organization.owners.filter(organization_user__user=request.user).exists():
        messages.error(
            request,
            "You don't have permission to view invitations for this organization.",
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    invitations = (
        OrganizationInvitation.objects.filter(organization=organization)
        .select_related("invited_by", "accepted_by")
        .order_by("-created_at")
    )

    return render(
        request,
        "organizations/invitation_list.html",
        {"organization": organization, "invitations": invitations},
    )


def organization_invitation_accept(request, token):
    """Accept organization invitation (public view, no login required)"""
    invitation = get_object_or_404(OrganizationInvitation, token=token)

    # Check if invitation can be accepted
    if not invitation.can_be_accepted():
        messages.error(request, "This invitation is no longer valid.")
        return render(
            request,
            "organizations/invitation_accept.html",
            {"invitation": invitation, "error": "invalid"},
        )

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to accept this invitation.")
            return redirect("account_login")

        # Check if the logged-in user's email matches the invitation
        if request.user.email != invitation.email:
            messages.error(
                request, "You can only accept invitations sent to your email address."
            )
            return render(
                request,
                "organizations/invitation_accept.html",
                {"invitation": invitation, "error": "email_mismatch"},
            )

        # Check if user is already a member
        if invitation.organization.users.filter(id=request.user.id).exists():
            messages.error(request, "You are already a member of this organization.")
            return render(
                request,
                "organizations/invitation_accept.html",
                {"invitation": invitation, "error": "already_member"},
            )

        # Accept the invitation
        with transaction.atomic():
            # Add user to organization
            org_user = OrganizationUser.objects.create(
                organization=invitation.organization,
                user=request.user,
                is_admin=invitation.is_admin,
            )

            # If admin, also create owner record
            if invitation.is_admin:
                OrganizationOwner.objects.create(
                    organization=invitation.organization, organization_user=org_user
                )

            # Update invitation status
            invitation.status = "accepted"
            invitation.accepted_by = request.user
            invitation.accepted_at = timezone.now()
            invitation.save()

        messages.success(
            request, f"Successfully joined {invitation.organization.name}!"
        )
        return redirect(
            "organization_detail", organization_pk=invitation.organization.pk
        )

    return render(
        request, "organizations/invitation_accept.html", {"invitation": invitation}
    )


@login_required
def organization_invitation_cancel(request, organization_pk, invitation_pk):
    """Cancel/delete an invitation"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    invitation = get_object_or_404(
        OrganizationInvitation, pk=invitation_pk, organization=organization
    )

    # Check if user is admin of the organization
    if not organization.owners.filter(organization_user__user=request.user).exists():
        messages.error(
            request,
            "You don't have permission to cancel invitations for this organization.",
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    if request.method == "POST":
        email = invitation.email
        invitation.delete()
        messages.success(request, f"Invitation to {email} has been canceled.")
        return redirect("organization_invitation_list", organization_pk=organization_pk)

    return render(
        request,
        "organizations/invitation_cancel.html",
        {"organization": organization, "invitation": invitation},
    )


@login_required
def organization_invitation_resend(request, organization_pk, invitation_pk):
    """Resend an invitation email"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    invitation = get_object_or_404(
        OrganizationInvitation, pk=invitation_pk, organization=organization
    )

    # Check if user is admin of the organization
    if not organization.owners.filter(organization_user__user=request.user).exists():
        messages.error(
            request,
            "You don't have permission to resend invitations for this organization.",
        )
        return redirect("organization_detail", organization_pk=organization_pk)

    # Only resend pending invitations
    if invitation.status != "pending":
        messages.error(request, "Can only resend pending invitations.")
        return redirect("organization_invitation_list", organization_pk=organization_pk)

    if request.method == "POST":
        try:
            # Update expiration date
            invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
            invitation.save()

            # Send email
            invitation_url = request.build_absolute_uri(
                reverse(
                    "organization_invitation_accept", kwargs={"token": invitation.token}
                )
            )

            subject = f"Invitation to join {organization.name} on Gemnar"
            html_message = render_to_string(
                "organizations/invitation_email.html",
                {
                    "organization": organization,
                    "invitation": invitation,
                    "invitation_url": invitation_url,
                    "inviter": request.user,
                },
            )

            send_mail(
                subject=subject,
                message=f"You've been invited to join {organization.name} on Gemnar. Visit: {invitation_url}",
                from_email="noreply@gemnar.com",
                recipient_list=[invitation.email],
                html_message=html_message,
                fail_silently=False,
            )

            messages.success(request, f"Invitation resent to {invitation.email}")

        except Exception as e:
            messages.error(request, f"Failed to resend invitation: {str(e)}")

    return redirect("organization_invitation_list", organization_pk=organization_pk)


@login_required
def brand_tweet_queue(request, organization_pk, brand_pk):
    """View and manage brand tweet queue for next 30 days"""
    from datetime import timedelta
    from django.utils import timezone
    from .models import BrandTweet, TweetStrategy

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check if user is member of the organization
    if not organization.users.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this brand.")
        return redirect("organization_list")

    # Get ALL tweets regardless of status or date
    now = timezone.now()
    now + timedelta(days=30)

    tweets = BrandTweet.objects.filter(brand=brand).order_by("scheduled_for")

    # Keep sent_tweets for backward compatibility (even though we're showing all tweets)
    sent_tweets = BrandTweet.objects.filter(brand=brand, status="posted").order_by(
        "-posted_at"
    )

    # Get active tweet strategies for the UI
    tweet_strategies = TweetStrategy.objects.filter(is_active=True).order_by(
        "category", "name"
    )

    # Check if current user is admin for editing permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    is_admin = org_user and org_user.is_admin

    # Calculate counts for status display
    approved_count = tweets.filter(status="approved").count()

    # Find next scheduled tweet
    next_scheduled_tweet = (
        tweets.filter(status__in=["draft", "approved"], scheduled_for__gt=now)
        .order_by("scheduled_for")
        .first()
    )

    # Get subscription info
    subscription_plan = "Free"  # Default
    upgrade_url = "/upgrade/"  # Default upgrade URL

    # Check if brand has subscription info
    if (
        hasattr(brand, "stripe_subscription_status")
        and brand.stripe_subscription_status
    ):
        if brand.stripe_subscription_status in ["active", "trialing"]:
            subscription_plan = brand.stripe_subscription_status.title()
        elif brand.stripe_subscription_status == "canceled":
            subscription_plan = "Canceled"

    context = {
        "organization": organization,
        "brand": brand,
        "tweets": tweets,
        "sent_tweets": sent_tweets,
        "tweet_strategies": tweet_strategies,
        "is_admin": is_admin,
        "is_superuser": request.user.is_superuser,
        "current_time": now,
        "date_range": "All tweets",
        "approved_count": approved_count,
        "next_scheduled_tweet": next_scheduled_tweet,
        "subscription_plan": subscription_plan,
        "upgrade_url": upgrade_url,
    }

    return render(request, "organizations/brand_tweet_queue.html", context)


@login_required
@require_POST
def brand_tweet_create(request, organization_pk, brand_pk):
    """Create a new brand tweet"""
    from .models import BrandTweet
    from django.utils import timezone

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        # Parse scheduled time
        scheduled_str = request.POST.get("scheduled_for")
        if scheduled_str:
            scheduled_for = timezone.datetime.fromisoformat(scheduled_str)
        else:
            scheduled_for = timezone.now() + timezone.timedelta(hours=1)

        tweet = BrandTweet.objects.create(
            brand=brand,
            content=request.POST.get("content", ""),
            scheduled_for=scheduled_for,
            status="draft",
        )

        # Process Twitter mentions in the tweet content
        from .utils import process_tweet_mentions

        process_tweet_mentions(
            tweet=tweet, organization=brand.organization, user=request.user
        )

        # Generate tracking link and add to content
        tracking_url = tweet.get_tracking_url()
        if tracking_url and not tweet.content.endswith(tracking_url):
            tweet.content = f"{tweet.content}\n\n{tracking_url}"
            tweet.tracking_link = tracking_url
            tweet.save()

        return JsonResponse(
            {
                "success": True,
                "tweet_id": tweet.id,
                "message": "Tweet created successfully",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def brand_tweet_update(request, organization_pk, brand_pk, tweet_id):
    """Update a brand tweet content inline"""
    from .models import BrandTweet
    import json

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    tweet = get_object_or_404(BrandTweet, pk=tweet_id, brand=brand)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        data = json.loads(request.body)

        if "content" in data:
            tweet.content = data["content"]
        if "status" in data:
            tweet.status = data["status"]
        if "scheduled_for" in data:
            tweet.scheduled_for = data["scheduled_for"]

        tweet.save()

        return JsonResponse({"success": True, "message": "Tweet updated successfully"})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def brand_tweet_generate_ai_text(request, organization_pk, brand_pk, tweet_id):
    """Generate AI text for a tweet"""
    logger.info(f"Starting AI tweet generation for tweet_id: {tweet_id}")

    try:
        # Import get_openai_client with detailed error handling
        try:
            from website.utils import get_openai_client

            logger.info("Successfully imported get_openai_client")
        except ImportError as e:
            logger.error(f"Failed to import get_openai_client: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Import error: {str(e)}. Please contact support.",
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error importing get_openai_client: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Import error: {str(e)}. Please contact support.",
                }
            )

        brand = get_object_or_404(Brand, pk=brand_pk, organization_id=organization_pk)
        tweet = get_object_or_404(BrandTweet, pk=tweet_id, brand=brand)

        data = json.loads(request.body)
        prompt = data.get("prompt", f"Write a engaging tweet for {brand.name}")

        logger.info(f"Attempting to get OpenAI client for brand: {brand.name}")

        # Configure OpenAI with detailed logging
        try:
            client = get_openai_client()
            if not client:
                logger.error("OpenAI client returned None - API key not configured")
                return JsonResponse(
                    {
                        "success": False,
                        "error": "OpenAI API key is not configured. Please contact the administrator to set up the API key in the variables table.",
                    }
                )
            logger.info("OpenAI client created successfully")
        except Exception as e:
            logger.error(f"Error creating OpenAI client: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        f"Failed to create OpenAI client: {str(e)}. "
                        "Please contact support."
                    ),
                }
            )

        # Generate tweet content
        try:
            logger.info(f"Generating tweet content with prompt: {prompt[:100]}...")
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional social media manager for {brand.name}. Write engaging, concise tweets that fit the brand voice. Keep tweets under 280 characters.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.7,
            )

            generated_content = response.choices[0].message.content.strip()
            logger.info(f"Successfully generated content: {generated_content[:50]}...")

            # Update tweet
            tweet.content = generated_content
            tweet.ai_prompt = prompt
            tweet.save()

            logger.info(f"Tweet {tweet_id} updated successfully")

            return JsonResponse(
                {
                    "success": True,
                    "content": generated_content,
                    "message": "AI text generated successfully",
                }
            )

        except Exception as openai_error:
            logger.error(f"OpenAI API error: {str(openai_error)}")
            if (
                "authentication" in str(openai_error).lower()
                or "api_key" in str(openai_error).lower()
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Invalid OpenAI API key. Please check the API key configuration.",
                    }
                )
            elif "rate_limit" in str(openai_error).lower():
                return JsonResponse(
                    {
                        "success": False,
                        "error": "OpenAI rate limit exceeded. Please try again later.",
                    }
                )
            elif (
                "quota" in str(openai_error).lower()
                or "billing" in str(openai_error).lower()
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "OpenAI quota exceeded. Please check your OpenAI billing and usage.",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"AI service error: {str(openai_error)}",
                    }
                )

    except Exception as e:
        logger.error(f"Unexpected error in AI text generation: {str(e)}")
        return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"})


@login_required
@require_POST
def brand_tweet_generate_ai_from_website(request, organization_pk, brand_pk):
    """Generate AI tweet content based on brand website content for inline form"""
    import requests
    from bs4 import BeautifulSoup
    import logging

    logger = logging.getLogger(__name__)

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        # Fetch content from brand website
        website_content = ""
        if brand.url:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(brand.url, headers=headers, timeout=10)
                response.raise_for_status()

                # Parse HTML content
                soup = BeautifulSoup(response.content, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Extract text content
                text = soup.get_text()

                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (
                    phrase.strip() for line in lines for phrase in line.split("  ")
                )
                website_content = " ".join(chunk for chunk in chunks if chunk)

                # Limit content length for API efficiency
                website_content = (
                    website_content[:2000]
                    if len(website_content) > 2000
                    else website_content
                )

            except Exception as web_error:
                logger.warning(
                    f"Failed to scrape website {brand.url}: {str(web_error)}"
                )
                # If website scraping fails, use brand description as fallback
                website_content = (
                    brand.description
                    if brand.description
                    else f"Content about {brand.name}"
                )
        else:
            website_content = (
                brand.description
                if brand.description
                else f"Content about {brand.name}"
            )

        # Configure OpenAI
        try:
            from website.utils import get_openai_client
        except ImportError as e:
            logger.error(f"Failed to import get_openai_client: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Import error: {str(e)}. Please contact support.",
                }
            )

        client = get_openai_client()
        if not client:
            logger.error("OpenAI API key is not configured")
            return JsonResponse(
                {
                    "success": False,
                    "error": "OpenAI API key is not configured. Please contact the administrator to set up the API key in the variables table.",
                }
            )

        # Create prompt based on website content
        prompt = f"""Based on the following website content for {brand.name}, write an engaging and fresh tweet that:
- Highlights something interesting or valuable from their content
- Is under 280 characters
- Uses an engaging tone that fits social media
- Includes relevant hashtags (2-3 max)
- Feels authentic and not overly promotional

Website content:
{website_content}

Create a tweet that would make people want to learn more about {brand.name}."""

        # Generate tweet content
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional social media manager for {brand.name}. Write engaging, concise tweets that fit the brand voice and highlight valuable content. Keep tweets under 280 characters and make them feel fresh and authentic.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.8,
            )

            generated_content = response.choices[0].message.content.strip()

            # Remove quotes if the AI wrapped the content in quotes
            if generated_content.startswith('"') and generated_content.endswith('"'):
                generated_content = generated_content[1:-1]

            return JsonResponse(
                {
                    "success": True,
                    "content": generated_content,
                    "message": "AI tweet generated from website content!",
                }
            )

        except Exception as openai_error:
            logger.error(f"OpenAI API error: {str(openai_error)}")
            if (
                "authentication" in str(openai_error).lower()
                or "api_key" in str(openai_error).lower()
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Invalid OpenAI API key. Please check the API key configuration.",
                    }
                )
            elif "rate_limit" in str(openai_error).lower():
                return JsonResponse(
                    {
                        "success": False,
                        "error": "OpenAI rate limit exceeded. Please try again later.",
                    }
                )
            elif (
                "quota" in str(openai_error).lower()
                or "billing" in str(openai_error).lower()
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "OpenAI quota exceeded. Please check your OpenAI billing and usage.",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"AI service error: {str(openai_error)}",
                    }
                )

    except Exception as e:
        logger.error(f"Unexpected error in AI tweet generation: {str(e)}")
        return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"})


@login_required
@require_POST
def brand_instagram_generate_ai_from_website(request, organization_pk, brand_pk):
    """Generate AI Instagram post content based on brand website content"""
    import requests
    from bs4 import BeautifulSoup
    import logging

    logger = logging.getLogger(__name__)

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        # Fetch content from brand website
        website_content = ""
        if brand.url:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(brand.url, headers=headers, timeout=10)
                response.raise_for_status()

                # Parse HTML content
                soup = BeautifulSoup(response.content, "html.parser")

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Extract text content
                text = soup.get_text()

                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (
                    phrase.strip() for line in lines for phrase in line.split("  ")
                )
                website_content = " ".join(chunk for chunk in chunks if chunk)

                # Limit content length for API efficiency
                website_content = (
                    website_content[:3000]
                    if len(website_content) > 3000
                    else website_content
                )

            except Exception as web_error:
                logger.warning(
                    f"Failed to scrape website {brand.url}: {str(web_error)}"
                )
                # If website scraping fails, use brand description as fallback
                website_content = (
                    brand.description
                    if brand.description
                    else f"Content about {brand.name}"
                )
        else:
            website_content = (
                brand.description
                if brand.description
                else f"Content about {brand.name}"
            )

        # Configure OpenAI
        try:
            from website.utils import get_openai_client
        except ImportError as e:
            logger.error(f"Failed to import get_openai_client: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Import error: {str(e)}. Please contact support.",
                }
            )

        client = get_openai_client()
        if not client:
            logger.error("OpenAI API key is not configured")
            return JsonResponse(
                {
                    "success": False,
                    "error": "OpenAI API key is not configured. Please contact the administrator to set up the API key in the variables table.",
                }
            )

        # Create prompt based on website content for Instagram
        prompt = f"""Based on the following website content for {brand.name}, write an engaging Instagram post that:
- Highlights something interesting or valuable from their content
- Is between 100-300 words for the caption 
- Uses an engaging tone that fits Instagram's visual platform
- Includes 5-10 relevant hashtags
- Feels authentic and connects with the audience
- Encourages engagement (likes, comments, shares)
- Is visually descriptive and inspiring

Website content:
{website_content}

Create an Instagram caption that would make people want to engage with {brand.name} and learn more about what they offer. Format it as a complete Instagram post with caption and hashtags."""

        # Generate Instagram content
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional social media manager for {brand.name}. Write engaging Instagram captions that showcase the brand's value, connect with the audience, and encourage engagement. Use a conversational tone and include strategic hashtags.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.8,
            )

            generated_content = response.choices[0].message.content.strip()

            # Remove quotes if the AI wrapped the content in quotes
            if generated_content.startswith('"') and generated_content.endswith('"'):
                generated_content = generated_content[1:-1]

            return JsonResponse(
                {
                    "success": True,
                    "content": generated_content,
                    "message": "AI Instagram post generated from website content!",
                }
            )

        except Exception as openai_error:
            logger.error(f"OpenAI API error: {str(openai_error)}")
            if (
                "authentication" in str(openai_error).lower()
                or "api_key" in str(openai_error).lower()
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Invalid OpenAI API key. Please check the API key configuration.",
                    }
                )
            elif "rate_limit" in str(openai_error).lower():
                return JsonResponse(
                    {
                        "success": False,
                        "error": "OpenAI rate limit exceeded. Please try again later.",
                    }
                )
            elif (
                "quota" in str(openai_error).lower()
                or "billing" in str(openai_error).lower()
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "error": "OpenAI quota exceeded. Please check your OpenAI billing and usage.",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"AI service error: {str(openai_error)}",
                    }
                )

    except Exception as e:
        logger.error(f"Unexpected error in AI Instagram generation: {str(e)}")
        return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"})


@login_required
@require_POST
def brand_tweet_generate_image(request, organization_pk, brand_pk, tweet_id):
    """Generate image for a brand tweet using AI"""
    from .models import BrandTweet
    import json
    import requests
    import os
    import uuid
    import logging
    import traceback
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    logger = logging.getLogger(__name__)
    logger.info(
        f"brand_tweet_generate_image called with org_pk={organization_pk}, brand_pk={brand_pk}, tweet_id={tweet_id}, user={request.user.id}"
    )

    try:
        organization = get_object_or_404(Organization, pk=organization_pk)
        brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
        tweet = get_object_or_404(BrandTweet, pk=tweet_id, brand=brand)
    except Exception as e:
        logger.error(
            f"Failed to get objects - Org: {organization_pk}, Brand: {brand_pk}, Tweet: {tweet_id}. Error: {str(e)}"
        )
        return JsonResponse(
            {"success": False, "error": "Tweet, brand, or organization not found"}
        )

    # User is already authenticated via @login_required decorator
    logger.info(
        f"Image generation authorized for user {request.user.id} (username: {request.user.username})"
    )

    try:
        # Log request details for debugging
        logger.info(
            f"Image generation request received - User: {request.user.id}, Tweet: {tweet_id}, Content-Type: {request.content_type}, Body length: {len(request.body) if request.body else 0}"
        )

        # Get the prompt from request body or use tweet content
        try:
            data = json.loads(request.body) if request.body else {}
            logger.info(f"Parsed request data: {data}")
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse request body as JSON: {request.body}. Error: {str(e)}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid request format - request body is not valid JSON",
                }
            )

        prompt = data.get("prompt", "").strip()

        # If no prompt provided, create one from tweet content and brand name
        if not prompt:
            if tweet.content:
                prompt = f"Create a professional marketing image for a social media post about: {tweet.content[:100]}. Brand: {brand.name}. Modern, clean design."
            else:
                prompt = f"Create a professional marketing image for {brand.name}. Modern, clean, business-focused design."

        # Validate prompt is not empty
        if not prompt or len(prompt.strip()) == 0:
            return JsonResponse(
                {"success": False, "error": "No prompt provided for image generation"}
            )

        # Get service preference (default to Runware)
        service = data.get("service", "runware")

        # Get quality preference (default to standard)
        quality = data.get("quality", "low")
        openai_quality = "hd" if quality == "high" else "standard"

        # Log the request details for debugging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Image generation request - Service: {service}, Prompt: {prompt[:50]}..., Tweet ID: {tweet_id}, Request data: {data}"
        )

        if service == "openai":
            # Use OpenAI image generation
            try:
                from website.utils import get_openai_client
            except ImportError as e:
                logger.error(f"Failed to import get_openai_client: {e}")
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Import error: {str(e)}. Please contact support.",
                    }
                )

            client = get_openai_client()
            if not client:
                logger.error("OpenAI API key is not configured")
                return JsonResponse(
                    {
                        "success": False,
                        "error": "OpenAI API key is not configured. Please contact the administrator to set up the API key in the variables table.",
                    }
                )

            # Generate image using OpenAI
            try:
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    n=1,
                    size="1024x1024",
                    quality=openai_quality,
                    response_format="url",
                )
            except Exception as openai_error:
                logger.error(f"OpenAI image generation error: {str(openai_error)}")
                if (
                    "authentication" in str(openai_error).lower()
                    or "api_key" in str(openai_error).lower()
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Invalid OpenAI API key. Please check the API key configuration.",
                        }
                    )
                elif "rate_limit" in str(openai_error).lower():
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "OpenAI rate limit exceeded. Please try again later.",
                        }
                    )
                elif (
                    "quota" in str(openai_error).lower()
                    or "billing" in str(openai_error).lower()
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "OpenAI quota exceeded. Please check your OpenAI billing and usage.",
                        }
                    )
                else:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": f"AI image generation error: {str(openai_error)}",
                        }
                    )

            if response.data and response.data[0].url:
                image_url = response.data[0].url

                # Download the image and save it to our media storage
                image_response = requests.get(image_url, timeout=30)
                if image_response.status_code == 200:
                    # Create filename
                    filename = f"brand_tweet_{tweet.id}_{uuid.uuid4().hex}.png"

                    # Save image to media storage
                    content = ContentFile(image_response.content)
                    saved_path = default_storage.save(
                        f"brand_tweets/{filename}", content
                    )

                    # Update tweet with image
                    tweet.image = saved_path
                    tweet.save()

                    return JsonResponse(
                        {
                            "success": True,
                            "message": "Image generated successfully!",
                            "image_url": default_storage.url(saved_path),
                            "prompt": prompt,
                            "service": "OpenAI DALL-E 3",
                        }
                    )
                else:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Failed to download generated image",
                        }
                    )
            else:
                return JsonResponse(
                    {"success": False, "error": "No image generated by OpenAI"}
                )

        elif service == "runware":
            # Use Runware image generation
            api_key = os.getenv("RUNWARE_API_KEY")
            if not api_key:
                logger.error("RUNWARE_API_KEY environment variable not configured")
                return JsonResponse(
                    {"success": False, "error": "Runware API key not configured in env"}
                )

            # Check credit balance before making API call
            from website.models import RunwarePricingData
            from decimal import Decimal

            # Get pricing for Runware image generation
            try:
                pricing = RunwarePricingData.objects.filter(
                    service_name__icontains="Image Generation", is_active=True
                ).first()

                if pricing and pricing.gemnar_price:
                    credit_cost = pricing.gemnar_price
                else:
                    # Fallback default cost if no pricing data
                    credit_cost = Decimal("0.02")  # $0.02 per image

                logger.info(f"Runware image generation cost: {credit_cost} credits")

                # Check if brand has sufficient credits
                if not brand.has_sufficient_credits(credit_cost):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": f"Insufficient credits. Need {credit_cost} credits, but balance is {brand.credits_balance}. Please add credits to continue.",
                            "credits_needed": str(credit_cost),
                            "current_balance": str(brand.credits_balance),
                        }
                    )

            except Exception as e:
                logger.error(f"Error checking credits: {str(e)}")
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Error checking credit balance. Please try again.",
                    }
                )

            logger.info(f"Using Runware API with key: {api_key[:10]}...")

            # Prepare Runware payload
            task_uuid = str(uuid.uuid4())
            payload = [
                {
                    "taskType": "imageInference",
                    "taskUUID": task_uuid,
                    "model": "runware:101@1",
                    "positivePrompt": prompt,
                    "width": 1024,
                    "height": 1024,
                    "steps": 30,
                }
            ]

            # Make request to Runware API
            logger.info(
                f"Making Runware API request with payload: {json.dumps(payload)}"
            )
            response = requests.post(
                "https://api.runware.ai/v1",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120,
            )
            logger.info(f"Runware API response status: {response.status_code}")

            if response.status_code != 200:
                error_message = "AI image generation failed"
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", error_message)
                except (json.JSONDecodeError, ValueError):
                    error_message = f"API error: {response.status_code}"

                return JsonResponse({"success": False, "error": error_message})

            try:
                response_data = response.json()
                logger.info(f"Runware API response type: {type(response_data)}")
                logger.info(
                    f"Runware API response structure: {json.dumps(response_data, indent=2)[:1000]}..."
                )
            except json.JSONDecodeError:
                logger.error(
                    f"Failed to parse Runware API response as JSON: {response.text[:500]}"
                )
                return JsonResponse(
                    {"success": False, "error": "Invalid response from AI service"}
                )

            # Handle different response formats from Runware API
            image_url = None

            # Case 1: Response is a list with results
            if isinstance(response_data, list) and len(response_data) > 0:
                result = response_data[0]
                if isinstance(result, dict):
                    if (
                        result.get("taskType") == "imageInference"
                        and "imageURL" in result
                    ):
                        image_url = result["imageURL"]
                        result.get("taskUUID")
                    elif "imageURL" in result:
                        # Sometimes the response might not have taskType but still has imageURL
                        image_url = result["imageURL"]
                        result.get("taskUUID")

            # Case 2: Response is a dict with nested data
            elif isinstance(response_data, dict):
                # Check if there's a data field with results
                if (
                    "data" in response_data
                    and isinstance(response_data["data"], list)
                    and len(response_data["data"]) > 0
                ):
                    result = response_data["data"][0]
                    if isinstance(result, dict) and "imageURL" in result:
                        image_url = result["imageURL"]
                        result.get("taskUUID")
                # Check if the dict itself contains the image URL
                elif "imageURL" in response_data:
                    image_url = response_data["imageURL"]
                    response_data.get("taskUUID")

            if image_url:
                # Download the image and save it
                logger.info(f"Downloading image from: {image_url}")
                try:
                    image_response = requests.get(image_url, timeout=30)
                    if image_response.status_code == 200:
                        # Create filename
                        filename = f"brand_tweet_{tweet.id}_{uuid.uuid4().hex}.png"

                        # Save image to media storage
                        content = ContentFile(image_response.content)
                        saved_path = default_storage.save(
                            f"brand_tweets/{filename}", content
                        )

                        # Update tweet with image
                        tweet.image = saved_path
                        tweet.save()

                        # Deduct credits for successful image generation
                        try:
                            success, message = brand.deduct_credits(
                                credit_cost,
                                f"Runware image generation for tweet {tweet.id}",
                                "usage",
                            )
                            if success:
                                logger.info(
                                    f"Credits deducted: {credit_cost}. New balance: {brand.credits_balance}"
                                )
                            else:
                                logger.error(f"Failed to deduct credits: {message}")
                        except Exception as e:
                            logger.error(f"Error deducting credits: {str(e)}")

                        return JsonResponse(
                            {
                                "success": True,
                                "message": "Image generated successfully!",
                                "image_url": default_storage.url(saved_path),
                                "prompt": prompt,
                                "service": "Runware AI",
                                "credits_used": str(credit_cost),
                                "credits_remaining": str(brand.credits_balance),
                            }
                        )
                    else:
                        logger.error(
                            f"Failed to download image: HTTP {image_response.status_code}"
                        )
                        return JsonResponse(
                            {
                                "success": False,
                                "error": f"Failed to download generated image (HTTP {image_response.status_code})",
                            }
                        )
                except requests.exceptions.Timeout:
                    logger.error("Timeout downloading image")
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Timeout downloading generated image",
                        }
                    )
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error downloading image: {e}")
                    return JsonResponse(
                        {
                            "success": False,
                            "error": f"Failed to download image: {str(e)}",
                        }
                    )
            else:
                # Log the full response for debugging
                logger.error(
                    f"No image URL found in response. Full response: {json.dumps(response_data, indent=2)}"
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": "No image URL found in AI service response",
                        "debug_response": (
                            response_data
                            if len(str(response_data)) < 1000
                            else "Response too large to include"
                        ),
                    }
                )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid service. Choose 'openai' or 'runware'",
                }
            )

    except Exception as e:
        # Get a logger for better error tracking
        logger = logging.getLogger(__name__)

        # Log the full traceback for debugging
        logger.error(f"Error in brand_tweet_generate_image: {traceback.format_exc()}")
        logger.error(f"Exception type: {type(e).__name__}, Message: {str(e)}")
        logger.error(
            f"Request details - User: {request.user.id}, Tweet: {tweet_id}, Method: {request.method}"
        )

        # Provide more specific error messages based on the exception type
        if isinstance(e, requests.exceptions.Timeout):
            error_message = "Image generation timed out. Please try again."
        elif isinstance(e, requests.exceptions.ConnectionError):
            error_message = "Failed to connect to image generation service. Please check your internet connection."
        elif isinstance(e, json.JSONDecodeError):
            error_message = "Invalid response from image generation service."
        elif isinstance(e, ValueError):
            error_message = f"Invalid data provided: {str(e)}"
        elif "Http404" in str(type(e)):
            error_message = "Tweet, brand, or organization not found."
        else:
            error_message = f"Image generation failed: {str(e)}"

        logger.error(f"Returning error response: {error_message}")
        return JsonResponse({"success": False, "error": error_message})


@login_required
@require_POST
def brand_tweet_post_now(request, organization_pk, brand_pk, tweet_id):
    """Post a brand tweet immediately"""
    from .models import BrandTweet

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    tweet = get_object_or_404(BrandTweet, pk=tweet_id, brand=brand)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        success, error = tweet.post_to_twitter()

        if success:
            # Send WebSocket message for successful tweet posting
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            room_group_name = f"tweet_queue_{organization_pk}_{brand_pk}"

            # Send real-time update to all connected clients
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    "type": "tweet_posted",
                    "tweet_id": tweet.id,
                    "posted_at": (
                        tweet.posted_at.isoformat() if tweet.posted_at else None
                    ),
                    "tweet_url": f"https://twitter.com/{brand.twitter_username}/status/{tweet.tweet_id}",
                },
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Tweet posted successfully!",
                    "tweet_url": f"https://twitter.com/{brand.twitter_username}/status/{tweet.tweet_id}",
                }
            )
        else:
            # Send WebSocket message for failed tweet posting
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            room_group_name = f"tweet_queue_{organization_pk}_{brand_pk}"

            # Send real-time update to all connected clients
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    "type": "tweet_failed",
                    "tweet_id": tweet.id,
                    "error_message": error,
                },
            )

            return JsonResponse({"success": False, "error": error})

    except Exception as e:
        # Send WebSocket message for unexpected errors
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        room_group_name = f"tweet_queue_{organization_pk}_{brand_pk}"

        # Send real-time update to all connected clients
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "tweet_failed",
                "tweet_id": tweet.id,
                "error_message": str(e),
            },
        )

        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_http_methods(["POST", "DELETE"])
def brand_tweet_delete(request, organization_pk, brand_pk, tweet_id):
    """Delete a brand tweet"""
    from .models import BrandTweet

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    tweet = get_object_or_404(BrandTweet, pk=tweet_id, brand=brand)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        tweet.delete()
        return JsonResponse(
            {
                "success": True,
                "message": "Tweet deleted successfully",
                "tweet_id": tweet_id,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_http_methods(["DELETE", "POST"])
def brand_instagram_post_delete(request, organization_pk, brand_pk, post_id):
    """Delete a brand Instagram post"""
    from .models import BrandInstagramPost

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    post = get_object_or_404(BrandInstagramPost, pk=post_id, brand=brand)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        post.delete()
        return JsonResponse(
            {"success": True, "message": "Instagram post deleted successfully"}
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def brand_tweet_delete_from_twitter(request, organization_pk, brand_pk, tweet_id):
    """Delete a tweet from Twitter (if posted) and update status in database"""
    from .models import BrandTweet
    import logging

    logger = logging.getLogger(__name__)

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    tweet = get_object_or_404(BrandTweet, pk=tweet_id, brand=brand)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        # Check if tweet was posted to Twitter
        if not tweet.twitter_id:
            return JsonResponse(
                {"success": False, "error": "Tweet was not posted to Twitter"}
            )

        # Try to delete from Twitter using the brand's Twitter API
        try:
            result = brand.delete_tweet_from_twitter(tweet.twitter_id)
            if result.get("success"):
                # Update tweet status to indicate it was deleted from Twitter
                tweet.is_posted = False
                tweet.twitter_id = None
                tweet.posted_at = None
                tweet.save()

                logger.info(f"Successfully deleted tweet {tweet.id} from Twitter")
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Tweet deleted from Twitter successfully",
                    }
                )
            else:
                logger.error(
                    f"Failed to delete tweet {tweet.id} from Twitter: {result.get('error')}"
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": f"Failed to delete from Twitter: {result.get('error')}",
                    }
                )
        except Exception as api_error:
            logger.error(
                f"Twitter API error deleting tweet {tweet.id}: {str(api_error)}"
            )
            return JsonResponse(
                {"success": False, "error": f"Twitter API error: {str(api_error)}"}
            )

    except Exception as e:
        logger.error(
            f"Unexpected error deleting tweet {tweet.id} from Twitter: {str(e)}"
        )
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def brand_tweet_update_schedule(request, organization_pk, brand_pk, tweet_id):
    """Update tweet schedule"""
    from .models import BrandTweet
    import json
    from django.utils import timezone
    from datetime import datetime

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    tweet = get_object_or_404(BrandTweet, pk=tweet_id, brand=brand)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        data = json.loads(request.body) if request.body else {}
        scheduled_for_str = data.get("scheduled_for")

        if not scheduled_for_str:
            return JsonResponse(
                {"success": False, "error": "scheduled_for is required"}
            )

        # Parse the datetime string
        try:
            # Convert from browser local time to UTC
            scheduled_for = datetime.fromisoformat(scheduled_for_str)
            # Make timezone aware if it isn't already
            if scheduled_for.tzinfo is None:
                scheduled_for = timezone.make_aware(scheduled_for)
        except ValueError as e:
            return JsonResponse(
                {"success": False, "error": f"Invalid datetime format: {str(e)}"}
            )

        # Update tweet
        tweet.scheduled_for = scheduled_for
        tweet.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Tweet schedule updated successfully",
                "scheduled_for": scheduled_for.isoformat(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def brand_tweet_refresh_metrics(request, organization_pk, brand_pk, tweet_id):
    """Refresh Twitter metrics for a specific tweet"""
    from .models import BrandTweet

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    tweet = get_object_or_404(BrandTweet, pk=tweet_id, brand=brand)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    # Early exit if tweet is not posted or doesn't have a tweet_id
    if tweet.status != "posted" or not tweet.tweet_id:
        return JsonResponse(
            {
                "success": False,
                "error": "Cannot refresh metrics for tweets that are not posted",
            }
        )

    # Early exit if brand doesn't have Twitter configuration
    if not brand.has_twitter_config:
        return JsonResponse(
            {"success": False, "error": "Brand does not have Twitter configuration"}
        )

    try:
        # Refresh metrics using the model method
        success, message = tweet.refresh_metrics()

        if success:
            # Return updated metrics
            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "metrics": {
                        "like_count": tweet.like_count,
                        "retweet_count": tweet.retweet_count,
                        "reply_count": tweet.reply_count,
                        "quote_count": tweet.quote_count,
                        "bookmark_count": tweet.bookmark_count,
                        "metrics_last_updated": (
                            tweet.metrics_last_updated.isoformat()
                            if tweet.metrics_last_updated
                            else None
                        ),
                    },
                }
            )
        else:
            return JsonResponse({"success": False, "error": message})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def brand_instagram_post_refresh_metrics(request, organization_pk, brand_pk, post_id):
    """Refresh Instagram metrics for a specific post"""
    from .models import BrandInstagramPost

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    instagram_post = get_object_or_404(BrandInstagramPost, pk=post_id, brand=brand)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        # Refresh metrics using the model method
        success, message = instagram_post.refresh_metrics()

        if success:
            # Return updated metrics
            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "metrics": {
                        "like_count": instagram_post.like_count,
                        "comment_count": instagram_post.comment_count,
                        "share_count": instagram_post.share_count,
                        "reach": instagram_post.reach,
                        "impressions": instagram_post.impressions,
                        "saved_count": instagram_post.saved_count,
                        "video_views": instagram_post.video_views,
                        "metrics_last_updated": (
                            instagram_post.metrics_last_updated.isoformat()
                            if instagram_post.metrics_last_updated
                            else None
                        ),
                    },
                }
            )
        else:
            return JsonResponse({"success": False, "error": message})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def brand_tweet_schedule_next_slot(request, organization_pk, brand_pk, tweet_id):
    """Schedule tweet for the next available time slot based on plan limits"""
    from .models import BrandTweet

    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
    tweet = get_object_or_404(BrandTweet, pk=tweet_id, brand=brand)

    # Check permissions
    org_user = organization.organization_users.filter(user=request.user).first()
    if not org_user or not org_user.is_admin:
        return JsonResponse({"success": False, "error": "Permission denied"})

    try:
        # Check if brand has an active subscription
        daily_limit = brand.get_daily_tweet_limit()
        if daily_limit == 0:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No active subscription plan found. Please upgrade to schedule tweets.",
                }
            )

        # Get the next available time slot
        next_slot = brand.get_next_available_time_slot()
        if not next_slot:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"No available time slots found within the next 30 days based on your plan limit of {daily_limit} tweet(s) per day.",
                }
            )

        # Update the tweet schedule
        tweet.scheduled_for = next_slot
        tweet.save()

        # Format the time for display
        from django.utils import timezone

        local_time = timezone.localtime(next_slot)
        formatted_time = local_time.strftime("%B %d, %Y at %I:%M %p")

        return JsonResponse(
            {
                "success": True,
                "message": f"Tweet scheduled for {formatted_time}",
                "scheduled_for": next_slot.isoformat(),
                "formatted_time": formatted_time,
            }
        )

    except Exception as e:
        logger.error(f"Error scheduling tweet {tweet_id} for next slot: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def brand_export(request, organization_pk, brand_pk):
    """Export brand data including all tokens and configuration"""
    organization = get_object_or_404(Organization, pk=organization_pk)
    brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)

    # Check if user has access to this organization
    if not organization.is_member(request.user):
        return JsonResponse({"success": False, "error": "Access denied"}, status=403)

    try:
        # Prepare brand data for export
        brand_data = {
            "export_version": "1.0",
            "export_date": timezone.now().isoformat(),
            "brand": {
                "name": brand.name,
                "url": brand.url,
                "description": brand.description,
                "logo_url": brand.logo.url if brand.logo else None,
                # Twitter configuration
                "twitter_api_key": brand.twitter_api_key,
                "twitter_api_secret": brand.twitter_api_secret,
                "twitter_access_token": brand.twitter_access_token,
                "twitter_access_token_secret": brand.twitter_access_token_secret,
                "twitter_bearer_token": brand.twitter_bearer_token,
                "twitter_username": brand.twitter_username,
                # Instagram configuration
                "instagram_access_token": brand.instagram_access_token,
                "instagram_user_id": brand.instagram_user_id,
                "instagram_username": brand.instagram_username,
                "instagram_app_id": brand.instagram_app_id,
                "instagram_app_secret": brand.instagram_app_secret,
                # Slack configuration
                "slack_webhook_url": brand.slack_webhook_url,
                "slack_channel": brand.slack_channel,
                "slack_notifications_enabled": brand.slack_notifications_enabled,
            },
        }

        # Create JSON response with appropriate headers for download
        from django.http import HttpResponse
        import json

        response = HttpResponse(
            json.dumps(brand_data, indent=2), content_type="application/json"
        )
        response[
            "Content-Disposition"
        ] = f'attachment; filename="brand_{brand.slug}_gemnar_data.json"'
        return response

    except Exception as e:
        logger.error(f"Error exporting brand {brand_pk}: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_POST
def brand_import(request, organization_pk):
    """Import brand data from JSON file"""
    organization = get_object_or_404(Organization, pk=organization_pk)

    # Check if user has access to this organization
    if not organization.is_member(request.user):
        return JsonResponse({"success": False, "error": "Access denied"}, status=403)

    try:
        if "brand_data" not in request.FILES:
            return JsonResponse({"success": False, "error": "No file uploaded"})

        uploaded_file = request.FILES["brand_data"]

        # Validate file type
        if not uploaded_file.name.endswith(".json"):
            return JsonResponse(
                {"success": False, "error": "Please upload a JSON file"}
            )

        # Parse JSON data
        try:
            brand_data = json.loads(uploaded_file.read().decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON file"})

        # Validate data structure
        if "brand" not in brand_data:
            return JsonResponse(
                {"success": False, "error": "Invalid brand data format"}
            )

        brand_info = brand_data["brand"]

        # Check required fields
        if not brand_info.get("name"):
            return JsonResponse({"success": False, "error": "Brand name is required"})

        if not brand_info.get("url"):
            return JsonResponse({"success": False, "error": "Brand URL is required"})

        # Create new brand with imported data
        with transaction.atomic():
            # Generate unique slug
            from django.utils.text import slugify

            base_slug = slugify(brand_info["name"])
            slug = base_slug
            counter = 1
            while Brand.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Create the brand
            brand = Brand.objects.create(
                name=brand_info["name"],
                slug=slug,
                url=brand_info["url"],
                description=brand_info.get("description", ""),
                owner=request.user,
                organization=organization,
                # Twitter configuration
                twitter_api_key=brand_info.get("twitter_api_key"),
                twitter_api_secret=brand_info.get("twitter_api_secret"),
                twitter_access_token=brand_info.get("twitter_access_token"),
                twitter_access_token_secret=brand_info.get(
                    "twitter_access_token_secret"
                ),
                twitter_bearer_token=brand_info.get("twitter_bearer_token"),
                twitter_username=brand_info.get("twitter_username"),
                # Instagram configuration
                instagram_access_token=brand_info.get("instagram_access_token"),
                instagram_user_id=brand_info.get("instagram_user_id"),
                instagram_username=brand_info.get("instagram_username"),
                instagram_app_id=brand_info.get("instagram_app_id"),
                instagram_app_secret=brand_info.get("instagram_app_secret"),
                # Slack configuration
                slack_webhook_url=brand_info.get("slack_webhook_url"),
                slack_channel=brand_info.get("slack_channel"),
                slack_notifications_enabled=brand_info.get(
                    "slack_notifications_enabled", False
                ),
            )

            logger.info(f"Successfully imported brand: {brand.name} (ID: {brand.id})")

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Brand '{brand.name}' imported successfully with all integrations",
                    "brand_id": brand.id,
                }
            )

    except Exception as e:
        logger.error(f"Error importing brand: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)})
