import logging
import traceback

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from website.models import WebLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run all minute-based automation tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging",
        )
        parser.add_argument(
            "--skip-tweets",
            action="store_true",
            help="Skip brand tweet processing",
        )
        parser.add_argument(
            "--skip-instagram",
            action="store_true",
            help="Skip Instagram post processing",
        )
        parser.add_argument(
            "--skip-stats",
            action="store_true",
            help="Skip system stats collection",
        )

    def handle(self, *args, **options):
        web_log = WebLog.log_minute_task(
            task_name="run_every_minute",
            description="Master automation task for all services",
            details={
                "dry_run": options["dry_run"],
                "verbose": options["verbose"],
                "skip_tweets": options["skip_tweets"],
                "skip_instagram": options["skip_instagram"],
                "skip_stats": options["skip_stats"],
            },
        )

        self.dry_run = options["dry_run"]
        self.verbose = options["verbose"]

        if self.verbose:
            msg = f"Starting automation tasks at {timezone.now()}"
            self.stdout.write(self.style.SUCCESS(msg))

        results = {
            "tweets": {"run": False, "success": False, "error": None},
            "instagram": {"run": False, "success": False, "error": None},
            "stats": {"run": False, "success": False, "error": None},
        }

        executed = 0
        successful = 0
        failed = 0

        try:
            # Run brand tweets
            if not options["skip_tweets"]:
                executed += 1
                results["tweets"]["run"] = True

                if self.verbose:
                    self.stdout.write("\n--- Running Tweet Processing ---")

                try:
                    call_command(
                        "send_brand_tweets",
                        dry_run=self.dry_run,
                        verbose=self.verbose,
                        limit=10,
                    )
                    results["tweets"]["success"] = True
                    successful += 1

                    if self.verbose:
                        msg = "✓ Tweet processing completed"
                        self.stdout.write(self.style.SUCCESS(msg))
                except Exception as e:
                    results["tweets"]["error"] = str(e)
                    failed += 1
                    logger.error(f"Tweet processing failed: {str(e)}")

                    if self.verbose:
                        msg = f"✗ Tweet processing failed: {str(e)}"
                        self.stdout.write(self.style.ERROR(msg))

            # Run Instagram posts
            if not options["skip_instagram"]:
                executed += 1
                results["instagram"]["run"] = True

                if self.verbose:
                    self.stdout.write("\n--- Running Instagram Processing ---")

                try:
                    call_command(
                        "send_brand_instagram_posts",
                        dry_run=self.dry_run,
                        verbose=self.verbose,
                        limit=10,
                    )
                    results["instagram"]["success"] = True
                    successful += 1

                    if self.verbose:
                        msg = "✓ Instagram processing completed"
                        self.stdout.write(self.style.SUCCESS(msg))
                except Exception as e:
                    results["instagram"]["error"] = str(e)
                    failed += 1
                    logger.error(f"Instagram processing failed: {str(e)}")

                    if self.verbose:
                        msg = f"✗ Instagram processing failed: {str(e)}"
                        self.stdout.write(self.style.ERROR(msg))

            # Collect system stats
            if not options["skip_stats"]:
                executed += 1
                results["stats"]["run"] = True

                if self.verbose:
                    self.stdout.write("\n--- Running Stats Collection ---")

                try:
                    call_command("collect_system_stats")
                    results["stats"]["success"] = True
                    successful += 1

                    if self.verbose:
                        msg = "✓ Stats collection completed"
                        self.stdout.write(self.style.SUCCESS(msg))
                except Exception as e:
                    results["stats"]["error"] = str(e)
                    failed += 1
                    logger.error(f"Stats collection failed: {str(e)}")

                    if self.verbose:
                        msg = f"✗ Stats collection failed: {str(e)}"
                        self.stdout.write(self.style.ERROR(msg))

            # Report results
            summary = f"Tasks completed: {successful}/{executed} successful"
            if failed > 0:
                summary += f", {failed} failed"

            if self.verbose:
                self.stdout.write("\n--- Summary ---")
                for task, result in results.items():
                    if result["run"]:
                        if result["success"]:
                            status = "SUCCESS"
                        else:
                            status = f"FAILED: {result['error']}"
                        self.stdout.write(f"{task}: {status}")
                self.stdout.write("")

            self.stdout.write(self.style.SUCCESS(summary))

            web_log.mark_completed(
                items_succeeded=successful,
                items_failed=failed,
                details={
                    **web_log.details,
                    "results": results,
                    "summary": {
                        "executed": executed,
                        "successful": successful,
                        "failed": failed,
                    },
                },
            )

        except Exception as e:
            error_message = str(e)
            error_traceback = traceback.format_exc()

            msg = f"Critical error in run_every_minute: {error_message}"
            logger.error(msg)
            logger.error(error_traceback)

            web_log.mark_failed(
                error_message=error_message,
                error_traceback=error_traceback,
                details={
                    **web_log.details,
                    "results": results,
                    "error_type": type(e).__name__,
                },
            )

            msg = f"Critical automation error: {error_message}"
            self.stdout.write(self.style.ERROR(msg))
            raise
