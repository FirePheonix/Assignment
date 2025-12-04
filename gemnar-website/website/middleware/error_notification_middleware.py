import logging
from django.http import Http404
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from ..utils.slack_notifications import SlackNotifier

logger = logging.getLogger(__name__)


class ErrorNotificationMiddleware(MiddlewareMixin):
    """Middleware to send Slack notifications for 500 errors"""

    def process_exception(self, request, exception):
        """Process exceptions and send notifications for 500 errors"""

        # Skip 404 errors - they're not server errors
        if isinstance(exception, Http404):
            return None

        # Skip if we're in debug mode (development)
        if settings.DEBUG:
            return None

        # Only send notifications for production environment
        if settings.ENVIRONMENT != "production":
            return None

        try:
            # Extract request information
            request_info = {
                "path": request.path,
                "method": request.method,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "ip": self._get_client_ip(request),
            }

            # Extract user information if available
            user_info = None
            if hasattr(request, "user") and request.user.is_authenticated:
                user_info = {
                    "username": request.user.username,
                    "id": request.user.id,
                }

            # Send Slack notification
            SlackNotifier.send_error_notification(
                error_type=type(exception).__name__,
                error_message=str(exception),
                request_info=request_info,
                user_info=user_info,
            )

            logger.info(
                f"Sent Slack notification for 500 error: {type(exception).__name__}"
            )

        except Exception as e:
            # Don't let notification errors break the application
            logger.error(f"Failed to send Slack notification for error: {str(e)}")

        # Return None to continue normal exception handling
        return None

    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
