import logging
import traceback

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from website.models import Brand, BrandInstagramPost, WebLog

# Setup logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send Instagram posts for brands that are ready to go"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode (no actual posts sent)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of brands to process (default: 10)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging",
        )

    def handle(self, *args, **options):
        # Create WebLog entry for this task execution
        web_log = WebLog.log_minute_task(
            task_name="send_brand_instagram_posts",
            description="Process brand Instagram posts and send approved ones to Instagram",
            details={
                "dry_run": options["dry_run"],
                "limit": options["limit"],
                "verbose": options["verbose"],
            },
        )

        # Setup Sentry cron monitoring
        monitor_slug = "cron-every-minute-instagram"

        self.dry_run = options["dry_run"]
        self.limit = options["limit"]
        self.verbose = options["verbose"]

        if self.verbose:
            self.stdout.write("Starting Instagram post automation...")

        try:
            # Report start to Sentry
            # self.report_sentry_cron_checkin(monitor_slug, "in_progress")

            # Get ready brands
            ready_brands = self.get_ready_brands()

            if self.verbose:
                self.stdout.write(f"Found {len(ready_brands)} ready brands")

            processed_count = 0

            for brand in ready_brands:
                if processed_count >= self.limit:
                    if self.verbose:
                        self.stdout.write(f"Reached limit of {self.limit} brands")
                    break

                try:
                    if self.verbose:
                        self.stdout.write(f"Processing brand: {brand.name}")

                    # Process approved Instagram posts for this brand
                    processed = self.process_brand_posts(brand)

                    if processed:
                        processed_count += 1

                except Exception as e:
                    logger.error(f"Error processing brand {brand.name}: {str(e)}")
                    if self.verbose:
                        self.stdout.write(
                            self.style.ERROR(f"Error processing {brand.name}: {str(e)}")
                        )

            # Mark as successful
            web_log.status = "completed"
            web_log.items_processed = len(ready_brands)
            web_log.items_succeeded = processed_count
            web_log.details.update(
                {
                    "brands_processed": processed_count,
                    "brands_found": len(ready_brands),
                }
            )
            web_log.save()

            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully processed {processed_count} brands"
                    )
                )

        except Exception as e:
            error_message = str(e)
            error_traceback = traceback.format_exc()

            logger.error(
                f"Critical error in send_brand_instagram_posts: {error_message}"
            )
            logger.error(error_traceback)

            # Mark as failed
            web_log.status = "failed"
            web_log.error_message = error_message
            web_log.error_traceback = error_traceback
            web_log.details.update(
                {"command_args": options, "error_type": type(e).__name__}
            )
            web_log.save()

            self.report_sentry_cron_failure(monitor_slug, error_message)
            raise

    def get_ready_brands(self):
        """Get brands that are ready to post to Instagram"""
        if self.verbose:
            self.stdout.write("=== DEBUGGING BRAND SELECTION ===")

        # Find brands with complete Instagram API configuration
        all_brands = Brand.objects.all()
        if self.verbose:
            self.stdout.write(f"Total brands in system: {all_brands.count()}")

        # Check Instagram API configuration
        brands_with_instagram = Brand.objects.filter(
            instagram_access_token__isnull=False,
            instagram_user_id__isnull=False,
            instagram_app_id__isnull=False,
            instagram_app_secret__isnull=False,
        ).exclude(
            instagram_access_token="",
            instagram_user_id="",
            instagram_app_id="",
            instagram_app_secret="",
        )

        if self.verbose:
            self.stdout.write(
                f"Brands with complete Instagram config: {brands_with_instagram.count()}"
            )
            for brand in brands_with_instagram:
                self.stdout.write(f"  - {brand.name} (owner: {brand.owner.username})")

        # Check for active payment status
        ready_brands = []
        for brand in brands_with_instagram:
            # Check if brand has active subscription or is in development mode
            has_active_subscription = brand.stripe_subscription_status in [
                "active",
                "trialing",
            ]

            # Allow posting if in debug mode or development environment
            is_development = (
                getattr(settings, "DEBUG", False)
                or getattr(settings, "ENVIRONMENT", "") == "development"
            )

            if self.verbose:
                self.stdout.write(f"\nBrand: {brand.name}")
                self.stdout.write(
                    f"  Subscription status: {brand.stripe_subscription_status}"
                )
                self.stdout.write(
                    f"  Has active subscription: {has_active_subscription}"
                )
                self.stdout.write(f"  Development mode: {is_development}")

            if has_active_subscription or is_development:
                ready_brands.append(brand)
                if self.verbose:
                    if has_active_subscription:
                        self.stdout.write(
                            "  ✓ Added to ready brands (active subscription)"
                        )
                    else:
                        self.stdout.write(
                            "  ✓ Added to ready brands (development mode)"
                        )
            elif self.verbose:
                self.stdout.write(
                    "  ✗ Skipped (no active subscription and not in development mode)"
                )

        if self.verbose:
            self.stdout.write(f"\nFinal ready brands count: {len(ready_brands)}")

        return ready_brands

    def process_brand_posts(self, brand):
        """Process Instagram posts for a specific brand"""
        now = timezone.now()

        # Check for approved posts ready to be posted
        approved_posts = BrandInstagramPost.objects.filter(
            brand=brand, status="approved", scheduled_for__lte=now
        )

        if self.verbose:
            self.stdout.write(
                f"Found {approved_posts.count()} approved posts ready to post"
            )

        posted_count = 0
        for post in approved_posts:
            if self.post_brand_instagram_post(post):
                posted_count += 1

        if self.verbose and posted_count > 0:
            self.stdout.write(
                f"Posted {posted_count} Instagram posts for brand: {brand.name}"
            )

        return posted_count > 0

    def post_brand_instagram_post(self, brand_post):
        """Post a BrandInstagramPost object to Instagram"""
        if self.dry_run:
            self.stdout.write(
                f"DRY RUN: Would post Instagram post: {brand_post.content[:50]}..."
            )
            return True

        try:
            if self.verbose:
                self.stdout.write(
                    f"Checking if Instagram post {brand_post.id} can be posted..."
                )
                self.stdout.write(f"  Status: {brand_post.status}")
                self.stdout.write(f"  Content length: {len(brand_post.content)}")
                self.stdout.write(f"  Has image: {bool(brand_post.image)}")
                self.stdout.write(
                    f"  Brand has Instagram config: {brand_post.brand.has_instagram_config}"
                )

            # Use the BrandInstagramPost's built-in posting method
            success, error = brand_post.post_to_instagram()

            if success:
                if self.verbose:
                    instagram_url = brand_post.get_instagram_url()
                    success_msg = (
                        f"Successfully posted Instagram post: "
                        f"{brand_post.content[:50]}..."
                    )
                    if instagram_url:
                        success_msg += f"\nInstagram URL: {instagram_url}"
                    self.stdout.write(self.style.SUCCESS(success_msg))
                return True
            else:
                logger.error(f"Failed to post Instagram post {brand_post.id}: {error}")
                if self.verbose:
                    self.stdout.write(self.style.ERROR(f"Failed to post: {error}"))
                return False

        except Exception as e:
            logger.error(f"Error posting Instagram post {brand_post.id}: {str(e)}")
            if self.verbose:
                self.stdout.write(self.style.ERROR(f"Exception occurred: {str(e)}"))
            return False

    def report_sentry_cron_checkin(self, monitor_slug, status):
        """Report cron job status to Sentry"""
        try:
            import sentry_sdk

            # Set extra data using proper Sentry API
            with sentry_sdk.configure_scope() as scope:
                scope.set_extra("monitor_slug", monitor_slug)
                scope.set_extra("status", status)

                # Simplified Sentry logging - just capture as message
                sentry_sdk.capture_message(
                    f"Instagram posting cron job {status}",
                    level="info",
                )
        except Exception as e:
            logger.warning(f"Failed to report to Sentry: {e}")

    def report_sentry_cron_failure(self, monitor_slug, error_message):
        """Report failed cron job to Sentry"""
        try:
            import sentry_sdk

            # Set extra data using proper Sentry API
            with sentry_sdk.configure_scope() as scope:
                scope.set_extra("monitor_slug", monitor_slug)

                # Capture the failure as an error message
                sentry_sdk.capture_message(
                    f"Instagram post automation failed: {error_message}",
                    level="error",
                )
        except Exception as e:
            logger.warning(f"Failed to report failure to Sentry: {e}")
