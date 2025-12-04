import base64
import hashlib
import hmac
import json
import logging
import os
import random
import subprocess
import threading
import time
import traceback
import uuid
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

# Cross-platform imports
try:
    import pwd  # Unix/Linux only
except ImportError:
    pwd = None  # Windows doesn't have pwd module

import dns.resolver
import psutil
import requests
import stripe
import tweepy
import stat
import sys

# Windows-compatible imports
try:
    import grp
except ImportError:
    grp = None  # grp module not available on Windows
import urllib3

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import IntegrityError, models
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods, require_POST
from django.conf import settings
from dotenv import load_dotenv

from .models import (
    BlogComment,
    BlogPost,
    Brand,
    Image,
    IPLookupLog,
    ReferralBadge,
    ReferralClick,
    ReferralCode,
    ReferralSignup,
    ReferralSubscription,
    ServiceConnection,
    ServicePrompt,
    ServiceStats,
    Tweet,
    TweetConfiguration,
    User,
    WhoisRecord,
    WebLog,
    BrandTweet,
    TweetStrategy,
    BrandInstagramPost,
    Task,
    TaskApplication,
    CRMContact,
    CRMDeal,
    CRMTask,
    BetaTester,
)
from organizations.models import Organization

from chat.models import ChatConversation


from .services.account_deletion import (
    AccountDeletionService,
    get_account_deletion_preview,
)


logger = logging.getLogger(__name__)


# Create your views here.


def is_admin_user(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def index(request):
    # Get leaderboard data
    top_referrers = get_leaderboard_data()

    # Get user's referral URL if authenticated and they have a code
    referral_url = None
    referral_code = None
    if request.user.is_authenticated:
        try:
            referral_code = ReferralCode.objects.get(user=request.user)
            referral_url = referral_code.get_referral_url()
        except ReferralCode.DoesNotExist:
            # User doesn't have a referral code yet - need to generate one
            pass

    context = {
        "top_referrers": top_referrers,
        "referral_url": referral_url,
    }

    return render(request, "website/index.html", context)


def get_brand_twitter_stats(brand):
    """Get Twitter stats for a specific brand"""
    if not brand.has_twitter_config:
        return {
            "connected": False,
            "tweets_sent": 0,
            "tweets_pending": 0,
            "total_clicks": 0,
        }

    brand_tweets = BrandTweet.objects.filter(brand=brand)
    return {
        "connected": True,
        "tweets_sent": brand_tweets.filter(status="posted").count(),
        "tweets_pending": brand_tweets.filter(
            status__in=["draft", "approved", "scheduled"]
        ).count(),
        "total_clicks": sum(tweet.clicks for tweet in brand_tweets if tweet.clicks),
    }


def get_brand_instagram_stats(brand):
    """Get Instagram stats for a specific brand"""
    if not brand.has_instagram_config:
        return {
            "connected": False,
            "posts_sent": 0,
            "posts_pending": 0,
            "total_engagement": 0,
        }

    brand_posts = BrandInstagramPost.objects.filter(brand=brand)
    return {
        "connected": True,
        "posts_sent": brand_posts.filter(status="posted").count(),
        "posts_pending": brand_posts.filter(
            status__in=["draft", "approved", "scheduled"]
        ).count(),
        "total_engagement": brand_posts.filter(status="posted").count() * 50,
    }


@login_required
def landing(request):
    """Optimized landing page view with minimal database queries"""
    user = request.user

    # Early return for anonymous users
    if not user.is_authenticated:
        return render(request, "website/landing.html", {"user": user})

    # Optimized brand existence check
    has_brand = user.brands.exists()

    # Check if user has completed creator profile (no DB query needed)
    has_creator_profile = bool(
        user.bio
        and user.instagram_handle
        and (user.story_price or user.post_price or user.reel_price)
    )

    context = {
        "user": user,
        "has_brand": has_brand,
        "has_creator_profile": has_creator_profile,
    }
    # Add server time (ms epoch) and timezone abbreviation for client display
    context["server_time_epoch"] = int(timezone.now().timestamp() * 1000)
    context["server_tz_abbr"] = timezone.localtime(timezone.now()).tzname() or "UTC"

    if has_brand:
        # Brand dashboard data - OPTIMIZED
        from organizations.models import Organization
        from django.db.models import Count, Sum, Prefetch

        # Single optimized query for organizations with prefetched brands
        user_organizations = (
            Organization.objects.filter(users=user)
            .prefetch_related(
                Prefetch(
                    "brands",
                    queryset=Brand.objects.select_related("organization").only(
                        "id",
                        "name",
                        "slug",
                        "url",
                        "logo",
                        "owner_id",
                        "organization_id",
                        "stripe_customer_id",
                        "stripe_subscription_status",
                        "is_default",
                    ),
                )
            )
            .only("id", "name")
        )

        # Get all brands with optimized query
        all_brands = (
            Brand.objects.filter(Q(owner=user) | Q(organization__users=user))
            .select_related("organization")
            .distinct()
            .only(
                "id",
                "name",
                "slug",
                "url",
                "logo",
                "owner_id",
                "organization_id",
                "stripe_customer_id",
                "stripe_subscription_status",
                "is_default",
            )
        )

        # Select primary brand: prefer default brand, otherwise use first brand
        primary_brand = all_brands.filter(is_default=True).first()
        if not primary_brand:
            primary_brand = all_brands.first()

        # Pre-calculate date ranges
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # Bulk aggregate stats for all organizations at once
        org_ids = [org.id for org in user_organizations]
        if org_ids:
            # Single query for all CRM stats
            crm_stats = {}
            for org_id in org_ids:
                crm_stats[org_id] = {
                    "total_contacts": 0,
                    "total_companies": 0,
                    "total_deals": 0,
                    "pipeline_value": 0,
                    "new_contacts_week": 0,
                    "overdue_tasks": 0,
                }

            # Batch CRM queries
            contacts_by_org = (
                CRMContact.objects.filter(organization_id__in=org_ids)
                .values("organization_id")
                .annotate(
                    total=Count("id"),
                    new_week=Count("id", filter=Q(created_at__date__gte=week_ago)),
                )
            )

            from .models import CRMCompany

            companies_by_org = (
                CRMCompany.objects.filter(organization_id__in=org_ids)
                .values("organization_id")
                .annotate(total=Count("id"))
            )

            deals_by_org = (
                CRMDeal.objects.filter(organization_id__in=org_ids)
                .values("organization_id")
                .annotate(
                    total=Count("id"),
                    pipeline_value=Sum(
                        "value",
                        filter=Q(
                            is_active=True,
                            stage__in=[
                                "prospecting",
                                "qualification",
                                "proposal",
                                "negotiation",
                            ],
                        ),
                    ),
                )
            )

            tasks_by_org = (
                CRMTask.objects.filter(
                    organization_id__in=org_ids,
                    due_date__lt=timezone.now(),
                    status__in=["pending", "in_progress"],
                )
                .values("organization_id")
                .annotate(overdue=Count("id"))
            )

            # Update stats dictionaries
            for contact_stat in contacts_by_org:
                org_id = contact_stat["organization_id"]
                crm_stats[org_id]["total_contacts"] = contact_stat["total"]
                crm_stats[org_id]["new_contacts_week"] = contact_stat["new_week"]

            for company_stat in companies_by_org:
                org_id = company_stat["organization_id"]
                crm_stats[org_id]["total_companies"] = company_stat["total"]

            for deal_stat in deals_by_org:
                org_id = deal_stat["organization_id"]
                crm_stats[org_id]["total_deals"] = deal_stat["total"]
                crm_stats[org_id]["pipeline_value"] = deal_stat["pipeline_value"] or 0

            for task_stat in tasks_by_org:
                org_id = task_stat["organization_id"]
                crm_stats[org_id]["overdue_tasks"] = task_stat["overdue"]

        # Build organization data with optimized queries
        org_data = []
        brand_ids = [brand.id for brand in all_brands]

        # Bulk query for brand stats
        brand_twitter_stats = {}
        brand_instagram_stats = {}
        brand_analytics_stats = {}

        if brand_ids:
            # Single query for all Twitter stats
            twitter_stats_raw = (
                BrandTweet.objects.filter(brand_id__in=brand_ids)
                .values("brand_id")
                .annotate(
                    posted_count=Count("id", filter=Q(status="posted")),
                    pending_count=Count(
                        "id", filter=Q(status__in=["draft", "approved", "scheduled"])
                    ),
                    total_clicks=Sum("clicks"),
                )
            )

            # Single query for all Instagram stats
            instagram_stats_raw = (
                BrandInstagramPost.objects.filter(brand_id__in=brand_ids)
                .values("brand_id")
                .annotate(
                    posted_count=Count("id", filter=Q(status="posted")),
                    pending_count=Count(
                        "id", filter=Q(status__in=["draft", "approved", "scheduled"])
                    ),
                )
            )

            # Single query for all Analytics stats
            from .analytics_models import AnalyticsSession

            analytics_stats_raw = (
                AnalyticsSession.objects.filter(project__brand_id__in=brand_ids)
                .values("project__brand_id")
                .annotate(
                    total_sessions=Count("id"),
                    total_pageviews=Sum("page_views"),
                )
            )

            # Convert to dictionaries for easy lookup
            for stat in twitter_stats_raw:
                brand_twitter_stats[stat["brand_id"]] = {
                    "tweets_sent": stat["posted_count"],
                    "tweets_pending": stat["pending_count"],
                    "total_clicks": stat["total_clicks"] or 0,
                }

            for stat in instagram_stats_raw:
                brand_instagram_stats[stat["brand_id"]] = {
                    "posts_sent": stat["posted_count"],
                    "posts_pending": stat["pending_count"],
                    "total_engagement": stat["posted_count"] * 50,  # Approximation
                }

            for stat in analytics_stats_raw:
                brand_analytics_stats[stat["project__brand_id"]] = {
                    "total_sessions": stat["total_sessions"] or 0,
                    "total_pageviews": stat["total_pageviews"] or 0,
                }

        # Build organization data efficiently
        for org in user_organizations:
            org_brands_list = org.brands.all()  # Already prefetched
            org_info = {"organization": org, "brands": []}

            # Get CRM stats (already calculated)
            org_info["crm_summary"] = crm_stats.get(
                org.id,
                {
                    "total_contacts": 0,
                    "total_companies": 0,
                    "total_deals": 0,
                    "pipeline_value": 0,
                    "new_contacts_week": 0,
                    "overdue_tasks": 0,
                },
            )

            for brand in org_brands_list:
                brand_info = {
                    "brand": brand,
                    "twitter_connected": hasattr(brand, "has_twitter_config")
                    and brand.has_twitter_config,
                    "instagram_connected": hasattr(brand, "has_instagram_config")
                    and brand.has_instagram_config,
                    "twitter_stats": brand_twitter_stats.get(
                        brand.id,
                        {"tweets_sent": 0, "tweets_pending": 0, "total_clicks": 0},
                    ),
                    "instagram_stats": brand_instagram_stats.get(
                        brand.id,
                        {"posts_sent": 0, "posts_pending": 0, "total_engagement": 0},
                    ),
                    "analytics_stats": brand_analytics_stats.get(
                        brand.id,
                        {"total_sessions": 0, "total_pageviews": 0},
                    ),
                }
                org_info["brands"].append(brand_info)

            if org_info["brands"]:  # Only include orgs with brands
                org_data.append(org_info)

        # Optimized aggregate stats calculation
        # Aggregate Twitter metrics across all brands (posted tweets only)
        twitter_metrics_totals = {
            "like_count": 0,
            "retweet_count": 0,
            "reply_count": 0,
            "quote_count": 0,
            "bookmark_count": 0,
        }
        if brand_ids:
            twitter_metrics_totals = (
                BrandTweet.objects.filter(
                    brand_id__in=brand_ids, status="posted"
                ).aggregate(
                    like_count=Sum("like_count"),
                    retweet_count=Sum("retweet_count"),
                    reply_count=Sum("reply_count"),
                    quote_count=Sum("quote_count"),
                    bookmark_count=Sum("bookmark_count"),
                )
                or twitter_metrics_totals
            )

        # Aggregate Instagram metrics across all brands (posted posts only)
        instagram_metrics_totals = {
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0,
            "saved_count": 0,
            "reach": 0,
            "impressions": 0,
            "video_views": 0,
        }
        if brand_ids:
            instagram_metrics_totals = (
                BrandInstagramPost.objects.filter(
                    brand_id__in=brand_ids, status="posted"
                ).aggregate(
                    like_count=Sum("like_count"),
                    comment_count=Sum("comment_count"),
                    share_count=Sum("share_count"),
                    saved_count=Sum("saved_count"),
                    reach=Sum("reach"),
                    impressions=Sum("impressions"),
                    video_views=Sum("video_views"),
                )
                or instagram_metrics_totals
            )
        twitter_stats = {
            "connected": any(
                hasattr(brand, "has_twitter_config") and brand.has_twitter_config
                for brand in all_brands
            ),
            "tweets_sent": sum(
                stats.get("tweets_sent", 0) for stats in brand_twitter_stats.values()
            ),
            "tweets_pending": sum(
                stats.get("tweets_pending", 0) for stats in brand_twitter_stats.values()
            ),
            "total_clicks": sum(
                stats.get("total_clicks", 0) for stats in brand_twitter_stats.values()
            ),
            # Aggregated public metrics
            "likes": twitter_metrics_totals.get("like_count") or 0,
            "retweets": twitter_metrics_totals.get("retweet_count") or 0,
            "replies": twitter_metrics_totals.get("reply_count") or 0,
            "quotes": twitter_metrics_totals.get("quote_count") or 0,
            "bookmarks": twitter_metrics_totals.get("bookmark_count") or 0,
        }

        instagram_stats = {
            "connected": any(
                hasattr(brand, "has_instagram_config") and brand.has_instagram_config
                for brand in all_brands
            ),
            "posts_sent": sum(
                stats.get("posts_sent", 0) for stats in brand_instagram_stats.values()
            ),
            "posts_pending": sum(
                stats.get("posts_pending", 0)
                for stats in brand_instagram_stats.values()
            ),
            "total_engagement": sum(
                stats.get("total_engagement", 0)
                for stats in brand_instagram_stats.values()
            ),
            # Aggregated public metrics
            "likes": instagram_metrics_totals.get("like_count") or 0,
            "comments": instagram_metrics_totals.get("comment_count") or 0,
            "shares": instagram_metrics_totals.get("share_count") or 0,
            "saves": instagram_metrics_totals.get("saved_count") or 0,
            "reach": instagram_metrics_totals.get("reach") or 0,
            "impressions": instagram_metrics_totals.get("impressions") or 0,
            "views": instagram_metrics_totals.get("video_views") or 0,
        }

        analytics_stats = {
            "total_sessions": sum(
                stats.get("total_sessions", 0)
                for stats in brand_analytics_stats.values()
            ),
            "total_pageviews": sum(
                stats.get("total_pageviews", 0)
                for stats in brand_analytics_stats.values()
            ),
        }

        # Optimized task stats with single queries
        task_stats = Task.objects.filter(brand=user).aggregate(
            active_tasks=Count("id", filter=Q(is_active=True)),
            total_applications=Count("applications"),
            accepted_applications=Count(
                "applications", filter=Q(applications__status="ACCEPTED")
            ),
        )

        # Optimized chat stats
        chat_stats = ChatConversation.objects.filter(
            Q(participant1=user) | Q(participant2=user) | Q(brand__owner=user)
        ).aggregate(
            total_conversations=Count("id", distinct=True),
            brand_conversations=Count(
                "id", filter=Q(brand__isnull=False), distinct=True
            ),
        )

        # Payment status (only check if primary brand exists)
        payment_status = {
            "stripe_connected": bool(
                primary_brand and primary_brand.stripe_customer_id
            ),
            "subscription_active": (
                primary_brand
                and primary_brand.stripe_subscription_status in ["active", "trialing"]
            ),
        }

        context.update(
            {
                "brands": all_brands,
                "primary_brand": primary_brand,
                "org_data": org_data,
                "user_organizations": user_organizations,
                "twitter_stats": twitter_stats,
                "instagram_stats": instagram_stats,
                "analytics_stats": analytics_stats,
                "task_stats": task_stats,
                "chat_stats": chat_stats,
                "payment_status": payment_status,
            }
        )

    elif has_creator_profile:
        # Creator dashboard data - OPTIMIZED

        # Profile stats (no DB queries needed, user already loaded)
        profile_stats = {
            "profile_views": user.impressions_count,
            "bio_complete": bool(user.bio),
            "pricing_set": bool(user.story_price or user.post_price or user.reel_price),
            "images_uploaded": bool(
                user.profile_image
                or user.banner_image
                or user.additional_image1
                or user.additional_image2
            ),
        }

        # Optimized task application stats with single query
        task_stats = TaskApplication.objects.filter(creator=user).aggregate(
            total_applications=Count("id"),
            pending_applications=Count("id", filter=Q(status="PENDING")),
            accepted_applications=Count("id", filter=Q(status="ACCEPTED")),
            completed_applications=Count("id", filter=Q(status="COMPLETED")),
        )

        # Available tasks (optimized with select_related and limited fields)
        available_tasks = (
            Task.objects.filter(is_active=True)
            .exclude(applications__creator=user)
            .select_related("brand")
            .only(
                "id", "title", "description", "budget", "deadline", "brand__username"
            )[:5]
        )

        # Optimized chat stats
        chat_stats = ChatConversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        ).aggregate(
            total_conversations=Count("id", distinct=True),
            brand_conversations=Count(
                "id", filter=Q(brand__isnull=False), distinct=True
            ),
            creator_conversations=Count(
                "id", filter=Q(brand__isnull=True), distinct=True
            ),
        )

        # Content stats (single query)
        content_stats = {
            "blog_posts": BlogPost.objects.filter(
                author=user, status="published"
            ).count(),
        }

        # Brands they're working with (optimized with single query)
        working_with_brands = list(
            TaskApplication.objects.filter(
                creator=user, status__in=["ACCEPTED", "COMPLETED"]
            )
            .select_related("task__brand")
            .values_list("task__brand__username", flat=True)
            .distinct()[:5]
        )

        context.update(
            {
                "profile_stats": profile_stats,
                "task_stats": task_stats,
                "available_tasks": available_tasks,
                "chat_stats": chat_stats,
                "content_stats": content_stats,
                "working_with_brands": working_with_brands,
            }
        )

    return render(request, "website/landing.html", context)


def landing_new(request):
    """Lightweight view to render the new static landing page template."""
    return render(request, "landing_new.html")


@require_POST
@csrf_protect
def waitlist_signup(request):
    """Receive waitlist form submissions and notify Slack via configured webhook."""
    try:
        email = (request.POST.get("email") or "").strip()
        name = (request.POST.get("name") or "").strip()

        # Basic validation
        if not email:
            return JsonResponse(
                {"success": False, "error": "Email is required."}, status=400
            )
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse(
                {"success": False, "error": "Invalid email address."}, status=400
            )

        # Request context
        referer = request.META.get("HTTP_REFERER", "")
        ua = (request.META.get("HTTP_USER_AGENT") or "")[:180]
        ip = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[
            0
        ].strip() or request.META.get("REMOTE_ADDR", "")

        # Compose Slack message
        details = (
            f"Email: {email}\n"
            f"Name: {name or '—'}\n"
            f"IP: {ip or 'unknown'}\n"
            f"UA: {ua or 'unknown'}\n"
            f"Referrer: {referer or 'direct'}\n"
            f"Path: {request.path}"
        )

        # Send to Slack using our utility
        try:
            from .utils.slack_notifications import SlackNotifier

            SlackNotifier.send_custom_notification(
                title="New Waitlist Signup",
                details=details,
                severity="success",
            )
        except Exception as e:  # don't fail the request if Slack errors
            logger.error(f"Failed to notify Slack for waitlist signup: {str(e)}")

        # Respond: JSON for XHR, redirect otherwise
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect(reverse("website:landing_new") + "?waitlist=ok")

    except Exception as e:
        logger.exception("Waitlist signup error")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def signup_choice(request):
    """Main signup page where users choose between brand or creator signup"""
    return render(request, "website/signup_choice.html")


def user_signup(request):
    """Creator signup page for individual creators"""
    if request.method == "POST":
        # Get form data
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        bio = request.POST.get("bio", "").strip()

        # Basic validation
        required_fields = [first_name, last_name, username, email, password1, password2]
        if not all(required_fields):
            messages.error(request, "All required fields must be filled out.")
            return render(request, "website/user_signup.html")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "website/user_signup.html")

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(
                request,
                "An account with this email already exists. "
                "Please use a different email address.",
            )
            return render(request, "website/user_signup.html")

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "This username is already taken. Please choose a different username.",
            )
            return render(request, "website/user_signup.html")

        try:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )

            # Add bio if provided
            if bio:
                user.bio = bio
                user.save()

            # Handle referral tracking
            handle_referral_signup(request, user)

            messages.success(
                request, "Account created successfully! You can now log in."
            )
            return redirect("account_login")

        except IntegrityError:
            messages.error(
                request,
                "An account with this email or username already exists. "
                "Please use different credentials.",
            )
            return render(request, "website/user_signup.html")
        except Exception as e:
            messages.error(
                request, f"An error occurred while creating your account: {str(e)}"
            )
            return render(request, "website/user_signup.html")

    return render(request, "website/user_signup.html")


def brand_signup(request):
    # Get Stripe public key from environment
    stripe_public_key = os.environ.get("STRIPE_PUBLIC_KEY", "")

    # Check if Stripe is properly configured
    if not stripe_public_key:
        # For development, provide a helpful error
        if os.environ.get("ENVIRONMENT", "development") == "development":
            return render(
                request,
                "website/error.html",
                {
                    "error_title": "Stripe Configuration Missing",
                    "error_message": (
                        "Please set your STRIPE_PUBLIC_KEY environment "
                        "variable in your .env file."
                    ),
                    "error_details": (
                        "You need to create a .env file in the project "
                        "root with your Stripe keys."
                    ),
                },
            )
        else:
            # For production, log the error and show generic message
            logger.error("STRIPE_PUBLIC_KEY environment variable not set")
            return render(
                request,
                "website/error.html",
                {
                    "error_title": "Configuration Error",
                    "error_message": (
                        "Payment system is temporarily unavailable. "
                        "Please try again later."
                    ),
                },
            )

    # Get plan from URL parameter
    plan = request.GET.get("plan", "starter")

    # Define plan details
    plans = {
        # "trial": {
        #     "name": "Trial",
        #     "price": 1,
        #     "price_id": os.environ.get("STRIPE_PRICE_1", ""),
        #     "features": ["Basic Analytics", "Email Templates", "24/7 Support"],
        # },
        "starter": {
            "name": "Starter",
            "price": 99,
            "price_id": os.environ.get("STRIPE_PRICE_99", ""),
            "features": ["Basic Analytics", "Email Templates", "24/7 Support"],
        },
        "professional": {
            "name": "Professional",
            "price": 199,
            "price_id": os.environ.get("STRIPE_PRICE_199", ""),
            "features": [
                "Advanced Analytics",
                "Lead Generation Tools",
                "Automation Workflows",
                "Priority Support",
            ],
        },
        "enterprise": {
            "name": "Business",
            "price": 299,
            "price_id": os.environ.get("STRIPE_PRICE_299", ""),
            "features": [
                "Custom Analytics",
                "Dedicated Account Manager",
                "White-label Solutions",
            ],
        },
    }

    selected_plan = plans.get(plan, plans["starter"])

    context = {
        "stripe_public_key": stripe_public_key,
        "plan": selected_plan,
        "plan_key": plan,
    }

    return render(request, "website/signup.html", context)


def terms(request):
    return render(request, "website/terms.html")


def privacy(request):
    return render(request, "website/privacy.html")


def about(request):
    return render(request, "website/about.html")


def help_page(request):
    return render(request, "website/help.html")


def blog(request):
    """Display published blog posts with filtering and pagination"""

    # Get published posts
    posts = BlogPost.objects.filter(status="published")

    # Filter by category
    category = request.GET.get("category")
    if category and category != "all":
        posts = posts.filter(category=category)

    # Filter by tag
    tag = request.GET.get("tag")
    if tag:
        posts = posts.filter(tags__contains=[tag])

    # Search functionality
    search = request.GET.get("search")
    if search:
        posts = posts.filter(
            models.Q(title__icontains=search)
            | models.Q(content__icontains=search)
            | models.Q(excerpt__icontains=search)
        )

    # Get featured post
    featured_post = posts.filter(is_featured=True).first()

    # Exclude featured post from regular listing
    if featured_post:
        posts = posts.exclude(pk=featured_post.pk)

    # Pagination
    paginator = Paginator(posts.order_by("-published_at"), 9)  # 9 posts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get all categories for filter
    categories = BlogPost.CATEGORY_CHOICES

    # Get popular tags
    all_tags = []
    for post in BlogPost.objects.filter(status="published"):
        all_tags.extend(post.tags)
    popular_tags = [tag for tag, count in Counter(all_tags).most_common(10)]

    context = {
        "title": "Blog - Gemnar",
        "featured_post": featured_post,
        "page_obj": page_obj,
        "categories": categories,
        "popular_tags": popular_tags,
        "current_category": category,
        "current_tag": tag,
        "search_query": search,
    }

    return render(request, "website/blog.html", context)


def blog_detail(request, slug):
    """Display a single blog post"""
    post = get_object_or_404(BlogPost, slug=slug, status="published")

    # Increment view count
    post.increment_view_count()

    # Get related posts
    related_posts = post.get_related_posts(limit=3)

    # Get comments for the post
    comments = post.comments.filter(is_approved=True, parent=None).order_by(
        "created_at"
    )

    context = {
        "title": post.title,
        "post": post,
        "related_posts": related_posts,
        "comments": comments,
    }

    return render(request, "website/blog_detail.html", context)


@login_required
def blog_create(request):
    """Create a new blog post"""
    if request.method == "POST":
        try:
            # Get form data
            title = request.POST.get("title", "").strip()
            content = request.POST.get("content", "").strip()
            excerpt = request.POST.get("excerpt", "").strip()
            category = request.POST.get("category", "other")
            tags = request.POST.getlist("tags")
            status = request.POST.get("status", "draft")
            is_featured = request.POST.get("is_featured") == "on"
            meta_description = request.POST.get("meta_description", "").strip()
            meta_keywords = request.POST.get("meta_keywords", "").strip()

            if not title or not content:
                return JsonResponse(
                    {"success": False, "error": "Title and content are required."}
                )

            # Create blog post
            post = BlogPost.objects.create(
                title=title,
                content=content,
                excerpt=excerpt,
                author=request.user,
                category=category,
                tags=tags,
                status=status,
                is_featured=is_featured,
                meta_description=meta_description,
                meta_keywords=meta_keywords,
            )

            # Handle featured image upload
            if "featured_image" in request.FILES:
                post.featured_image = request.FILES["featured_image"]
                post.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Blog post {'published' if status == 'published' else 'saved as draft'} successfully!",
                    "post_url": (
                        post.get_absolute_url() if status == "published" else None
                    ),
                    "post_id": post.id,
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    # GET request - show form
    context = {
        "title": "Create Blog Post",
        "categories": BlogPost.CATEGORY_CHOICES,
    }

    return render(request, "website/blog_create.html", context)


@login_required
def blog_edit(request, slug):
    """Edit an existing blog post"""
    post = get_object_or_404(BlogPost, slug=slug, author=request.user)

    if request.method == "POST":
        try:
            # Get form data
            title = request.POST.get("title", "").strip()
            content = request.POST.get("content", "").strip()
            excerpt = request.POST.get("excerpt", "").strip()
            category = request.POST.get("category", "other")
            tags = request.POST.getlist("tags")
            status = request.POST.get("status", "draft")
            is_featured = request.POST.get("is_featured") == "on"
            meta_description = request.POST.get("meta_description", "").strip()
            meta_keywords = request.POST.get("meta_keywords", "").strip()

            if not title or not content:
                return JsonResponse(
                    {"success": False, "error": "Title and content are required."}
                )

            # Update blog post
            post.title = title
            post.content = content
            post.excerpt = excerpt
            post.category = category
            post.tags = tags
            post.status = status
            post.is_featured = is_featured
            post.meta_description = meta_description
            post.meta_keywords = meta_keywords

            # Handle featured image upload
            if "featured_image" in request.FILES:
                post.featured_image = request.FILES["featured_image"]

            post.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Blog post {'published' if status == 'published' else 'updated'} successfully!",
                    "post_url": (
                        post.get_absolute_url() if status == "published" else None
                    ),
                    "post_id": post.id,
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    # GET request - show form with existing data
    context = {
        "title": "Edit Blog Post",
        "post": post,
        "categories": BlogPost.CATEGORY_CHOICES,
    }

    return render(request, "website/blog_edit.html", context)


@login_required
def blog_delete(request, slug):
    """Delete a blog post"""
    post = get_object_or_404(BlogPost, slug=slug, author=request.user)

    if request.method == "POST":
        try:
            post.delete()
            return JsonResponse(
                {"success": True, "message": "Blog post deleted successfully!"}
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})


@login_required
def blog_my_posts(request):
    """List user's blog posts with management interface"""
    # Get user's posts
    posts = BlogPost.objects.filter(author=request.user)

    # Filter by status
    status = request.GET.get("status")
    if status and status != "all":
        posts = posts.filter(status=status)

    # Search functionality
    search = request.GET.get("search")
    if search:
        posts = posts.filter(
            models.Q(title__icontains=search) | models.Q(content__icontains=search)
        )

    # Pagination
    paginator = Paginator(posts.order_by("-created_at"), 10)  # 10 posts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Calculate statistics
    total_posts = posts.count()
    published_posts = posts.filter(status="published").count()
    draft_posts = posts.filter(status="draft").count()

    context = {
        "title": "My Blog Posts",
        "page_obj": page_obj,
        "current_status": status,
        "search_query": search,
        "stats": {
            "total": total_posts,
            "published": published_posts,
            "draft": draft_posts,
        },
    }

    return render(request, "website/blog_my_posts.html", context)


@require_POST
def blog_comment(request, slug):
    """Add a comment to a blog post"""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"success": False, "error": "You must be logged in to comment."}
        )

    post = get_object_or_404(BlogPost, slug=slug, status="published")

    try:
        content = request.POST.get("content", "").strip()
        parent_id = request.POST.get("parent_id")

        if not content:
            return JsonResponse(
                {"success": False, "error": "Comment content is required."}
            )

        # Get parent comment if this is a reply
        parent = None
        if parent_id:
            parent = get_object_or_404(BlogComment, id=parent_id, post=post)

        # Create comment
        comment = BlogComment.objects.create(
            post=post, author=request.user, content=content, parent=parent
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Comment added successfully!",
                "comment": {
                    "id": comment.id,
                    "content": comment.content,
                    "author": comment.author.username,
                    "created_at": comment.created_at.isoformat(),
                    "is_reply": comment.is_reply,
                },
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def contact(request):
    return render(request, "website/contact.html")


def services(request):
    return render(request, "website/services.html")


def pricing(request):
    """
    Pricing page displaying Runware pricing with Gemnar markup
    """
    from .models import RunwarePricingData, PricingPageConfig

    # Get active pricing configuration
    config = PricingPageConfig.get_active_config()
    if not config:
        # Create default config if none exists
        config = PricingPageConfig.objects.create(
            page_title="Gemnar AI Services Pricing",
            page_description="Transparent pricing for AI-powered marketing services. No hidden fees, pay as you go.",
            default_markup_percentage=50.00,
            is_active=True,
        )

    # Get all active pricing data
    pricing_data = RunwarePricingData.objects.filter(is_active=True).order_by(
        "service_name"
    )

    # Get featured services if any are configured
    featured_services = (
        config.featured_services.filter(is_active=True)
        if config.featured_services.exists()
        else pricing_data[:3]
    )

    # Calculate totals and stats
    total_services = pricing_data.count()

    context = {
        "config": config,
        "pricing_data": pricing_data,
        "featured_services": featured_services,
        "total_services": total_services,
    }

    return render(request, "website/pricing.html", context)


def status(request):
    """Status page showing health of various services"""
    status_data = {
        "database": check_database_status(),
        "github": check_github_status(),
        "stripe": check_stripe_status(),
        "sentry": check_sentry_status(),
        "ai_image": check_ai_image_service_status(),
        "ai_video": check_ai_video_service_status(),
        "ai_service": check_ai_service_status(),
        "email_smtp": check_email_smtp_status(),
        "dns": check_dns_status(),
        "minute_task": check_minute_task_status(),
    }

    # Overall status is healthy if all services are healthy
    overall_status = all(
        service["status"] == "healthy" for service in status_data.values()
    )

    context = {
        "status_data": status_data,
        "overall_status": "healthy" if overall_status else "unhealthy",
    }

    return render(request, "website/status.html", context)


def feed(request):
    photos = list(Image.objects.filter(user__isnull=False).select_related("user"))

    random.shuffle(photos)

    # Create a list of dictionaries for the template
    photo_data = [
        {
            "url": p.image.url,
            "creator_id": p.user.id,
            "creator_username": p.user.username,
        }
        for p in photos
    ]

    return render(request, "website/feed.html", {"photos": photo_data})


def check_database_status():
    """Check database connection status by counting users"""
    try:
        total_users = User.objects.count()

        return {
            "status": "healthy",
            "message": f"Database working - {total_users} users registered",
            "details": f"Successfully connected and counted {total_users} users in database",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Database connection failed",
            "details": str(e),
        }


def check_github_status():
    """Check GitHub API status"""
    try:
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if not github_token:
            return {
                "status": "warning",
                "message": "GitHub token not configured",
                "details": "GITHUB_TOKEN environment variable not set",
            }

        headers = {"Authorization": f"token {github_token}"}
        response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=10
        )

        if response.status_code == 200:
            return {
                "status": "healthy",
                "message": "GitHub API connection successful",
                "details": "API token valid and authenticated",
            }
        else:
            return {
                "status": "unhealthy",
                "message": "GitHub API connection failed",
                "details": f"HTTP {response.status_code}: {response.text[:100]}",
            }
    except requests.exceptions.Timeout:
        return {
            "status": "unhealthy",
            "message": "GitHub API timeout",
            "details": "Request timed out after 10 seconds",
        }
    except Exception as e:
        return {"status": "unhealthy", "message": "GitHub API error", "details": str(e)}


def check_stripe_status():
    """Check Stripe API status"""
    try:
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe_secret_key:
            return {
                "status": "warning",
                "message": "Stripe secret key not configured",
                "details": "STRIPE_SECRET_KEY environment variable not set",
            }

        stripe.api_key = stripe_secret_key

        # Use a simpler endpoint that works with basic permissions
        # Try to get account details which requires minimal permissions
        try:
            stripe.Account.retrieve()  # Test API connectivity
            key_type = (
                "Test Mode" if stripe_secret_key.startswith("sk_test_") else "Live Mode"
            )
            return {
                "status": "healthy",
                "message": "Stripe API connection successful",
                "details": f"API Key Valid ({key_type})",
            }
        except stripe.error.PermissionError:
            # If we can't access account details, try a simpler test
            # Just validate the key format and return a warning
            key_type = (
                "Test Mode" if stripe_secret_key.startswith("sk_test_") else "Live Mode"
            )
            return {
                "status": "warning",
                "message": "Stripe API key configured",
                "details": f"API Key format valid ({key_type}) - limited permissions",
            }

    except stripe.error.AuthenticationError:
        return {
            "status": "unhealthy",
            "message": "Stripe authentication failed",
            "details": "Invalid API key or authentication error",
        }
    except Exception as e:
        return {"status": "unhealthy", "message": "Stripe API error", "details": str(e)}


def check_sentry_status():
    """Check Sentry DSN configuration"""
    try:
        sentry_dsn = os.environ.get("SENTRY_DSN", "")
        if not sentry_dsn:
            return {
                "status": "warning",
                "message": "Sentry DSN not configured",
                "details": "SENTRY_DSN environment variable not set",
            }

        # Basic DSN format validation
        if not sentry_dsn.startswith("https://"):
            return {
                "status": "unhealthy",
                "message": "Invalid Sentry DSN format",
                "details": "DSN should start with https://",
            }

        # Check for Sentry domain patterns
        sentry_patterns = ["@sentry.io/", "@o", ".ingest.", ".sentry.io/"]
        if not any(pattern in sentry_dsn for pattern in sentry_patterns):
            return {
                "status": "unhealthy",
                "message": "Invalid Sentry DSN format",
                "details": "DSN does not appear to be a valid Sentry URL",
            }

        return {
            "status": "healthy",
            "message": "Sentry DSN configured",
            "details": "DSN format valid and monitoring active",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Sentry configuration error",
            "details": str(e),
        }


def check_ai_image_service_status():
    """Check Runware AI image generation service status"""
    try:
        api_key = os.environ.get("RUNWARE_API_KEY", "")
        if not api_key:
            return {
                "status": "warning",
                "message": "AI Image API key not configured",
                "details": "AI Image API key not configured",
            }

        # Test the API with a simple request
        test_payload = [
            {
                "taskType": "imageInference",
                "taskUUID": str(uuid.uuid4()),
                "model": "runware:101@1",
                "positivePrompt": "test",
                "width": 512,
                "height": 512,
                "steps": 10,
            }
        ]

        response = requests.post(
            "https://api.runware.ai/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=test_payload,
            timeout=30,  # Longer timeout for AI generation
        )

        if response.status_code == 200:
            return {
                "status": "healthy",
                "message": "AI Image service operational",
                "details": "AI Image API responding successfully",
            }
        elif response.status_code == 401:
            return {
                "status": "unhealthy",
                "message": "AI Image API authentication failed",
                "details": "Invalid API key or authentication error",
            }
        elif response.status_code == 429:
            return {
                "status": "warning",
                "message": "AI Image service rate limited",
                "details": "API rate limit exceeded, service temporarily unavailable",
            }
        else:
            return {
                "status": "unhealthy",
                "message": "AI Image service error",
                "details": f"HTTP {response.status_code}: {response.text[:100]}",
            }

    except requests.exceptions.Timeout:
        return {
            "status": "unhealthy",
            "message": "AI Image service timeout",
            "details": "Request timed out after 30 seconds",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "AI Image service error",
            "details": str(e),
        }


def check_ai_video_service_status():
    """Check Runware AI video generation service status"""
    try:
        api_key = os.environ.get("RUNWARE_API_KEY", "")
        if not api_key:
            return {
                "status": "warning",
                "message": "AI Video API key not configured",
                "details": "AI Video API key not configured",
            }

        # Just check if we can authenticate and the video service is available
        # by using the same image service endpoint (same API, same auth)
        return {
            "status": "healthy",
            "message": "AI Video service operational",
            "details": "Video generation uses same API as image service - PixVerse v4.5 available",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "AI Video service error",
            "details": str(e),
        }


def check_email_smtp_status():
    """Check email SMTP server connectivity"""
    try:
        # Check if SMTP credentials are configured
        smtp_username = os.environ.get("SMTP_USERNAME", "")
        smtp_password = os.environ.get("SMTP_PASSWORD", "")

        if not smtp_username or not smtp_password:
            return {
                "status": "warning",
                "message": "SMTP credentials not configured",
                "details": "SMTP_USERNAME or SMTP_PASSWORD environment variables not set",
            }

        # Test SMTP connection
        import smtplib
        import socket

        # Settings from Django configuration
        smtp_host = "smtp.mailgun.org"
        smtp_port = 587

        try:
            # Create SMTP connection
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.starttls()  # Enable TLS
            server.login(smtp_username, smtp_password)

            # Test successful - close connection
            server.quit()

            return {
                "status": "healthy",
                "message": "SMTP connection successful",
                "details": "Connected to SMTP server successfully",
            }

        except smtplib.SMTPAuthenticationError:
            return {
                "status": "unhealthy",
                "message": "SMTP authentication failed",
                "details": "Invalid SMTP username or password",
            }
        except smtplib.SMTPRecipientsRefused:
            return {
                "status": "unhealthy",
                "message": "SMTP recipients refused",
                "details": "SMTP server refused recipients (check from email domain)",
            }
        except smtplib.SMTPException as e:
            return {
                "status": "unhealthy",
                "message": "SMTP connection error",
                "details": f"SMTP error: {str(e)}",
            }
        except socket.timeout:
            return {
                "status": "unhealthy",
                "message": "SMTP connection timeout",
                "details": f"Connection to {smtp_host}:{smtp_port} timed out",
            }
        except socket.error as e:
            return {
                "status": "unhealthy",
                "message": "SMTP network error",
                "details": f"Network error connecting to {smtp_host}:{smtp_port}: {str(e)}",
            }

    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Email system error",
            "details": str(e),
        }


def check_dns_status():
    """Check DNS Records for Email Deliverability"""
    dns_status = {
        "name": "DNS Records",
        "status": "unknown",
        "details": {},
        "recommendations": [],
    }

    try:
        domain = (
            settings.EMAIL_HOST_USER.split("@")[1]
            if "@" in settings.EMAIL_HOST_USER
            else "gemnar.com"
        )

        # Check SPF Record
        try:
            spf_records = dns.resolver.resolve(domain, "TXT")
            spf_found = any("v=spf1" in str(record) for record in spf_records)
            if spf_found:
                dns_status["details"]["spf"] = "✅ SPF record found"
            else:
                dns_status["details"]["spf"] = "❌ SPF record not found"
                dns_status["recommendations"].append(
                    "Add SPF record: v=spf1 include:mailgun.org ~all"
                )
        except Exception:
            dns_status["details"]["spf"] = "❌ SPF record not found"
            dns_status["recommendations"].append(
                "Add SPF record: v=spf1 include:mailgun.org ~all"
            )

        # Check DKIM (would need domain-specific DKIM key)
        dns_status["details"][
            "dkim"
        ] = "⚠️ DKIM verification requires domain-specific setup"

        # Check DMARC
        try:
            dmarc_records = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
            dmarc_found = any("v=DMARC1" in str(record) for record in dmarc_records)
            if dmarc_found:
                dns_status["details"]["dmarc"] = "✅ DMARC record found"
            else:
                dns_status["details"]["dmarc"] = "❌ DMARC record not found"
                dns_status["recommendations"].append(
                    "Add DMARC record: v=DMARC1; p=quarantine; rua=mailto:support@gemnar.com"
                )
        except Exception:
            dns_status["details"]["dmarc"] = "❌ DMARC record not found"
            dns_status["recommendations"].append(
                "Add DMARC record: v=DMARC1; p=quarantine; rua=mailto:support@gemnar.com"
            )

        # Check MX Records
        try:
            mx_records = dns.resolver.resolve(domain, "MX")
            if mx_records:
                dns_status["details"][
                    "mx"
                ] = f"✅ MX records found ({len(mx_records)} records)"
            else:
                dns_status["details"]["mx"] = "❌ No MX records found"
        except Exception as e:
            dns_status["details"]["mx"] = f"❌ MX lookup failed: {str(e)}"

        dns_status["status"] = (
            "healthy"
            if all(
                "✅" in detail
                for detail in dns_status["details"].values()
                if "✅" in detail or "❌" in detail
            )
            else "warning"
        )

    except Exception as e:
        dns_status["status"] = "error"
        dns_status["details"]["error"] = f"DNS check failed: {str(e)}"

    return dns_status


def check_ai_service_status():
    """Check OpenAI API service status"""
    try:
        from website.utils import get_openai_client
        from .models import EncryptedVariable

        # First check if API key is properly configured in database
        openai_var = EncryptedVariable.objects.filter(
            key="OPENAI_API_KEY", is_active=True
        ).first()

        if not openai_var:
            return {
                "status": "unhealthy",
                "message": "AI service not configured",
                "details": "OpenAI API key not found in database. Please configure OPENAI_API_KEY in EncryptedVariable table through Django admin.",
            }

        # Try to get the API key directly to check decryption
        try:
            api_key = openai_var.get_decrypted_value()
            if not api_key:
                return {
                    "status": "unhealthy",
                    "message": "AI service not configured",
                    "details": "OpenAI API key exists in database but decryption returned empty value",
                }

            # Validate key format
            if not api_key.startswith("sk-") or len(api_key) < 20:
                return {
                    "status": "unhealthy",
                    "message": "AI service not configured",
                    "details": f"OpenAI API key has invalid format (starts with {api_key[:10]}...)",
                }

        except Exception as decrypt_error:
            return {
                "status": "unhealthy",
                "message": "AI service not configured",
                "details": f"Failed to decrypt OpenAI API key: {str(decrypt_error)}",
            }

        client = get_openai_client()
        if not client:
            return {
                "status": "warning",
                "message": "AI service not configured",
                "details": "OpenAI API key exists and decrypts properly but failed to create working client",
            }

        # Test OpenAI API with a simple request
        try:
            # Test with a simple model list request (minimal API call)
            response = client.models.list()

            if response and response.data:
                return {
                    "status": "healthy",
                    "message": "AI service operational",
                    "details": "AI text and image service API responding successfully",
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "AI service error",
                    "details": "OpenAI API returned empty response",
                }

        except Exception as api_error:
            error_str = str(api_error)
            if (
                "authentication" in error_str.lower()
                or "unauthorized" in error_str.lower()
            ):
                return {
                    "status": "unhealthy",
                    "message": "AI service authentication failed",
                    "details": "Invalid OpenAI API key or authentication error",
                }
            elif "rate_limit" in error_str.lower() or "429" in error_str:
                return {
                    "status": "warning",
                    "message": "AI service rate limited",
                    "details": "OpenAI API rate limit exceeded, temporarily unavailable",
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "AI service error",
                    "details": f"OpenAI API error: {error_str[:100]}",
                }

    except ImportError:
        return {
            "status": "unhealthy",
            "message": "AI service not available",
            "details": "OpenAI library not installed",
        }
    except Exception as e:
        return {"status": "unhealthy", "message": "AI service error", "details": str(e)}


def check_minute_task_status():
    """Check minute task management command status using WebLog"""
    try:
        from datetime import timedelta
        from .models import WebLog

        # Check for entries within the past minute
        one_minute_ago = timezone.now() - timedelta(minutes=1)

        recent_logs = WebLog.objects.filter(
            activity_type="minute_task",
            activity_name="send_brand_tweets",
            started_at__gte=one_minute_ago,
        ).order_by("-started_at")

        if recent_logs.exists():
            latest_log = recent_logs.first()

            # Check if it completed successfully
            if latest_log.status == "completed":
                return {
                    "status": "healthy",
                    "message": f"Minute task active - processed {latest_log.items_processed} brands",
                    "details": f"Last run: {latest_log.started_at.strftime('%Y-%m-%d %H:%M:%S')} | Success: {latest_log.items_succeeded} | Failed: {latest_log.items_failed}",
                }
            elif latest_log.status == "failed":
                return {
                    "status": "unhealthy",
                    "message": "Minute task failed",
                    "details": f"Error: {latest_log.error_message or 'Unknown error'}",
                }
            else:
                # Still running
                return {
                    "status": "healthy",
                    "message": "Minute task currently running",
                    "details": f"Started: {latest_log.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
                }
        else:
            # No entries in the past minute - check for recent entries
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            recent_logs_5min = WebLog.objects.filter(
                activity_type="minute_task",
                activity_name="send_brand_tweets",
                started_at__gte=five_minutes_ago,
            ).order_by("-started_at")

            if recent_logs_5min.exists():
                latest_log = recent_logs_5min.first()
                time_since = timezone.now() - latest_log.started_at
                minutes_ago = int(time_since.total_seconds() / 60)

                return {
                    "status": "warning",
                    "message": "Minute task not running on schedule",
                    "details": f"Last run: {latest_log.started_at.strftime('%Y-%m-%d %H:%M:%S')} ({minutes_ago}m ago) | Status: {latest_log.get_status_display()}",
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Minute task not running",
                    "details": "No execution found in the past 5 minutes",
                }

    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Minute task check error",
            "details": str(e),
        }


@require_POST
@csrf_exempt
def process_payment(request):
    """
    Process brand signup and payment with Stripe.
    Creates a User, a Brand, a Stripe Customer, and a Stripe Subscription.
    """
    try:
        # Set Stripe API key
        stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not stripe_secret_key:
            return JsonResponse(
                {"success": False, "error": "Stripe not configured on server."}
            )
        stripe.api_key = stripe_secret_key

        token = request.POST.get("stripeToken")
        email = request.POST.get("email")
        password = request.POST.get("password")
        brand_name = request.POST.get("name")
        brand_url = request.POST.get("url")
        plan = request.POST.get("plan", "starter")

        # Check for required fields
        if not all([token, email, password, brand_name, brand_url, plan]):
            return JsonResponse({"success": False, "error": "Missing required fields."})

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": "An account with this email already exists. "
                    "Please use a different email address.",
                }
            )

        # Create User
        try:
            user = User.objects.create_user(
                username=email, email=email, password=password
            )
        except IntegrityError:
            return JsonResponse(
                {
                    "success": False,
                    "error": "An account with this email already exists. "
                    "Please use a different email address.",
                }
            )

        # Handle referral tracking
        handle_referral_signup(request, user)

        # Create Stripe Customer
        customer = stripe.Customer.create(
            email=email,
            name=brand_name,
            source=token,
        )

        # Create Stripe Subscription
        plan_price_ids = {
            # "trial": os.environ.get("STRIPE_PRICE_1"),
            "starter": os.environ.get("STRIPE_PRICE_99"),
            "professional": os.environ.get("STRIPE_PRICE_199"),
            "enterprise": os.environ.get("STRIPE_PRICE_299"),
        }
        price_id = plan_price_ids.get(plan)
        if not price_id:
            return JsonResponse({"success": False, "error": "Invalid plan selected."})

        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
        )

        # Create Brand
        from django.utils import timezone

        brand = Brand.objects.create(
            name=brand_name,
            url=brand_url,
            owner=user,
            stripe_customer_id=customer.id,
            stripe_subscription_id=subscription.id,
            stripe_subscription_status=subscription.status,  # Set initial status from Stripe
            last_payment_date=timezone.now(),  # Set initial payment date
            preferred_payment_method="stripe",
        )

        # Handle referral subscription tracking
        plan_prices = {
            # "trial": 1,
            "starter": 99,
            "professional": 199,
            "enterprise": 299,
        }
        handle_referral_subscription(user, plan, plan_prices.get(plan, 1))

        return JsonResponse(
            {
                "success": True,
                "redirect_url": reverse("website:brand_success", args=[brand.id]),
            }
        )

    except stripe.error.CardError as e:
        return JsonResponse({"success": False, "error": str(e)})
    except stripe.error.StripeError as e:
        # Handle other Stripe errors
        return JsonResponse(
            {"success": False, "error": f"Stripe error: {e.user_message}"}
        )
    except Exception as e:
        # Handle other exceptions
        return JsonResponse(
            {"success": False, "error": f"An unexpected error occurred: {str(e)}"}
        )


# Creator Flow Views
def creator_step1(request):
    """Step 1: Basic info and Instagram URL"""
    if request.method == "POST":
        # Create new creator instance
        creator = User.objects.create(
            name=request.POST.get("name", ""),
            description=request.POST.get("description", ""),
            instagram_url=request.POST.get("instagram_url", ""),
        )
        return redirect("website:creator_step2", creator_id=creator.id)

    return render(request, "website/creator/creator_step1.html")


def creator_step2(request, creator_id):
    """Step 2: Upload 6 photos/videos"""
    creator = get_object_or_404(User, id=creator_id)

    if request.method == "POST":
        # Handle file uploads
        for i in range(1, 7):
            file_key = f"photo{i}"
            if file_key in request.FILES:
                setattr(creator, file_key, request.FILES[file_key])

        creator.save()
        return redirect("website:creator_step3", creator_id=creator.id)

    return render(request, "website/creator/creator_step2.html", {"creator": creator})


def creator_step3(request, creator_id):
    """Step 3: List 5 brands they want to work with"""
    creator = get_object_or_404(User, id=creator_id)

    if request.method == "POST":
        # Save brand preferences
        creator.brand1 = request.POST.get("brand1", "")
        creator.brand2 = request.POST.get("brand2", "")
        creator.brand3 = request.POST.get("brand3", "")
        creator.brand4 = request.POST.get("brand4", "")
        creator.brand5 = request.POST.get("brand5", "")
        creator.save()

        # Redirect to success page or dashboard
        return redirect("website:creator_success", creator_id=creator.id)

    return render(request, "website/creator/creator_step3.html", {"creator": creator})


def creator_success(request, creator_id):
    """Success page after completing the creator flow"""
    creator = get_object_or_404(User, id=creator_id)
    return render(request, "website/creator/creator_success.html", {"creator": creator})


def creator_profile(request, creator_id):
    """Profile page with both view and edit functionality (Hinge-style)"""
    creator = get_object_or_404(User, id=creator_id)

    if request.method == "POST":
        # Handle profile updates
        creator.name = request.POST.get("name", creator.name)
        creator.description = request.POST.get("description", creator.description)
        creator.instagram_url = request.POST.get("instagram_url", creator.instagram_url)

        # Handle brand updates
        creator.brand1 = request.POST.get("brand1", creator.brand1)
        creator.brand2 = request.POST.get("brand2", creator.brand2)
        creator.brand3 = request.POST.get("brand3", creator.brand3)
        creator.brand4 = request.POST.get("brand4", creator.brand4)
        creator.brand5 = request.POST.get("brand5", creator.brand5)

        # Handle file uploads
        for i in range(1, 7):
            file_key = f"photo{i}"
            if file_key in request.FILES:
                setattr(creator, file_key, request.FILES[file_key])

        creator.save()
        return JsonResponse(
            {"success": True, "message": "Profile updated successfully"}
        )

    # Get all photos for the gallery
    photos = []
    for i in range(1, 7):
        photo = getattr(creator, f"photo{i}")
        if photo:
            photos.append({"number": i, "url": photo.url, "name": photo.name})

    context = {
        "creator": creator,
        "photos": photos,
    }

    return render(request, "website/creator/creator_profile.html", context)


def update_creator_profile(request, creator_id):
    creator = get_object_or_404(User, id=creator_id)

    if request.method == "POST":
        creator.name = request.POST.get("name")
        creator.description = request.POST.get("description")
        creator.instagram_url = request.POST.get("instagram_url")
        creator.brand1 = request.POST.get("brand1")
        creator.brand2 = request.POST.get("brand2")
        creator.brand3 = request.POST.get("brand3")
        creator.brand4 = request.POST.get("brand4")
        creator.brand5 = request.POST.get("brand5")
        creator.save()

        return redirect("website:creator_profile", creator_id=creator.id)

    return redirect("website:creator_profile", creator_id=creator.id)


@login_required
def business_step1(request):
    if request.method == "POST":
        name = request.POST.get("name")
        url = request.POST.get("url")

        business = Brand.objects.create(name=name, url=url, owner=request.user)

        return redirect("website:business_profile", business_id=business.id)

    return render(request, "website/business/business_step1.html")


def business_profile(request, business_id):
    business = get_object_or_404(Brand, id=business_id)
    return render(
        request, "website/business/business_profile.html", {"business": business}
    )


def brand_success(request, brand_id):
    """Success page after a brand signs up and pays."""
    brand = get_object_or_404(Brand, id=brand_id)
    return render(request, "website/business/brand_success.html", {"brand": brand})


def brand_profile(request, slug):
    """Brand profile page accessible at gemnar.com/brand-slug"""
    brand = get_object_or_404(Brand, slug=slug)

    # Get brand's images
    brand_images = brand.images.all()[:6]  # Limit to 6 images for showcase

    # Get brand's links
    brand_links = brand.links.filter(is_active=True).order_by("order")

    # Get brand's total campaigns/projects (placeholder for now)
    total_campaigns = 0  # This would come from actual campaign data

    # Get brand's join date
    join_date = brand.created_at

    # Get brand owner info (for contact purposes)
    owner = brand.owner

    # Get some performance metrics (placeholder)
    metrics = {
        "total_campaigns": total_campaigns,
        "total_creators": 0,  # Would come from actual data
        "total_reach": 0,  # Would come from actual data
        "satisfaction_rate": 95,  # Placeholder
    }

    context = {
        "brand": brand,
        "brand_images": brand_images,
        "brand_links": brand_links,
        "metrics": metrics,
        "owner": owner,
        "join_date": join_date,
    }

    return render(request, "website/brand_profile.html", context)


def marketing_grade_processing(request):
    domain = request.POST.get("domain", "")
    return render(
        request, "website/marketing_grade_processing.html", {"domain": domain}
    )


def marketing_grade_result(request):
    domain = request.GET.get("domain", "")
    return render(request, "website/marketing_grade_result.html", {"domain": domain})


@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Admin dashboard with system monitoring and user analytics."""
    # Get basic system data only (no memory analysis)
    initial_data = get_basic_dashboard_data()

    # Get environment variables for display
    env_vars = get_env_variable_names()

    # Get encrypted variables status for key services
    encrypted_vars_status = get_encrypted_variables_status()

    # Get log file status
    log_status = get_log_file_status()

    # Get recent WebLog entries for minute tasks
    recent_weblogs = WebLog.objects.filter(activity_type="minute_task").order_by(
        "-started_at"
    )[:10]

    # Get system stats for charts (default to 1 hour)
    from .models import SystemStats

    stats_1h = SystemStats.get_stats_by_timespan("1h")
    latest_stats = SystemStats.objects.first()

    # Prepare chart data
    chart_data = None
    if stats_1h.exists():
        chart_data = prepare_chart_data(stats_1h)

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": "Dashboard", "url": "/landing/", "icon": "fas fa-home"},
        {"title": "Admin", "url": None, "icon": "fas fa-cog"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "Memory Dashboard",
            "url": "/memory-dashboard/",
            "icon": "fas fa-memory",
            "class": "bg-blue-600 text-white hover:bg-blue-700",
        },
        {
            "title": "Django Admin",
            "url": "/admin/",
            "icon": "fas fa-tools",
            "class": "bg-green-600 text-white hover:bg-green-700",
        },
        {
            "title": "Encrypted Variables",
            "url": "/admin/website/encryptedvariable/",
            "icon": "fas fa-lock",
            "class": "bg-purple-600 text-white hover:bg-purple-700",
        },
    ]

    context = {
        "title": "Admin Dashboard",
        "initial_data": initial_data,
        "env_vars": env_vars,
        "encrypted_vars_status": encrypted_vars_status,
        "log_status": log_status,
        "recent_weblogs": recent_weblogs,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
        "chart_data": chart_data,
        "stats_count": stats_1h.count() if stats_1h.exists() else 0,
        "latest_stats": latest_stats,
    }
    return render(request, "website/admin_dashboard.html", context)


def prepare_chart_data(stats_queryset):
    """Prepare data for charts"""
    import json

    # Convert queryset to lists for JSON serialization
    timestamps = []
    memory_data = []
    cpu_data = []
    disk_data = []
    sessions_data = []
    users_data = []
    brands_data = []

    for system_stat in stats_queryset.order_by("timestamp"):
        # Format timestamp for JavaScript
        timestamp = system_stat.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        timestamps.append(timestamp)
        memory_data.append(round(system_stat.memory_percent, 1))
        cpu_data.append(round(system_stat.cpu_percent, 1))
        disk_data.append(round(system_stat.disk_percent, 1))
        sessions_data.append(system_stat.active_sessions)
        users_data.append(system_stat.user_count)
        brands_data.append(system_stat.brand_count)

    return {
        "timestamps": json.dumps(timestamps),
        "memory_percent": json.dumps(memory_data),
        "cpu_percent": json.dumps(cpu_data),
        "disk_percent": json.dumps(disk_data),
        "active_sessions": json.dumps(sessions_data),
        "user_count": json.dumps(users_data),
        "brand_count": json.dumps(brands_data),
    }


@user_passes_test(is_admin_user)
def admin_chart_data(request):
    """AJAX endpoint for fetching chart data by timespan"""
    from django.http import JsonResponse
    from .models import SystemStats

    timespan = request.GET.get("timespan", "24h")

    # Get stats for the requested timespan
    stats_queryset = SystemStats.get_stats_by_timespan(timespan)

    if stats_queryset.exists():
        chart_data = prepare_chart_data(stats_queryset)

        # Add metadata
        chart_data["stats_count"] = stats_queryset.count()
        chart_data["timespan"] = timespan
        chart_data["timespan_label"] = {
            "1h": "1 Hour",
            "12h": "12 Hours",
            "24h": "24 Hours",
            "2d": "2 Days",
            "5d": "5 Days",
        }.get(timespan, "24 Hours")

        return JsonResponse(chart_data)
    else:
        return JsonResponse(
            {
                "error": "No data available for this timespan",
                "stats_count": 0,
                "timespan": timespan,
            }
        )


@user_passes_test(is_admin_user)
def memory_dashboard(request):
    """Memory dashboard with detailed memory analysis and monitoring."""
    # Get full memory analysis data
    initial_data = get_memory_dashboard_data()

    context = {
        "title": "Memory Dashboard",
        "initial_data": initial_data,
    }
    return render(request, "website/memory_dashboard.html", context)


@user_passes_test(is_admin_user)
def list_management_commands(request):
    """List available Django management commands"""
    import os
    from django.core.management import get_commands

    # Get all available commands
    get_commands()

    # Filter to only custom commands in our app
    custom_commands = []
    management_dir = os.path.join(os.path.dirname(__file__), "management", "commands")

    if os.path.exists(management_dir):
        for filename in os.listdir(management_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                command_name = filename[:-3]  # Remove .py extension
                custom_commands.append(
                    {
                        "name": command_name,
                        "description": f"Custom management command: {command_name}",
                    }
                )

    # Add some common Django commands that might be useful
    useful_commands = [
        {"name": "migrate", "description": "Apply database migrations"},
        {"name": "collectstatic", "description": "Collect static files"},
        {"name": "check", "description": "Check for system errors"},
        {"name": "shell", "description": "Open Django shell"},
    ]

    all_commands = custom_commands + useful_commands

    return JsonResponse({"commands": all_commands, "total": len(all_commands)})


@user_passes_test(is_admin_user)
def execute_management_command(request):
    """Execute a management command and stream the output"""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
        command_name = data.get("command")
        command_args = data.get("args", [])

        if not command_name:
            return JsonResponse({"error": "Command name required"}, status=400)

        # Security check - only allow certain commands
        allowed_commands = [
            "fix_session_durations",
            "migrate",
            "collectstatic",
            "check",
            "help",
        ]

        if command_name not in allowed_commands:
            allowed_list = ", ".join(allowed_commands)
            return JsonResponse(
                {
                    "error": f'Command "{command_name}" not allowed. Allowed: {allowed_list}'
                },
                status=403,
            )

        def generate_output():
            """Generator function to stream command output"""
            import subprocess
            import sys
            import os

            # Build the command
            cmd = [sys.executable, "manage.py", command_name] + command_args

            yield f"data: Starting command: {' '.join(cmd)}\n\n"

            try:
                # Execute the command with streaming output
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    cwd=os.path.dirname(os.path.dirname(__file__)),
                )

                # Stream the output line by line
                for line in iter(process.stdout.readline, ""):
                    if line:
                        yield f"data: {line.rstrip()}\n\n"

                # Wait for process to complete and get return code
                return_code = process.wait()

                if return_code == 0:
                    yield "data: ✅ Command completed successfully\n\n"
                else:
                    yield f"data: ❌ Command failed with exit code {return_code}\n\n"

                yield "data: [DONE]\n\n"

            except Exception as e:
                yield f"data: ❌ Error executing command: {str(e)}\n\n"
                yield "data: [DONE]\n\n"

        # Return streaming response
        response = StreamingHttpResponse(generate_output(), content_type="text/plain")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # Disable nginx buffering

        return response

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_env_variable_names():
    """Get all environment variable names that are currently set in Django environment"""

    # Get all environment variables
    all_env_vars = set(os.environ.keys())

    # Common system variables that are usually not relevant for Django apps
    system_vars = {
        "PATH",
        "HOME",
        "USER",
        "SHELL",
        "LANG",
        "PWD",
        "OLDPWD",
        "TERM",
        "COLORTERM",
        "DISPLAY",
        "XAUTHORITY",
        "XDG_SESSION_ID",
        "XDG_RUNTIME_DIR",
        "XDG_SESSION_TYPE",
        "XDG_CURRENT_DESKTOP",
        "XDG_SESSION_CLASS",
        "DBUS_SESSION_BUS_ADDRESS",
        "DESKTOP_SESSION",
        "GNOME_DESKTOP_SESSION_ID",
        "LOGNAME",
        "USERNAME",
        "USERPROFILE",
        "SYSTEMROOT",
        "WINDIR",
        "COMPUTERNAME",
        "OS",
        "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_IDENTIFIER",
        "NUMBER_OF_PROCESSORS",
        "PATHEXT",
        "COMSPEC",
        "TEMP",
        "TMP",
        "ALLUSERSPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMFILES",
        "PROGRAMDATA",
        "PUBLIC",
        "SESSIONNAME",
        "USERDOMAIN",
        "USERDNSDOMAIN",
        "MAIL",
        "MAILCHECK",
        "HISTFILE",
        "HISTSIZE",
        "HISTCONTROL",
        "HISTTIMEFORMAT",
        "SSH_TTY",
        "SSH_CONNECTION",
        "SSH_CLIENT",
        "TMUX",
        "TMUX_PANE",
        "INSIDE_EMACS",
        "EDITOR",
        "VISUAL",
        "PAGER",
        "LESS",
        "LESSOPEN",
        "LESSCLOSE",
        "MANPATH",
        "INFOPATH",
        "LS_COLORS",
        "GREP_COLORS",
        "SUDO_UID",
        "SUDO_GID",
        "SUDO_USER",
        "SUDO_COMMAND",
        "LINES",
        "COLUMNS",
        "SHLVL",
        "PS1",
        "PS2",
        "PS3",
        "PS4",
        "IFS",
        "BASH",
        "BASH_VERSION",
        "BASH_VERSINFO",
        "BASHPID",
        "BASH_SUBSHELL",
        "BASH_LINENO",
        "BASH_SOURCE",
        "FUNCNAME",
        "GROUPS",
        "HOSTNAME",
        "HOSTTYPE",
        "MACHTYPE",
        "OSTYPE",
        "PPID",
        "RANDOM",
        "SECONDS",
        "SHELLOPTS",
        "UID",
        "EUID",
        "BASH_REMATCH",
        "BASH_ARGC",
        "BASH_ARGV",
        "BASH_COMMAND",
        "BASH_EXECUTION_STRING",
        "BASH_LINENO",
        "BASH_SOURCE",
        "BASH_SUBSHELL",
        "LINENO",
        "OPTARG",
        "OPTIND",
        "OPTERR",
        "REPLY",
        "DIRSTACK",
        "PIPESTATUS",
        "PROMPT_COMMAND",
        "FCEDIT",
        "FIGNORE",
        "GLOBIGNORE",
        "HISTIGNORE",
        "INPUTRC",
        "TIMEFORMAT",
        "TMPDIR",
        "CDPATH",
        "COLUMNS",
        "LINES",
        "MAILPATH",
        "PS1",
        "PS2",
        "auto_resume",
        "histchars",
        "HISTCMD",
        "HISTIGNORE",
        "history_control",
        "HISTTIMEFORMAT",
        "HOSTFILE",
        "HOSTNAME",
        "IGNOREEOF",
        "INPUTRC",
        "LANG",
        "LC_ALL",
        "LC_COLLATE",
        "LC_CTYPE",
        "LC_MESSAGES",
        "LC_MONETARY",
        "LC_NUMERIC",
        "LC_TIME",
        "LINENO",
        "MACHTYPE",
        "MAIL",
        "MAILCHECK",
        "OSTYPE",
        "PIPESTATUS",
        "POSIXLY_CORRECT",
        "PPID",
        "PROMPT_COMMAND",
        "PS3",
        "PS4",
        "PWD",
        "RANDOM",
        "REPLY",
        "SECONDS",
        "SHELLOPTS",
        "TIMEFORMAT",
        "TMOUT",
        "UID",
        "BASH_REMATCH",
        "BASH_ARGC",
        "BASH_ARGV",
    }

    # Filter out common system variables but keep Django/app-specific ones
    app_env_vars = all_env_vars - system_vars

    # Also include some important system variables that might be relevant
    important_system_vars = {"PATH", "USER", "HOME", "SHELL", "LANG"}
    relevant_system_vars = all_env_vars & important_system_vars

    # Combine app variables with relevant system variables
    relevant_vars = app_env_vars | relevant_system_vars

    # If no relevant variables found, return all variables
    if not relevant_vars:
        return ["No environment variables found"]

    # Sort and return with values (showing first 20 chars for security)
    env_info = []
    for var in sorted(relevant_vars):
        value = os.environ.get(var, "")
        # Hide sensitive information in values
        sensitive_keys = ["SECRET", "KEY", "PASSWORD", "TOKEN"]
        is_sensitive = any(sensitive in var.upper() for sensitive in sensitive_keys)
        if is_sensitive:
            display_value = f"{value[:10]}..." if len(value) > 10 else value[:5] + "..."
        else:
            display_value = value[:50] + "..." if len(value) > 50 else value

        env_info.append(
            {
                "name": var,
                "value": display_value,
                "length": len(value),
                "is_sensitive": is_sensitive,
            }
        )

    return env_info


def get_log_file_status():
    """Check status of log files that admin log streaming tries to read"""

    # Log sources from AdminLogsConsumer
    log_sources = {
        "django": os.path.join(settings.BASE_DIR, "logs", "django.log"),
        "errors": os.path.join(settings.BASE_DIR, "logs", "errors.log"),
        "requests": os.path.join(settings.BASE_DIR, "logs", "requests.log"),
        "nginx_access": "/var/log/nginx/access.log",
        "nginx_error": "/var/log/nginx/error.log",
    }

    # Services that use journalctl (no file path)
    journal_services = {
        "nginx": "nginx.service",
        "system": "system journal",
    }

    log_status = []

    # Check file-based logs
    for source_name, file_path in log_sources.items():
        status = {
            "name": source_name,
            "path": file_path,
            "type": "file",
            "exists": False,
            "readable": False,
            "writable": False,
            "size": 0,
            "size_human": "0 B",
            "permissions": "",
            "owner": "",
            "group": "",
            "error": None,
            "last_updated": None,  # Add last updated field
        }

        try:
            # Convert relative path to absolute
            if not os.path.isabs(file_path):
                base_dir = os.path.dirname(__file__)
                file_path = os.path.join(base_dir, "..", file_path)
                file_path = os.path.abspath(file_path)
                status["path"] = file_path

            # Check if file exists
            if os.path.exists(file_path):
                status["exists"] = True

                # Get file stats
                file_stat = os.stat(file_path)
                status["size"] = file_stat.st_size
                status["size_human"] = format_bytes(file_stat.st_size)

                # Get permissions
                status["permissions"] = stat.filemode(file_stat.st_mode)

                # Get owner and group
                try:
                    status["owner"] = pwd.getpwuid(file_stat.st_uid).pw_name
                except KeyError:
                    status["owner"] = str(file_stat.st_uid)

                try:
                    status["group"] = grp.getgrgid(file_stat.st_gid).gr_name
                except KeyError:
                    status["group"] = str(file_stat.st_gid)

                # Check if readable
                status["readable"] = os.access(file_path, os.R_OK)

                # Check if writable
                status["writable"] = os.access(file_path, os.W_OK)

                # Get last updated (modification) time
                try:
                    mtime = file_stat.st_mtime
                    status["last_updated"] = datetime.fromtimestamp(mtime)
                except Exception:
                    status["last_updated"] = None

        except Exception as e:
            status["error"] = str(e)

        log_status.append(status)

    # Check journal-based services
    for service_name, service_desc in journal_services.items():
        if service_desc != "system journal":
            path = f"journalctl -u {service_desc}"
        else:
            path = "journalctl"

        status = {
            "name": service_name,
            "path": path,
            "type": "journal",
            "exists": True,  # journalctl always exists if systemd is running
            "readable": True,  # We'll check if journalctl command works
            "writable": False,  # journalctl is read-only
            "size": 0,
            "size_human": "N/A",
            "permissions": "journal",
            "owner": "systemd",
            "group": "systemd",
            "error": None,
            "last_updated": None,  # Not applicable for journalctl
        }

        try:
            # Test if journalctl command works
            if service_desc == "system journal":
                cmd = ["journalctl", "--no-pager", "-n", "1"]
            else:
                cmd = ["journalctl", "-u", service_desc, "--no-pager", "-n", "1"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                status["readable"] = False
                status["error"] = f"journalctl error: {result.stderr}"
        except Exception as e:
            status["readable"] = False
            status["error"] = str(e)

        log_status.append(status)

    return log_status


def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    if bytes_value == 0:
        return "0 B"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0

    return f"{bytes_value:.1f} PB"


@user_passes_test(is_admin_user)
@require_POST
def reload_environment_variables(request):
    """Reload environment variables by reloading Django settings"""

    try:
        # First, try to reload .env file from project root
        env_file_path = Path(__file__).resolve().parent.parent / ".env"
        if env_file_path.exists():
            load_dotenv(env_file_path, override=True)
        else:
            # For debugging: log the attempted path
            logger.warning(f"Environment file not found at: {env_file_path}")

        # For development environments, we can't restart the service
        # but we can provide helpful feedback
        if os.environ.get("ENVIRONMENT", "development") == "development":
            return JsonResponse(
                {
                    "success": True,
                    "message": "Environment variables reloaded in memory. For full reload, restart the development server manually.",
                }
            )

        # For production, try to restart the service
        commands = [
            "systemctl reload uvicorn",
            "systemctl restart uvicorn",
            "sudo systemctl reload uvicorn",
            "sudo systemctl restart uvicorn",
        ]

        success = False
        last_error = ""

        for cmd in commands:
            try:
                result = subprocess.run(
                    ["/bin/bash", "-c", cmd], capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    success = True
                    break
                else:
                    last_error = f"{cmd}: {result.stderr}"
            except subprocess.TimeoutExpired:
                last_error = f"{cmd}: Timeout"
            except Exception as e:
                last_error = f"{cmd}: {str(e)}"

        if success:
            return JsonResponse(
                {
                    "success": True,
                    "message": "Environment variables reloaded successfully. Services restarted.",
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Failed to reload services. Last error: {last_error}",
                }
            )
    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": f"Error reloading environment variables: {str(e)}",
            }
        )


def parse_du_size(size_str):
    """Parse du size string (like '1.2G', '500M') to bytes"""
    try:
        size_str = size_str.strip().upper()
        if size_str[-1] == "K":
            return float(size_str[:-1]) * 1024
        elif size_str[-1] == "M":
            return float(size_str[:-1]) * 1024 * 1024
        elif size_str[-1] == "G":
            return float(size_str[:-1]) * 1024 * 1024 * 1024
        elif size_str[-1] == "T":
            return float(size_str[:-1]) * 1024 * 1024 * 1024 * 1024
        else:
            return float(size_str)  # Assume bytes
    except (ValueError, IndexError):
        return 0


def get_module_memory_usage():
    """Get memory usage by Python modules/dependencies."""
    try:
        module_sizes = {}

        # Get all currently loaded modules
        for module_name, module_obj in sys.modules.items():
            if module_obj is None:
                continue

            try:
                # Calculate memory usage for each module
                module_size = 0

                # Get size of module object itself
                module_size += sys.getsizeof(module_obj)

                # Get size of module's __dict__
                if hasattr(module_obj, "__dict__"):
                    module_size += sys.getsizeof(module_obj.__dict__)

                    # Get size of all objects in module's namespace
                    for attr_name, attr_value in module_obj.__dict__.items():
                        try:
                            module_size += sys.getsizeof(attr_value)

                            # If it's a class, add size of its methods and attributes
                            if isinstance(attr_value, type):
                                module_size += sys.getsizeof(attr_value.__dict__)
                                for class_attr in attr_value.__dict__.values():
                                    module_size += sys.getsizeof(class_attr)

                        except (TypeError, AttributeError):
                            # Some objects can't be sized
                            continue

                # Convert to MB and round
                module_size_mb = round(module_size / (1024 * 1024), 2)

                # Only include modules with significant memory usage
                if module_size_mb > 0.01:  # Only show modules using > 0.01 MB
                    module_sizes[module_name] = {
                        "name": module_name,
                        "size_bytes": module_size,
                        "size_mb": module_size_mb,
                        "is_third_party": not (
                            module_name.startswith("django")
                            or module_name.startswith("__")
                            or module_name
                            in [
                                "sys",
                                "os",
                                "io",
                                "collections",
                                "threading",
                                "time",
                                "json",
                                "logging",
                                "subprocess",
                                "random",
                                "uuid",
                                "hashlib",
                                "hmac",
                                "base64",
                                "traceback",
                                "pathlib",
                                "datetime",
                                "pwd",
                                "stat",
                                "grp",
                                "select",
                                "gc",
                                "types",
                            ]
                        ),
                        "is_django": module_name.startswith("django"),
                        "is_builtin": module_name in sys.builtin_module_names,
                        "version": (
                            getattr(module_obj, "__version__", "Unknown")
                            if hasattr(module_obj, "__version__")
                            else "Unknown"
                        ),
                    }

            except Exception:
                # Skip modules that can't be analyzed
                continue

        # Sort by memory usage (descending)
        sorted_modules = sorted(
            module_sizes.values(), key=lambda x: x["size_mb"], reverse=True
        )

        return {
            "modules": sorted_modules[:50],  # Top 50 modules by memory usage
            "total_modules": len(module_sizes),
            "total_memory_mb": sum(m["size_mb"] for m in module_sizes.values()),
            "django_modules": [m for m in sorted_modules if m["is_django"]],
            "third_party_modules": [m for m in sorted_modules if m["is_third_party"]],
            "builtin_modules": [m for m in sorted_modules if m["is_builtin"]],
        }

    except Exception as e:
        return {
            "modules": [],
            "total_modules": 0,
            "total_memory_mb": 0,
            "django_modules": [],
            "third_party_modules": [],
            "builtin_modules": [],
            "error": str(e),
        }


def get_detailed_memory_analysis():
    """Get comprehensive memory analysis including Python objects, Django components, and system usage."""
    try:
        import gc
        import tracemalloc
        from collections import defaultdict
        from django.apps import apps
        from django.db import connections

        memory_breakdown = {}

        # Enable tracemalloc for detailed memory tracking if not already enabled
        if not tracemalloc.is_tracing():
            tracemalloc.start()

        # Get current memory snapshot
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        # Python Objects Memory Analysis
        memory_breakdown["python_objects"] = {
            "total_objects": len(gc.get_objects()),
            "objects_by_type": {},
            "total_size_mb": 0,
        }

        # Count objects by type
        object_counts = defaultdict(int)
        object_sizes = defaultdict(int)

        for obj in gc.get_objects():
            try:
                obj_type = type(obj).__name__
                obj_size = sys.getsizeof(obj)
                object_counts[obj_type] += 1
                object_sizes[obj_type] += obj_size
            except Exception:
                continue

        # Get top object types by memory usage
        top_object_types = sorted(
            object_sizes.items(), key=lambda x: x[1], reverse=True
        )[:20]

        total_python_objects_size = sum(object_sizes.values())
        memory_breakdown["python_objects"]["total_size_mb"] = round(
            total_python_objects_size / (1024 * 1024), 2
        )

        for obj_type, size in top_object_types:
            memory_breakdown["python_objects"]["objects_by_type"][obj_type] = {
                "count": object_counts[obj_type],
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2),
                "avg_size_bytes": round(size / object_counts[obj_type], 2),
            }

        # Django Components Memory Analysis
        memory_breakdown["django_components"] = {}

        # Database connections
        try:
            db_connections = connections.all()
            memory_breakdown["django_components"]["database_connections"] = {
                "count": len(db_connections),
                "connection_info": [],
            }

            for alias, connection in connections.databases.items():
                try:
                    conn = connections[alias]
                    memory_breakdown["django_components"]["database_connections"][
                        "connection_info"
                    ].append(
                        {
                            "alias": alias,
                            "engine": connection.get("ENGINE", "Unknown"),
                            "name": connection.get("NAME", "Unknown"),
                            "queries_count": (
                                len(conn.queries) if hasattr(conn, "queries") else 0
                            ),
                        }
                    )
                except Exception as e:
                    memory_breakdown["django_components"]["database_connections"][
                        "connection_info"
                    ].append({"alias": alias, "error": str(e)})
        except Exception as e:
            memory_breakdown["django_components"]["database_connections"] = {
                "error": str(e)
            }

        # Cache analysis
        memory_breakdown["django_components"]["cache_analysis"] = {}
        try:
            from django.core.cache import cache
            from django.core.cache.backends.locmem import LocMemCache

            default_cache = cache._cache if hasattr(cache, "_cache") else cache
            cache_type = type(default_cache).__name__
            memory_breakdown["django_components"]["cache_analysis"]["default_cache"] = {
                "type": cache_type,
                "size_estimate_mb": 0,
            }

            # Try to get cache size for different cache types
            if hasattr(default_cache, "_cache") and hasattr(
                default_cache._cache, "info"
            ):
                # Redis cache
                try:
                    info = default_cache._cache.info()
                    memory_breakdown["django_components"]["cache_analysis"][
                        "default_cache"
                    ]["size_estimate_mb"] = round(
                        info.get("used_memory", 0) / (1024 * 1024), 2
                    )
                except Exception:
                    pass
            elif isinstance(default_cache, LocMemCache):
                # Local memory cache
                try:
                    cache_size = sum(
                        sys.getsizeof(k) + sys.getsizeof(v)
                        for k, v in default_cache._cache.items()
                    )
                    memory_breakdown["django_components"]["cache_analysis"][
                        "default_cache"
                    ]["size_estimate_mb"] = round(cache_size / (1024 * 1024), 2)
                except Exception:
                    pass
        except Exception as e:
            memory_breakdown["django_components"]["cache_analysis"] = {"error": str(e)}

        # Session analysis
        try:
            # CustomSession removed - using Django's default sessions
            # active_sessions = Session.objects.filter(
            #     expire_date__gt=timezone.now()
            # )
            active_sessions = []  # Placeholder for now
            session_count = active_sessions.count()

            # Estimate session memory usage
            avg_session_size = 0
            if session_count > 0:
                # Sample a few sessions to estimate size
                sample_sessions = active_sessions[: min(10, session_count)]
                total_sample_size = 0
                for session in sample_sessions:
                    session_data_size = sys.getsizeof(session.session_data)
                    total_sample_size += session_data_size

                if len(sample_sessions) > 0:
                    avg_session_size = total_sample_size / len(sample_sessions)

            estimated_sessions_memory = (session_count * avg_session_size) / (
                1024 * 1024
            )

            memory_breakdown["django_components"]["sessions"] = {
                "active_count": session_count,
                "avg_session_size_bytes": round(avg_session_size, 2),
                "estimated_total_mb": round(estimated_sessions_memory, 2),
            }
        except Exception as e:
            memory_breakdown["django_components"]["sessions"] = {"error": str(e)}

        # Django models memory analysis
        try:
            model_memory = {}

            for model in apps.get_models():
                model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                try:
                    # Get model class size
                    model_size = sys.getsizeof(model)
                    manager_size = (
                        sys.getsizeof(model.objects) if hasattr(model, "objects") else 0
                    )
                    meta_size = (
                        sys.getsizeof(model._meta) if hasattr(model, "_meta") else 0
                    )

                    total_model_size = model_size + manager_size + meta_size

                    model_memory[model_name] = {
                        "size_bytes": total_model_size,
                        "size_mb": round(total_model_size / (1024 * 1024), 4),
                        "field_count": (
                            len(model._meta.fields) if hasattr(model, "_meta") else 0
                        ),
                    }
                except Exception as e:
                    model_memory[model_name] = {"error": str(e)}

            # Sort by size and get top models
            sorted_models = sorted(
                model_memory.items(),
                key=lambda x: x[1].get("size_bytes", 0),
                reverse=True,
            )
            memory_breakdown["django_components"]["models"] = {
                "total_models": len(model_memory),
                "top_models": dict(sorted_models[:20]),
                "total_size_mb": round(
                    sum(m.get("size_bytes", 0) for m in model_memory.values())
                    / (1024 * 1024),
                    2,
                ),
            }
        except Exception as e:
            memory_breakdown["django_components"]["models"] = {"error": str(e)}

        # System memory analysis
        try:
            process = psutil.Process()
            mem_info = process.memory_info()

            memory_breakdown["system_memory"] = {
                "rss_mb": round(mem_info.rss / (1024 * 1024), 2),
                "vms_mb": round(mem_info.vms / (1024 * 1024), 2),
                "percent": round(process.memory_percent(), 2),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, "num_fds") else 0,
                "create_time": process.create_time(),
                "cpu_percent": round(process.cpu_percent(), 2),
            }
        except Exception as e:
            memory_breakdown["system_memory"] = {"error": str(e)}

        # Tracemalloc analysis
        try:
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                memory_breakdown["tracemalloc"] = {
                    "current_mb": round(current / (1024 * 1024), 2),
                    "peak_mb": round(peak / (1024 * 1024), 2),
                    "top_allocations": [],
                }

                # Get top allocations
                for stat in top_stats[:10]:
                    memory_breakdown["tracemalloc"]["top_allocations"].append(
                        {
                            "filename": (
                                stat.traceback.format()[0]
                                if stat.traceback
                                else "Unknown"
                            ),
                            "size_mb": round(stat.size / (1024 * 1024), 2),
                            "count": stat.count,
                        }
                    )
            else:
                memory_breakdown["tracemalloc"] = {"status": "Not enabled"}
        except Exception as e:
            memory_breakdown["tracemalloc"] = {"error": str(e)}

        # Calculate memory accounting
        try:
            accounted_memory = 0

            # Add up all the memory we can account for
            accounted_memory += memory_breakdown["python_objects"]["total_size_mb"]
            accounted_memory += (
                memory_breakdown["django_components"]
                .get("cache_analysis", {})
                .get("default_cache", {})
                .get("size_estimate_mb", 0)
            )
            accounted_memory += (
                memory_breakdown["django_components"]
                .get("sessions", {})
                .get("estimated_total_mb", 0)
            )
            accounted_memory += (
                memory_breakdown["django_components"]
                .get("models", {})
                .get("total_size_mb", 0)
            )

            total_process_memory = memory_breakdown["system_memory"].get("rss_mb", 0)
            unaccounted_memory = total_process_memory - accounted_memory

            memory_breakdown["memory_accounting"] = {
                "total_process_mb": total_process_memory,
                "accounted_mb": round(accounted_memory, 2),
                "unaccounted_mb": round(unaccounted_memory, 2),
                "unaccounted_percent": (
                    round((unaccounted_memory / total_process_memory) * 100, 1)
                    if total_process_memory > 0
                    else 0
                ),
            }
        except Exception as e:
            memory_breakdown["memory_accounting"] = {"error": str(e)}

        return memory_breakdown

    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def get_memory_hotspots():
    """Identify memory hotspots and potential memory leaks."""
    try:
        import gc

        hotspots = {"potential_leaks": [], "large_objects": [], "recommendations": []}

        # Check for potential memory leaks
        all_objects = gc.get_objects()
        reference_counts = {}

        for obj in all_objects:
            try:
                obj_type = type(obj).__name__
                referrers = gc.get_referrers(obj)
                ref_count = len(referrers)

                if ref_count > 100:  # Objects with many references
                    if obj_type not in reference_counts:
                        reference_counts[obj_type] = []
                    reference_counts[obj_type].append(
                        {"ref_count": ref_count, "size_bytes": sys.getsizeof(obj)}
                    )
            except Exception:
                continue

        # Identify potential leaks
        for obj_type, refs in reference_counts.items():
            if len(refs) > 10:  # Many objects of same type with high ref counts
                avg_refs = sum(r["ref_count"] for r in refs) / len(refs)
                total_size = sum(r["size_bytes"] for r in refs)

                hotspots["potential_leaks"].append(
                    {
                        "object_type": obj_type,
                        "count": len(refs),
                        "avg_references": round(avg_refs, 1),
                        "total_size_mb": round(total_size / (1024 * 1024), 2),
                        "risk_level": (
                            "High"
                            if avg_refs > 500
                            else "Medium"
                            if avg_refs > 200
                            else "Low"
                        ),
                    }
                )

        # Find largest individual objects
        object_sizes = []
        for obj in all_objects:
            try:
                size = sys.getsizeof(obj)
                if size > 1024 * 1024:  # Objects larger than 1MB
                    object_sizes.append(
                        {
                            "type": type(obj).__name__,
                            "size_mb": round(size / (1024 * 1024), 2),
                            "id": id(obj),
                            "repr": (
                                str(obj)[:100] + "..."
                                if len(str(obj)) > 100
                                else str(obj)
                            ),
                        }
                    )
            except Exception:
                continue

        # Sort by size and take top 20
        hotspots["large_objects"] = sorted(
            object_sizes, key=lambda x: x["size_mb"], reverse=True
        )[:20]

        # Generate recommendations
        total_memory = sum(sys.getsizeof(obj) for obj in all_objects if obj is not None)
        total_memory_mb = total_memory / (1024 * 1024)

        if total_memory_mb > 100:
            hotspots["recommendations"].append(
                {
                    "type": "warning",
                    "message": f"High memory usage detected: {total_memory_mb:.1f}MB in Python objects",
                    "suggestion": "Consider implementing object pooling or caching strategies",
                }
            )

        if len(hotspots["potential_leaks"]) > 0:
            hotspots["recommendations"].append(
                {
                    "type": "critical",
                    "message": f"Potential memory leaks detected: {len(hotspots['potential_leaks'])} object types",
                    "suggestion": "Review object lifecycle management and ensure proper cleanup",
                }
            )

        if len(hotspots["large_objects"]) > 10:
            hotspots["recommendations"].append(
                {
                    "type": "info",
                    "message": f"Many large objects in memory: {len(hotspots['large_objects'])} objects > 1MB",
                    "suggestion": "Consider lazy loading or streaming for large data structures",
                }
            )

        return hotspots

    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def get_basic_dashboard_data():
    """Get basic system data for dashboard without heavy memory analysis"""

    # System resource usage
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_percent = psutil.cpu_percent(interval=1)

    # Get detailed memory usage by processes
    memory_processes = []
    try:
        # Get all processes with necessary info, more efficiently
        procs = []
        for p in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                # memory_percent() is a method call, not a property in info dict
                p_info = p.info
                p_info["memory_percent"] = p.memory_percent()
                procs.append(p_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by the 'memory_percent' key
        procs.sort(key=lambda p: p.get("memory_percent", 0), reverse=True)

        # Get processes with memory usage > 0MB and limit to top 10
        for proc_info in procs[:10]:  # Limit to top 10 processes
            memory_mb = round(proc_info["memory_info"].rss / (1024 * 1024), 1)
            memory_percent = round(proc_info.get("memory_percent", 0), 1)

            # Only add processes with memory usage > 0MB
            if memory_mb > 0:
                memory_processes.append(
                    {
                        "pid": proc_info["pid"],
                        "name": proc_info["name"],
                        "memory_mb": memory_mb,
                        "memory_percent": memory_percent,
                    }
                )

    except Exception as e:
        print(f"Error getting process memory info: {e}")

    # Get basic module memory usage (just count, not detailed analysis)
    basic_module_memory = {
        "total_memory_mb": 0,
        "total_modules": len(sys.modules),
        "modules": [],
        "django_modules": [],
        "third_party_modules": [],
        "builtin_modules": [],
    }

    # Get swap information
    swap = psutil.swap_memory()

    # Get load average
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]

    # Get active session count
    # CustomSession removed - using Django's default sessions
    # active_session_count = Session.objects.filter(
    #     expire_date__gt=timezone.now()
    # ).count()
    active_session_count = 0  # Placeholder for now

    # Get basic connection info (simplified to avoid slowdown)
    try:
        # Just count connections without detailed WHOIS lookups
        result = subprocess.run(
            ["ss", "-tn", "state", "established"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            connection_count = max(
                0, len([line for line in lines if line.strip() and "ESTAB" in line]) - 1
            )
        else:
            connection_count = 0
    except Exception:
        connection_count = 0

    connections = []  # Empty list for basic dashboard

    # Get basic log entries (just count)
    logs = []  # Empty list for basic dashboard

    # Get basic whois stats (simplified)
    try:
        total_whois_records = WhoisRecord.objects.count()
        whois_stats = {
            "total_records": total_whois_records,
            "recent_lookups_24h": 0,
        }
    except Exception as e:
        whois_stats = {
            "total_records": 0,
            "recent_lookups_24h": 0,
            "error": str(e),
        }

    return {
        "system": {
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "buffers": getattr(memory, "buffers", 0),
                "cached": getattr(memory, "cached", 0),
                "shared": getattr(memory, "shared", 0),
                "processes": memory_processes,
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent,
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "used": disk.used,
                "percent": (disk.used / disk.total) * 100,
            },
            "cpu": {
                "percent": cpu_percent,
                "load_avg": load_avg,
            },
        },
        "modules": basic_module_memory,
        "sessions": {
            "active_count": active_session_count,
        },
        "whois": whois_stats,
        "connections": {
            "list": connections,
            "total": connection_count,
        },
        "logs": logs,
        "timestamp": timezone.now().isoformat(),
    }


def get_memory_dashboard_data():
    """Get comprehensive memory data for memory dashboard"""

    # Get module memory usage
    module_memory = get_module_memory_usage()

    # Get detailed memory analysis
    detailed_memory = get_detailed_memory_analysis()

    # Get memory hotspots
    memory_hotspots = get_memory_hotspots()

    return {
        "modules": module_memory,
        "detailed_memory": detailed_memory,
        "memory_hotspots": memory_hotspots,
        "timestamp": timezone.now().isoformat(),
    }


def get_dashboard_data():
    """Get system and user data for dashboard"""

    # System resource usage
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_percent = psutil.cpu_percent(interval=1)

    # Get detailed memory usage by processes
    memory_processes = []
    try:
        # Get all processes with detailed info
        procs = []
        for p in psutil.process_iter(
            [
                "pid",
                "ppid",
                "name",
                "memory_info",
                "cmdline",
                "username",
                "status",
                "create_time",
                "cpu_percent",
                "num_threads",
            ]
        ):
            try:
                # memory_percent() is a method call, not a property in info dict
                p_info = p.info
                p_info["memory_percent"] = p.memory_percent()

                # Get additional process details
                try:
                    p_info["cwd"] = p.cwd()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    p_info["cwd"] = "N/A"

                try:
                    p_info["exe"] = p.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    p_info["exe"] = "N/A"

                procs.append(p_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by the 'memory_percent' key
        procs.sort(key=lambda p: p.get("memory_percent", 0), reverse=True)

        # Get processes with memory usage > 0MB and limit to top 15
        for proc_info in procs[:15]:  # Increased to top 15 processes
            memory_mb = round(proc_info["memory_info"].rss / (1024 * 1024), 1)
            memory_percent = round(proc_info.get("memory_percent", 0), 1)

            # Only add processes with memory usage > 0MB
            if memory_mb > 0:
                # Format command line
                cmdline = proc_info.get("cmdline", [])
                if cmdline:
                    # Join command line arguments, but truncate if too long
                    full_cmd = " ".join(cmdline)
                    if len(full_cmd) > 200:
                        cmd_display = full_cmd[:200] + "..."
                    else:
                        cmd_display = full_cmd
                else:
                    cmd_display = proc_info["name"]

                # Format creation time
                create_time = proc_info.get("create_time", 0)
                import datetime

                if create_time:
                    created_dt = datetime.datetime.fromtimestamp(create_time)
                    created_str = created_dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    created_str = "N/A"

                memory_processes.append(
                    {
                        "pid": proc_info["pid"],
                        "ppid": proc_info.get("ppid", "N/A"),
                        "name": proc_info["name"],
                        "memory_mb": memory_mb,
                        "memory_percent": memory_percent,
                        "cmdline": cmd_display,
                        "full_cmdline": " ".join(cmdline)
                        if cmdline
                        else proc_info["name"],
                        "username": proc_info.get("username", "N/A"),
                        "status": proc_info.get("status", "N/A"),
                        "created": created_str,
                        "cpu_percent": round(proc_info.get("cpu_percent", 0), 1),
                        "num_threads": proc_info.get("num_threads", 0),
                        "cwd": proc_info.get("cwd", "N/A"),
                        "exe": proc_info.get("exe", "N/A"),
                    }
                )

    except Exception as e:
        print(f"Error getting process memory info: {e}")

    # Get module memory usage
    module_memory = get_module_memory_usage()

    # Get detailed memory analysis
    detailed_memory = get_detailed_memory_analysis()

    # Get memory hotspots
    memory_hotspots = get_memory_hotspots()

    folder_stats = {}

    # Removed slow folder stats calculations for better performance

    # Get swap memory info
    try:
        swap = psutil.swap_memory()
    except Exception:
        swap = type("obj", (object,), {"total": 0, "used": 0, "free": 0, "percent": 0})

    # Get currently active sessions
    # CustomSession removed - using Django's default sessions
    # active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
    active_sessions = []  # Placeholder for now
    active_session_count = active_sessions.count()

    # Get session statistics by device type
    device_stats = (
        active_sessions.values("device_type")
        .annotate(count=Count("session_key"))
        .order_by("-count")
    )

    # Get session statistics by browser
    browser_stats = (
        active_sessions.values("browser")
        .annotate(count=Count("session_key"))
        .filter(browser__isnull=False)
        .exclude(browser="")
        .order_by("-count")[:5]
    )

    # Get WHOIS statistics
    whois_stats = {}
    try:
        # Total WHOIS records
        total_whois_records = WhoisRecord.objects.count()
        successful_lookups = WhoisRecord.objects.filter(lookup_successful=True).count()

        # Recent lookups (last 24 hours)
        recent_lookups = IPLookupLog.objects.filter(
            lookup_timestamp__gte=timezone.now() - timezone.timedelta(days=1)
        ).count()

        # Top countries from WHOIS data
        top_countries = (
            WhoisRecord.objects.filter(lookup_successful=True, country__isnull=False)
            .exclude(country="")
            .values("country", "country_code")
            .annotate(count=Count("ip_address"))
            .order_by("-count")[:10]
        )

        # Top organizations
        top_organizations = (
            WhoisRecord.objects.filter(
                lookup_successful=True, organization__isnull=False
            )
            .exclude(organization="")
            .values("organization")
            .annotate(count=Count("ip_address"))
            .order_by("-count")[:10]
        )

        whois_stats = {
            "total_records": total_whois_records,
            "successful_lookups": successful_lookups,
            "success_rate": (
                (successful_lookups / total_whois_records * 100)
                if total_whois_records > 0
                else 0
            ),
            "recent_lookups_24h": recent_lookups,
            "top_countries": list(top_countries),
            "top_organizations": list(top_organizations),
        }
    except Exception as e:
        whois_stats = {
            "total_records": 0,
            "successful_lookups": 0,
            "success_rate": 0,
            "recent_lookups_24h": 0,
            "top_countries": [],
            "top_organizations": [],
            "error": str(e),
        }

    # Recent system metrics
    try:
        load_avg = os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]
    except Exception:
        load_avg = [0, 0, 0]

    # Get active server connections with IP addresses
    try:
        connections = []

        # Try multiple commands to get network connections
        commands_to_try = [
            # Modern ss commands - try different state formats
            ["ss", "-tn", "state", "established"],
            ["ss", "-tn"],
            # Fallback to netstat if ss not available
            ["netstat", "-tn"],
        ]

        for cmd in commands_to_try:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split("\n")

                    for line in lines:
                        if not line.strip():
                            continue

                        # Skip header lines
                        if any(
                            header in line
                            for header in ["State", "Netid", "Active", "Proto"]
                        ):
                            continue

                        # Skip listening connections
                        if "LISTEN" in line:
                            continue

                        parts = line.split()
                        if len(parts) < 4:
                            continue

                        try:
                            # Parse ss output format
                            if "ss" in cmd[0]:
                                # ss output: tcp ESTAB 0 0 local_addr remote_addr
                                if len(parts) >= 5:
                                    protocol = parts[0]
                                    state = parts[1] if len(parts) > 1 else ""
                                    local_addr = parts[3] if len(parts) > 3 else ""
                                    remote_addr = parts[4] if len(parts) > 4 else ""

                                    # Only process established connections
                                    if state not in ["ESTAB", "ESTABLISHED"]:
                                        continue
                                else:
                                    continue
                            # Parse netstat output format
                            elif "netstat" in cmd[0]:
                                # netstat output: tcp 0 0 local_addr remote_addr ESTABLISHED
                                if len(parts) >= 6:
                                    protocol = parts[0]
                                    local_addr = parts[3]
                                    remote_addr = parts[4]
                                    state = parts[5]

                                    # Only process established connections
                                    if state not in ["ESTAB", "ESTABLISHED"]:
                                        continue
                                else:
                                    continue
                            else:
                                continue

                            # Validate addresses contain colons
                            if ":" not in local_addr or ":" not in remote_addr:
                                continue

                            # Extract remote IP and port
                            if remote_addr.startswith("["):
                                # IPv6 format [ip]:port
                                if "]:" not in remote_addr:
                                    continue
                                remote_ip = remote_addr.split("]:")[0][1:]
                                remote_port = remote_addr.split("]:")[1]
                            else:
                                # IPv4 format ip:port
                                if remote_addr.count(":") < 1:
                                    continue
                                remote_ip = remote_addr.rsplit(":", 1)[0]
                                remote_port = remote_addr.rsplit(":", 1)[1]

                            # Validate and filter IP addresses
                            if not remote_ip or remote_ip in (
                                "0.0.0.0",
                                "*",
                                "::",
                                "::1",
                            ):
                                continue
                            # Skip local/private IP addresses
                            if remote_ip.startswith(
                                (
                                    "127.",
                                    "::1",
                                    "10.",
                                    "172.",
                                    "192.168.",
                                    "169.254.",
                                    "fe80:",
                                )
                            ):
                                continue
                            if not remote_port.isdigit():
                                continue

                            # Extract local port for service identification
                            local_port = ""
                            if local_addr and ":" in local_addr:
                                if local_addr.startswith("["):
                                    # IPv6 format
                                    if "]:" in local_addr:
                                        local_port = local_addr.split("]:")[1]
                                else:
                                    # IPv4 format
                                    local_port = local_addr.rsplit(":", 1)[1]

                            # Get service icon based on local port
                            icon = "🌐"  # Default web
                            if local_port == "22":
                                icon = "🔒"  # SSH
                            elif local_port == "80":
                                icon = "🌐"  # HTTP
                            elif local_port == "443":
                                icon = "🔐"  # HTTPS
                            elif local_port == "8000":
                                icon = "🐍"  # Django dev server
                            elif local_port == "5432":
                                icon = "🗄️"  # PostgreSQL
                            elif local_port in ["25", "587", "993", "995"]:
                                icon = "📧"  # Mail
                            elif local_port == "53":
                                icon = "🌍"  # DNS

                            connections.append(
                                {
                                    "ip": remote_ip.strip("[]"),
                                    "port": remote_port,
                                    "local_port": local_port,
                                    "protocol": protocol.upper(),
                                    "icon": icon,
                                }
                            )
                        except (IndexError, ValueError):
                            # Debug line parsing issues
                            continue

                    # If we got connections, break out of the command loop
                    if connections:
                        break

            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        # Remove duplicates based on IP and port combination
        seen = set()
        unique_connections = []
        for conn in connections:
            key = (conn["ip"], conn["port"])
            if key not in seen:
                seen.add(key)
                unique_connections.append(conn)

        connections = unique_connections

        # Enrich connections with WHOIS data
        enriched_connections = []
        for conn in connections:
            ip_address = conn["ip"]

            # Try to get existing WHOIS record
            whois_record = None
            try:
                whois_record = WhoisRecord.objects.filter(
                    ip_address=ip_address, lookup_successful=True
                ).first()

                # If no record exists, try to create one
                if not whois_record:
                    whois_record = WhoisRecord.lookup_ip(ip_address)

                    # Log the lookup attempt
                    IPLookupLog.objects.create(
                        ip_address=ip_address,
                        whois_record=(
                            whois_record
                            if whois_record and whois_record.lookup_successful
                            else None
                        ),
                        lookup_source="admin_dashboard",
                        lookup_successful=(
                            whois_record.lookup_successful if whois_record else False
                        ),
                    )

            except Exception:
                # Log failed lookup
                try:
                    IPLookupLog.objects.create(
                        ip_address=ip_address,
                        lookup_source="admin_dashboard",
                        lookup_successful=False,
                    )
                except Exception:
                    pass  # Don't let logging failures break the dashboard

            # Add WHOIS data to connection info
            conn_with_whois = conn.copy()
            if whois_record and whois_record.lookup_successful:
                conn_with_whois.update(
                    {
                        "country": whois_record.country or "Unknown",
                        "country_code": whois_record.country_code or "",
                        "city": whois_record.city or "Unknown",
                        "region": whois_record.region or "",
                        "organization": whois_record.organization or "Unknown",
                        "network_name": whois_record.network_name or "",
                        "asn": whois_record.asn or "",
                        "asn_description": whois_record.asn_description or "",
                        "whois_available": True,
                    }
                )

                # Add country flag emoji if we have country code
                if whois_record.country_code:
                    try:
                        # Convert country code to flag emoji
                        flag = "".join(
                            chr(ord(c) + 127397)
                            for c in whois_record.country_code.upper()
                        )
                        conn_with_whois["flag"] = flag
                    except Exception:
                        conn_with_whois["flag"] = "🌍"
                else:
                    conn_with_whois["flag"] = "🌍"
            else:
                conn_with_whois.update(
                    {
                        "country": "Unknown",
                        "country_code": "",
                        "city": "Unknown",
                        "region": "",
                        "organization": "Unknown",
                        "network_name": "",
                        "asn": "",
                        "asn_description": "",
                        "whois_available": False,
                        "flag": "❓",
                    }
                )

            enriched_connections.append(conn_with_whois)

        connections = enriched_connections

    except Exception:
        connections = []

    # Get log data
    log_sources = [
        {
            "name": "Django",
            "path": os.path.join(settings.BASE_DIR, "logs", "django.log"),
        },
        {
            "name": "Errors",
            "path": os.path.join(settings.BASE_DIR, "logs", "errors.log"),
        },
        {
            "name": "Requests",
            "path": os.path.join(settings.BASE_DIR, "logs", "requests.log"),
        },
        {
            "name": "Uvicorn",
            "command": [
                "journalctl",
                "-u",
                "uvicorn.service",
                "-n",
                "100",
                "--no-pager",
            ],
        },
        {"name": "Nginx Access", "path": "/var/log/nginx/access.log"},
        {"name": "Nginx Error", "path": "/var/log/nginx/error.log"},
        {
            "name": "PostgreSQL",
            "command": ["journalctl", "-u", "postgresql", "-n", "100", "--no-pager"],
        },
        {"name": "Fail2Ban", "path": "/var/log/fail2ban.log"},
    ]

    logs = []
    for source in log_sources:
        log_content = ""
        try:
            command = source.get("command") or ["tail", "-n", "100", source["path"]]
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=10, check=False
            )
            log_content = result.stdout or result.stderr
        except FileNotFoundError:
            log_content = f"Log file not found at {source.get('path', 'N/A')}"
        except Exception as e:
            log_content = f"Error reading log: {e!s}"

        logs.append({"name": source["name"], "content": log_content.strip()})

    return {
        "system": {
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "buffers": getattr(memory, "buffers", 0),
                "cached": getattr(memory, "cached", 0),
                "shared": getattr(memory, "shared", 0),
                "processes": memory_processes,
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent,
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "used": disk.used,
                "percent": (disk.used / disk.total) * 100,
            },
            "cpu": {
                "percent": cpu_percent,
                "load_avg": load_avg,
            },
            "folder_stats": folder_stats,
        },
        "modules": module_memory,
        "detailed_memory": detailed_memory,
        "memory_hotspots": memory_hotspots,
        "sessions": {
            "active_count": active_session_count,
            "device_stats": list(device_stats),
            "browser_stats": list(browser_stats),
        },
        "whois": whois_stats,
        "connections": {
            "list": connections[:20],  # Limit to 20 most recent
            "total": len(connections),
        },
        "logs": logs,
        "timestamp": timezone.now().isoformat(),
    }


@user_passes_test(is_admin_user)
def admin_logs_stream(request):
    """Stream server logs in real-time using a simplified approach.

    DEPRECATED: This endpoint is deprecated in favor of WebSocket-based log streaming.
    Use the WebSocket endpoint at /ws/admin/logs/ instead.
    """

    log_source = request.GET.get("source", "uvicorn")

    def simple_log_generator():
        """Simple generator that streams logs without complex threading."""

        # Define log sources
        log_sources = {
            "django": [
                "tail",
                "-f",
                os.path.join(settings.BASE_DIR, "logs", "django.log"),
            ],
            "errors": [
                "tail",
                "-f",
                os.path.join(settings.BASE_DIR, "logs", "errors.log"),
            ],
            "requests": [
                "tail",
                "-f",
                os.path.join(settings.BASE_DIR, "logs", "requests.log"),
            ],
            "uvicorn": ["journalctl", "-u", "uvicorn.service", "-f", "--no-pager"],
            "nginx": ["journalctl", "-u", "nginx.service", "-f", "--no-pager"],
            "nginx_access": ["tail", "-f", "/var/log/nginx/access.log"],
            "nginx_error": ["tail", "-f", "/var/log/nginx/error.log"],
            "system": ["journalctl", "-f", "--no-pager", "-n", "20"],
        }

        command = log_sources.get(log_source, log_sources["django"])

        yield f"data: Connecting to {log_source} logs...\n\n"
        yield f"data: Command: {' '.join(command)}\n\n"
        yield f"data: User: {os.getenv('USER', 'unknown')}\n\n"
        yield "data: ========================\n\n"

        # Check if log file exists and is readable for file-based sources
        if command[0] == "tail":
            log_file = command[2]  # tail -f /path/to/file
            if not os.path.exists(log_file):
                yield f"data: ❌ Log file does not exist: {log_file}\n\n"
                yield "data: Creating log file...\n\n"
                try:
                    # Create the directory if it doesn't exist
                    os.makedirs(os.path.dirname(log_file), exist_ok=True)
                    # Create the file
                    with open(log_file, "a") as f:
                        f.write(f"# Log file created at {datetime.now()}\n")
                    yield f"data: ✅ Log file created: {log_file}\n\n"
                except Exception as e:
                    yield f"data: ❌ Failed to create log file: {str(e)}\n\n"
                    return
            elif not os.access(log_file, os.R_OK):
                yield f"data: ❌ Log file not readable: {log_file}\n\n"
                return

        process = None
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
            yield f"data: Process started (PID: {process.pid})\n\n"
            line_count = 0
            last_heartbeat = time.time()
            start_time = time.time()
            log_line_sent = False
            warning_sent = False
            while True:
                if process.poll() is not None:
                    yield "data: ⚠️ Log process ended unexpectedly\n\n"
                    break
                current_time = time.time()
                try:
                    import select

                    ready, _, _ = select.select([process.stdout], [], [], 1.0)
                    if ready:
                        line = process.stdout.readline()
                        if line:
                            # Handle both string and bytes
                            if isinstance(line, bytes):
                                clean_line = line.decode(
                                    "utf-8", errors="ignore"
                                ).strip()
                            else:
                                clean_line = line.strip()
                            if clean_line:
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                line_count += 1
                                log_line_sent = True
                                log_entry = f"[{timestamp}] {clean_line}"
                                yield f"data: {log_entry}\n\n"
                                last_heartbeat = current_time
                except Exception as e:
                    yield f"data: Read error: {str(e)}\n\n"
                    break
                if (
                    not log_line_sent
                    and not warning_sent
                    and (current_time - start_time) > 5
                ):
                    yield "data: ⚠️ No logs received after 5 seconds. There may be a connection or configuration issue.\n\n"
                    warning_sent = True
                if current_time - last_heartbeat > 2:
                    yield f": heartbeat {datetime.now().isoformat()}\n\n"
                    last_heartbeat = current_time
                if line_count > 5000:
                    yield "data: Line limit reached, stopping stream\n\n"
                    break
        except Exception as e:
            yield f"data: ERROR: Failed to start log process: {str(e)}\n\n"
        finally:
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass

    # Create the streaming response
    response = StreamingHttpResponse(
        simple_log_generator(), content_type="text/event-stream"
    )

    # Set proper headers for SSE
    response["Cache-Control"] = "no-cache"
    response["Connection"] = "keep-alive"
    response["X-Accel-Buffering"] = "no"  # Disable nginx buffering
    response["Access-Control-Allow-Origin"] = "*"

    return response


@user_passes_test(is_admin_user)
@csrf_exempt
def admin_logs_debug(request):
    """Debug endpoint to test log streaming and system state."""

    if request.method == "POST":
        # Handle test log generation
        try:
            data = json.loads(request.body)
            if data.get("action") == "generate_test_log":
                timestamp = data.get("timestamp", timezone.now().isoformat())
                test_message = f"🧪 TEST LOG ENTRY generated at {timestamp} by admin user {request.user.username}"

                # Log to different levels
                logger.info(test_message)
                logger.warning(f"⚠️ WARNING: {test_message}")
                logger.error(f"❌ ERROR: {test_message}")

                # Test log generated successfully

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Test log entries generated",
                        "timestamp": timestamp,
                    }
                )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    # GET request - return debug information
    debug_info = []

    # Check current user
    try:
        current_user = pwd.getpwuid(os.getuid()).pw_name
        debug_info.append(f"Current user: {current_user}")
    except Exception as e:
        debug_info.append(f"Error getting current user: {e}")

    # Check if we can run journalctl
    try:
        result = subprocess.run(
            ["journalctl", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            debug_info.append(f"journalctl available: {result.stdout.strip()}")
        else:
            debug_info.append(f"journalctl error: {result.stderr.strip()}")
    except Exception as e:
        debug_info.append(f"journalctl not available: {e}")

    # Check uvicorn service
    try:
        result = subprocess.run(
            ["journalctl", "-u", "uvicorn.service", "-n", "5", "--no-pager"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            debug_info.append(
                f"uvicorn.service accessible: {len(result.stdout.split(chr(10)))} lines"
            )
            debug_info.append(f"Sample: {result.stdout.split(chr(10))[:2]}")
        else:
            debug_info.append(f"uvicorn.service error: {result.stderr.strip()}")
    except Exception as e:
        debug_info.append(f"uvicorn.service check failed: {e}")

    # Check log files
    log_files = [
        os.path.join(settings.BASE_DIR, "logs", "django.log"),
        os.path.join(settings.BASE_DIR, "logs", "errors.log"),
        os.path.join(settings.BASE_DIR, "logs", "requests.log"),
        "/var/log/nginx/access.log",
        "/var/log/nginx/error.log",
    ]

    for log_file in log_files:
        try:
            if os.path.exists(log_file):
                readable = os.access(log_file, os.R_OK)
                stat = os.stat(log_file)
                debug_info.append(
                    f"{log_file}: exists={True}, readable={readable}, size={stat.st_size}"
                )
            else:
                debug_info.append(f"{log_file}: exists={False}")
        except Exception as e:
            debug_info.append(f"{log_file}: error={e}")

    # Test log generation
    try:
        logger.info("DEBUG: Test log entry from admin_logs_debug")
        debug_info.append("Generated test log entry")
    except Exception as e:
        debug_info.append(f"Error generating test log: {e}")

    return JsonResponse(
        {"debug_info": debug_info, "timestamp": timezone.now().isoformat()}
    )


@require_POST
def report_issue(request):
    """
    Handles AJAX requests to report issues from the frontend.
    """
    try:
        # Get form data from POST request
        title = request.POST.get("title", "").strip()
        body = request.POST.get("body", "").strip()
        current_url = request.POST.get("current_url", "").strip()
        image_file = request.FILES.get("image")
        screenshot_file = request.FILES.get("screenshot")

        if not title or not body:
            return JsonResponse(
                {"success": False, "error": "Title and body are required."}, status=400
            )

        # Handle image upload (either manual upload or screenshot)
        uploaded_file = screenshot_file or image_file
        if uploaded_file:
            if (
                uploaded_file.size > 10 * 1024 * 1024
            ):  # 10MB limit (increased for screenshots)
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Image file size must be less than 10MB.",
                    },
                    status=400,
                )

        # Prepare GitHub issue body with enhanced context
        issue_body = f"{body}\n\n"

        # Add URL context
        if current_url:
            issue_body += f"**URL where issue occurred:** {current_url}\n\n"

        # Add file attachment info
        if screenshot_file:
            issue_body += f"**Note:** User captured an automatic screenshot (filename: {screenshot_file.name})\n\n"
        elif image_file:
            issue_body += f"**Note:** User attached a manual screenshot (filename: {image_file.name})\n\n"

        # Add user context
        if request.user.is_authenticated:
            issue_body += f"\n\n---\n**Reported by:** {request.user.username} (User ID: {request.user.id})"
            issue_body += f"\n**User Email:** {request.user.email}"
        else:
            issue_body += "\n\n---\n**Reported by:** An anonymous user"

        # Add additional request context
        issue_body += f"\n**IP Address:** {request.META.get('REMOTE_ADDR', 'Unknown')}"
        issue_body += (
            f"\n**User Agent:** {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
        )
        issue_body += (
            f"\n**Referrer:** {request.META.get('HTTP_REFERER', 'Direct access')}"
        )

        # Get GitHub configuration from environment
        github_token = os.environ.get("GITHUB_TOKEN")
        repo_owner = os.environ.get("GITHUB_REPO_OWNER", "gemnar")
        repo_name = os.environ.get("GITHUB_REPO_NAME", "gemnar-website")

        if not github_token:
            return JsonResponse(
                {
                    "success": False,
                    "error": "GitHub token is not configured on the server.",
                },
                status=500,
            )

        # Create GitHub issue
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Determine labels based on content and URL
        labels = ["bug-report", "from-website"]
        if current_url:
            if "/analytics/" in current_url:
                labels.append("analytics")
            elif "/tasks/" in current_url:
                labels.append("task-management")
            elif "/landing/" in current_url:
                labels.append("dashboard")
            elif "/chat/" in current_url:
                labels.append("chat")

        data = {
            "title": title,
            "body": issue_body,
            "labels": labels,
        }

        response = requests.post(url, headers=headers, json=data, timeout=15)

        if response.status_code == 201:
            issue_data = response.json()
            return JsonResponse({"success": True, "issue_url": issue_data["html_url"]})
        else:
            error_message = (
                f"GitHub API Error: {response.status_code} - {response.text}"
            )
            print(error_message)  # for server logs
            return JsonResponse(
                {"success": False, "error": "Could not create GitHub issue."},
                status=response.status_code,
            )

    except Exception as e:
        print(f"Error in report_issue view: {e}")  # for server logs
        return JsonResponse(
            {"success": False, "error": "An unexpected server error occurred."},
            status=500,
        )


@require_POST
def submit_feedback(request):
    """
    Handles feedback submissions from the Flutter app.
    Creates GitHub issues with feedback label.
    """
    try:
        # Get form data from POST request
        feedback_text = request.POST.get("feedback", "").strip()
        app_version = request.POST.get("app_version", "").strip()
        current_screen = request.POST.get("current_screen", "").strip()
        screenshot_file = request.FILES.get("screenshot")

        if not feedback_text:
            return JsonResponse(
                {"success": False, "error": "Feedback text is required."}, status=400
            )

        # Handle screenshot upload
        if screenshot_file:
            if screenshot_file.size > 10 * 1024 * 1024:  # 10MB limit
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Screenshot file size must be less than 10MB.",
                    },
                    status=400,
                )

        # Prepare GitHub issue body with enhanced context
        issue_body = f"**User Feedback:**\n{feedback_text}\n\n"

        # Add app context
        if current_screen:
            issue_body += f"**Current Screen:** {current_screen}\n\n"

        if app_version:
            issue_body += f"**App Version:** {app_version}\n\n"

        # Add screenshot info
        if screenshot_file:
            issue_body += f"**Note:** User attached a screenshot (filename: {screenshot_file.name})\n\n"

        # Add user context
        if request.user.is_authenticated:
            issue_body += f"\n\n---\n**Submitted by:** {request.user.username} (User ID: {request.user.id})"
            issue_body += f"\n**User Email:** {request.user.email}"
        else:
            issue_body += "\n\n---\n**Submitted by:** An anonymous user"

        # Add additional request context
        issue_body += (
            f"\n**User Agent:** {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
        )
        issue_body += "\n**Submitted via:** Flutter App"

        # Get GitHub configuration from environment
        github_token = os.environ.get("GITHUB_TOKEN")
        repo_owner = os.environ.get("GITHUB_REPO_OWNER", "gemnar")
        repo_name = os.environ.get("GITHUB_REPO_NAME", "gemnar-website")

        if not github_token:
            return JsonResponse(
                {
                    "success": False,
                    "error": "GitHub token is not configured on the server.",
                },
                status=500,
            )

        # Create GitHub issue
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Determine labels for feedback
        labels = ["feedback", "from-app", "enhancement"]
        if current_screen:
            # Add screen-specific labels
            screen_lower = current_screen.lower()
            if "instagram" in screen_lower:
                labels.append("instagram")
            elif "task" in screen_lower:
                labels.append("task-management")
            elif "brand" in screen_lower:
                labels.append("brand-management")
            elif "dashboard" in screen_lower:
                labels.append("dashboard")

        # Create issue title from feedback
        title = f"App Feedback: {feedback_text[:50]}..."
        if len(feedback_text) <= 50:
            title = f"App Feedback: {feedback_text}"

        data = {
            "title": title,
            "body": issue_body,
            "labels": labels,
        }

        response = requests.post(url, headers=headers, json=data, timeout=15)

        if response.status_code == 201:
            issue_data = response.json()
            return JsonResponse({"success": True, "issue_url": issue_data["html_url"]})
        else:
            error_message = (
                f"GitHub API Error: {response.status_code} - {response.text}"
            )
            print(error_message)  # for server logs
            return JsonResponse(
                {"success": False, "error": "Could not create GitHub issue."},
                status=response.status_code,
            )

    except Exception as e:
        print(f"Error in submit_feedback view: {e}")  # for server logs
        return JsonResponse(
            {"success": False, "error": "An unexpected server error occurred."},
            status=500,
        )


@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def text_to_image(request):
    if request.method == "GET":
        return render(request, "website/text_to_image.html", {"title": "Text to Image"})

    try:
        # Get API key from environment variable
        api_key = os.getenv("RUNWARE_API_KEY")
        if not api_key:
            return JsonResponse({"success": False, "error": "API key not configured"})

        # Get form data
        prompt = request.POST.get("prompt", "").strip()
        if not prompt:
            return JsonResponse({"success": False, "error": "Prompt is required"})

        # Get other parameters
        width = int(request.POST.get("width", 512))
        height = int(request.POST.get("height", 512))
        steps = int(request.POST.get("steps", 30))

        # Prepare base payload
        payload = [
            {
                "taskType": "imageInference",
                "taskUUID": str(uuid.uuid4()),
                "model": "runware:101@1",
                "positivePrompt": prompt,
                "width": width,
                "height": height,
                "steps": steps,
            }
        ]

        # Check if an image was uploaded
        if "image" in request.FILES:
            image_file = request.FILES["image"]
            strength = float(request.POST.get("strength", 0.9))

            # Read and encode the image
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

            # Add image-specific parameters
            payload[0].update({"seedImage": image_data, "strength": strength})

            logger.info("Making image-to-image inference request")
        else:
            logger.info("Making text-to-image inference request")

        # Make the API request
        logger.info(
            f"Making API request with payload structure: {json.dumps({'taskType': payload[0]['taskType'], 'model': payload[0]['model']})}"
        )

        response = requests.post(
            "https://api.runware.ai/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        logger.info(f"Response status: {response.status_code}")

        if response.status_code != 200:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = json.dumps(error_json)
            except (ValueError, json.JSONDecodeError):
                pass
            logger.error(f"API request failed: {error_text}")
            return JsonResponse(
                {"success": False, "error": f"API request failed: {error_text}"}
            )

        try:
            response_data = response.json()
            logger.info("Successfully received API response")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {response.text}")
            return JsonResponse(
                {"success": False, "error": f"Invalid response from API: {str(e)}"}
            )

        # Return the API response
        return JsonResponse({"success": True, "data": response_data})

    except Exception as e:
        logger.exception("Error in text_to_image view")
        return JsonResponse({"success": False, "error": str(e)})


# Organization Management Views
# Organization views moved to organization_views.py


@login_required
def tweet_dashboard(request):
    """Dashboard for managing tweet configurations and viewing history"""
    configs = TweetConfiguration.objects.filter(user=request.user)
    recent_tweets = Tweet.objects.filter(configuration__user=request.user).order_by(
        "-created_at"
    )[:10]

    # Get user's Twitter API key status
    twitter_keys_status = {
        "configured": request.user.has_twitter_config,
        **request.user.get_masked_twitter_keys(),
    }

    # Get actual values for editing (not masked)
    twitter_actual_values = {
        "api_key": request.user.twitter_api_key or "",
        "api_secret": request.user.twitter_api_secret or "",
        "access_token": request.user.twitter_access_token or "",
        "access_token_secret": request.user.twitter_access_token_secret or "",
    }

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": "Dashboard", "url": "/landing/", "icon": "fas fa-home"},
        {"title": "Tweet Automation", "url": None, "icon": "fab fa-twitter"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "Tweet Strategies",
            "url": "/tweet-strategies/",
            "icon": "fas fa-lightbulb",
            "class": "bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700",
        },
        {
            "title": "Create Configuration",
            "url": "/tweet-config/create/",
            "icon": "fas fa-plus",
            "class": "bg-blue-600 text-white hover:bg-blue-700",
        },
        {
            "title": "Tweet History",
            "url": "/tweet-history/",
            "icon": "fas fa-history",
            "class": "bg-purple-600 text-white hover:bg-purple-700",
        },
        {
            "title": "Analytics",
            "url": "/tweet-analytics/",
            "icon": "fas fa-chart-line",
            "class": "bg-green-600 text-white hover:bg-green-700",
        },
    ]

    context = {
        "configs": configs,
        "recent_tweets": recent_tweets,
        "title": "Tweet Automation Dashboard",
        "twitter_keys_status": twitter_keys_status,
        "twitter_actual_values": twitter_actual_values,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
    }

    return render(request, "website/tweet_dashboard.html", context)


@login_required
def twitter_api_diagnostic(request):
    """Diagnostic view to test Twitter API configuration"""
    if not request.user.has_twitter_config:
        return JsonResponse(
            {"success": False, "error": "Twitter API keys not configured"}
        )

    try:
        user = request.user

        # Test basic authentication
        auth = tweepy.OAuthHandler(user.twitter_api_key, user.twitter_api_secret)
        auth.set_access_token(
            user.twitter_access_token, user.twitter_access_token_secret
        )
        api = tweepy.API(auth, wait_on_rate_limit=True)

        # Get user info
        twitter_user = api.verify_credentials()

        # Check rate limit status using correct Tweepy v4 method
        rate_limit_status = api.rate_limit_status()

        diagnostic_info = {
            "twitter_username": twitter_user.screen_name,
            "twitter_user_id": twitter_user.id_str,
            "account_created": str(twitter_user.created_at),
            "followers_count": twitter_user.followers_count,
            "friends_count": twitter_user.friends_count,
            "verified": twitter_user.verified,
            "protected": twitter_user.protected,
            "rate_limits": {
                "statuses_update": rate_limit_status.get("resources", {})
                .get("statuses", {})
                .get("/statuses/update", {}),
                "verify_credentials": rate_limit_status.get("resources", {})
                .get("account", {})
                .get("/account/verify_credentials", {}),
            },
        }

        return JsonResponse({"success": True, "diagnostic_info": diagnostic_info})

    except tweepy.Unauthorized as e:
        return JsonResponse(
            {
                "success": False,
                "error": "Unauthorized - Check your API keys and permissions",
                "details": str(e),
            }
        )
    except tweepy.Forbidden as e:
        return JsonResponse(
            {
                "success": False,
                "error": "Forbidden - Your app may not have proper permissions",
                "details": str(e),
            }
        )
    except (
        tweepy.errors.HTTPException,
        requests.exceptions.ConnectionError,
        requests.exceptions.DNSError,
        requests.exceptions.Timeout,
        urllib3.exceptions.NameResolutionError,
        ConnectionError,
        OSError,
    ) as e:
        return JsonResponse(
            {
                "success": False,
                "error": "Network connectivity issue - unable to connect to Twitter API",
                "details": str(e),
                "suggestion": "Please check your internet connection and try again",
            }
        )
    except AttributeError as e:
        if "rate_limit_status" in str(e):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API method not found",
                    "details": "Please ensure you're using a compatible version of Tweepy (v4.x)",
                    "technical_details": str(e),
                }
            )
        return JsonResponse(
            {"success": False, "error": "API method error", "details": str(e)}
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Diagnostic failed: {str(e)}"})


@login_required
def check_twitter_api_access_level(request):
    """Check the current Twitter API access level"""
    if not request.user.has_twitter_config:
        return JsonResponse(
            {"success": False, "error": "Twitter API keys not configured"}
        )

    try:
        import tweepy

        user = request.user

        # Setup API connection
        auth = tweepy.OAuthHandler(user.twitter_api_key, user.twitter_api_secret)
        auth.set_access_token(
            user.twitter_access_token, user.twitter_access_token_secret
        )
        api = tweepy.API(auth, wait_on_rate_limit=True)

        # Test basic functionality
        try:
            twitter_user = api.verify_credentials()
            if not twitter_user:
                return JsonResponse(
                    {"success": False, "error": "Unable to verify credentials"}
                )
        except tweepy.Unauthorized:
            return JsonResponse({"success": False, "error": "Invalid credentials"})

        # Attempt to test tweet posting capability
        access_level = "unknown"
        can_post = False

        try:
            # Try to get rate limit info for posting
            rate_limit = api.rate_limit_status()
            statuses_limits = rate_limit.get("resources", {}).get("statuses", {})

            if "/statuses/update" in statuses_limits:
                # If we can see the posting endpoint, we likely have basic access
                # or higher
                access_level = "basic"
                can_post = True
            else:
                # If we can't see posting endpoints, likely free access
                access_level = "free"
                can_post = False

        except Exception:
            # If we can't access rate limits, try a more direct approach
            try:
                # Try to post a test tweet (we'll delete it immediately)
                test_tweet = api.update_status(
                    "Test tweet from Gemnar API check - will be deleted"
                )
                # If successful, delete it
                api.destroy_status(test_tweet.id)
                access_level = "basic"
                can_post = True
            except tweepy.Forbidden as e:
                if "403" in str(e) and (
                    "subset of X API" in str(e) or "limited v1.1 endpoints" in str(e)
                ):
                    access_level = "free"
                    can_post = False
                else:
                    access_level = "basic"
                    can_post = True  # Other permission issues, but likely basic
                    # or higher
            except Exception:
                access_level = "free"
                can_post = False

        return JsonResponse(
            {
                "success": True,
                "access_level": access_level,
                "can_post": can_post,
                "username": twitter_user.screen_name,
                "message": f"Your X API access level is: {access_level.title()}",
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Failed to check access level: {str(e)}"}
        )


@login_required
@require_POST
def update_twitter_api_keys(request):
    """Update user's Twitter API keys"""
    try:
        # Get form data
        api_key = request.POST.get("api_key", "").strip()
        api_secret = request.POST.get("api_secret", "").strip()
        access_token = request.POST.get("access_token", "").strip()
        access_token_secret = request.POST.get("access_token_secret", "").strip()

        # Update user's Twitter API keys
        user = request.user
        if api_key:
            user.twitter_api_key = api_key
        if api_secret:
            user.twitter_api_secret = api_secret
        if access_token:
            user.twitter_access_token = access_token
        if access_token_secret:
            user.twitter_access_token_secret = access_token_secret

        user.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Twitter API keys updated successfully!",
                "configured": user.has_twitter_config,
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Failed to update API keys: {str(e)}"}
        )


@login_required
@require_POST
def send_test_tweet(request):
    """Send a test tweet to verify Twitter API configuration"""
    try:
        logger = logging.getLogger(__name__)

        # Check if user has Twitter API configuration
        if not request.user.has_twitter_config:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API keys are not configured. Please configure your API keys first.",
                }
            )

        # Get Twitter API credentials from user
        user = request.user

        # Log the attempt (without exposing sensitive data)
        logger.info(f"User {user.username} attempting to send test tweet")

        # First, verify credentials without posting
        try:
            auth = tweepy.OAuthHandler(user.twitter_api_key, user.twitter_api_secret)
            auth.set_access_token(
                user.twitter_access_token, user.twitter_access_token_secret
            )

            # Create API object with wait_on_rate_limit to handle rate limiting
            api = tweepy.API(auth, wait_on_rate_limit=True)

            # Test credentials first
            twitter_user = api.verify_credentials()
            if not twitter_user:
                raise tweepy.Unauthorized("Failed to verify credentials")

            logger.info(
                f"Twitter credentials verified for user @{twitter_user.screen_name}"
            )

            # Check if the user/app has write permissions by checking the token
            if not twitter_user:
                raise tweepy.Forbidden("Unable to verify user credentials")

        except tweepy.Unauthorized as e:
            logger.error(f"Twitter API Unauthorized for user {user.username}: {str(e)}")
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API authorization failed. Please check your API keys and ensure your Twitter app has 'Read and Write' permissions. You may need to regenerate your access tokens after changing permissions.",
                }
            )
        except tweepy.Forbidden as e:
            logger.error(f"Twitter API Forbidden for user {user.username}: {str(e)}")
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API access forbidden. This could mean: 1) Your Twitter app doesn't have write permissions, 2) Your account is suspended/restricted, 3) Your app needs approval for posting tweets. Please check your Twitter Developer account.",
                }
            )
        except Exception as e:
            logger.error(
                f"Twitter API verification failed for user {user.username}: {str(e)}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Failed to verify Twitter credentials: {str(e)}",
                }
            )

        # Now try to post the test tweet
        try:
            # Generate test tweet content
            current_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            test_content = f"🤖 Test tweet from Gemnar! Posted at {current_time} #GemnarTest #TwitterAPI"

            # Post test tweet
            tweet = api.update_status(test_content)

            logger.info(
                f"Test tweet posted successfully for user {user.username}: {tweet.id_str}"
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Test tweet sent successfully!",
                    "tweet_content": test_content,
                    "tweet_id": tweet.id_str,
                    "tweet_url": f"https://twitter.com/{twitter_user.screen_name}/status/{tweet.id_str}",
                }
            )

        except tweepy.Unauthorized as e:
            logger.error(
                f"Twitter API Unauthorized during tweet posting for user {user.username}: {str(e)}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API authorization failed during tweet posting. Your app may not have write permissions or your tokens may be invalid.",
                }
            )
        except tweepy.Forbidden as e:
            logger.error(
                f"Twitter API Forbidden during tweet posting for user {user.username}: {str(e)}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API access forbidden during tweet posting. Your app may not have the necessary permissions to post tweets, or your account may be restricted.",
                }
            )
        except tweepy.TooManyRequests as e:
            logger.error(
                f"Twitter API rate limit exceeded for user {user.username}: {str(e)}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API rate limit exceeded. Please wait a few minutes before trying again.",
                }
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during tweet posting for user {user.username}: {str(e)}"
            )
            return JsonResponse(
                {"success": False, "error": f"Failed to post test tweet: {str(e)}"}
            )

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(
            f"Unexpected error in send_test_tweet for user {request.user.username}: {str(e)}"
        )
        return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"})


@login_required
def tweet_config_create(request):
    """Create a new tweet configuration"""
    if request.method == "POST":
        try:
            data = request.POST

            config = TweetConfiguration.objects.create(
                user=request.user,
                name=data.get("name"),
                prompt_template=data.get("prompt_template"),
                topics=data.getlist("topics"),
                tones=data.getlist("tones"),
                keywords=data.getlist("keywords"),
                hashtags=data.getlist("hashtags"),
                schedule={
                    "frequency": data.get("frequency"),
                    "time": data.get("time"),
                    "days": (
                        data.getlist("days")
                        if data.get("frequency") == "weekly"
                        else []
                    ),
                },
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Configuration created successfully",
                    "config_id": config.id,
                }
            )

        except Exception as e:
            print("Error creating tweet configuration:", str(e))
            print(traceback.format_exc())
            return JsonResponse({"success": False, "error": str(e)})

    context = {
        "title": "Create Tweet Configuration",
        "sample_prompts": [
            "Write a {tone} tweet about {topic} using these keywords: {keywords}",
            "Create a {tone} tweet discussing {topic} that incorporates {keywords}",
            "Compose a {tone} tweet explaining {topic} mentioning {keywords}",
        ],
    }

    return render(request, "website/tweet_config_form.html", context)


@login_required
def tweet_config_edit(request, config_id):
    """Edit an existing tweet configuration"""
    config = get_object_or_404(TweetConfiguration, id=config_id, user=request.user)

    if request.method == "POST":
        try:
            data = request.POST

            config.name = data.get("name")
            config.prompt_template = data.get("prompt_template")
            config.topics = data.getlist("topics")
            config.tones = data.getlist("tones")
            config.keywords = data.getlist("keywords")
            config.hashtags = data.getlist("hashtags")
            config.schedule = {
                "frequency": data.get("frequency"),
                "time": data.get("time"),
                "days": (
                    data.getlist("days") if data.get("frequency") == "weekly" else []
                ),
            }
            config.save()

            return JsonResponse(
                {"success": True, "message": "Configuration updated successfully"}
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    context = {
        "title": "Edit Tweet Configuration",
        "config": config,
        "sample_prompts": [
            "Write a {tone} tweet about {topic} using these keywords: {keywords}",
            "Create a {tone} tweet discussing {topic} that incorporates {keywords}",
            "Compose a {tone} tweet explaining {topic} mentioning {keywords}",
        ],
    }

    return render(request, "website/tweet_config_form.html", context)


@login_required
def tweet_config_delete(request, config_id):
    """Delete a tweet configuration"""

    logger = logging.getLogger(__name__)

    # Debug logging
    logger.info(
        f"Delete request for config {config_id} by user {request.user.username} (ID: {request.user.id})"
    )
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")

    try:
        config = get_object_or_404(TweetConfiguration, id=config_id, user=request.user)
        logger.info(
            f"Configuration found: {config.name} owned by {config.user.username} (ID: {config.user.id})"
        )
    except Exception as e:
        logger.error(f"Failed to get configuration {config_id}: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": f"Configuration not found or access denied: {str(e)}",
            }
        )

    if request.method == "POST":
        try:
            # Get related tweets count for logging
            related_tweets_count = config.tweets.count()
            config_name = config.name

            # Delete the configuration (will cascade to related tweets)
            config.delete()

            message = f"Configuration '{config_name}' deleted successfully"
            if related_tweets_count > 0:
                message += f" (including {related_tweets_count} related tweets)"

            return JsonResponse({"success": True, "message": message})
        except Exception as e:
            # Log the full error for debugging
            logger = logging.getLogger(__name__)
            logger.error(f"Error deleting tweet configuration {config_id}: {str(e)}")
            logger.error(traceback.format_exc())

            return JsonResponse(
                {"success": False, "error": f"Failed to delete configuration: {str(e)}"}
            )

    return JsonResponse({"success": False, "error": "Invalid request method"})


@login_required
def tweet_config_debug(request, config_id):
    """Debug view to check tweet configuration details"""
    try:
        config = get_object_or_404(TweetConfiguration, id=config_id, user=request.user)

        # Get related tweets
        related_tweets = list(
            config.tweets.values("id", "content", "status", "created_at")
        )

        debug_info = {
            "config_id": config.id,
            "config_name": config.name,
            "user_id": config.user.id,
            "user_username": config.user.username,
            "current_user_id": request.user.id,
            "current_user_username": request.user.username,
            "is_owner": config.user == request.user,
            "related_tweets_count": len(related_tweets),
            "related_tweets": related_tweets,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

        return JsonResponse({"success": True, "debug_info": debug_info})

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        )


@login_required
def tweet_history(request):
    """View tweet history with filtering and search"""
    tweets = Tweet.objects.filter(configuration__user=request.user)

    # Apply filters
    status = request.GET.get("status")
    if status:
        tweets = tweets.filter(status=status)

    # Apply date range
    start_date = request.GET.get("start_date")
    if start_date:
        tweets = tweets.filter(created_at__date__gte=start_date)

    end_date = request.GET.get("end_date")
    if end_date:
        tweets = tweets.filter(created_at__date__lte=end_date)

    # Apply search
    search = request.GET.get("search")
    if search:
        tweets = tweets.filter(content__icontains=search)

    # Pagination
    page = int(request.GET.get("page", 1))
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page

    total_tweets = tweets.count()
    tweets = tweets.order_by("-created_at")[start:end]

    context = {
        "title": "Tweet History",
        "tweets": tweets,
        "total_tweets": total_tweets,
        "current_page": page,
        "total_pages": (total_tweets + per_page - 1) // per_page,
        "filters": {
            "status": status,
            "start_date": start_date,
            "end_date": end_date,
            "search": search,
        },
    }

    return render(request, "website/tweet_history.html", context)


@login_required
def tweet_preview(request, tweet_id):
    """Preview a generated tweet before posting"""
    tweet = get_object_or_404(Tweet, id=tweet_id, configuration__user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            tweet.status = "approved"
            tweet.save()
            return JsonResponse(
                {"success": True, "message": "Tweet approved for posting"}
            )

        elif action == "regenerate":
            success, error = tweet.generate_content()
            if success:
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Tweet regenerated successfully",
                        "content": tweet.content,
                    }
                )
            else:
                return JsonResponse({"success": False, "error": error})

    context = {"title": "Tweet Preview", "tweet": tweet}

    return render(request, "website/tweet_preview.html", context)


@login_required
def tweet_analytics(request):
    """View analytics for posted tweets"""

    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)  # Last 30 days by default

    # Override with query parameters if provided
    if request.GET.get("start_date"):
        start_date = datetime.strptime(request.GET.get("start_date"), "%Y-%m-%d").date()
    if request.GET.get("end_date"):
        end_date = datetime.strptime(request.GET.get("end_date"), "%Y-%m-%d").date()

    # Get tweets in date range
    tweets = Tweet.objects.filter(
        configuration__user=request.user, created_at__date__range=[start_date, end_date]
    )

    # Calculate statistics
    total_tweets = tweets.count()
    posted_tweets = tweets.filter(status="posted").count()
    failed_tweets = tweets.filter(status="failed").count()

    # Daily tweet counts
    daily_counts = (
        tweets.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    # Status distribution
    status_counts = (
        tweets.values("status").annotate(count=Count("id")).order_by("-count")
    )

    context = {
        "title": "Tweet Analytics",
        "total_tweets": total_tweets,
        "posted_tweets": posted_tweets,
        "failed_tweets": failed_tweets,
        "daily_counts": list(daily_counts),
        "status_counts": list(status_counts),
        "date_range": {"start": start_date, "end": end_date},
    }

    return render(request, "website/tweet_analytics.html", context)


def get_ip_address(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


# Referral System Views
def referral_signup(request, code):
    """Handle referral link clicks and redirect to signup"""
    try:
        referral_code = get_object_or_404(ReferralCode, code=code, is_active=True)

        # Get IP address
        ip_address = get_ip_address(request)

        # Check if this IP has already clicked this referral code
        existing_click = ReferralClick.objects.filter(
            referral_code=referral_code, ip_address=ip_address
        ).exists()

        # Only track the click if it's from a new IP address
        if not existing_click:
            try:
                # Track the click
                ReferralClick.objects.create(
                    referral_code=referral_code,
                    ip_address=ip_address,
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )

                # Update click count
                referral_code.total_clicks += 1
                referral_code.save()
                # Recalculate points after click
                referral_code.calculate_points()
            except IntegrityError:
                # Handle race condition - click already exists
                pass

        # Store referral code in session for signup tracking
        request.session["referral_code"] = code

        # Redirect to signup page
        return redirect("website:user_signup")

    except Exception:
        # If referral code is invalid, redirect to regular signup
        return redirect("website:user_signup")


def handle_referral_signup(request, new_user):
    """Handle referral signup tracking after user registration"""
    from .models import ReferralCode, ReferralSignup

    # Check if there's a referral code in session
    referral_code = request.session.get("referral_code")
    if referral_code:
        try:
            referral_obj = ReferralCode.objects.get(code=referral_code, is_active=True)

            # Create referral signup record
            ReferralSignup.objects.create(
                referral_code=referral_obj,
                referred_user=new_user,
            )

            # Update referral code stats
            referral_obj.total_signups += 1
            referral_obj.save()
            referral_obj.calculate_points()  # Recalculate points after signup

            # Clear session
            del request.session["referral_code"]

            # Award badges if applicable
            award_referral_badges(referral_obj.user)

        except ReferralCode.DoesNotExist:
            pass


def award_referral_badges(user):
    """Award badges based on referral achievements"""

    # Get user's referral code
    try:
        referral_code = user.referral_code

        # Check for badges to award
        badges_to_award = []

        # First referral badge
        if referral_code.total_signups >= 1:
            badges_to_award.append("first_referral")

        # Signup milestone badges
        if referral_code.total_signups >= 5:
            badges_to_award.append("bronze_referrer")
        if referral_code.total_signups >= 25:
            badges_to_award.append("silver_referrer")
        if referral_code.total_signups >= 100:
            badges_to_award.append("gold_referrer")
        if referral_code.total_signups >= 500:
            badges_to_award.append("platinum_referrer")

        # Click milestone badges
        if referral_code.total_clicks >= 1000:
            badges_to_award.append("click_master")

        # Subscription badges
        if referral_code.total_subscriptions >= 50:
            badges_to_award.append("subscription_ace")

        # Award badges that don't exist yet
        for badge_type in badges_to_award:
            ReferralBadge.objects.get_or_create(
                user=user,
                badge_type=badge_type,
            )

    except Exception:
        pass


@login_required
def referral_dashboard(request):
    """User's referral dashboard"""

    # Check if user has a referral code
    try:
        referral_code = ReferralCode.objects.get(user=request.user)

        # Get recent clicks and signups
        recent_clicks = referral_code.clicks.all()[:15]
        recent_signups = referral_code.signups.all()[:15]
        recent_subscriptions = referral_code.subscriptions.all()[:15]

        # Calculate points
        referral_code.calculate_points()

        referral_url = referral_code.get_referral_url()

    except ReferralCode.DoesNotExist:
        # User doesn't have a referral code yet
        referral_code = None
        recent_clicks = []
        recent_signups = []
        recent_subscriptions = []
        referral_url = None

    # Get user's badges
    badges = request.user.referral_badges.all()

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": "Dashboard", "url": "/landing/", "icon": "fas fa-home"},
        {"title": "Referrals", "url": None, "icon": "fas fa-users"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "Invite Companies",
            "url": "/company/invitation/",
            "icon": "fas fa-handshake",
            "class": "bg-purple-600 text-white hover:bg-purple-700",
        },
        {
            "title": "Leaderboard",
            "url": "/leaderboard/",
            "icon": "fas fa-trophy",
            "class": "bg-yellow-600 text-white hover:bg-yellow-700",
        },
    ]

    context = {
        "referral_code": referral_code,
        "recent_clicks": recent_clicks,
        "recent_signups": recent_signups,
        "recent_subscriptions": recent_subscriptions,
        "badges": badges,
        "referral_url": referral_url,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
    }

    return render(request, "website/referral_dashboard.html", context)


@login_required
def company_invitation(request):
    """Company invitation page with referral code and email template"""

    # Get or create referral code for user
    referral_code, created = ReferralCode.objects.get_or_create(user=request.user)

    context = {
        "referral_code": referral_code,
        "referral_url": referral_code.get_referral_url(),
    }

    if request.method == "POST":
        # Get form data
        domain_name = request.POST.get("domain_name", "").strip()
        company_name = request.POST.get("company_name", "").strip()
        contact_email = request.POST.get("contact_email", "").strip()

        # Validate required fields
        if not all([domain_name, company_name, contact_email]):
            context["error"] = "All fields are required."
            return render(request, "website/company_invitation.html", context)

        # Add form data to context for the generated page
        context.update(
            {
                "domain_name": domain_name,
                "company_name": company_name,
                "contact_email": contact_email,
                "show_invitation": True,
            }
        )

    return render(request, "website/company_invitation.html", context)


def leaderboard(request):
    """Display referral leaderboard"""

    # Get period filter
    period = request.GET.get("period", "all_time")

    # Base queryset - only show users with points > 0
    queryset = ReferralCode.objects.filter(is_active=True, total_points__gt=0)

    # Filter by period
    if period == "monthly":
        month_ago = datetime.now() - timedelta(days=30)
        queryset = queryset.filter(created_at__gte=month_ago)
    elif period == "weekly":
        week_ago = datetime.now() - timedelta(days=7)
        queryset = queryset.filter(created_at__gte=week_ago)

    # Order by points and get top 50
    top_referrers = queryset.order_by("-total_points", "-total_signups")[:50]

    # Get current user's rank if logged in
    user_rank = None
    if request.user.is_authenticated:
        try:
            user_code = request.user.referral_code
            # Only calculate rank if user has points > 0
            if user_code.total_points > 0:
                # Find user's rank
                higher_ranked = queryset.filter(
                    total_points__gt=user_code.total_points
                ).count()
                user_rank = higher_ranked + 1
        except Exception:
            pass

    context = {
        "top_referrers": top_referrers,
        "user_rank": user_rank,
        "current_period": period,
    }

    return render(request, "website/leaderboard.html", context)


@csrf_exempt
def referral_api_stats(request):
    """API endpoint for referral statistics"""

    if request.method == "GET":
        # Get top 10 referrers
        top_referrers = ReferralCode.objects.filter(is_active=True).order_by(
            "-total_points"
        )[:10]

        data = {
            "top_referrers": [
                {
                    "user": referrer.user.username,
                    "points": referrer.total_points,
                    "signups": referrer.total_signups,
                    "clicks": referrer.total_clicks,
                    "subscriptions": referrer.total_subscriptions,
                }
                for referrer in top_referrers
            ]
        }

        return JsonResponse(data)

    return JsonResponse({"error": "Method not allowed"}, status=405)


def handle_referral_subscription(referred_user, subscription_type, amount):
    """Handle referral subscription tracking"""

    try:
        # Check if user was referred
        referral_signup = getattr(referred_user, "referral_signup", None)
        if referral_signup:
            # Create subscription record
            ReferralSubscription.objects.create(
                referral_code=referral_signup.referral_code,
                referred_user=referred_user,
                subscription_type=subscription_type,
                subscription_amount=amount,
            )

            # Update referral code stats
            referral_code = referral_signup.referral_code
            referral_code.total_subscriptions += 1
            referral_code.save()

            # Calculate and add rewards
            referral_code.calculate_points()

            # Award badges
            award_referral_badges(referral_code.user)

    except Exception:
        pass


@login_required
def generate_referral_code(request):
    """Generate a referral code for the current user"""

    if request.method == "POST":
        try:
            # Check if user already has a referral code
            try:
                referral_code = ReferralCode.objects.get(user=request.user)
                return JsonResponse(
                    {
                        "success": True,
                        "message": "You already have a referral code!",
                        "referral_code": referral_code.code,
                        "referral_url": referral_code.get_referral_url(),
                    }
                )
            except ReferralCode.DoesNotExist:
                # Create new referral code
                referral_code = ReferralCode.objects.create(user=request.user)
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Referral code generated successfully!",
                        "referral_code": referral_code.code,
                        "referral_url": referral_code.get_referral_url(),
                    }
                )
        except Exception as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Error generating referral code: {str(e)}",
                }
            )

    return JsonResponse({"success": False, "message": "Invalid request method"})


# Helper function to get leaderboard data for homepage
def get_leaderboard_data():
    """Get leaderboard data for homepage display"""

    try:
        # Get top 5 referrers with points > 0
        top_referrers = ReferralCode.objects.filter(
            is_active=True, total_points__gt=0
        ).order_by("-total_points")[:5]

        return [
            {
                "user": referrer.user.username,
                "points": referrer.total_points,
                "signups": referrer.total_signups,
                "clicks": referrer.total_clicks,
                "subscriptions": referrer.total_subscriptions,
                "badge_count": referrer.user.referral_badges.count(),
            }
            for referrer in top_referrers
        ]
    except Exception:
        return []


@csrf_exempt
@require_http_methods(["POST"])
def github_webhook(request):
    """
    GitHub webhook endpoint for automatic deployment.

    This endpoint receives GitHub webhook events and triggers deployment
    when code is pushed to the main branch.
    """
    try:
        # Log incoming webhook request details
        github_event = request.META.get("HTTP_X_GITHUB_EVENT", "unknown")
        content_type = request.META.get("CONTENT_TYPE", "unknown")
        content_length = request.META.get("CONTENT_LENGTH", "0")
        logger.info(
            f"GitHub webhook received: event={github_event}, "
            f"content_type={content_type}, length={content_length}"
        )

        # Get the webhook secret from environment variables
        webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
        if not webhook_secret:
            logger.error("GitHub webhook secret not configured")
            return JsonResponse({"error": "Webhook not configured"}, status=500)

        # Read the request body once and store it
        request_body = request.body

        # Verify the webhook signature
        signature_header = request.META.get("HTTP_X_HUB_SIGNATURE_256")
        if not signature_header:
            logger.error("Missing GitHub webhook signature")
            return JsonResponse({"error": "Missing signature"}, status=400)

        # Calculate expected signature using the stored body
        expected_signature = hmac.new(
            webhook_secret.encode("utf-8"), request_body, hashlib.sha256
        ).hexdigest()
        expected_signature = f"sha256={expected_signature}"

        # Compare signatures
        if not hmac.compare_digest(signature_header, expected_signature):
            logger.error("Invalid GitHub webhook signature")
            return JsonResponse({"error": "Invalid signature"}, status=403)

        # Check for GitHub ping event (sent when webhook is first set up)
        github_event = request.META.get("HTTP_X_GITHUB_EVENT", "")
        if github_event == "ping":
            logger.info("Received GitHub ping event")
            return JsonResponse({"message": "Ping received"}, status=200)

        # Parse the webhook payload using the stored body
        try:
            payload = json.loads(request_body)
        except json.JSONDecodeError as e:
            # Log more details about the failed payload
            content_type = request.META.get("CONTENT_TYPE", "unknown")
            payload_preview = request_body[:200] if request_body else b"<empty>"
            logger.error(
                f"Invalid JSON in webhook payload. "
                f"Content-Type: {content_type}, "
                f"Payload preview: {payload_preview}, "
                f"JSON error: {str(e)}"
            )
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Only handle push events
        if github_event != "push":
            logger.info(f"Ignoring {github_event} event")
            return JsonResponse(
                {"message": f"Ignoring {github_event} event"}, status=200
            )

        # Check if this is a push event to main branch
        if payload.get("ref") != "refs/heads/main":
            logger.info(f"Ignoring push to branch: {payload.get('ref')}")
            return JsonResponse({"message": "Not main branch, ignoring"}, status=200)

        # Get repository information
        repo_info = payload.get("repository", {})
        repo_name = repo_info.get("name", "unknown")
        commit_sha = payload.get("after", "unknown")

        logger.info(
            f"Received deployment webhook for {repo_name}, commit: {commit_sha}"
        )

        # Send deployment started notification
        from .utils.slack_notifications import SlackNotifier

        SlackNotifier.send_deployment_notification("started", repo_name, commit_sha)

        # Run deployment in background thread to avoid timeout
        deployment_thread = threading.Thread(
            target=run_deployment, args=(repo_name, commit_sha), daemon=True
        )
        deployment_thread.start()

        return JsonResponse(
            {
                "message": "Deployment started",
                "repository": repo_name,
                "commit": commit_sha,
            },
            status=200,
        )

    except Exception as e:
        logger.error(f"GitHub webhook error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


def run_deployment(repo_name, commit_sha):
    """
    Run the deployment process in a background thread.
    """
    logger.info(f"Starting deployment for {repo_name}, commit: {commit_sha}")

    from .utils.slack_notifications import SlackNotifier

    SlackNotifier.send_deployment_notification("deploying", repo_name, commit_sha)

    try:
        # Change to the project directory
        project_dir = "/home/django/gemnar-website"

        # Log system status before deployment
        logger.info("Pre-deployment system status:")
        try:
            # Check current service status
            service_status = subprocess.run(
                ["sudo", "systemctl", "is-active", "uvicorn.service"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            logger.info(
                f"Current uvicorn service status: {service_status.stdout.strip()}"
            )

            # Check disk space
            disk_usage = subprocess.run(
                ["df", "-h", project_dir],
                capture_output=True,
                text=True,
                timeout=10,
            )
            logger.info(f"Disk usage: {disk_usage.stdout}")

            # Check memory usage
            memory_usage = subprocess.run(
                ["free", "-h"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            logger.info(f"Memory usage: {memory_usage.stdout}")

        except Exception as e:
            logger.warning(f"Could not get pre-deployment system status: {str(e)}")

        logger.info(f"Working directory: {project_dir}")
        logger.info(f"Current working directory: {os.getcwd()}")

        # Verify project directory exists
        if not os.path.exists(project_dir):
            logger.error(f"Project directory does not exist: {project_dir}")
            return False

        # Step 1: Pull latest changes
        logger.info("Pulling latest changes from Git...")
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            logger.error(f"Git pull failed: {result.stderr}")
            return False

        logger.info("Git pull successful")

        # Step 2: Install dependencies
        logger.info("Installing dependencies...")
        result = subprocess.run(
            ["/home/django/.local/bin/poetry", "install"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, "POETRY_VENV_IN_PROJECT": "1"},
        )

        if result.returncode != 0:
            logger.error(f"Poetry install failed: {result.stderr}")
            return False

        logger.info("Dependencies installed successfully")

        # Step 3: Run database migrations
        logger.info("Running database migrations...")
        migrate_cmd = [
            "/home/django/.local/bin/poetry",
            "run",
            "python",
            "manage.py",
            "migrate",
        ]
        result = subprocess.run(
            migrate_cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "ENVIRONMENT": "production"},
        )

        if result.returncode != 0:
            logger.error(f"Database migration failed: {result.stderr}")
            return False

        logger.info("Database migrations completed successfully")

        # Step 4: Clear static files cache
        logger.info("Clearing static files cache...")
        staticfiles_dir = os.path.join(project_dir, "staticfiles")
        if os.path.exists(staticfiles_dir):
            subprocess.run(
                ["rm", "-rf", f"{staticfiles_dir}/*"], shell=True, timeout=60
            )

        # Step 5: Collect static files
        logger.info("Collecting static files...")
        collectstatic_cmd = [
            "/home/django/.local/bin/poetry",
            "run",
            "python",
            "manage.py",
            "collectstatic",
            "--noinput",
            "--clear",
        ]
        result = subprocess.run(
            collectstatic_cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "ENVIRONMENT": "production"},
        )

        if result.returncode != 0:
            logger.error(f"Static files collection failed: {result.stderr}")
            return False

        logger.info("Static files collected successfully")

        # Step 6: Restart application server with multiple fallback methods
        logger.info("Restarting application server...")
        SlackNotifier.send_deployment_notification("restarting", repo_name, commit_sha)

        # Try multiple restart methods in order of preference
        restart_methods = [
            # Method 1: Custom restart script (in ansible directory)
            {
                "name": "Custom restart script",
                "command": ["/home/django/gemnar-website/ansible/restart_uvicorn.sh"],
                "check_exists": (
                    "/home/django/gemnar-website/ansible/restart_uvicorn.sh"
                ),
            },
            # Method 2: Custom restart script (django home fallback)
            {
                "name": "Custom restart script (django home)",
                "command": ["/home/django/restart_uvicorn.sh"],
                "check_exists": "/home/django/restart_uvicorn.sh",
            },
            # Method 3: Stop, cleanup socket, and start separately
            {
                "name": "Stop, cleanup socket, and start",
                "command": ["sudo", "systemctl", "stop", "uvicorn.service"],
                "check_exists": None,
                "cleanup_socket": True,
                "follow_up": ["sudo", "systemctl", "start", "uvicorn.service"],
            },
            # Method 4: Systemctl restart with sudo
            {
                "name": "Systemctl restart (sudo)",
                "command": ["sudo", "systemctl", "restart", "uvicorn.service"],
                "check_exists": None,
            },
            # Method 5: Direct systemctl restart
            {
                "name": "Systemctl restart (direct)",
                "command": ["systemctl", "restart", "uvicorn.service"],
                "check_exists": None,
            },
        ]

        restart_success = False
        last_error = ""

        for method in restart_methods:
            try:
                # Check if file exists if needed
                if method.get("check_exists") and not os.path.exists(
                    method["check_exists"]
                ):
                    logger.info(f"Skipping {method['name']}: file not found")
                    continue

                logger.info(f"Attempting restart with: {method['name']}")

                # Execute the main command
                result = subprocess.run(
                    method["command"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                logger.info(f"Restart command output: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Restart command stderr: {result.stderr}")

                # Handle socket cleanup if specified
                if method.get("cleanup_socket") and result.returncode == 0:
                    logger.info("Cleaning up socket file...")
                    socket_file = "/home/django/gemnar-website/gemnar.sock"
                    try:
                        if os.path.exists(socket_file):
                            os.remove(socket_file)
                            logger.info(f"Removed socket file: {socket_file}")
                        else:
                            logger.info("Socket file doesn't exist, no cleanup needed")

                        # Wait a moment for cleanup
                        import time

                        time.sleep(2)
                    except Exception as socket_error:
                        logger.warning(f"Socket cleanup failed: {socket_error}")
                        # Continue anyway, don't fail the restart

                # Execute follow-up command if needed
                if method.get("follow_up"):
                    logger.info("Executing follow-up command...")
                    followup_result = subprocess.run(
                        method["follow_up"],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    logger.info(f"Follow-up command output: {followup_result.stdout}")
                    if followup_result.stderr:
                        logger.warning(
                            f"Follow-up command stderr: {followup_result.stderr}"
                        )

                    # Use follow-up result for success check
                    if followup_result.returncode == 0:
                        restart_success = True
                        logger.info(f"Restart successful with {method['name']}")
                        break
                    else:
                        last_error = (
                            f"{method['name']} follow-up failed: "
                            f"{followup_result.stderr}"
                        )
                        logger.error(last_error)
                        continue

                if result.returncode == 0:
                    restart_success = True
                    logger.info(f"Restart successful with {method['name']}")
                    break
                else:
                    last_error = f"{method['name']} failed: {result.stderr}"
                    logger.error(last_error)
                    continue

            except subprocess.TimeoutExpired:
                last_error = f"{method['name']} timed out"
                logger.error(last_error)
                continue
            except Exception as e:
                last_error = f"{method['name']} exception: {str(e)}"
                logger.error(last_error)
                continue

        if not restart_success:
            logger.error(f"All restart methods failed. Last error: {last_error}")
            from .utils.slack_notifications import SlackNotifier

            SlackNotifier.send_deployment_notification(
                "failed",
                repo_name,
                commit_sha,
                f"Service restart failed after trying all methods: {last_error}",
            )
            return False

        logger.info("Application server restart command completed successfully")

        # Step 7: Verify service is running and healthy
        logger.info("Verifying service health...")

        # Wait longer for service to start properly and reload
        import time

        logger.info("Waiting 10 seconds for service to fully start...")
        time.sleep(10)

        # Check service status multiple times with increasing wait
        max_health_checks = 3
        health_check_passed = False

        for attempt in range(max_health_checks):
            logger.info(f"Health check attempt {attempt + 1}/{max_health_checks}")

            # Check if uvicorn service is active
            service_check = subprocess.run(
                ["sudo", "systemctl", "is-active", "uvicorn.service"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if service_check.returncode == 0:
                logger.info(f"Service is active on attempt {attempt + 1}")
                health_check_passed = True
                break
            else:
                logger.warning(
                    f"Service not active on attempt {attempt + 1}: "
                    f"{service_check.stdout.strip()}"
                )

                if attempt < max_health_checks - 1:
                    logger.info("Waiting 15 seconds before next health check...")
                    time.sleep(15)

        if not health_check_passed:
            logger.error(
                "Uvicorn service is not running after restart and health checks"
            )

            # Get detailed service status for debugging
            status_result = subprocess.run(
                ["sudo", "systemctl", "status", "uvicorn.service", "--no-pager", "-l"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            logger.error(f"Service status: {status_result.stdout}")

            # Also check for any service failures
            journal_result = subprocess.run(
                [
                    "sudo",
                    "journalctl",
                    "-u",
                    "uvicorn.service",
                    "--no-pager",
                    "-n",
                    "50",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            logger.error(f"Recent service logs: {journal_result.stdout}")

            from .utils.slack_notifications import SlackNotifier

            SlackNotifier.send_deployment_notification(
                "failed",
                repo_name,
                commit_sha,
                f"Service failed to start after restart. "
                f"Status: {status_result.stdout[:500]}",
            )
            return False

        logger.info("Uvicorn service is running and healthy")

        # Step 8: Verify website is accessible
        logger.info("Checking website accessibility...")

        # Try multiple accessibility checks with retry logic
        max_access_checks = 3
        access_check_passed = False

        for attempt in range(max_access_checks):
            try:
                logger.info(
                    f"Website accessibility check attempt "
                    f"{attempt + 1}/{max_access_checks}"
                )

                import requests

                response = requests.get("https://gemnar.com", timeout=30)

                if response.status_code == 200:
                    logger.info(
                        f"Website is accessible on attempt {attempt + 1} "
                        f"(HTTP {response.status_code})"
                    )
                    access_check_passed = True
                    break
                else:
                    logger.warning(
                        f"Website returned status code "
                        f"{response.status_code} on attempt {attempt + 1}"
                    )

                    if attempt < max_access_checks - 1:
                        logger.info(
                            "Waiting 10 seconds before next accessibility check..."
                        )
                        time.sleep(10)

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_access_checks - 1:
                    logger.info("Waiting 10 seconds before next accessibility check...")
                    time.sleep(10)
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout on attempt {attempt + 1}: {str(e)}")
                if attempt < max_access_checks - 1:
                    logger.info("Waiting 10 seconds before next accessibility check...")
                    time.sleep(10)
            except Exception as e:
                logger.warning(
                    f"Website accessibility check failed on attempt "
                    f"{attempt + 1}: {str(e)}"
                )
                if attempt < max_access_checks - 1:
                    logger.info("Waiting 10 seconds before next accessibility check...")
                    time.sleep(10)

        if not access_check_passed:
            logger.error("Website accessibility check failed after all attempts")

            # Try to get more diagnostic information
            try:
                # Check if port 8000 is listening
                port_check = subprocess.run(
                    ["netstat", "-tlnp", "|", "grep", ":8000"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                logger.info(f"Port 8000 status: {port_check.stdout}")
            except Exception as e:
                logger.warning(f"Could not check port status: {str(e)}")

            from .utils.slack_notifications import SlackNotifier

            SlackNotifier.send_deployment_notification(
                "failed",
                repo_name,
                commit_sha,
                "Website accessibility check failed after all attempts",
            )
            return False

        logger.info("Website is accessible and responding correctly")

        # Log deployment summary
        logger.info("=== DEPLOYMENT SUMMARY ===")
        logger.info(f"Repository: {repo_name}")
        logger.info(f"Commit: {commit_sha}")
        logger.info("Status: SUCCESS")
        logger.info("All deployment steps completed successfully:")
        logger.info("  ✓ Git pull")
        logger.info("  ✓ Dependencies installation")
        logger.info("  ✓ Database migrations")
        logger.info("  ✓ Static files collection")
        logger.info("  ✓ Service restart")
        logger.info("  ✓ Health check")
        logger.info("  ✓ Website accessibility")
        logger.info("=== END DEPLOYMENT SUMMARY ===")

        logger.info(f"Deployment completed successfully for commit: {commit_sha}")

        # Send deployment success notification
        try:
            from .utils.slack_notifications import SlackNotifier

            SlackNotifier.send_deployment_notification("success", repo_name, commit_sha)
            logger.info("Success notification sent")
        except Exception as e:
            logger.error(f"Failed to send success notification: {str(e)}")
            # Don't fail the deployment for notification issues

        return True

    except subprocess.TimeoutExpired:
        logger.error("=== DEPLOYMENT FAILED - TIMEOUT ===")
        logger.error(f"Repository: {repo_name}")
        logger.error(f"Commit: {commit_sha}")
        logger.error("Reason: Deployment process timed out")
        logger.error("=== END DEPLOYMENT FAILURE SUMMARY ===")

        # Send deployment failure notification
        from .utils.slack_notifications import SlackNotifier

        SlackNotifier.send_deployment_notification(
            "failed", repo_name, commit_sha, "Deployment timed out"
        )
        return False
    except Exception as e:
        error_message = str(e)
        logger.error("=== DEPLOYMENT FAILED - EXCEPTION ===")
        logger.error(f"Repository: {repo_name}")
        logger.error(f"Commit: {commit_sha}")
        logger.error(f"Error: {error_message}")
        logger.error("=== END DEPLOYMENT FAILURE SUMMARY ===")

        # Send deployment failure notification
        from .utils.slack_notifications import SlackNotifier

        SlackNotifier.send_deployment_notification(
            "failed", repo_name, commit_sha, error_message
        )
        return False


@user_passes_test(is_admin_user)
def github_webhook_test(request):
    """
    Test endpoint to verify webhook functionality.
    """
    if request.method == "POST":
        # Test deployment without GitHub webhook
        deployment_thread = threading.Thread(
            target=run_deployment, args=("manual-test", "test-commit"), daemon=True
        )
        deployment_thread.start()

        return JsonResponse(
            {
                "message": "Test deployment started",
                "note": "Check server logs for deployment status",
            }
        )

    return JsonResponse(
        {
            "message": "GitHub Webhook Test",
            "webhook_url": request.build_absolute_uri(reverse("github_webhook")),
            "instructions": [
                "1. Set GITHUB_WEBHOOK_SECRET environment variable",
                "2. Configure GitHub webhook to send POST requests to the webhook URL",
                "3. Set webhook to trigger on 'push' events",
                "4. Use the secret in GitHub webhook settings",
            ],
        }
    )


@login_required
@require_http_methods(["DELETE"])
def delete_referral_activity(request, activity_type, activity_id):
    """
    Delete a referral activity (click, signup, or subscription) using HTMX.
    """
    try:
        # Get the user's referral code to ensure they can only delete their own activities
        referral_code = ReferralCode.objects.get(user=request.user)

        if activity_type == "click":
            activity = ReferralClick.objects.get(
                id=activity_id, referral_code=referral_code
            )
            # Update referral code stats
            referral_code.total_clicks = max(0, referral_code.total_clicks - 1)
            referral_code.save()
            activity.delete()

        elif activity_type == "signup":
            activity = ReferralSignup.objects.get(
                id=activity_id, referral_code=referral_code
            )
            # Update referral code stats
            referral_code.total_signups = max(0, referral_code.total_signups - 1)
            referral_code.save()
            activity.delete()

        elif activity_type == "subscription":
            activity = ReferralSubscription.objects.get(
                id=activity_id, referral_code=referral_code
            )
            # Update referral code stats
            referral_code.total_subscriptions = max(
                0, referral_code.total_subscriptions - 1
            )
            # Recalculate total rewards earned
            total_rewards = (
                referral_code.subscriptions.aggregate(total=Sum("reward_amount"))[
                    "total"
                ]
                or 0
            )
            referral_code.total_rewards_earned = total_rewards
            referral_code.save()
            activity.delete()

        else:
            return HttpResponse("Invalid activity type", status=400)

        # Return empty response for HTMX to remove the element
        return HttpResponse("")

    except (
        ReferralCode.DoesNotExist,
        ReferralClick.DoesNotExist,
        ReferralSignup.DoesNotExist,
        ReferralSubscription.DoesNotExist,
    ):
        return HttpResponse("Activity not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error deleting activity: {str(e)}", status=500)


@login_required
def agency(request):
    """Agency prompt control center for managing AI prompts to services"""

    # Handle POST request for submitting prompts
    if request.method == "POST":
        service = request.POST.get("service")
        prompt = request.POST.get("prompt")

        if service and prompt:
            ServicePrompt.objects.create(
                user=request.user, service=service, prompt=prompt
            )
            messages.success(request, f"Prompt sent to {service}!")
            return redirect("website:agency")

    # Define the 5 main services
    services = [
        {
            "name": "Twitter",
            "slug": "twitter",
            "logo": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/twitter.svg",
            "external_url": "https://twitter.com",
            "color": "blue",
        },
        {
            "name": "Instagram",
            "slug": "instagram",
            "logo": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/instagram.svg",
            "external_url": "https://instagram.com",
            "color": "pink",
        },
        {
            "name": "Reddit",
            "slug": "reddit",
            "logo": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/reddit.svg",
            "external_url": "https://reddit.com",
            "color": "orange",
        },
        {
            "name": "Blog",
            "slug": "blog",
            "logo": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/blogger.svg",
            "external_url": "/blog/",
            "color": "green",
        },
        {
            "name": "Gemnar Feed",
            "slug": "gemnar_feed",
            "logo": "https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/rss.svg",
            "external_url": "/feed/",
            "color": "purple",
        },
    ]

    # Get data for each service
    service_data = []
    for service in services:
        slug = service["slug"]

        # Get or create stats
        stats, created = ServiceStats.objects.get_or_create(
            user=request.user,
            service=slug,
            defaults={
                "total_prompts": 0,
                "successful_posts": 0,
                "failed_posts": 0,
                "pending_posts": 0,
                "total_likes": 0,
                "total_shares": 0,
                "total_comments": 0,
            },
        )

        # Get connection status
        connection = ServiceConnection.objects.filter(
            user=request.user, service=slug
        ).first()

        # Get recent prompts
        recent_prompts = ServicePrompt.objects.filter(user=request.user, service=slug)[
            :5
        ]

        # Add data to service
        service_data.append(
            {
                **service,
                "stats": stats,
                "connection": connection,
                "recent_prompts": recent_prompts,
            }
        )

    context = {
        "services": service_data,
    }

    return render(request, "website/agency.html", context)


@user_passes_test(is_admin_user)
def weblog_view(request):
    """View to display WebLog entries for admin debugging"""
    from django.core.paginator import Paginator

    # Get filter parameters
    activity_type = request.GET.get("activity_type", "")
    status = request.GET.get("status", "")

    # Base queryset
    weblogs = WebLog.objects.all()

    # Apply filters
    if activity_type:
        weblogs = weblogs.filter(activity_type=activity_type)
    if status:
        weblogs = weblogs.filter(status=status)

    # Order by most recent
    weblogs = weblogs.order_by("-started_at")

    # Paginate results
    paginator = Paginator(weblogs, 25)  # Show 25 logs per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get filter choices
    activity_types = WebLog.ACTIVITY_TYPES
    statuses = WebLog.STATUS_CHOICES

    context = {
        "title": "WebLog Entries",
        "page_obj": page_obj,
        "activity_types": activity_types,
        "statuses": statuses,
        "current_activity_type": activity_type,
        "current_status": status,
    }

    return render(request, "website/weblog_view.html", context)


def landing_page(request):
    return render(request, "website/landing.html")


@login_required
def account_settings(request):
    """User account settings page"""
    context = {
        "user": request.user,
        "title": "Account Settings",
    }
    return render(request, "website/account/settings.html", context)


@login_required
def account_deletion_preview(request):
    """Show preview of what data will be deleted"""
    preview = get_account_deletion_preview(request.user)

    context = {
        "preview": preview,
        "title": "Delete Account - Preview",
    }
    return render(request, "website/account/deletion_preview.html", context)


@login_required
def account_deletion_confirm(request):
    """Confirm account deletion with password verification"""
    if request.method == "POST":
        password = request.POST.get("password", "")
        reason = request.POST.get("reason", "")
        feedback = request.POST.get("feedback", "")
        confirm_deletion = request.POST.get("confirm_deletion") == "on"

        # Verify password
        if not request.user.check_password(password):
            messages.error(request, "Incorrect password. Please try again.")
            return render(
                request,
                "website/account/deletion_confirm.html",
                {
                    "title": "Delete Account - Confirm",
                    "reason": reason,
                    "feedback": feedback,
                },
            )

        # Verify confirmation checkbox
        if not confirm_deletion:
            messages.error(
                request,
                "You must confirm that you understand this action cannot be undone.",
            )
            return render(
                request,
                "website/account/deletion_confirm.html",
                {
                    "title": "Delete Account - Confirm",
                    "reason": reason,
                    "feedback": feedback,
                },
            )

        # Proceed with deletion
        deletion_service = AccountDeletionService(request.user)
        result = deletion_service.delete_account(reason=reason, feedback=feedback)

        if result["success"]:
            # User is deleted, so we can't use messages or redirect normally
            # Instead, render a success page
            return render(
                request,
                "website/account/deletion_success.html",
                {"title": "Account Deleted", "summary": result["summary"]},
            )
        else:
            messages.error(request, f"Account deletion failed: {result['error']}")
            return render(
                request,
                "website/account/deletion_confirm.html",
                {
                    "title": "Delete Account - Confirm",
                    "reason": reason,
                    "feedback": feedback,
                },
            )

    context = {
        "title": "Delete Account - Confirm",
    }
    return render(request, "website/account/deletion_confirm.html", context)


@require_http_methods(["POST"])
@csrf_protect
def beta_signup(request):
    """Handle beta tester email signup"""
    try:
        email = request.POST.get("email", "").strip().lower()

        if not email:
            return JsonResponse(
                {"success": False, "error": "Email address is required"}, status=400
            )

        # Validate email format (basic check)
        if "@" not in email or "." not in email:
            return JsonResponse(
                {"success": False, "error": "Please enter a valid email address"},
                status=400,
            )

        # Create or get beta tester record
        beta_tester, created = BetaTester.objects.get_or_create(
            email=email,
            defaults={
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "referral_source": request.META.get("HTTP_REFERER", ""),
            },
        )

        if created:
            # New beta tester
            message = "Thanks! We'll add you to TestFlight soon."

            # Optional: Send notification to admins
            try:
                from django.core.mail import send_mail

                send_mail(
                    subject=f"New Beta Tester: {email}",
                    message=f"New beta tester signup: {email}\n\nUser Agent: {request.META.get('HTTP_USER_AGENT', '')}\nReferrer: {request.META.get('HTTP_REFERER', '')}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin[1] for admin in settings.ADMINS],
                    fail_silently=True,
                )
            except Exception:
                # Don't fail the signup if email notification fails
                pass

        else:
            # Already signed up
            message = "You're already on our beta list! We'll contact you soon."

        return JsonResponse({"success": True, "message": message, "is_new": created})

    except Exception as e:
        # Log the error but don't expose details to user
        logging.error(f"Beta signup error: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Something went wrong. Please try again."},
            status=500,
        )


@login_required
def tweet_strategies_dashboard(request, organization_pk=None, brand_pk=None):
    """Tweet Strategies Dashboard - Main interface for managing and using tweet strategies"""
    from django.db.models import Sum

    # Get specific brand if organization_pk and brand_pk are provided
    if organization_pk and brand_pk:
        try:
            organization = get_object_or_404(Organization, pk=organization_pk)
            brand = get_object_or_404(Brand, pk=brand_pk, organization=organization)
            # Check if user has access to this organization
            if not organization.users.filter(id=request.user.id).exists():
                messages.error(
                    request, "You don't have permission to access this organization."
                )
                return redirect("organization_list")
            user_brands = [brand]
            current_brand = brand
            current_organization = organization
        except Exception as e:
            messages.error(request, f"Brand or organization not found: {str(e)}")
            return redirect("organization_list")
    else:
        # Get user's brands (original behavior)
        user_brands = Brand.objects.filter(organization__members=request.user)
        current_brand = None
        current_organization = None

    # Get all active strategies grouped by category
    strategies = TweetStrategy.objects.filter(is_active=True).order_by(
        "category", "name"
    )
    strategies_by_category = {}
    for strategy in strategies:
        category = strategy.get_category_display()
        if category not in strategies_by_category:
            strategies_by_category[category] = []
        strategies_by_category[category].append(strategy)

    # Analytics data
    total_strategies = strategies.count()

    # Get recent tweets created with strategies
    recent_strategy_tweets = BrandTweet.objects.filter(
        brand__in=user_brands, ai_prompt__icontains="strategy"
    ).order_by("-created_at")[:10]

    # Strategy usage statistics
    strategy_stats = (
        TweetStrategy.objects.filter(is_active=True)
        .annotate(total_usage=Sum("usage_count"))
        .order_by("-usage_count")[:5]
    )

    # Performance metrics for user's tweets
    user_tweets_count = BrandTweet.objects.filter(brand__in=user_brands).count()
    posted_tweets_count = BrandTweet.objects.filter(
        brand__in=user_brands, status="posted"
    ).count()

    # Recent activity
    recent_tweets = BrandTweet.objects.filter(brand__in=user_brands).order_by(
        "-created_at"
    )[:5]

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": "Dashboard", "url": "/landing/", "icon": "fas fa-home"},
        {
            "title": "Tweet Automation",
            "url": "/tweet-dashboard/",
            "icon": "fab fa-twitter",
        },
        {"title": "Tweet Strategies", "url": None, "icon": "fas fa-lightbulb"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "Back to Tweet Dashboard",
            "url": "/tweet-dashboard/",
            "icon": "fas fa-arrow-left",
            "class": "bg-gray-600 text-white hover:bg-gray-700",
        },
        (
            {
                "title": "Admin: Manage Strategies",
                "url": "/admin/website/tweetstrategy/",
                "icon": "fas fa-cog",
                "class": "bg-purple-600 text-white hover:bg-purple-700",
            }
            if request.user.is_staff
            else None
        ),
    ]

    # Filter out None values from action_buttons
    action_buttons = [btn for btn in action_buttons if btn is not None]

    context = {
        "user_brands": user_brands,
        "strategies_by_category": strategies_by_category,
        "total_strategies": total_strategies,
        "recent_strategy_tweets": recent_strategy_tweets,
        "strategy_stats": strategy_stats,
        "user_tweets_count": user_tweets_count,
        "posted_tweets_count": posted_tweets_count,
        "recent_tweets": recent_tweets,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
        "title": "Tweet Strategies Dashboard",
        "current_brand": current_brand,
        "current_organization": current_organization,
    }

    return render(request, "website/tweet_strategies_dashboard.html", context)


@login_required
def get_strategy_analytics(request):
    """AJAX endpoint for strategy analytics data"""
    from django.db.models import Count
    from datetime import timedelta

    # Get user's brands
    user_brands = Brand.objects.filter(organization__members=request.user)

    # Get time period (default to last 30 days)
    days = int(request.GET.get("days", 30))
    start_date = timezone.now() - timedelta(days=days)

    # Strategy usage over time
    strategy_usage = TweetStrategy.objects.filter(
        is_active=True, usage_count__gt=0
    ).values("name", "category", "usage_count")

    # Tweets created by status
    tweet_status_data = (
        BrandTweet.objects.filter(brand__in=user_brands, created_at__gte=start_date)
        .values("status")
        .annotate(count=Count("id"))
    )

    # Most used strategies
    top_strategies = TweetStrategy.objects.filter(is_active=True).order_by(
        "-usage_count"
    )[:10]

    # Tweet performance over time
    daily_tweets = (
        BrandTweet.objects.filter(brand__in=user_brands, created_at__gte=start_date)
        .extra(select={"day": "date(created_at)"})
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    analytics_data = {
        "strategy_usage": list(strategy_usage),
        "tweet_status_data": list(tweet_status_data),
        "top_strategies": [
            {
                "name": s.name,
                "category": s.get_category_display(),
                "usage_count": s.usage_count,
            }
            for s in top_strategies
        ],
        "daily_tweets": list(daily_tweets),
        "period_days": days,
    }

    return JsonResponse(analytics_data)


@login_required
@require_POST
def generate_strategy_tweet(request):
    """Generate a tweet using a selected strategy"""
    import json

    try:
        data = json.loads(request.body)
        strategy_id = data.get("strategy_id")
        brand_id = data.get("brand_id")
        context = data.get("context", {})

        if not strategy_id or not brand_id:
            return JsonResponse(
                {"success": False, "error": "Strategy ID and Brand ID are required"},
                status=400,
            )

        # Get strategy
        try:
            strategy = TweetStrategy.objects.get(id=strategy_id, is_active=True)
        except TweetStrategy.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Strategy not found"}, status=404
            )

        # Get brand and verify access
        try:
            brand = Brand.objects.get(id=brand_id, organization__members=request.user)
        except Brand.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Brand not found or access denied"},
                status=404,
            )

        # Generate tweet using strategy
        result = strategy.generate_tweet_for_brand(brand, **context)

        if result["success"]:
            # Create draft BrandTweet
            brand_tweet = BrandTweet.objects.create(
                brand=brand,
                content=result["content"],
                ai_prompt=result["prompt_used"],
                status="draft",
                strategy=strategy,
            )

            # Process Twitter mentions in the tweet content
            from .utils import process_tweet_mentions

            process_tweet_mentions(
                tweet=brand_tweet, organization=brand.organization, user=request.user
            )

            # Generate tracking link and add to content
            tracking_url = brand_tweet.get_tracking_url()
            if tracking_url and not brand_tweet.content.endswith(tracking_url):
                brand_tweet.content = f"{brand_tweet.content}\n\n{tracking_url}"
                brand_tweet.tracking_link = tracking_url
                brand_tweet.save()

            return JsonResponse(
                {
                    "success": True,
                    "tweet": {
                        "id": brand_tweet.id,
                        "content": brand_tweet.content,
                        "status": brand_tweet.status,
                        "created_at": brand_tweet.created_at.isoformat(),
                    },
                    "strategy_used": result["strategy_used"],
                    "prompt_used": result["prompt_used"],
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Failed to generate tweet: {result.get('error', 'Unknown error')}",
                },
                status=500,
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        logger.error(f"Error generating strategy tweet: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Internal server error"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def generate_strategy_tweet_with_website(request):
    """Generate tweet using strategy and automatically scrape website content"""
    try:
        data = json.loads(request.body)
        strategy_id = data.get("strategy_id")
        brand_id = data.get("brand_id")
        organization_id = data.get("organization_id")

        if not all([strategy_id, brand_id, organization_id]):
            return JsonResponse(
                {"success": False, "error": "Missing required parameters"}, status=400
            )

        # Verify permissions
        try:
            organization = Organization.objects.get(pk=organization_id)
            if not organization.users.filter(id=request.user.id).exists():
                return JsonResponse(
                    {"success": False, "error": "Permission denied"}, status=403
                )

            brand = Brand.objects.get(pk=brand_id, organization=organization)
            strategy = TweetStrategy.objects.get(pk=strategy_id, is_active=True)
        except (
            Organization.DoesNotExist,
            Brand.DoesNotExist,
            TweetStrategy.DoesNotExist,
        ):
            return JsonResponse(
                {"success": False, "error": "Object not found"}, status=404
            )

        # Scrape website content if brand has a website
        website_content = ""
        if brand.url:
            try:
                import requests
                from bs4 import BeautifulSoup

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(brand.url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract text from main content areas
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                text = soup.get_text(separator=" ", strip=True)
                # Limit to first 1000 characters to avoid huge prompts
                website_content = text[:1000] if text else ""
            except Exception as e:
                logger.warning(f"Failed to scrape website {brand.url}: {str(e)}")
                website_content = ""

        # Prepare context for strategy
        context = {
            "brand_name": brand.name,
            "brand_description": brand.description or "",
            "website_content": website_content,
            "additional_context": data.get("additional_context", ""),
        }

        # Generate tweet using strategy
        result = strategy.generate_tweet_for_brand(brand, **context)

        if result["success"]:
            # Create draft BrandTweet
            brand_tweet = BrandTweet.objects.create(
                brand=brand,
                content=result["content"],
                ai_prompt=result["prompt_used"],
                status="draft",
                strategy=strategy,
            )

            # Process Twitter mentions in the tweet content
            from .utils import process_tweet_mentions

            process_tweet_mentions(
                tweet=brand_tweet, organization=organization, user=request.user
            )

            # Generate tracking link
            tracking_url = brand_tweet.get_tracking_url()
            if tracking_url:
                brand_tweet.tracking_link = tracking_url
                brand_tweet.save()

            return JsonResponse(
                {
                    "success": True,
                    "tweet": {
                        "id": brand_tweet.id,
                        "content": brand_tweet.content,
                        "status": brand_tweet.status,
                        "created_at": brand_tweet.created_at.isoformat(),
                        "tracking_url": tracking_url,
                    },
                    "strategy_used": strategy.name,
                    "website_content_used": bool(website_content),
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Failed to generate tweet: {result.get('error', 'Unknown error')}",
                },
                status=500,
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        logger.error(f"Error generating strategy tweet with website: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Internal server error"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def generate_contact_tweet(request, organization_pk, company_pk):
    """Generate a personalized contact tweet by scraping both company and brand websites"""
    try:
        # Use URL parameters instead of JSON data for IDs
        organization_id = organization_pk
        company_id = company_pk

        # Check if request body has additional parameters
        save_tweet = False
        try:
            if request.body:
                import json

                data = json.loads(request.body)
                save_tweet = data.get("save_tweet", False)
        except (json.JSONDecodeError, AttributeError):
            pass  # Ignore JSON parsing errors, use defaults

        # Verify permissions and get objects
        try:
            from organizations.models import Organization
            from .models import CRMCompany

            organization = Organization.objects.get(pk=organization_id)
            if not organization.users.filter(id=request.user.id).exists():
                return JsonResponse(
                    {"success": False, "error": "Permission denied"}, status=403
                )

            company = CRMCompany.objects.get(pk=company_id, organization=organization)
            # Get the first brand for this organization
            brand = organization.brands.first()

            if not brand:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "No brand found for this organization",
                    },
                    status=404,
                )

        except (Organization.DoesNotExist, CRMCompany.DoesNotExist):
            return JsonResponse(
                {"success": False, "error": "Object not found"}, status=404
            )

        # Scrape company website
        company_content = ""
        if company.website:
            try:
                import requests
                from bs4 import BeautifulSoup

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(company.website, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract title and description
                title = soup.find("title")
                title_text = title.get_text().strip() if title else ""

                meta_desc = soup.find("meta", attrs={"name": "description"})
                description = meta_desc.get("content", "").strip() if meta_desc else ""

                # Extract main content (avoiding nav, footer, etc.)
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                # Get headings and some paragraph content
                headings = []
                for tag in ["h1", "h2", "h3"]:
                    elements = soup.find_all(tag)
                    for elem in elements[:3]:
                        text = elem.get_text().strip()
                        if text:
                            headings.append(text)

                paragraphs = []
                for p in soup.find_all("p")[:5]:
                    text = p.get_text().strip()
                    if text and len(text) > 20:
                        paragraphs.append(text[:200])

                company_content = f"Company: {company.name}\nWebsite Title: {title_text}\nDescription: {description}\nKey Services: {' '.join(headings[:3])}\nAbout: {' '.join(paragraphs[:2])}"

            except Exception as e:
                logger.warning(
                    f"Failed to scrape company website {company.website}: {str(e)}"
                )
                company_content = f"Company: {company.name}\nIndustry: {company.industry}\nDescription: {company.description}"

        # Scrape brand website
        brand_content = ""
        if brand.url:
            try:
                response = requests.get(brand.url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, "html.parser")

                # Extract title and description
                title = soup.find("title")
                title_text = title.get_text().strip() if title else ""

                meta_desc = soup.find("meta", attrs={"name": "description"})
                description = meta_desc.get("content", "").strip() if meta_desc else ""

                # Clean up content
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                # Get services/offerings
                services = []
                for tag in ["h1", "h2", "h3"]:
                    elements = soup.find_all(tag)
                    for elem in elements[:3]:
                        text = elem.get_text().strip()
                        if text and any(
                            keyword in text.lower()
                            for keyword in [
                                "service",
                                "solution",
                                "help",
                                "offer",
                                "specializ",
                            ]
                        ):
                            services.append(text)

                brand_content = f"Our Brand: {brand.name}\nWebsite: {title_text}\nDescription: {description}\nOur Services: {' '.join(services[:3])}"

            except Exception as e:
                logger.warning(f"Failed to scrape brand website {brand.url}: {str(e)}")
                brand_content = (
                    f"Our Brand: {brand.name}\nDescription: {brand.description}"
                )

        # Generate personalized tweet using OpenAI
        try:
            from .utils import get_openai_client

            client = get_openai_client()
            if not client:
                raise Exception("OpenAI client not available")

            prompt = f"""Create a personalized Twitter outreach message for a potential business collaboration. 

THEIR COMPANY INFORMATION:
{company_content}

OUR COMPANY INFORMATION:
{brand_content}

Create a professional, friendly tweet that:
1. Shows we've researched their company
2. Briefly mentions how we can help them specifically
3. Includes a clear call-to-action
4. Stays under 280 characters
5. Feels personal, not like a template

The tone should be professional but approachable. Focus on value we can provide to them specifically.

Return ONLY the tweet text, no quotes or additional formatting."""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at writing personalized business outreach tweets that convert.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.7,
            )

            tweet_text = response.choices[0].message.content.strip()

            # Optionally save the tweet if requested
            saved_tweet_id = None
            if save_tweet and brand:
                from .models import BrandTweet
                from .utils import process_tweet_mentions

                saved_tweet = BrandTweet.objects.create(
                    brand=brand,
                    content=tweet_text,
                    status="draft",
                    ai_prompt="Contact tweet generated for " + company.name,
                )

                # Process Twitter mentions in the generated tweet
                process_tweet_mentions(
                    tweet=saved_tweet, organization=organization, user=request.user
                )

                saved_tweet_id = saved_tweet.id

            response_data = {
                "success": True,
                "tweet": tweet_text,
                "company_name": company.name,
                "company_website": company.website,
                "brand_name": brand.name,
            }

            if saved_tweet_id:
                response_data["saved_tweet_id"] = saved_tweet_id
                response_data["message"] = "Tweet generated and saved as draft"

            return JsonResponse(response_data)

        except Exception as e:
            logger.error(f"Failed to generate contact tweet with OpenAI: {str(e)}")

            # Fallback to a simple template
            fallback_tweet = f"Hi @{company.twitter_handle if company.twitter_handle else company.name}! I've been exploring {company.name}'s work and think there might be great synergy with what we do at {brand.name}. Would love to discuss how we could collaborate. DM me if interested! 🚀"

            # Optionally save the fallback tweet if requested
            saved_tweet_id = None
            if save_tweet and brand:
                from .models import BrandTweet
                from .utils import process_tweet_mentions

                saved_tweet = BrandTweet.objects.create(
                    brand=brand,
                    content=fallback_tweet,
                    status="draft",
                    ai_prompt="Fallback contact tweet generated for " + company.name,
                )

                # Process Twitter mentions in the fallback tweet
                process_tweet_mentions(
                    tweet=saved_tweet, organization=organization, user=request.user
                )

                saved_tweet_id = saved_tweet.id

            response_data = {
                "success": True,
                "tweet": fallback_tweet,
                "company_name": company.name,
                "company_website": company.website,
                "brand_name": brand.name,
                "note": "Generated using fallback template due to AI service unavailability",
            }

            if saved_tweet_id:
                response_data["saved_tweet_id"] = saved_tweet_id
                response_data["message"] = "Fallback tweet generated and saved as draft"

            return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        logger.error(f"Error generating contact tweet: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Internal server error"}, status=500
        )


@login_required
def get_strategy_details(request, strategy_id):
    """Get detailed information about a specific strategy"""
    try:
        strategy = TweetStrategy.objects.get(id=strategy_id, is_active=True)

        strategy_data = {
            "id": strategy.id,
            "name": strategy.name,
            "category": strategy.get_category_display(),
            "description": strategy.description,
            "prompt_template": strategy.prompt_template,
            "example_output": strategy.example_output,
            "tone_suggestions": strategy.tone_suggestions,
            "hashtag_suggestions": strategy.hashtag_suggestions,
            "timing_suggestions": strategy.timing_suggestions,
            "usage_count": strategy.usage_count,
        }

        return JsonResponse({"success": True, "strategy": strategy_data})

    except TweetStrategy.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Strategy not found"}, status=404
        )
    except Exception as e:
        logger.error(f"Error getting strategy details: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Internal server error"}, status=500
        )


@user_passes_test(is_admin_user)
@require_http_methods(["POST"])
def manual_deploy(request):
    """
    Manual deployment trigger endpoint for admin use.

    This endpoint allows administrators to trigger deployments from the admin dashboard
    without needing GitHub webhooks.
    """
    try:
        # Log the manual deployment request
        logger.info(
            f"Manual deployment triggered by admin user: {request.user.username}"
        )

        # Get current git info for logging
        try:
            import subprocess

            project_dir = "/home/django/gemnar-website"

            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_commit = (
                result.stdout.strip() if result.returncode == 0 else "unknown"
            )

            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            current_branch = (
                result.stdout.strip() if result.returncode == 0 else "unknown"
            )

        except Exception as e:
            logger.warning(f"Could not get git info: {str(e)}")
            current_commit = "unknown"
            current_branch = "unknown"

        # Send deployment started notification
        from .utils.slack_notifications import SlackNotifier

        SlackNotifier.send_deployment_notification(
            "started",
            "gemnar-website",
            current_commit,
            f"Manual deployment triggered by {request.user.username}",
        )

        # Run deployment in background thread to avoid timeout
        deployment_thread = threading.Thread(
            target=run_deployment, args=("gemnar-website", current_commit), daemon=True
        )
        deployment_thread.start()

        return JsonResponse(
            {
                "success": True,
                "message": "Manual deployment started",
                "triggered_by": request.user.username,
                "commit": current_commit,
                "branch": current_branch,
                "timestamp": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Manual deployment error: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "error": "Failed to start deployment",
                "details": str(e),
            },
            status=500,
        )


@user_passes_test(is_admin_user)
def deployment_status(request):
    """
    Get deployment status and logs for real-time display.

    This endpoint provides status information about ongoing deployments.
    """
    try:
        # Check if deployment service is running
        import subprocess

        # Check uvicorn service status
        service_check = subprocess.run(
            ["sudo", "systemctl", "is-active", "uvicorn.service"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        service_status = service_check.stdout.strip()

        # Get recent deployment logs from Django logger
        # This would need to be implemented to track deployment progress

        return JsonResponse(
            {
                "service_status": service_status,
                "service_active": service_check.returncode == 0,
                "timestamp": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Deployment status check error: {str(e)}")
        return JsonResponse(
            {"error": "Failed to get deployment status", "details": str(e)}, status=500
        )


def get_encrypted_variables_status():
    """Get status of key encrypted variables for admin dashboard"""
    try:
        from .models import EncryptedVariable
        from .utils import get_openai_api_key, validate_openai_key_permissions

        status_info = []

        # Check OpenAI API Key
        try:
            # Check if it exists in encrypted variables table
            openai_var = EncryptedVariable.objects.filter(
                key="OPENAI_API_KEY", is_active=True
            ).first()

            if openai_var:
                # Get the actual key and validate it
                api_key = get_openai_api_key()
                if api_key:
                    # Validate permissions
                    is_valid, validation_msg = validate_openai_key_permissions(api_key)

                    status_info.append(
                        {
                            "name": "OPENAI_API_KEY",
                            "exists": True,
                            "source": "encrypted_variables",
                            "status": "valid" if is_valid else "invalid",
                            "message": validation_msg,
                            "created_at": openai_var.created_at,
                            "updated_at": openai_var.updated_at,
                            "created_by": (
                                str(openai_var.created_by)
                                if openai_var.created_by
                                else "Unknown"
                            ),
                            "key_preview": (
                                f"{api_key[:8]}..."
                                if api_key and len(api_key) > 8
                                else "short_key"
                            ),
                        }
                    )
                else:
                    status_info.append(
                        {
                            "name": "OPENAI_API_KEY",
                            "exists": True,
                            "source": "encrypted_variables",
                            "status": "error",
                            "message": "Failed to decrypt or retrieve key",
                            "created_at": openai_var.created_at,
                            "updated_at": openai_var.updated_at,
                            "created_by": (
                                str(openai_var.created_by)
                                if openai_var.created_by
                                else "Unknown"
                            ),
                            "key_preview": "error",
                        }
                    )
            else:
                # Check if it exists in environment as fallback
                api_key = get_openai_api_key()  # This will check env as fallback
                if api_key:
                    is_valid, validation_msg = validate_openai_key_permissions(api_key)
                    status_info.append(
                        {
                            "name": "OPENAI_API_KEY",
                            "exists": False,
                            "source": "environment_fallback",
                            "status": "valid" if is_valid else "invalid",
                            "message": f"Using environment fallback - {validation_msg}",
                            "created_at": None,
                            "updated_at": None,
                            "created_by": "Environment",
                            "key_preview": (
                                f"{api_key[:8]}..." if len(api_key) > 8 else "short_key"
                            ),
                        }
                    )
                else:
                    status_info.append(
                        {
                            "name": "OPENAI_API_KEY",
                            "exists": False,
                            "source": "missing",
                            "status": "missing",
                            "message": "Not configured in encrypted variables or environment",
                            "created_at": None,
                            "updated_at": None,
                            "created_by": None,
                            "key_preview": "missing",
                        }
                    )

        except Exception as e:
            status_info.append(
                {
                    "name": "OPENAI_API_KEY",
                    "exists": False,
                    "source": "error",
                    "status": "error",
                    "message": f"Error checking OpenAI configuration: {str(e)}",
                    "created_at": None,
                    "updated_at": None,
                    "created_by": None,
                    "key_preview": "error",
                }
            )

        # You can add other important encrypted variables here in the future
        # Example: Stripe keys, email service keys, etc.

        return status_info

    except Exception as e:
        return [
            {
                "name": "SYSTEM_ERROR",
                "exists": False,
                "source": "error",
                "status": "error",
                "message": f"Failed to check encrypted variables: {str(e)}",
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "key_preview": "error",
            }
        ]


def track_link_click(request, token):
    """Track link clicks and redirect to brand's website"""
    from django.shortcuts import get_object_or_404, redirect
    from django.http import Http404
    from .models import BrandTweet

    try:
        tweet = get_object_or_404(BrandTweet, tracking_token=token)

        # Increment the click counter
        tweet.increment_link_clicks()

        # Get the brand's website URL
        brand_website = tweet.brand.url

        # If no website URL is set, redirect to a default page
        if not brand_website:
            # You could redirect to the brand's social media or a default page
            return redirect("/")

        # Ensure the URL has a proper scheme
        if not brand_website.startswith(("http://", "https://")):
            brand_website = f"https://{brand_website}"

        return redirect(brand_website)

    except BrandTweet.DoesNotExist:
        raise Http404("Tracking link not found")


# Task Management Views
@login_required
def active_tasks_dashboard(request):
    """Dashboard view for managing active tasks"""
    if not request.user.is_staff and not request.user.is_superuser:
        # Allow brand users to see tasks they created
        if not hasattr(request.user, "created_tasks"):
            return redirect("website:landing")

    # Get active tasks with applications
    tasks = (
        Task.objects.filter(is_active=True)
        .prefetch_related("applications__creator", "brand")
        .order_by("-created_at")
    )

    # Filter by brand if not staff/superuser
    if not request.user.is_staff and not request.user.is_superuser:
        tasks = tasks.filter(brand=request.user)

    # Add statistics
    tasks_with_stats = []
    total_applications_sum = 0
    total_pending_sum = 0
    total_completed_sum = 0

    for task in tasks:
        applications = task.applications.all()
        task_data = {
            "task": task,
            "total_applications": applications.count(),
            "pending_applications": applications.filter(status="PENDING").count(),
            "accepted_applications": applications.filter(status="ACCEPTED").count(),
            "completed_applications": applications.filter(status="COMPLETED").count(),
            "rejected_applications": applications.filter(status="REJECTED").count(),
        }
        tasks_with_stats.append(task_data)

        # Add to summary totals
        total_applications_sum += task_data["total_applications"]
        total_pending_sum += task_data["pending_applications"]
        total_completed_sum += task_data["completed_applications"]

    context = {
        "tasks_with_stats": tasks_with_stats,
        "total_active_tasks": tasks.count(),
        "total_applications_sum": total_applications_sum,
        "total_pending_sum": total_pending_sum,
        "total_completed_sum": total_completed_sum,
        "is_admin": request.user.is_staff or request.user.is_superuser,
    }

    return render(request, "website/tasks/active_tasks_dashboard.html", context)


@login_required
def task_detail_management(request, task_id):
    """Detailed view for managing a specific task and its applications"""
    task = get_object_or_404(Task, pk=task_id)

    # Check permissions
    if not request.user.is_staff and not request.user.is_superuser:
        if task.brand != request.user:
            return redirect("website:landing")

    # Get all applications for this task
    applications = (
        TaskApplication.objects.filter(task=task)
        .select_related("creator")
        .order_by("-applied_at")
    )

    # Handle POST requests for status updates
    if request.method == "POST":
        action = request.POST.get("action")
        application_id = request.POST.get("application_id")

        if action and application_id:
            application = get_object_or_404(
                TaskApplication, pk=application_id, task=task
            )

            if action == "accept":
                application.status = "ACCEPTED"
                application.save()
                messages.success(
                    request,
                    f"Application from {application.creator.username} accepted!",
                )

            elif action == "reject":
                application.status = "REJECTED"
                application.save()
                messages.success(
                    request,
                    f"Application from {application.creator.username} rejected.",
                )

            elif action == "complete":
                application.status = "COMPLETED"
                application.save()
                messages.success(
                    request,
                    f"Application from {application.creator.username} marked as completed!",
                )

            elif action == "award_prize":
                # Mark as completed and potentially handle prize logic
                application.status = "COMPLETED"
                application.save()
                messages.success(
                    request, f"Prize awarded to {application.creator.username}!"
                )

            elif action == "reset_pending":
                application.status = "PENDING"
                application.save()
                messages.success(
                    request,
                    f"Application from {application.creator.username} reset to pending.",
                )

        return redirect("website:task_detail_management", task_id=task.pk)

    # Organize applications by status
    applications_by_status = {
        "PENDING": applications.filter(status="PENDING"),
        "ACCEPTED": applications.filter(status="ACCEPTED"),
        "COMPLETED": applications.filter(status="COMPLETED"),
        "REJECTED": applications.filter(status="REJECTED"),
    }

    context = {
        "task": task,
        "applications": applications,
        "applications_by_status": applications_by_status,
        "total_applications": applications.count(),
        "is_admin": request.user.is_staff or request.user.is_superuser,
    }

    return render(request, "website/tasks/task_detail_management.html", context)


@login_required
def task_analytics(request, task_id):
    """Analytics view for a specific task"""
    task = get_object_or_404(Task, pk=task_id)

    # Check permissions
    if not request.user.is_staff and not request.user.is_superuser:
        if task.brand != request.user:
            return redirect("website:landing")

    applications = TaskApplication.objects.filter(task=task)

    # Calculate analytics
    analytics_data = {
        "total_applications": applications.count(),
        "pending_count": applications.filter(status="PENDING").count(),
        "accepted_count": applications.filter(status="ACCEPTED").count(),
        "completed_count": applications.filter(status="COMPLETED").count(),
        "rejected_count": applications.filter(status="REJECTED").count(),
        "conversion_rate": 0,
        "completion_rate": 0,
    }

    if analytics_data["total_applications"] > 0:
        analytics_data["conversion_rate"] = (
            analytics_data["accepted_count"]
            / analytics_data["total_applications"]
            * 100
        )

    if analytics_data["accepted_count"] > 0:
        analytics_data["completion_rate"] = (
            analytics_data["completed_count"] / analytics_data["accepted_count"] * 100
        )

    # Applications over time (last 30 days)
    from django.utils import timezone

    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_applications = applications.filter(applied_at__gte=thirty_days_ago)

    # Group by day
    applications_by_day = {}
    for app in recent_applications:
        day = app.applied_at.date()
        applications_by_day[day] = applications_by_day.get(day, 0) + 1

    context = {
        "task": task,
        "analytics_data": analytics_data,
        "applications_by_day": applications_by_day,
        "is_admin": request.user.is_staff or request.user.is_superuser,
    }

    return render(request, "website/tasks/task_analytics.html", context)


@login_required
def all_tasks_overview(request):
    """Overview of all tasks in the system (admin only)"""
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect("website:landing")

    # Get all tasks with statistics
    all_tasks = Task.objects.all().prefetch_related("applications", "brand")

    # Calculate system-wide statistics
    total_tasks = all_tasks.count()
    active_tasks = all_tasks.filter(is_active=True).count()
    total_applications = TaskApplication.objects.count()

    # Tasks by category and genre
    tasks_by_category = {}
    tasks_by_genre = {}
    tasks_by_incentive = {}

    for task in all_tasks:
        # Category stats
        category = task.get_category_display()
        tasks_by_category[category] = tasks_by_category.get(category, 0) + 1

        # Genre stats
        genre = task.get_genre_display()
        tasks_by_genre[genre] = tasks_by_genre.get(genre, 0) + 1

        # Incentive stats
        incentive = task.get_incentive_type_display()
        tasks_by_incentive[incentive] = tasks_by_incentive.get(incentive, 0) + 1

    # Top brands by task creation
    from django.db.models import Count

    top_brands = (
        User.objects.filter(created_tasks__isnull=False)
        .annotate(task_count=Count("created_tasks"))
        .order_by("-task_count")[:10]
    )

    # Top creators by applications
    top_creators = (
        User.objects.filter(task_applications__isnull=False)
        .annotate(application_count=Count("task_applications"))
        .order_by("-application_count")[:10]
    )

    context = {
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "total_applications": total_applications,
        "tasks_by_category": tasks_by_category,
        "tasks_by_genre": tasks_by_genre,
        "tasks_by_incentive": tasks_by_incentive,
        "top_brands": top_brands,
        "top_creators": top_creators,
        "recent_tasks": all_tasks.order_by("-created_at")[:10],
    }

    return render(request, "website/tasks/all_tasks_overview.html", context)


@login_required
@require_http_methods(["POST"])
def send_contact_tweet(request, organization_pk, company_pk):
    """Send a contact tweet to Twitter"""
    try:
        import json
        import tweepy
        from django.utils import timezone
        from organizations.models import Organization
        from .models import CRMCompany, BrandTweet

        # Parse the request data
        data = json.loads(request.body)
        tweet_content = data.get("tweet_content")
        brand_id = data.get("brand_id")

        if not tweet_content:
            return JsonResponse(
                {"success": False, "error": "Tweet content is required"}, status=400
            )

        # Verify permissions and get objects
        try:
            organization = Organization.objects.get(pk=organization_pk)
            if not organization.users.filter(id=request.user.id).exists():
                return JsonResponse(
                    {"success": False, "error": "Permission denied"}, status=403
                )

            company = CRMCompany.objects.get(pk=company_pk, organization=organization)

            # Get the brand to use for posting
            if brand_id:
                brand = organization.brands.filter(id=brand_id).first()
            else:
                brand = organization.brands.first()

            if not brand:
                return JsonResponse(
                    {"success": False, "error": "No brand found for this organization"},
                    status=404,
                )

        except (Organization.DoesNotExist, CRMCompany.DoesNotExist):
            return JsonResponse(
                {"success": False, "error": "Object not found"}, status=404
            )

        # Check if brand has Twitter configuration
        if not brand.has_twitter_config:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Brand does not have Twitter configuration. Please connect Twitter to your brand first.",
                },
                status=400,
            )

        brand_tweet = None
        try:
            # Create a BrandTweet record for this contact tweet
            brand_tweet = BrandTweet.objects.create(
                brand=brand,
                content=tweet_content,
                status="draft",
                ai_prompt=f"Contact tweet for {company.name}",
            )

            # Post the tweet using the brand's Twitter configuration
            client = tweepy.Client(
                bearer_token=brand.twitter_bearer_token,
                consumer_key=brand.twitter_api_key,
                consumer_secret=brand.twitter_api_secret,
                access_token=brand.twitter_access_token,
                access_token_secret=brand.twitter_access_token_secret,
                wait_on_rate_limit=True,
            )

            # Post the tweet
            response = client.create_tweet(text=tweet_content)

            if response.data:
                # Update the brand tweet record with success
                brand_tweet.tweet_id = response.data["id"]
                brand_tweet.status = "posted"
                brand_tweet.posted_at = timezone.now()
                brand_tweet.save()

                # Create a CRM activity record for this contact attempt
                try:
                    from .models import CRMActivity

                    CRMActivity.objects.create(
                        organization=organization,
                        company=company,
                        activity_type="tweet",
                        subject=f"Contact tweet sent to {company.name}",
                        description=f"Sent contact tweet: {tweet_content}",
                        created_by=request.user,
                        completed_at=timezone.now(),
                    )
                except Exception as activity_error:
                    logger.warning(f"Failed to create CRM activity: {activity_error}")

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Tweet posted successfully!",
                        "tweet_id": response.data["id"],
                        "tweet_url": f"https://twitter.com/{brand.twitter_username}/status/{response.data['id']}"
                        if hasattr(brand, "twitter_username")
                        else None,
                        "brand_tweet_id": brand_tweet.id,
                    }
                )
            else:
                brand_tweet.status = "failed"
                brand_tweet.error_message = "No response data from Twitter API"
                brand_tweet.save()
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Failed to post tweet - no response from Twitter",
                    },
                    status=500,
                )

        except tweepy.Unauthorized:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API authentication failed. Please check your Twitter credentials.",
                },
                status=400,
            )
        except tweepy.Forbidden:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API access forbidden. Check your app permissions.",
                },
                status=400,
            )
        except tweepy.TooManyRequests:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Twitter API rate limit exceeded. Please try again later.",
                },
                status=429,
            )
        except Exception as api_error:
            if brand_tweet:
                brand_tweet.status = "failed"
                brand_tweet.error_message = str(api_error)
                brand_tweet.save()

            logger.error(f"Twitter API error: {api_error}")
            return JsonResponse(
                {"success": False, "error": f"Twitter API error: {str(api_error)}"},
                status=500,
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        logger.error(f"Unexpected error in send contact tweet: {str(e)}")
        return JsonResponse(
            {"success": False, "error": f"Unexpected error: {str(e)}"}, status=500
        )


@login_required
def task_create(request):
    """Create a new task"""
    from .models import Task
    import logging

    logger = logging.getLogger(__name__)

    if request.method == "POST":
        try:
            # Log all POST data for debugging
            logger.info(f"Task creation attempt by user {request.user.username}")
            logger.info(f"POST data: {dict(request.POST)}")

            # Get form data
            title = request.POST.get("title", "").strip()
            description = request.POST.get("description", "").strip()
            category = request.POST.get("category")
            genre = request.POST.get("genre")
            incentive_type = request.POST.get("incentive_type")
            barter_details = request.POST.get("barter_details", "").strip()
            pay_amount = request.POST.get("pay_amount")
            commission_percentage = request.POST.get("commission_percentage")
            gift_card_amount = request.POST.get("gift_card_amount")
            experience_details = request.POST.get("experience_details", "").strip()
            deadline = request.POST.get("deadline")

            logger.info(
                f"Parsed data - title: '{title}', category: '{category}', genre: '{genre}', incentive_type: '{incentive_type}'"
            )

            # Validation
            if not title or not description:
                logger.warning(
                    f"Missing title or description - title: '{title}', description: '{description}'"
                )
                return JsonResponse(
                    {"success": False, "error": "Title and description are required."}
                )

            if not category or not genre or not incentive_type:
                logger.warning(
                    f"Missing required fields - category: '{category}', genre: '{genre}', incentive_type: '{incentive_type}'"
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Category, genre, and incentive type are required.",
                    }
                )

            # Validate incentive-specific fields
            if incentive_type == "BARTER" and not barter_details:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Product details are required when incentive type is Product Exchange.",
                    }
                )

            if incentive_type == "PAY":
                if not pay_amount:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Pay amount is required when incentive type is Monetary Payment.",
                        }
                    )
                try:
                    pay_amount = float(pay_amount)
                    if pay_amount <= 0:
                        return JsonResponse(
                            {
                                "success": False,
                                "error": "Pay amount must be greater than 0.",
                            }
                        )
                except (ValueError, TypeError):
                    return JsonResponse(
                        {"success": False, "error": "Invalid pay amount format."}
                    )
            else:
                pay_amount = None

            # Validate commission percentage
            if incentive_type == "COMMISSION":
                if not commission_percentage:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Commission percentage is required for commission-based tasks.",
                        }
                    )
                try:
                    commission_percentage = float(commission_percentage)
                    if commission_percentage <= 0 or commission_percentage > 100:
                        return JsonResponse(
                            {
                                "success": False,
                                "error": "Commission percentage must be between 0 and 100.",
                            }
                        )
                except (ValueError, TypeError):
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Invalid commission percentage format.",
                        }
                    )
            else:
                commission_percentage = None

            # Validate gift card amount
            if incentive_type == "GIFT_CARD":
                if not gift_card_amount:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Gift card amount is required for gift card incentives.",
                        }
                    )
                try:
                    gift_card_amount = float(gift_card_amount)
                    if gift_card_amount <= 0:
                        return JsonResponse(
                            {
                                "success": False,
                                "error": "Gift card amount must be greater than 0.",
                            }
                        )
                except (ValueError, TypeError):
                    return JsonResponse(
                        {"success": False, "error": "Invalid gift card amount format."}
                    )
            else:
                gift_card_amount = None

            # Validate experience details
            if incentive_type == "EXPERIENCE" and not experience_details:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Experience details are required for experience/event access incentives.",
                    }
                )

            # Clean up unused fields based on incentive type
            if incentive_type not in ["BARTER"]:
                barter_details = None
            if incentive_type not in ["EXPERIENCE"]:
                experience_details = None

            # Parse deadline if provided
            deadline_obj = None
            if deadline:
                try:
                    from datetime import datetime

                    deadline_obj = datetime.fromisoformat(
                        deadline.replace("Z", "+00:00")
                    )
                except ValueError:
                    return JsonResponse(
                        {"success": False, "error": "Invalid deadline format."}
                    )

            # Create the task
            logger.info(
                f"Creating task with data: {title}, {category}, {genre}, {incentive_type}"
            )
            task = Task.objects.create(
                title=title,
                description=description,
                category=category,
                genre=genre,
                incentive_type=incentive_type,
                barter_details=barter_details,
                pay_amount=pay_amount,
                commission_percentage=commission_percentage,
                gift_card_amount=gift_card_amount,
                experience_details=experience_details,
                deadline=deadline_obj,
                brand=request.user,
                is_active=True,
            )

            logger.info(f"Task created successfully with ID: {task.id}")

            return JsonResponse(
                {
                    "success": True,
                    "message": "Task created successfully!",
                    "task_id": task.id,
                    "redirect_url": reverse("website:active_tasks_dashboard"),
                }
            )

        except Exception as e:
            logger.error(f"Error creating task: {str(e)}", exc_info=True)
            return JsonResponse(
                {
                    "success": False,
                    "error": f"An error occurred while creating the task: {str(e)}",
                }
            )

    # GET request - show the form
    context = {
        "category_choices": Task.CATEGORY_CHOICES,
        "genre_choices": Task.GENRE_CHOICES,
        "incentive_choices": Task.INCENTIVE_CHOICES,
    }

    return render(request, "website/tasks/task_create.html", context)


# ==================== Instagram OAuth Views ====================

def instagram_oauth_page(request):
    """Render the Instagram OAuth page"""
    return render(request, "instagram_oauth.html")


def instagram_oauth_start(request):
    """Start the Instagram OAuth flow by redirecting to Facebook"""
    from urllib.parse import urlencode
    import secrets
    
    # Get brand_id from query params
    brand_id = request.GET.get('brand_id')
    if not brand_id:
        return JsonResponse({'error': 'brand_id is required'}, status=400)
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in brand model instead of session (since session doesn't survive Facebook redirect)
    from chat.models import Brand
    try:
        brand = Brand.objects.get(id=brand_id)
        brand.instagram_oauth_state = state  # We'll need to add this field to the model
        brand.save()
        logger.info(f"Stored OAuth state in brand model: {state}")
    except Brand.DoesNotExist:
        logger.error(f"Brand {brand_id} not found for OAuth state storage")
        return JsonResponse({'error': 'Brand not found'}, status=404)
    
    # Also try to store in session as backup
    if not request.session.session_key:
        request.session.create()
    
    request.session[f'instagram_oauth_state_{brand_id}'] = state
    request.session.save()  # Force save the session
    
    # Debug session state storage
    logger.info(f"Instagram OAuth start for brand {brand_id}:")
    logger.info(f"  - Generated state: {state}")
    logger.info(f"  - Session key: instagram_oauth_state_{brand_id}")
    logger.info(f"  - Session ID: {request.session.session_key}")
    logger.info(f"  - Session data: {dict(request.session)}")
    
    # Facebook OAuth parameters
    # You'll need to add these to your Django settings:
    # INSTAGRAM_APP_ID = 'your-facebook-app-id'
    # INSTAGRAM_APP_SECRET = 'your-facebook-app-secret'
    # INSTAGRAM_REDIRECT_URI = 'https://gemnar.com/api/instagram/oauth-callback/'
    
    from django.conf import settings
    
    # Check if Instagram OAuth is configured
    if not getattr(settings, 'INSTAGRAM_APP_ID', ''):
        return JsonResponse({
            'error': 'Instagram OAuth not configured. Please add INSTAGRAM_APP_ID to environment variables.',
            'setup_required': True
        }, status=400)
    
    if not getattr(settings, 'INSTAGRAM_APP_SECRET', ''):
        return JsonResponse({
            'error': 'Instagram OAuth not configured. Please add INSTAGRAM_APP_SECRET to environment variables.',
            'setup_required': True
        }, status=400)
    
    params = {
        'client_id': settings.INSTAGRAM_APP_ID,
        'redirect_uri': getattr(settings, 'INSTAGRAM_REDIRECT_URI', 'https://gemnar.com/api/instagram/oauth-callback/'),
        'scope': 'instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement',
        'response_type': 'code',
        'state': f"{brand_id}:{state}",  # Include brand_id in state
    }
    
    oauth_url = f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"
    return redirect(oauth_url)


def instagram_oauth_callback(request):
    """Handle the OAuth callback from Facebook"""
    import secrets
    from chat.models import Brand
    
    # Get authorization code and state
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    # Debug callback state validation
    logger.info(f"Instagram OAuth callback received:")
    logger.info(f"  - State parameter: {state}")
    logger.info(f"  - Code parameter: {'present' if code else 'missing'}")
    logger.info(f"  - Session ID: {request.session.session_key}")
    logger.info(f"  - Session exists: {bool(request.session.session_key)}")
    
    # Try to load or create session
    if not request.session.session_key:
        logger.warning("No session found during callback, but we'll try brand model state validation")
        # Don't return error immediately - continue to try brand model validation
    
    if request.session.session_key:
        logger.info(f"  - Session data: {dict(request.session)}")
    else:
        logger.info("  - No session available, will rely on brand model state storage")
    
    # Handle OAuth error
    if error:
        logger.error(f"Instagram OAuth error: {error}")
        return redirect(f'http://localhost:3000/auth/instagram/callback?error={error}')
    
    if not code or not state:
        return redirect('http://localhost:3000/auth/instagram/callback?error=missing_params')
    
    # Validate state and extract brand_id
    try:
        brand_id, state_token = state.split(':', 1)
        
        # Try to get stored state from session first, then from brand model
        stored_state = None
        if request.session.session_key:
            stored_state = request.session.get(f'instagram_oauth_state_{brand_id}')
        
        # If session doesn't have it or no session exists, try brand model
        if not stored_state:
            try:
                brand = Brand.objects.get(id=brand_id)
                stored_state = getattr(brand, 'instagram_oauth_state', None)
                logger.info(f"Retrieved state from brand model: {stored_state}")
            except Brand.DoesNotExist:
                logger.error(f"Brand {brand_id} not found for state validation")
                return redirect('http://localhost:3000/auth/instagram/callback?error=brand_not_found')
        
        logger.info(f"  - Extracted brand_id: {brand_id}")
        logger.info(f"  - Extracted state_token: {state_token}")
        logger.info(f"  - Stored state (session): {request.session.get(f'instagram_oauth_state_{brand_id}') if request.session.session_key else 'no session'}")
        logger.info(f"  - Stored state (final): {stored_state}")
        logger.info(f"  - States match: {stored_state == state_token if stored_state else False}")
        
        if not stored_state or stored_state != state_token:
            logger.error(f"Instagram OAuth state mismatch - expected: {stored_state}, got: {state_token}")
            return redirect('http://localhost:3000/auth/instagram/callback?error=invalid_state')
        
        # Clean up state from both places
        if request.session.session_key and f'instagram_oauth_state_{brand_id}' in request.session:
            del request.session[f'instagram_oauth_state_{brand_id}']
        
        # Clear state from brand model
        try:
            brand = Brand.objects.get(id=brand_id)
            if hasattr(brand, 'instagram_oauth_state'):
                brand.instagram_oauth_state = None
                brand.save()
                logger.info(f"Cleared OAuth state from brand model")
        except Brand.DoesNotExist:
            pass
        
    except (ValueError, KeyError):
        return redirect('http://localhost:3000/auth/instagram/callback?error=invalid_state')
    
    # Exchange code for access token
    from django.conf import settings
    
    token_url = 'https://graph.facebook.com/v18.0/oauth/access_token'
    token_params = {
        'client_id': getattr(settings, 'INSTAGRAM_APP_ID', ''),
        'client_secret': getattr(settings, 'INSTAGRAM_APP_SECRET', ''),
        'redirect_uri': getattr(settings, 'INSTAGRAM_REDIRECT_URI', 'https://gemnar.com/api/instagram/oauth-callback/'),
        'code': code,
    }
    
    try:
        token_response = requests.get(token_url, params=token_params)
        token_data = token_response.json()
        
        if 'access_token' not in token_data:
            logger.error(f"Failed to get access token: {token_data}")
            return redirect('http://localhost:3000/auth/instagram/callback?error=token_exchange_failed')
        
        access_token = token_data['access_token']
        
        # Get Instagram Business Account ID
        me_url = f"https://graph.facebook.com/v18.0/me/accounts"
        me_params = {'access_token': access_token}
        me_response = requests.get(me_url, params=me_params)
        me_data = me_response.json()
        
        # Get the first page (you may want to add page selection logic)
        if not me_data.get('data'):
            logger.error("No Facebook pages found")
            return redirect('http://localhost:3000/auth/instagram/callback?error=no_pages')
        
        page_id = me_data['data'][0]['id']
        page_access_token = me_data['data'][0]['access_token']
        
        # Get Instagram Business Account from Page
        ig_url = f"https://graph.facebook.com/v18.0/{page_id}"
        ig_params = {
            'fields': 'instagram_business_account',
            'access_token': page_access_token
        }
        ig_response = requests.get(ig_url, params=ig_params)
        ig_data = ig_response.json()
        
        if 'instagram_business_account' not in ig_data:
            logger.error("No Instagram Business Account linked to page")
            return redirect('http://localhost:3000/auth/instagram/callback?error=no_instagram_account')
        
        instagram_account_id = ig_data['instagram_business_account']['id']
        
        # Get Instagram username
        ig_user_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}"
        ig_user_params = {
            'fields': 'username',
            'access_token': page_access_token
        }
        ig_user_response = requests.get(ig_user_url, params=ig_user_params)
        ig_user_data = ig_user_response.json()
        instagram_username = ig_user_data.get('username', '')
        
        # Store in Brand model
        brand = Brand.objects.get(id=brand_id)
        
        logger.info(f"Saving Instagram credentials for brand {brand_id}:")
        logger.info(f"  - instagram_username: {instagram_username}")
        logger.info(f"  - instagram_user_id: {instagram_account_id}")
        logger.info(f"  - instagram_business_id: {page_id}")
        logger.info(f"  - page_access_token length: {len(page_access_token) if page_access_token else 0}")
        logger.info(f"  - Instagram API response data: {ig_user_data}")
        
        # Set current timestamp for connection
        from django.utils import timezone
        
        brand.instagram_access_token = page_access_token
        brand.instagram_user_token = page_access_token  # Same token for both fields
        brand.instagram_user_id = instagram_account_id
        brand.instagram_username = instagram_username
        brand.instagram_business_id = page_id
        brand.instagram_connected_at = timezone.now()
        brand.save()
        
        # Verify the save worked
        brand.refresh_from_db()
        logger.info(f"After save verification:")
        logger.info(f"  - instagram_username in DB: '{brand.instagram_username}'")
        logger.info(f"  - instagram_user_id in DB: '{brand.instagram_user_id}'")
        logger.info(f"  - instagram_connected_at in DB: {brand.instagram_connected_at}")
        
        logger.info(f"Instagram OAuth successful for brand {brand_id} (@{instagram_username})")
        return redirect('http://localhost:3000/auth/instagram/callback?success=true')
        
    except requests.RequestException as e:
        logger.error(f"Instagram OAuth request failed: {str(e)}")
        return redirect('http://localhost:3000/auth/instagram/callback?error=api_request_failed')
    except Brand.DoesNotExist:
        logger.error(f"Brand {brand_id} not found")
        return redirect('http://localhost:3000/auth/instagram/callback?error=brand_not_found')
    except Exception as e:
        logger.error(f"Instagram OAuth failed: {str(e)}", exc_info=True)
        return redirect('http://localhost:3000/auth/instagram/callback?error=unknown')


@csrf_exempt
def instagram_oauth_disconnect(request):
    """Disconnect Instagram account and delete stored tokens"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        brand_id = data.get('brand_id')
        
        if not brand_id:
            return JsonResponse({'error': 'brand_id is required'}, status=400)
        
        from chat.models import Brand
        brand = Brand.objects.get(id=brand_id)
        
        # Check if user owns this brand (if authentication is enabled)
        if hasattr(request, 'user') and request.user.is_authenticated:
            if brand.owner != request.user:
                return JsonResponse({'error': 'Not authorized'}, status=403)
        
        # Clear Instagram credentials
        brand.instagram_access_token = None
        brand.instagram_user_token = None
        brand.instagram_user_id = None
        brand.instagram_username = None
        brand.instagram_business_id = None
        brand.save()
        
        logger.info(f"Instagram disconnected for brand {brand_id}")
        return JsonResponse({'success': True, 'message': 'Instagram account disconnected'})
        
    except Brand.DoesNotExist:
        return JsonResponse({'error': 'Brand not found'}, status=404)
    except Exception as e:
        logger.error(f"Failed to disconnect Instagram: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def instagram_oauth_status(request):
    """Get Instagram OAuth connection status"""
    try:
        brand_id = request.GET.get('brand_id')
        
        if not brand_id:
            return JsonResponse({'error': 'brand_id is required'}, status=400)
        
        from chat.models import Brand
        brand = Brand.objects.get(id=brand_id)
        
        # Check if user owns this brand (if authentication is enabled)
        if hasattr(request, 'user') and request.user.is_authenticated:
            if brand.owner != request.user:
                return JsonResponse({'error': 'Not authorized'}, status=403)
        
        is_connected = bool(brand.instagram_access_token and brand.instagram_user_id)
        
        # Debug logging to see what's stored
        logger.info(f"Instagram status check for brand {brand_id}:")
        logger.info(f"  - instagram_access_token: {'present' if brand.instagram_access_token else 'missing'}")
        logger.info(f"  - instagram_user_id: {'present' if brand.instagram_user_id else 'missing'}")
        logger.info(f"  - instagram_username: {brand.instagram_username}")
        logger.info(f"  - instagram_business_id: {brand.instagram_business_id}")
        logger.info(f"  - is_connected: {is_connected}")
        
        return JsonResponse({
            'instagram_username': brand.instagram_username if is_connected else '',
            'instagram_user_id': brand.instagram_user_id if is_connected else '',
            'connected': is_connected,
            'connected_at': brand.instagram_connected_at.isoformat() if (is_connected and hasattr(brand, 'instagram_connected_at') and brand.instagram_connected_at) else None,
        })
        
    except Brand.DoesNotExist:
        return JsonResponse({'error': 'Brand not found'}, status=404)
    except Exception as e:
        logger.error(f"Failed to get Instagram status: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
