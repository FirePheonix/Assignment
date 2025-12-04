from django.apps import AppConfig
import os
import threading
import psutil
import socket


class WebsiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "website"

    def ready(self):
        import website.signals  # noqa: F401

        # Send startup notification
        # Use run_once to prevent it from running multiple times in development
        # due to the reloader.
        if os.environ.get("RUN_ONCE") is None:
            os.environ["RUN_ONCE"] = "True"

            hostname = socket.gethostname()
            if "vultr" in hostname:
                from website.utils.slack_notifications import SlackNotifier

                current_process = psutil.Process()
                mem = psutil.virtual_memory()

                message = f"🚀 Django started on {hostname} (PID {current_process.pid}) - {mem.used / 1024**2:.0f}MB used"

                # Send notification in background thread to not block startup
                threading.Thread(
                    target=SlackNotifier.send_notification,
                    args=(message,),
                    kwargs={"username": "Gemnar Server", "icon_emoji": ":rocket:"},
                ).start()
