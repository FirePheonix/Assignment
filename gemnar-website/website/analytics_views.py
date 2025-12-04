"""
Analytics views for brand dashboard integration
"""

import json
import gzip
import secrets
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.db import transaction
from .analytics_models import (
    AnalyticsProject,
    AnalyticsSession,
    AnalyticsPageView,
    AnalyticsRecording,
)
from .models import Brand


def calculate_funnel_data(project, start_date, end_date):
    """Calculate funnel data for conversion analysis"""

    # Define funnel steps based on common patterns
    funnel_steps = [
        {"name": "Landing Page", "paths": ["/"]},
        {
            "name": "Product/Service Pages",
            "paths": ["/products", "/services", "/pricing"],
        },
        {"name": "Contact/About Pages", "paths": ["/contact", "/about"]},
        {"name": "Form Pages", "paths": ["/signup", "/register", "/subscribe"]},
    ]

    # Calculate sessions that reached each step
    total_sessions = project.sessions.filter(
        started_at__gte=start_date, started_at__lte=end_date
    ).count()

    funnel_data = []
    for i, step in enumerate(funnel_steps):
        # Find sessions that visited any of the paths in this step
        sessions_with_step = (
            project.sessions.filter(
                started_at__gte=start_date,
                started_at__lte=end_date,
                pageviews__path__in=[path for path in step["paths"]],
            )
            .distinct()
            .count()
        )

        conversion_rate = (
            (sessions_with_step / total_sessions * 100) if total_sessions > 0 else 0
        )
        drop_off_rate = (100 - conversion_rate) if i > 0 else 0

        funnel_data.append(
            {
                "step": i + 1,
                "name": step["name"],
                "sessions": sessions_with_step,
                "conversion_rate": round(conversion_rate, 1),
                "drop_off_rate": round(drop_off_rate, 1),
            }
        )

    return funnel_data


def calculate_conversion_metrics(project, start_date, end_date):
    """Calculate conversion metrics"""
    # Goal completion tracking (can be customized)
    goal_paths = ["/thank-you", "/success", "/confirmation", "/checkout-complete"]

    total_sessions = project.sessions.filter(
        started_at__gte=start_date, started_at__lte=end_date
    ).count()

    conversion_sessions = (
        project.sessions.filter(
            started_at__gte=start_date,
            started_at__lte=end_date,
            pageviews__path__in=goal_paths,
        )
        .distinct()
        .count()
    )

    conversion_rate = (
        (conversion_sessions / total_sessions * 100) if total_sessions > 0 else 0
    )

    return {
        "total_sessions": total_sessions,
        "conversion_sessions": conversion_sessions,
        "conversion_rate": round(conversion_rate, 2),
        "goal_paths": goal_paths,
    }


@login_required
def analytics_dashboard(request, brand_id):
    """Main analytics dashboard for a brand"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)

    # Get the analytics project for this brand
    project = brand.analytics_projects.filter(is_active=True).first()

    if not project:
        return redirect("website:analytics_setup", brand_id=brand_id)

    # Calculate date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    # Get basic metrics
    total_sessions = project.sessions.filter(started_at__gte=start_date).count()

    total_pageviews = AnalyticsPageView.objects.filter(
        session__project=project, started_at__gte=start_date
    ).count()

    # Calculate average session duration with fallback calculation
    sessions_for_duration = project.sessions.filter(started_at__gte=start_date)

    # First try to get average from stored duration_seconds
    # Only include positive, reasonable durations (not 0 and not > 24 hours)
    stored_avg_duration = sessions_for_duration.filter(
        duration_seconds__gt=0,
        duration_seconds__lt=86400,  # 24 hours max
    ).aggregate(avg_duration=Avg("duration_seconds"))["avg_duration"]

    # If no stored durations or they're all zero, calculate from timestamps
    if not stored_avg_duration or stored_avg_duration == 0:
        # Calculate duration from start/last_activity timestamps
        calculated_durations = []
        for session in sessions_for_duration:
            if session.last_activity and session.started_at:
                time_diff = session.last_activity - session.started_at
                duration = time_diff.total_seconds()
                # Only include positive durations between 1 second and 24 hours
                if 1 <= duration <= 86400:
                    calculated_durations.append(duration)

        if calculated_durations:
            total_duration = sum(calculated_durations)
            avg_session_duration = total_duration / len(calculated_durations)
        else:
            avg_session_duration = 0
    else:
        avg_session_duration = stored_avg_duration

    bounce_rate = 0
    if total_sessions > 0:
        bounced_sessions = project.sessions.filter(
            started_at__gte=start_date, is_bounce=True
        ).count()
        bounce_rate = (bounced_sessions / total_sessions) * 100

    # Get top pages with better duration filtering
    top_pages = (
        AnalyticsPageView.objects.filter(
            session__project=project, started_at__gte=start_date
        )
        .values("path")
        .annotate(
            views=Count("id"),
            avg_duration=Avg(
                "duration_seconds",
                filter=Q(
                    duration_seconds__gt=0,
                    duration_seconds__lt=3600,  # 1 hour max for pageviews
                ),
            ),
            avg_load_time=Avg(
                "load_time_ms",
                filter=Q(
                    load_time_ms__isnull=False,
                    load_time_ms__gt=0,
                    load_time_ms__lt=30000,  # 30 seconds max load time
                ),
            ),
        )
        .order_by("-views")[:10]
    )

    # Calculate average page load time for the project
    # First try with strict filtering
    avg_page_load_time = AnalyticsPageView.objects.filter(
        session__project=project,
        started_at__gte=start_date,
        load_time_ms__isnull=False,
        load_time_ms__gt=0,
        load_time_ms__lt=30000,  # 30 seconds max
    ).aggregate(avg_load=Avg("load_time_ms"))["avg_load"]

    # If no data with strict filtering, try with more lenient filtering
    if not avg_page_load_time:
        avg_page_load_time = AnalyticsPageView.objects.filter(
            session__project=project,
            started_at__gte=start_date,
            load_time_ms__isnull=False,
            load_time_ms__gt=0,
        ).aggregate(avg_load=Avg("load_time_ms"))["avg_load"]

    # Final fallback to 0 if still no data
    avg_page_load_time = avg_page_load_time or 0

    # Get device breakdown
    device_breakdown = (
        project.sessions.filter(started_at__gte=start_date)
        .values("device_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Get browser breakdown
    browser_breakdown = (
        project.sessions.filter(started_at__gte=start_date)
        .values("browser")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    # Get daily traffic for the chart
    daily_traffic = []
    for i in range(30):
        date = start_date + timedelta(days=i)
        sessions = project.sessions.filter(started_at__date=date.date()).count()
        pageviews = AnalyticsPageView.objects.filter(
            session__project=project, started_at__date=date.date()
        ).count()
        daily_traffic.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "sessions": sessions,
                "pageviews": pageviews,
            }
        )

    # Get recent sessions for activity feed
    recent_sessions = project.sessions.filter(started_at__gte=start_date).order_by(
        "-started_at"
    )[:10]

    # Calculate funnel data
    funnel_data = calculate_funnel_data(project, start_date, end_date)

    # Get conversion metrics
    conversion_metrics = calculate_conversion_metrics(project, start_date, end_date)

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": brand.name, "url": None, "icon": "fas fa-store"},
        {"title": "Analytics", "url": None, "icon": "fas fa-chart-line"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "All Pages",
            "url": f"/brand/{brand.id}/analytics/pages/",
            "icon": "fas fa-list",
            "class": "bg-green-600 text-white hover:bg-green-700",
        },
        {
            "title": "Session Recordings",
            "url": f"/brand/{brand.id}/analytics/sessions/",
            "icon": "fas fa-video",
            "class": "bg-blue-600 text-white hover:bg-blue-700",
        },
        {
            "title": "Heatmaps",
            "url": f"/brand/{brand.id}/analytics/heatmaps/",
            "icon": "fas fa-fire",
            "class": "bg-purple-600 text-white hover:bg-purple-700",
        },
        {
            "title": "Settings",
            "url": f"/brand/{brand.id}/analytics/settings/",
            "icon": "fas fa-cog",
            "class": "bg-gray-600 text-white hover:bg-gray-700",
        },
    ]

    context = {
        "brand": brand,
        "project": project,
        "total_sessions": total_sessions,
        "total_pageviews": total_pageviews,
        "avg_session_duration": round(avg_session_duration, 1),
        "avg_page_load_time": round(avg_page_load_time, 0),
        "bounce_rate": round(bounce_rate, 1),
        "top_pages": top_pages,
        "device_breakdown": device_breakdown,
        "browser_breakdown": browser_breakdown,
        "daily_traffic": daily_traffic,
        "recent_sessions": recent_sessions,
        "funnel_data": funnel_data,
        "conversion_metrics": conversion_metrics,
        "tracking_code": project.tracking_code,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
    }

    return render(request, "website/analytics/dashboard.html", context)


@login_required
def analytics_setup(request, brand_id):
    """Set up analytics tracking for a brand"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)

    if request.method == "POST":
        website_url = request.POST.get("website_url")
        project_name = request.POST.get("project_name", f"{brand.name} Website")

        if not website_url:
            messages.error(request, "Website URL is required")
            return render(request, "website/analytics/setup.html", {"brand": brand})

        # Generate unique tracking code
        tracking_code = "GA-" + secrets.token_hex(8).upper()

        # Create analytics project
        AnalyticsProject.objects.create(
            brand=brand,
            name=project_name,
            website_url=website_url,
            tracking_code=tracking_code,
        )

        messages.success(request, "Analytics tracking has been set up successfully!")
        return redirect("website:analytics_dashboard", brand_id=brand_id)

    return render(request, "website/analytics/setup.html", {"brand": brand})


@login_required
def analytics_sessions(request, brand_id):
    """View detailed session list with recordings"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

    # Get filter parameters
    device_filter = request.GET.get("device", "")
    browser_filter = request.GET.get("browser", "")
    date_filter = request.GET.get("date", "7")  # Default to last 7 days

    # Calculate date range
    end_date = timezone.now()
    if date_filter == "1":
        start_date = end_date - timedelta(days=1)
    elif date_filter == "7":
        start_date = end_date - timedelta(days=7)
    elif date_filter == "30":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=7)

    # Build query
    sessions = project.sessions.filter(started_at__gte=start_date)

    if device_filter:
        sessions = sessions.filter(device_type=device_filter)

    if browser_filter:
        sessions = sessions.filter(browser__icontains=browser_filter)

    sessions = sessions.order_by("-started_at")

    # Pagination
    paginator = Paginator(sessions, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get filter options
    device_options = project.sessions.values_list("device_type", flat=True).distinct()
    browser_options = project.sessions.values_list("browser", flat=True).distinct()

    context = {
        "brand": brand,
        "project": project,
        "page_obj": page_obj,
        "device_filter": device_filter,
        "browser_filter": browser_filter,
        "date_filter": date_filter,
        "device_options": device_options,
        "browser_options": browser_options,
    }

    return render(request, "website/analytics/sessions.html", context)


@login_required
def analytics_session_replay(request, brand_id, session_id):
    """View session replay for a specific session"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    session = get_object_or_404(AnalyticsSession, id=session_id, project__brand=brand)

    # Get all page views and recordings for this session
    pageviews = session.pageviews.prefetch_related("recording", "events").all()

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": brand.name, "url": None, "icon": "fas fa-store"},
        {
            "title": "Analytics",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-chart-line",
        },
        {
            "title": "Sessions",
            "url": f"/brand/{brand.id}/analytics/sessions/",
            "icon": "fas fa-users",
        },
        {"title": "Session Replay", "url": None, "icon": "fas fa-video"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "Back to Sessions",
            "url": f"/brand/{brand.id}/analytics/sessions/",
            "icon": "fas fa-arrow-left",
            "class": "bg-blue-600 text-white hover:bg-blue-700",
        },
        {
            "title": "Analytics Dashboard",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-chart-bar",
            "class": "bg-purple-600 text-white hover:bg-purple-700",
        },
    ]

    context = {
        "brand": brand,
        "session": session,
        "pageviews": pageviews,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
    }

    return render(request, "website/analytics/session_replay.html", context)


@login_required
def analytics_heatmaps(request, brand_id):
    """View heatmaps for the website"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

    # Get popular pages for heatmap generation
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    popular_pages = (
        AnalyticsPageView.objects.filter(
            session__project=project, started_at__gte=start_date
        )
        .values("path", "url")
        .annotate(
            views=Count("id"),
            avg_scroll_depth=Avg("scroll_depth_percentage"),
            total_clicks=Sum("clicks_count"),
        )
        .order_by("-views")[:20]
    )

    # Get existing heatmaps
    existing_heatmaps = project.heatmaps.filter(
        date_from__gte=start_date.date()
    ).order_by("-created_at")

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": brand.name, "url": None, "icon": "fas fa-store"},
        {
            "title": "Analytics",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-chart-line",
        },
        {"title": "Heatmaps", "url": None, "icon": "fas fa-fire"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "Analytics Dashboard",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-arrow-left",
            "class": "bg-blue-600 text-white hover:bg-blue-700",
        },
        {
            "title": "Session Recordings",
            "url": f"/brand/{brand.id}/analytics/sessions/",
            "icon": "fas fa-video",
            "class": "bg-green-600 text-white hover:bg-green-700",
        },
        {
            "title": "All Pages",
            "url": f"/brand/{brand.id}/analytics/pages/",
            "icon": "fas fa-list",
            "class": "bg-gray-600 text-white hover:bg-gray-700",
        },
        {
            "title": "Settings",
            "url": f"/brand/{brand.id}/analytics/settings/",
            "icon": "fas fa-cog",
            "class": "bg-gray-600 text-white hover:bg-gray-700",
        },
    ]

    context = {
        "brand": brand,
        "project": project,
        "popular_pages": popular_pages,
        "existing_heatmaps": existing_heatmaps,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
    }

    return render(request, "website/analytics/heatmaps.html", context)


@login_required
def analytics_settings(request, brand_id):
    """Analytics project settings"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

    if request.method == "POST":
        project.name = request.POST.get("name", project.name)
        project.website_url = request.POST.get("website_url", project.website_url)
        project.record_mouse_movements = "record_mouse" in request.POST
        project.record_clicks = "record_clicks" in request.POST
        project.record_form_inputs = "record_forms" in request.POST
        project.record_scrolls = "record_scrolls" in request.POST
        project.sample_rate = float(request.POST.get("sample_rate", 1.0))
        project.save()

        messages.success(request, "Settings updated successfully!")
        return redirect("website:analytics_settings", brand_id=brand_id)

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": brand.name, "url": None, "icon": "fas fa-store"},
        {
            "title": "Analytics",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-chart-line",
        },
        {"title": "Settings", "url": None, "icon": "fas fa-cog"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "Back to Dashboard",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-arrow-left",
            "class": "bg-gray-600 text-white hover:bg-gray-700",
        }
    ]

    context = {
        "brand": brand,
        "project": project,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
    }

    return render(request, "website/analytics/settings.html", context)


@login_required
def analytics_api_data(request, brand_id):
    """API endpoint for chart data"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

    data_type = request.GET.get("type", "traffic")
    days = int(request.GET.get("days", 30))

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    if data_type == "traffic":
        # Daily traffic data
        daily_data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            sessions = project.sessions.filter(started_at__date=date.date()).count()
            pageviews = AnalyticsPageView.objects.filter(
                session__project=project, started_at__date=date.date()
            ).count()
            daily_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "sessions": sessions,
                    "pageviews": pageviews,
                }
            )
        return JsonResponse({"data": daily_data})

    elif data_type == "devices":
        # Device breakdown
        device_data = list(
            project.sessions.filter(started_at__gte=start_date)
            .values("device_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return JsonResponse({"data": device_data})

    elif data_type == "pages":
        # Top pages with proper duration filtering
        page_data = list(
            AnalyticsPageView.objects.filter(
                session__project=project, started_at__gte=start_date
            )
            .values("path")
            .annotate(
                views=Count("id"),
                avg_duration=Avg(
                    "duration_seconds",
                    filter=Q(
                        duration_seconds__gt=0,
                        duration_seconds__lt=3600,  # 1 hour max for pageviews
                    ),
                ),
                avg_load_time=Avg(
                    "load_time_ms",
                    filter=Q(
                        load_time_ms__isnull=False,
                        load_time_ms__gt=0,
                        load_time_ms__lt=30000,  # 30 seconds max load time
                    ),
                ),
            )
            .order_by("-views")[:10]
        )
        return JsonResponse({"data": page_data})

    elif data_type == "performance":
        # Page load performance metrics
        performance_data = list(
            AnalyticsPageView.objects.filter(
                session__project=project,
                started_at__gte=start_date,
                load_time_ms__isnull=False,
            )
            .values("path")
            .annotate(
                avg_load_time=Avg("load_time_ms"),
                avg_dom_loaded=Avg("dom_content_loaded_ms"),
                avg_first_paint=Avg("first_paint_ms"),
                avg_lcp=Avg("largest_contentful_paint_ms"),
                avg_fid=Avg("first_input_delay_ms"),
                samples=Count("id"),
            )
            .order_by("-samples")[:10]
        )
        return JsonResponse({"data": performance_data})

    return JsonResponse({"error": "Invalid data type"}, status=400)


@login_required
def analytics_recording_data(request, pageview_id):
    """Get recording data for session replay"""
    pageview = get_object_or_404(AnalyticsPageView, id=pageview_id)

    # Security check: ensure user owns the brand that this pageview belongs to
    brand = pageview.session.project.brand
    if brand.owner != request.user:
        return JsonResponse({"success": False, "error": "Access denied"}, status=403)

    try:
        recording = pageview.recording
        # Decompress mouse movement data
        compressed_data = recording.mouse_movements
        if isinstance(compressed_data, bytes):
            decompressed_data = gzip.decompress(compressed_data).decode("utf-8")
        else:
            decompressed_data = compressed_data

        mouse_movements = json.loads(decompressed_data)

        # Get events for this page view
        events = list(
            pageview.events.values(
                "event_type",
                "timestamp",
                "element_tag",
                "element_text",
                "x_coordinate",
                "y_coordinate",
                "data",
            )
        )

        return JsonResponse(
            {
                "success": True,
                "mouse_movements": mouse_movements,
                "events": events,
                "duration": recording.recording_duration,
                "pageview": {
                    "url": pageview.url,
                    "title": pageview.title,
                    "viewport_width": pageview.viewport_width,
                    "viewport_height": pageview.viewport_height,
                },
            }
        )

    except AnalyticsRecording.DoesNotExist:
        return JsonResponse({"success": False, "error": "No recording data available"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@require_POST
@login_required
def delete_session_recording(request, session_id):
    """Delete a session recording and all associated data"""
    try:
        # Get the session and verify ownership
        session = get_object_or_404(
            AnalyticsSession, id=session_id, project__brand__owner=request.user
        )

        # Use transaction to ensure data consistency
        with transaction.atomic():
            # Get all pageviews for this session
            pageviews = session.pageviews.all()

            # Delete all recordings associated with pageviews
            recordings_deleted = 0
            for pageview in pageviews:
                try:
                    recording = pageview.recording
                    recording.delete()
                    recordings_deleted += 1
                except AnalyticsRecording.DoesNotExist:
                    # No recording for this pageview, skip
                    pass

            # Also delete all events associated with pageviews
            from .analytics_models import AnalyticsEvent

            events_deleted = AnalyticsEvent.objects.filter(
                pageview__in=pageviews
            ).count()
            AnalyticsEvent.objects.filter(pageview__in=pageviews).delete()

        return JsonResponse(
            {
                "success": True,
                "message": f"Deleted {recordings_deleted} recordings and {events_deleted} events for session",
                "recordings_deleted": recordings_deleted,
                "events_deleted": events_deleted,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def analytics_all_pages(request, brand_id):
    """View all pages being viewed in real-time"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

    # Get recent page views (last 24 hours)
    end_date = timezone.now()
    start_date = end_date - timedelta(hours=24)

    recent_pageviews = (
        AnalyticsPageView.objects.filter(
            session__project=project, started_at__gte=start_date
        )
        .select_related("session")
        .order_by("-started_at")[:100]
    )

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": brand.name, "url": None, "icon": "fas fa-store"},
        {
            "title": "Analytics",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-chart-line",
        },
        {"title": "All Pages", "url": None, "icon": "fas fa-list"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "Back to Dashboard",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-arrow-left",
            "class": "bg-blue-600 text-white hover:bg-blue-700",
        },
        {
            "title": "Session Recordings",
            "url": f"/brand/{brand.id}/analytics/sessions/",
            "icon": "fas fa-video",
            "class": "bg-purple-600 text-white hover:bg-purple-700",
        },
    ]

    context = {
        "brand": brand,
        "project": project,
        "recent_pageviews": recent_pageviews,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
    }

    return render(request, "website/analytics/all_pages.html", context)


@login_required
def analytics_all_events(request, brand_id):
    """View all events happening in real-time"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

    # Get recent events (last 24 hours)
    end_date = timezone.now()
    start_date = end_date - timedelta(hours=24)

    from .analytics_models import AnalyticsEvent

    recent_events = (
        AnalyticsEvent.objects.filter(
            pageview__session__project=project, timestamp__gte=start_date
        )
        .select_related("pageview", "pageview__session")
        .order_by("-timestamp")[:100]
    )

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": brand.name, "url": None, "icon": "fas fa-store"},
        {
            "title": "Analytics",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-chart-line",
        },
        {
            "title": "Session Recordings",
            "url": f"/brand/{brand.id}/analytics/sessions/",
            "icon": "fas fa-video",
        },
        {"title": "All Events", "url": None, "icon": "fas fa-mouse-pointer"},
    ]

    # Action buttons
    action_buttons = [
        {
            "title": "Back to Sessions",
            "url": f"/brand/{brand.id}/analytics/sessions/",
            "icon": "fas fa-arrow-left",
            "class": "bg-blue-600 text-white hover:bg-blue-700",
        },
        {
            "title": "Analytics Dashboard",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-chart-bar",
            "class": "bg-purple-600 text-white hover:bg-purple-700",
        },
    ]

    context = {
        "brand": brand,
        "project": project,
        "recent_events": recent_events,
        "breadcrumbs": breadcrumbs,
        "action_buttons": action_buttons,
    }

    return render(request, "website/analytics/all_events.html", context)


@login_required
def analytics_pages_stream(request, brand_id):
    """Server-Sent Events endpoint for real-time page views"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

    def event_stream():
        import time

        while True:
            # Get the latest page view
            latest_pageview = (
                AnalyticsPageView.objects.filter(session__project=project)
                .select_related("session")
                .order_by("-started_at")
                .first()
            )

            if latest_pageview:
                data = {
                    "id": str(latest_pageview.id),
                    "url": latest_pageview.url,
                    "title": latest_pageview.title,
                    "path": latest_pageview.path,
                    "timestamp": latest_pageview.started_at.isoformat(),
                    "session_id": str(latest_pageview.session.id),
                    "ip_address": latest_pageview.session.ip_address,
                    "browser": latest_pageview.session.browser,
                    "device_type": latest_pageview.session.device_type,
                }
                yield f"data: {json.dumps(data)}\n\n"

            time.sleep(2)  # Check for new data every 2 seconds

    from django.http import StreamingHttpResponse

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["Connection"] = "keep-alive"
    return response


@login_required
def analytics_events_stream(request, brand_id):
    """Server-Sent Events endpoint for real-time events"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

    def event_stream():
        import time
        from .analytics_models import AnalyticsEvent

        while True:
            # Get the latest event
            latest_event = (
                AnalyticsEvent.objects.filter(pageview__session__project=project)
                .select_related("pageview", "pageview__session")
                .order_by("-timestamp")
                .first()
            )

            if latest_event:
                data = {
                    "id": str(latest_event.id),
                    "event_type": latest_event.event_type,
                    "timestamp": latest_event.timestamp.isoformat(),
                    "element_tag": latest_event.element_tag,
                    "element_classes": latest_event.element_classes,
                    "element_id": latest_event.element_id,
                    "element_text": (
                        latest_event.element_text[:50]
                        if latest_event.element_text
                        else ""
                    ),
                    "x_coordinate": latest_event.x_coordinate,
                    "y_coordinate": latest_event.y_coordinate,
                    "page_url": latest_event.pageview.url,
                    "page_path": latest_event.pageview.path,
                    "session_id": str(latest_event.pageview.session.id),
                    "ip_address": latest_event.pageview.session.ip_address,
                }
                yield f"data: {json.dumps(data)}\n\n"

            time.sleep(1)  # Check for new data every 1 second

    from django.http import StreamingHttpResponse

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["Connection"] = "keep-alive"
    return response


@require_POST
@login_required
def generate_heatmap(request, brand_id):
    """Generate a heatmap for a specific page"""
    import json
    from datetime import timedelta

    try:
        brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
        project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

        # Parse request data
        data = json.loads(request.body)
        page_path = data.get("page_path", "")

        if not page_path:
            return JsonResponse(
                {"success": False, "error": "Page path is required"}, status=400
            )

        # Calculate date range (last 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        # Get page views for this path
        pageviews = AnalyticsPageView.objects.filter(
            session__project=project, path=page_path, started_at__gte=start_date
        ).select_related("session")

        if pageviews.count() < 5:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Not enough data to generate heatmap. Need at least 5 page views, found {pageviews.count()}",
                }
            )

        # Group by viewport size to find the most common
        viewport_groups = {}
        for pv in pageviews:
            if pv.viewport_width and pv.viewport_height:
                key = f"{pv.viewport_width}x{pv.viewport_height}"
                if key not in viewport_groups:
                    viewport_groups[key] = []
                viewport_groups[key].append(pv)

        if not viewport_groups:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No viewport data available for heatmap generation",
                }
            )

        # Use the most common viewport size
        most_common_viewport = max(
            viewport_groups.keys(), key=lambda k: len(viewport_groups[k])
        )
        viewport_pageviews = viewport_groups[most_common_viewport]
        viewport_width, viewport_height = most_common_viewport.split("x")
        viewport_width, viewport_height = int(viewport_width), int(viewport_height)

        # Generate click heatmap data
        click_data = []
        scroll_data = []

        for pv in viewport_pageviews:
            # Simulate click data (in a real implementation, you'd get this from recordings)
            # For now, we'll create sample data based on scroll depth
            scroll_percentage = pv.scroll_depth_percentage or 0
            clicks_count = pv.clicks_count or 0

            # Add simulated click points based on page engagement
            for i in range(min(clicks_count, 10)):  # Limit to 10 clicks per pageview
                click_data.append(
                    {
                        "x": min(
                            viewport_width * 0.8,
                            max(50, viewport_width * 0.1 + (i * 50)),
                        ),
                        "y": min(
                            viewport_height * (scroll_percentage / 100),
                            viewport_height * 0.9,
                        ),
                        "count": 1,
                    }
                )

            # Add scroll data
            scroll_data.append({"depth": scroll_percentage, "count": 1})

        # Aggregate click data by proximity
        aggregated_clicks = []
        proximity_threshold = 50  # pixels

        for click in click_data:
            merged = False
            for agg_click in aggregated_clicks:
                distance = (
                    (click["x"] - agg_click["x"]) ** 2
                    + (click["y"] - agg_click["y"]) ** 2
                ) ** 0.5
                if distance < proximity_threshold:
                    # Merge clicks
                    agg_click["count"] += click["count"]
                    merged = True
                    break

            if not merged:
                aggregated_clicks.append(click.copy())

        # Create or update heatmap
        from .analytics_models import AnalyticsHeatmap

        heatmap, created = AnalyticsHeatmap.objects.update_or_create(
            project=project,
            url_pattern=page_path,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            date_from=start_date.date(),
            defaults={
                "date_to": end_date.date(),
                "click_data": json.dumps(aggregated_clicks),
                "scroll_data": json.dumps(scroll_data),
                "attention_data": json.dumps([]),  # Placeholder for attention data
                "sample_size": len(viewport_pageviews),
            },
        )

        action = "created" if created else "updated"

        return JsonResponse(
            {
                "success": True,
                "message": f"Heatmap {action} successfully",
                "heatmap_id": str(heatmap.id),
                "sample_size": len(viewport_pageviews),
                "viewport": f"{viewport_width}x{viewport_height}",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
@login_required
def generate_all_heatmaps(request, brand_id):
    """Generate heatmaps for all popular pages"""
    import json
    from datetime import timedelta

    try:
        brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
        project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)

        # Calculate date range (last 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        # Get popular pages
        popular_pages = (
            AnalyticsPageView.objects.filter(
                session__project=project, started_at__gte=start_date
            )
            .values("path")
            .annotate(
                views=Count("id"),
                avg_scroll_depth=Avg("scroll_depth_percentage"),
                total_clicks=Sum("clicks_count"),
            )
            .filter(views__gte=5)  # Only pages with at least 5 views
            .order_by("-views")[:10]  # Top 10 pages
        )

        generated_count = 0
        errors = []

        for page in popular_pages:
            try:
                # Simulate the heatmap generation for each page
                page_path = page["path"]

                # Get page views for this path
                pageviews = AnalyticsPageView.objects.filter(
                    session__project=project, path=page_path, started_at__gte=start_date
                ).select_related("session")

                # Group by viewport size
                viewport_groups = {}
                for pv in pageviews:
                    if pv.viewport_width and pv.viewport_height:
                        key = f"{pv.viewport_width}x{pv.viewport_height}"
                        if key not in viewport_groups:
                            viewport_groups[key] = []
                        viewport_groups[key].append(pv)

                if not viewport_groups:
                    continue

                # Use the most common viewport size
                most_common_viewport = max(
                    viewport_groups.keys(), key=lambda k: len(viewport_groups[k])
                )
                viewport_pageviews = viewport_groups[most_common_viewport]
                viewport_width, viewport_height = most_common_viewport.split("x")
                viewport_width, viewport_height = (
                    int(viewport_width),
                    int(viewport_height),
                )

                # Generate simplified heatmap data
                click_data = []
                scroll_data = []

                for pv in viewport_pageviews:
                    scroll_percentage = pv.scroll_depth_percentage or 0
                    clicks_count = pv.clicks_count or 0

                    # Simplified click simulation
                    if clicks_count > 0:
                        click_data.append(
                            {
                                "x": viewport_width * 0.5,  # Center of page
                                "y": viewport_height
                                * (
                                    scroll_percentage / 200
                                ),  # Upper half based on scroll
                                "count": clicks_count,
                            }
                        )

                    scroll_data.append({"depth": scroll_percentage, "count": 1})

                # Create or update heatmap
                from .analytics_models import AnalyticsHeatmap

                heatmap, created = AnalyticsHeatmap.objects.update_or_create(
                    project=project,
                    url_pattern=page_path,
                    viewport_width=viewport_width,
                    viewport_height=viewport_height,
                    date_from=start_date.date(),
                    defaults={
                        "date_to": end_date.date(),
                        "click_data": json.dumps(click_data),
                        "scroll_data": json.dumps(scroll_data),
                        "attention_data": json.dumps([]),
                        "sample_size": len(viewport_pageviews),
                    },
                )

                generated_count += 1

            except Exception as e:
                errors.append(
                    f"Failed to generate heatmap for {page['path']}: {str(e)}"
                )

        return JsonResponse(
            {
                "success": True,
                "message": f"Generated {generated_count} heatmaps",
                "generated_count": generated_count,
                "total_pages": len(popular_pages),
                "errors": errors,
            }
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def analytics_heatmap_view(request, brand_id, heatmap_id):
    """View individual heatmap"""
    from .analytics_models import AnalyticsHeatmap
    import json

    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = get_object_or_404(AnalyticsProject, brand=brand, is_active=True)
    heatmap = get_object_or_404(AnalyticsHeatmap, id=heatmap_id, project=project)

    # Parse JSON data
    try:
        click_data = json.loads(heatmap.click_data) if heatmap.click_data else []
        scroll_data = json.loads(heatmap.scroll_data) if heatmap.scroll_data else []
        attention_data = (
            json.loads(heatmap.attention_data) if heatmap.attention_data else []
        )
    except json.JSONDecodeError:
        click_data = []
        scroll_data = []
        attention_data = []

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": brand.name, "url": None, "icon": "fas fa-store"},
        {
            "title": "Analytics",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-chart-line",
        },
        {
            "title": "Heatmaps",
            "url": f"/brand/{brand.id}/analytics/heatmaps/",
            "icon": "fas fa-fire",
        },
        {"title": "View Heatmap", "url": None, "icon": "fas fa-eye"},
    ]

    context = {
        "brand": brand,
        "project": project,
        "heatmap": heatmap,
        "click_data": click_data,
        "scroll_data": scroll_data,
        "attention_data": attention_data,
        "breadcrumbs": breadcrumbs,
    }

    return render(request, "website/analytics/heatmap_view.html", context)


@login_required
def page_detail_analytics(request, brand_id, path):
    """Detailed analytics for a specific page path"""
    brand = get_object_or_404(Brand, id=brand_id, owner=request.user)
    project = brand.analytics_projects.filter(is_active=True).first()

    if not project:
        return redirect("website:analytics_setup", brand_id=brand_id)

    # Decode the path parameter (it will be URL encoded)
    import urllib.parse

    decoded_path = urllib.parse.unquote(path)

    # Calculate date range (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    # Get all pageviews for this path
    pageviews = (
        AnalyticsPageView.objects.filter(
            session__project=project, path=decoded_path, started_at__gte=start_date
        )
        .select_related("session")
        .order_by("-started_at")
    )

    # Calculate page statistics
    total_views = pageviews.count()
    unique_sessions = pageviews.values("session").distinct().count()

    # Average metrics
    avg_duration = (
        pageviews.filter(duration_seconds__gt=0, duration_seconds__lt=3600).aggregate(
            avg=Avg("duration_seconds")
        )["avg"]
        or 0
    )

    avg_load_time = (
        pageviews.filter(
            load_time_ms__isnull=False, load_time_ms__gt=0, load_time_ms__lt=30000
        ).aggregate(avg=Avg("load_time_ms"))["avg"]
        or 0
    )

    avg_scroll_depth = (
        pageviews.aggregate(avg=Avg("scroll_depth_percentage"))["avg"] or 0
    )

    # Performance metrics
    performance_metrics = {
        "avg_load_time": round(avg_load_time, 0),
        "avg_dom_loaded": round(
            pageviews.filter(
                dom_content_loaded_ms__isnull=False, dom_content_loaded_ms__gt=0
            ).aggregate(avg=Avg("dom_content_loaded_ms"))["avg"]
            or 0,
            0,
        ),
        "avg_first_paint": round(
            pageviews.filter(
                first_paint_ms__isnull=False, first_paint_ms__gt=0
            ).aggregate(avg=Avg("first_paint_ms"))["avg"]
            or 0,
            0,
        ),
        "avg_lcp": round(
            pageviews.filter(
                largest_contentful_paint_ms__isnull=False,
                largest_contentful_paint_ms__gt=0,
            ).aggregate(avg=Avg("largest_contentful_paint_ms"))["avg"]
            or 0,
            0,
        ),
    }

    # Engagement metrics
    engagement_metrics = {
        "total_clicks": pageviews.aggregate(total=Sum("clicks_count"))["total"] or 0,
        "total_form_interactions": pageviews.aggregate(total=Sum("form_interactions"))[
            "total"
        ]
        or 0,
        "avg_scroll_depth": round(avg_scroll_depth, 1),
    }

    # Device breakdown for this page
    device_breakdown = (
        pageviews.values("session__device_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Browser breakdown for this page
    browser_breakdown = (
        pageviews.values("session__browser")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    # Traffic sources (referrers)
    traffic_sources = (
        pageviews.filter(session__referrer__isnull=False)
        .exclude(session__referrer="")
        .values("session__referrer")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    # Hourly distribution
    hourly_distribution = []
    for hour in range(24):
        views = pageviews.filter(started_at__hour=hour).count()
        hourly_distribution.append(
            {"hour": hour, "views": views, "label": f"{hour:02d}:00"}
        )

    # Daily views for the last 30 days
    daily_views = []
    for i in range(30):
        date = start_date + timedelta(days=i)
        views = pageviews.filter(started_at__date=date.date()).count()
        unique_sessions_day = (
            pageviews.filter(started_at__date=date.date())
            .values("session")
            .distinct()
            .count()
        )

        daily_views.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "views": views,
                "unique_sessions": unique_sessions_day,
                "label": date.strftime("%m/%d"),
            }
        )

    # Exit rate calculation
    # Pages where this was the last page in the session
    exit_sessions = 0
    for session in pageviews.values("session").distinct():
        session_id = session["session"]
        last_page = (
            AnalyticsPageView.objects.filter(session_id=session_id)
            .order_by("-started_at")
            .first()
        )

        if last_page and last_page.path == decoded_path:
            exit_sessions += 1

    exit_rate = (exit_sessions / unique_sessions * 100) if unique_sessions > 0 else 0

    # Page timing distribution
    load_time_buckets = {
        "fast": pageviews.filter(load_time_ms__lt=1000).count(),
        "average": pageviews.filter(
            load_time_ms__gte=1000, load_time_ms__lt=3000
        ).count(),
        "slow": pageviews.filter(load_time_ms__gte=3000).count(),
    }

    # Pagination for detailed pageview list
    paginator = Paginator(pageviews, 50)  # 50 pageviews per page
    page_number = request.GET.get("page")
    pageviews_page = paginator.get_page(page_number)

    # Breadcrumb navigation
    breadcrumbs = [
        {"title": brand.name, "url": None, "icon": "fas fa-store"},
        {
            "title": "Analytics",
            "url": f"/brand/{brand.id}/analytics/",
            "icon": "fas fa-chart-line",
        },
        {"title": "Page Details", "url": None, "icon": "fas fa-file-alt"},
    ]

    context = {
        "brand": brand,
        "project": project,
        "page_path": decoded_path,
        "total_views": total_views,
        "unique_sessions": unique_sessions,
        "avg_duration": round(avg_duration, 1),
        "exit_rate": round(exit_rate, 1),
        "performance_metrics": performance_metrics,
        "engagement_metrics": engagement_metrics,
        "device_breakdown": device_breakdown,
        "browser_breakdown": browser_breakdown,
        "traffic_sources": traffic_sources,
        "hourly_distribution": hourly_distribution,
        "daily_views": daily_views,
        "load_time_buckets": load_time_buckets,
        "pageviews_page": pageviews_page,
        "breadcrumbs": breadcrumbs,
    }

    return render(request, "website/analytics/page_detail.html", context)
