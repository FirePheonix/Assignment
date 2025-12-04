"""
Analytics API endpoints for receiving tracking data from websites
"""

import json
import gzip
import logging
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .analytics_models import (
    AnalyticsProject,
    AnalyticsSession,
    AnalyticsPageView,
    AnalyticsEvent,
    AnalyticsRecording,
)

logger = logging.getLogger(__name__)


def is_valid_uuid(uuid_str):
    """Check if a string is a valid UUID"""
    if not uuid_str:
        return False
    try:
        uuid.UUID(str(uuid_str))
        return True
    except (ValueError, TypeError):
        return False


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
    return ip


def parse_user_agent(user_agent):
    """Parse user agent string to extract browser and device info"""
    if not user_agent:
        return {"device_type": "unknown", "browser": "", "os": ""}

    user_agent_lower = user_agent.lower()

    # Detect device type
    if "mobile" in user_agent_lower or "android" in user_agent_lower:
        device_type = "mobile"
    elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
        device_type = "tablet"
    elif "bot" in user_agent_lower or "crawler" in user_agent_lower:
        device_type = "bot"
    else:
        device_type = "desktop"

    # Detect browser
    if "chrome" in user_agent_lower:
        browser = "Chrome"
    elif "firefox" in user_agent_lower:
        browser = "Firefox"
    elif "safari" in user_agent_lower:
        browser = "Safari"
    elif "edge" in user_agent_lower:
        browser = "Edge"
    else:
        browser = "Unknown"

    # Detect OS
    if "windows" in user_agent_lower:
        os = "Windows"
    elif "mac" in user_agent_lower:
        os = "macOS"
    elif "linux" in user_agent_lower:
        os = "Linux"
    elif "android" in user_agent_lower:
        os = "Android"
    elif "ios" in user_agent_lower:
        os = "iOS"
    else:
        os = "Unknown"

    return {"device_type": device_type, "browser": browser, "os": os}


@csrf_exempt
@require_http_methods(["POST"])
def analytics_pageview(request):
    """Handle page view tracking"""
    try:
        data = json.loads(request.body)
        tracking_code = data.get("tracking_code")

        if not tracking_code:
            return JsonResponse({"error": "Missing tracking code"}, status=400)

        # Get analytics project
        try:
            project = AnalyticsProject.objects.get(
                tracking_code=tracking_code, is_active=True
            )
        except AnalyticsProject.DoesNotExist:
            return JsonResponse({"error": "Invalid tracking code"}, status=404)

        # Get or create session
        session_id = data.get("session_id")
        ip_address = get_client_ip(request)
        user_agent = data.get("user_agent", "")
        user_agent_info = parse_user_agent(user_agent)

        session, created = AnalyticsSession.objects.get_or_create(
            project=project,
            session_id=session_id,
            defaults={
                "ip_address": ip_address,
                "user_agent": user_agent,
                "referrer": data.get("referrer", ""),
                "browser": user_agent_info["browser"],
                "os": user_agent_info["os"],
                "device_type": user_agent_info["device_type"],
            },
        )

        if not created:
            # Update session activity
            session.last_activity = timezone.now()
            session.page_views += 1
            if session.page_views > 1:
                session.is_bounce = False
            # Update session duration with validation
            duration = (timezone.now() - session.started_at).total_seconds()
            # Validate session duration: should be positive and reasonable (max 24 hours)
            if duration < 0:
                duration = 0
            elif duration > 86400:  # 24 hours max
                duration = 86400
            session.duration_seconds = duration
            session.save()
        else:
            # For newly created sessions, initialize duration
            session.duration_seconds = 0
            session.save()

        # Create page view
        pageview = AnalyticsPageView.objects.create(
            session=session,
            url=data.get("url", ""),
            title=data.get("title", ""),
            path=data.get("path", ""),
            query_params=data.get("query_params", ""),
            viewport_width=data.get("viewport_width"),
            viewport_height=data.get("viewport_height"),
            screen_width=data.get("screen_width"),
            screen_height=data.get("screen_height"),
            # Page load performance metrics
            load_time_ms=data.get("load_time_ms"),
            dom_content_loaded_ms=data.get("dom_content_loaded_ms"),
            first_paint_ms=data.get("first_paint_ms"),
            largest_contentful_paint_ms=data.get("largest_contentful_paint_ms"),
            first_input_delay_ms=data.get("first_input_delay_ms"),
        )

        return JsonResponse(
            {
                "success": True,
                "page_view_id": str(pageview.id),
                "session_id": session_id,
            }
        )

    except Exception as e:
        logger.error(f"Error in analytics_pageview: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analytics_event(request):
    """Handle event tracking (clicks, form interactions, etc.)"""
    try:
        data = json.loads(request.body)
        tracking_code = data.get("tracking_code")
        page_view_id = data.get("page_view_id")

        if not tracking_code or not page_view_id:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # Validate page_view_id is a valid UUID
        if not is_valid_uuid(page_view_id):
            return JsonResponse({"error": "Invalid page view ID format"}, status=400)

        # Verify tracking code and get page view
        try:
            pageview = AnalyticsPageView.objects.select_related("session__project").get(
                id=page_view_id,
                session__project__tracking_code=tracking_code,
                session__project__is_active=True,
            )
        except AnalyticsPageView.DoesNotExist:
            return JsonResponse({"error": "Invalid page view"}, status=404)

        # Create event
        event = AnalyticsEvent.objects.create(
            pageview=pageview,
            event_type=data.get("event_type", "custom"),
            element_tag=data.get("element_tag", ""),
            element_classes=data.get("element_classes", ""),
            element_id=data.get("element_id", ""),
            element_text=data.get("element_text", ""),
            x_coordinate=data.get("x_coordinate"),
            y_coordinate=data.get("y_coordinate"),
            data=data.get("data", {}),
        )

        # Update page view metrics
        if data.get("event_type") == "click":
            pageview.clicks_count += 1
            pageview.save()
        elif data.get("event_type") in ["form_focus", "form_submit"]:
            pageview.form_interactions += 1
            pageview.save()

        return JsonResponse({"success": True, "event_id": str(event.id)})

    except Exception as e:
        logger.error(f"Error in analytics_event: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analytics_update_pageview(request):
    """Update pageview with complete load metrics after page load"""
    try:
        data = json.loads(request.body)
        tracking_code = data.get("tracking_code")
        page_view_id = data.get("page_view_id")

        if not tracking_code or not page_view_id:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # Validate page_view_id is a valid UUID
        if not is_valid_uuid(page_view_id):
            return JsonResponse({"error": "Invalid page view ID format"}, status=400)

        # Get the pageview
        try:
            pageview = AnalyticsPageView.objects.select_related("session__project").get(
                id=page_view_id,
                session__project__tracking_code=tracking_code,
                session__project__is_active=True,
            )
        except AnalyticsPageView.DoesNotExist:
            return JsonResponse({"error": "Invalid page view"}, status=404)

        # Update load metrics if provided
        update_fields = []
        if data.get("load_time_ms") is not None:
            pageview.load_time_ms = data.get("load_time_ms")
            update_fields.append("load_time_ms")
        if data.get("dom_content_loaded_ms") is not None:
            pageview.dom_content_loaded_ms = data.get("dom_content_loaded_ms")
            update_fields.append("dom_content_loaded_ms")
        if data.get("first_paint_ms") is not None:
            pageview.first_paint_ms = data.get("first_paint_ms")
            update_fields.append("first_paint_ms")
        if data.get("largest_contentful_paint_ms") is not None:
            pageview.largest_contentful_paint_ms = data.get(
                "largest_contentful_paint_ms"
            )
            update_fields.append("largest_contentful_paint_ms")
        if data.get("first_input_delay_ms") is not None:
            pageview.first_input_delay_ms = data.get("first_input_delay_ms")
            update_fields.append("first_input_delay_ms")

        if update_fields:
            pageview.save(update_fields=update_fields)

        return JsonResponse({"success": True, "updated_fields": update_fields})

    except Exception as e:
        logger.error(f"Error in analytics_update_pageview: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analytics_recording(request):
    """Handle mouse movement recording data"""
    try:
        data = json.loads(request.body)
        tracking_code = data.get("tracking_code")
        page_view_id = data.get("page_view_id")

        if not tracking_code or not page_view_id:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # Validate page_view_id is a valid UUID
        if not is_valid_uuid(page_view_id):
            return JsonResponse({"error": "Invalid page view ID format"}, status=400)

        # Verify tracking code and get page view
        try:
            pageview = AnalyticsPageView.objects.select_related("session__project").get(
                id=page_view_id,
                session__project__tracking_code=tracking_code,
                session__project__is_active=True,
            )
        except AnalyticsPageView.DoesNotExist:
            return JsonResponse({"error": "Invalid page view"}, status=404)

        # Check if project has recording enabled
        if not pageview.session.project.record_mouse_movements:
            return JsonResponse({"success": True, "message": "Recording disabled"})

        # Compress mouse movement data
        mouse_data = data.get("mouse_movements", "")
        compressed_data = gzip.compress(mouse_data.encode("utf-8"))

        # Get or create recording
        recording, created = AnalyticsRecording.objects.get_or_create(
            pageview=pageview,
            defaults={
                "mouse_movements": compressed_data,
                "recording_duration": data.get("recording_duration", 0),
                "data_size_bytes": len(compressed_data),
                "compression_type": "gzip",
            },
        )

        if not created:
            # Update existing recording
            recording.mouse_movements = compressed_data
            recording.recording_duration = data.get("recording_duration", 0)
            recording.data_size_bytes = len(compressed_data)
            recording.save()

        return JsonResponse({"success": True, "recording_id": str(recording.id)})

    except Exception as e:
        logger.error(f"Error in analytics_recording: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analytics_metrics(request):
    """Handle page metrics updates (duration, scroll depth, etc.)"""
    try:
        data = json.loads(request.body)
        tracking_code = data.get("tracking_code")
        page_view_id = data.get("page_view_id")

        if not tracking_code or not page_view_id:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # Validate page_view_id is a valid UUID
        if not is_valid_uuid(page_view_id):
            return JsonResponse({"error": "Invalid page view ID format"}, status=400)

        # Verify tracking code and get page view
        try:
            pageview = AnalyticsPageView.objects.select_related("session__project").get(
                id=page_view_id,
                session__project__tracking_code=tracking_code,
                session__project__is_active=True,
            )
        except AnalyticsPageView.DoesNotExist:
            return JsonResponse({"error": "Invalid page view"}, status=404)

        # Update page view metrics with validation
        duration_seconds = data.get("duration_seconds", 0)
        # Validate duration: should be positive and reasonable (max 1 hour per page)
        if duration_seconds < 0:
            duration_seconds = 0
        elif duration_seconds > 3600:  # 1 hour max per page
            duration_seconds = 3600

        pageview.duration_seconds = duration_seconds
        pageview.scroll_depth_percentage = data.get("scroll_depth_percentage", 0)
        pageview.clicks_count = data.get("clicks_count", 0)
        pageview.form_interactions = data.get("form_interactions", 0)

        # Set end time if page is being closed
        if data.get("is_final_update"):
            pageview.ended_at = timezone.now()

        pageview.save()

        # Update session duration with validation
        session = pageview.session
        session_duration = (timezone.now() - session.started_at).total_seconds()
        # Validate session duration: should be positive and reasonable (max 24 hours)
        if session_duration < 0:
            session_duration = 0
        elif session_duration > 86400:  # 24 hours max
            session_duration = 86400

        session.duration_seconds = session_duration
        session.save()

        return JsonResponse({"success": True})

    except Exception as e:
        logger.error(f"Error in analytics_metrics: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@require_http_methods(["GET"])
def analytics_script(request, tracking_code):
    """Generate JavaScript tracking script for a project"""

    script_content = f"""
(function() {{
    'use strict';
    
    const TRACKING_CODE = '{tracking_code}';
    const API_BASE = window.location.origin;
    let sessionId = null;
    let pageViewId = null;
    let startTime = Date.now();
    let isUnloading = false;
    
    // Generate or get session ID
    function getSessionId() {{
        let stored = sessionStorage.getItem('gemnar_session_id');
        if (!stored) {{
            stored = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('gemnar_session_id', stored);
        }}
        return stored;
    }}
    
    // Get page load performance metrics
    function getPageLoadMetrics() {{
        if (!window.performance || !window.performance.timing) {{
            return {{}};
        }}
        
        const timing = window.performance.timing;
        const navigation = timing.navigationStart;
        
        const metrics = {{
            load_time_ms: timing.loadEventEnd > 0 ? timing.loadEventEnd - navigation : null,
            dom_content_loaded_ms: timing.domContentLoadedEventEnd > 0 ? timing.domContentLoadedEventEnd - navigation : null,
            first_paint_ms: null,
            largest_contentful_paint_ms: null,
            first_input_delay_ms: null
        }};
        
        // Get paint metrics if available
        if (window.performance.getEntriesByType) {{
            const paintEntries = window.performance.getEntriesByType('paint');
            paintEntries.forEach(entry => {{
                if (entry.name === 'first-paint') {{
                    metrics.first_paint_ms = Math.round(entry.startTime);
                }}
            }});
            
            // Get LCP if available
            if (window.PerformanceObserver) {{
                try {{
                    new PerformanceObserver((list) => {{
                        const entries = list.getEntries();
                        const lastEntry = entries[entries.length - 1];
                        metrics.largest_contentful_paint_ms = Math.round(lastEntry.startTime);
                    }}).observe({{entryTypes: ['largest-contentful-paint']}});
                }} catch (e) {{
                    // LCP not supported
                }}
                
                // Get FID if available
                try {{
                    new PerformanceObserver((list) => {{
                        const entries = list.getEntries();
                        entries.forEach(entry => {{
                            metrics.first_input_delay_ms = entry.processingStart - entry.startTime;
                        }});
                    }}).observe({{entryTypes: ['first-input']}});
                }} catch (e) {{
                    // FID not supported
                }}
            }}
        }}
        
        return metrics;
    }}
    
    // Send data to API
    function sendData(endpoint, data) {{
        if (isUnloading) {{
            // Use sendBeacon for unload events
            if (navigator.sendBeacon) {{
                const blob = new Blob([JSON.stringify(data)], {{type: 'application/json'}});
                navigator.sendBeacon(API_BASE + endpoint, blob);
                return;
            }}
        }}
        
        fetch(API_BASE + endpoint, {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify(data),
            keepalive: true
        }}).catch(err => {{
            console.warn('Analytics tracking failed:', err);
        }});
    }}
    
    // Track page view
    function trackPageView() {{
        sessionId = getSessionId();
        
        const pageViewData = {{
            tracking_code: TRACKING_CODE,
            session_id: sessionId,
            url: window.location.href,
            title: document.title,
            path: window.location.pathname,
            query_params: window.location.search,
            referrer: document.referrer,
            user_agent: navigator.userAgent,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight,
            screen_width: screen.width,
            screen_height: screen.height,
            ...getPageLoadMetrics()
        }};
        
        // Send pageview data and get the real pageview ID from response
        fetch(API_BASE + '/api/analytics/pageview', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify(pageViewData),
            keepalive: true
        }}).then(response => response.json())
          .then(data => {{
              if (data.success && data.page_view_id) {{
                  pageViewId = data.page_view_id;
              }}
          }})
          .catch(err => {{
              console.warn('Analytics pageview tracking failed:', err);
              // Generate fallback ID if API fails
              pageViewId = 'pv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
          }});
    }}
    
    // Track metrics (scroll, clicks, etc.)
    let scrollDepth = 0;
    let clickCount = 0;
    let formInteractions = 0;
    
    function updateMetrics() {{
        if (!pageViewId) return;
        
        const duration = Math.round((Date.now() - startTime) / 1000);
        
        const metricsData = {{
            tracking_code: TRACKING_CODE,
            page_view_id: pageViewId,
            duration_seconds: duration,
            scroll_depth_percentage: scrollDepth,
            clicks_count: clickCount,
            form_interactions: formInteractions,
            is_final_update: isUnloading
        }};
        
        sendData('/api/analytics/metrics', metricsData);
    }}
    
    // Track scroll depth
    function trackScroll() {{
        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = Math.round((scrollTop / docHeight) * 100);
        scrollDepth = Math.max(scrollDepth, scrollPercent);
    }}
    
    // Event listeners
    document.addEventListener('click', () => clickCount++);
    document.addEventListener('scroll', trackScroll);
    document.addEventListener('input', (e) => {{
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {{
            formInteractions++;
        }}
    }});
    
    // Track initial page view immediately for basic data
    trackPageView();
    
    // Update with complete load metrics after window load
    function updateLoadMetrics() {{
        if (!pageViewId) return;
        
        const loadMetrics = getPageLoadMetrics();
        if (loadMetrics.load_time_ms) {{
            sendData('/api/analytics/update-pageview', {{
                tracking_code: TRACKING_CODE,
                page_view_id: pageViewId,
                ...loadMetrics
            }});
        }}
    }}
    
    // Wait for complete page load to get accurate load times
    if (document.readyState === 'complete') {{
        setTimeout(updateLoadMetrics, 100); // Small delay to ensure timing data is available
    }} else {{
        window.addEventListener('load', () => {{
            setTimeout(updateLoadMetrics, 100);
        }});
    }}
    
    // Update metrics periodically
    setInterval(updateMetrics, 5000);
    
    // Final update on page unload
    window.addEventListener('beforeunload', () => {{
        isUnloading = true;
        updateMetrics();
    }});
    
    window.addEventListener('visibilitychange', () => {{
        if (document.visibilityState === 'hidden') {{
            updateMetrics();
        }}
    }});
}})();
"""

    return HttpResponse(script_content, content_type="application/javascript")
