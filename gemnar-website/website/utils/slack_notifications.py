import requests
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Utility class for sending Slack notifications"""

    # Hardcoded Slack webhook URLs as requested
    DEPLOYMENT_WEBHOOK_URL = (
        "https://hooks.slack.com/services/T091J0AGT5J/B095XJ33Q1F/"
        "IBG0Bm8j0g98TV7gC0QlLn8R"
    )

    ERROR_WEBHOOK_URL = (
        "https://hooks.slack.com/services/T091J0AGT5J/B095D0BUHMZ/"
        "7Vi3YOjXopvmEhYlYAOtwDr0"
    )

    @classmethod
    def send_notification(
        cls,
        message,
        webhook_url=None,
        channel=None,
        username="Gemnar Bot",
        icon_emoji=":robot_face:",
    ):
        """Send a notification to Slack"""
        try:
            # Use deployment webhook as default if no specific URL provided
            if webhook_url is None:
                webhook_url = cls.DEPLOYMENT_WEBHOOK_URL

            payload = {
                "text": message,
                "username": username,
                "icon_emoji": icon_emoji,
            }

            if channel:
                payload["channel"] = channel

            response = requests.post(webhook_url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
                logger.info(f"Response: {response.text}")
                return True
            else:
                logger.error(
                    f"Failed to send Slack notification: "
                    f"Status {response.status_code} - {response.text}"
                )
                logger.error(f"Payload sent: {payload}")
                return False

        except requests.exceptions.Timeout:
            logger.error("Slack notification timed out after 10 seconds")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error sending Slack notification: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack notification: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    @classmethod
    def send_deployment_notification(
        cls, status, repo_name, commit_sha, error_message=None
    ):
        """Send deployment notification to Slack"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        if status == "started":
            message = (
                f"🚀 *Deployment Started*\n"
                f"Repository: `{repo_name}`\n"
                f"Commit: `{commit_sha}`\n"
                f"Time: {timestamp}"
            )
            icon = ":rocket:"
        elif status == "deploying":
            message = (
                f"🚀 *Deployment Deploying*\n"
                f"Repository: `{repo_name}`\n"
                f"Commit: `{commit_sha}`\n"
                f"Time: {timestamp}"
            )
            icon = ":rocket:"
        elif status == "restarting":
            message = (
                f"🔄 *Deployment Restarting*\n"
                f"Repository: `{repo_name}`\n"
                f"Commit: `{commit_sha}`\n"
                f"Time: {timestamp}"
            )
            icon = ":rocket:"
        elif status == "success":
            message = (
                f"✅ *Deployment Successful*\n"
                f"Repository: `{repo_name}`\n"
                f"Commit: `{commit_sha}`\n"
                f"Time: {timestamp}\n"
                f"Website: https://gemnar.com"
            )
            icon = ":white_check_mark:"
        elif status == "failed":
            message = (
                f"❌ *Deployment Failed*\n"
                f"Repository: `{repo_name}`\n"
                f"Commit: `{commit_sha}`\n"
                f"Time: {timestamp}\n"
                f"Error: {error_message or 'Unknown error'}"
            )
            icon = ":x:"
        else:
            message = (
                f"⚠️ *Deployment Status Unknown*\n"
                f"Repository: `{repo_name}`\n"
                f"Commit: `{commit_sha}`\n"
                f"Status: {status}\n"
                f"Time: {timestamp}"
            )
            icon = ":warning:"

        return cls.send_notification(
            message=message,
            webhook_url=cls.DEPLOYMENT_WEBHOOK_URL,
            username="Gemnar Deployment",
            icon_emoji=icon,
        )

    @classmethod
    def send_error_notification(
        cls, error_type, error_message, request_info=None, user_info=None
    ):
        """Send 500 error notification to Slack"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        message = (
            f"🚨 *Server Error (500)*\n"
            f"Error Type: `{error_type}`\n"
            f"Time: {timestamp}\n"
            f"Environment: {settings.ENVIRONMENT}\n"
        )

        if error_message:
            # Truncate long error messages
            if len(error_message) > 500:
                error_message = error_message[:500] + "... (truncated)"
            message += f"Error: ```{error_message}```\n"

        if request_info:
            message += f"Path: `{request_info.get('path', 'Unknown')}`\n"
            message += f"Method: `{request_info.get('method', 'Unknown')}`\n"
            if request_info.get("user_agent"):
                user_agent = request_info["user_agent"][:100]
                message += f"User Agent: `{user_agent}...`\n"
            if request_info.get("ip"):
                message += f"IP: `{request_info['ip']}`\n"

        if user_info:
            username = user_info.get("username", "Anonymous")
            user_id = user_info.get("id", "N/A")
            message += f"User: `{username}` (ID: {user_id})\n"

        message += "Website: https://gemnar.com"

        return cls.send_notification(
            message=message,
            webhook_url=cls.ERROR_WEBHOOK_URL,
            username="Gemnar Error Monitor",
            icon_emoji=":fire:",
        )

    @classmethod
    def send_custom_notification(cls, title, details, severity="info"):
        """Send custom notification to Slack"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        if severity == "critical":
            icon = ":fire:"
            prefix = "🚨"
        elif severity == "warning":
            icon = ":warning:"
            prefix = "⚠️"
        elif severity == "success":
            icon = ":white_check_mark:"
            prefix = "✅"
        else:
            icon = ":information_source:"
            prefix = "ℹ️"

        message = f"{prefix} *{title}*\nTime: {timestamp}\nDetails: {details}"

        return cls.send_notification(
            message=message,
            webhook_url=cls.DEPLOYMENT_WEBHOOK_URL,
            username="Gemnar Monitor",
            icon_emoji=icon,
        )
