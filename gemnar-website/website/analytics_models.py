"""
Analytics models for brand website tracking service.
This provides comprehensive user behavior analytics similar to Hotjar.
"""

from django.db import models
from django.db.models import JSONField
import uuid


class AnalyticsProject(models.Model):
    """
    Analytics project for a brand's website(s)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(
        "Brand", on_delete=models.CASCADE, related_name="analytics_projects"
    )
    name = models.CharField(max_length=200)
    website_url = models.URLField()
    tracking_code = models.CharField(max_length=32, unique=True)
    is_active = models.BooleanField(default=True)

    # Settings
    record_mouse_movements = models.BooleanField(default=True)
    record_clicks = models.BooleanField(default=True)
    record_form_inputs = models.BooleanField(default=True)
    record_scrolls = models.BooleanField(default=True)
    sample_rate = models.FloatField(default=1.0)  # 0.0 to 1.0

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_projects"

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class AnalyticsSession(models.Model):
    """
    A user session on a tracked website
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        AnalyticsProject, on_delete=models.CASCADE, related_name="sessions"
    )
    session_id = models.CharField(max_length=64)  # Client-generated session ID

    # User info
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.URLField(blank=True)

    # Parsed user agent data
    browser = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=[
            ("desktop", "Desktop"),
            ("mobile", "Mobile"),
            ("tablet", "Tablet"),
            ("bot", "Bot"),
        ],
        default="desktop",
    )

    # Geographic data
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)

    # Session data
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    duration_seconds = models.IntegerField(default=0)
    page_views = models.IntegerField(default=0)
    is_bounce = models.BooleanField(default=True)  # Single page visit

    class Meta:
        db_table = "analytics_sessions"
        indexes = [
            models.Index(fields=["project", "-started_at"]),
            models.Index(fields=["session_id"]),
            models.Index(fields=["-started_at"]),
        ]

    def __str__(self):
        return f"Session {self.session_id[:8]} - {self.ip_address}"


class AnalyticsPageView(models.Model):
    """
    A page view within a session
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        AnalyticsSession, on_delete=models.CASCADE, related_name="pageviews"
    )

    # Page info
    url = models.URLField()
    title = models.CharField(max_length=500, blank=True)
    path = models.CharField(max_length=500)
    query_params = models.TextField(blank=True)

    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)

    # Page Load Performance Metrics (in milliseconds)
    load_time_ms = models.IntegerField(
        null=True, blank=True, help_text="Total page load time in ms"
    )
    dom_content_loaded_ms = models.IntegerField(
        null=True, blank=True, help_text="Time until DOM content loaded in ms"
    )
    first_paint_ms = models.IntegerField(
        null=True, blank=True, help_text="Time to first paint in ms"
    )
    largest_contentful_paint_ms = models.IntegerField(
        null=True, blank=True, help_text="Time to largest contentful paint in ms"
    )
    first_input_delay_ms = models.FloatField(
        null=True, blank=True, help_text="First input delay in ms"
    )

    # Engagement metrics
    scroll_depth_percentage = models.IntegerField(default=0)  # Max scroll
    clicks_count = models.IntegerField(default=0)
    form_interactions = models.IntegerField(default=0)

    # Viewport info
    viewport_width = models.IntegerField(null=True)
    viewport_height = models.IntegerField(null=True)
    screen_width = models.IntegerField(null=True)
    screen_height = models.IntegerField(null=True)

    class Meta:
        db_table = "analytics_pageviews"
        indexes = [
            models.Index(fields=["session", "-started_at"]),
            models.Index(fields=["url"]),
            models.Index(fields=["-started_at"]),
        ]


class AnalyticsEvent(models.Model):
    """
    User interaction events (clicks, form submissions, etc.)
    """

    EVENT_TYPES = [
        ("click", "Click"),
        ("form_submit", "Form Submit"),
        ("form_focus", "Form Focus"),
        ("scroll", "Scroll"),
        ("resize", "Window Resize"),
        ("error", "JavaScript Error"),
        ("custom", "Custom Event"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pageview = models.ForeignKey(
        AnalyticsPageView, on_delete=models.CASCADE, related_name="events"
    )

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Element info
    element_tag = models.CharField(max_length=50, blank=True)
    element_classes = models.TextField(blank=True)
    element_id = models.CharField(max_length=200, blank=True)
    element_text = models.TextField(blank=True)

    # Position data
    x_coordinate = models.IntegerField(null=True)
    y_coordinate = models.IntegerField(null=True)

    # Additional data
    data = JSONField(default=dict)  # Event-specific data

    class Meta:
        db_table = "analytics_events"
        indexes = [
            models.Index(fields=["pageview", "timestamp"]),
            models.Index(fields=["event_type", "timestamp"]),
        ]


class AnalyticsRecording(models.Model):
    """
    Mouse movement and interaction recordings for session replay
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pageview = models.OneToOneField(
        AnalyticsPageView, on_delete=models.CASCADE, related_name="recording"
    )

    # Recording data (compressed JSON)
    mouse_movements = models.TextField()  # Compressed JSON of mouse positions
    dom_mutations = models.TextField(blank=True)  # DOM changes during session
    console_logs = models.TextField(blank=True)  # Console messages
    network_requests = models.TextField(blank=True)  # Network activity

    # Metadata
    recording_duration = models.IntegerField(default=0)  # Duration in ms
    data_size_bytes = models.IntegerField(default=0)
    compression_type = models.CharField(max_length=20, default="gzip")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_recordings"


class AnalyticsHeatmap(models.Model):
    """
    Aggregated heatmap data for pages
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        AnalyticsProject, on_delete=models.CASCADE, related_name="heatmaps"
    )

    url_pattern = models.CharField(max_length=500)  # URL or pattern
    viewport_width = models.IntegerField()
    viewport_height = models.IntegerField()

    # Heatmap data
    click_data = models.TextField()  # JSON of click coordinates and counts
    scroll_data = models.TextField()  # JSON of scroll heatmap data
    attention_data = models.TextField()  # JSON of attention/hover data

    # Metadata
    sample_size = models.IntegerField(default=0)  # Number of sessions included
    date_from = models.DateField()
    date_to = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_heatmaps"
        unique_together = [
            ["project", "url_pattern", "viewport_width", "viewport_height", "date_from"]
        ]


class AnalyticsFunnel(models.Model):
    """
    Conversion funnel configuration and tracking
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        AnalyticsProject, on_delete=models.CASCADE, related_name="funnels"
    )

    name = models.CharField(max_length=200)
    steps = JSONField()  # Array of funnel steps with URL patterns

    # Metrics (calculated periodically)
    total_entries = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_funnels"


class AnalyticsAlert(models.Model):
    """
    Automated alerts for significant changes in metrics
    """

    ALERT_TYPES = [
        ("conversion_drop", "Conversion Rate Drop"),
        ("traffic_spike", "Traffic Spike"),
        ("error_increase", "Error Rate Increase"),
        ("bounce_increase", "Bounce Rate Increase"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        AnalyticsProject, on_delete=models.CASCADE, related_name="alerts"
    )

    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    threshold = models.FloatField()
    is_active = models.BooleanField(default=True)

    # Last triggered
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_alerts"
