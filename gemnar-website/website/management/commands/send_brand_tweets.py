import logging
import traceback

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from website.models import Brand, WebLog

# Setup logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process tweet queue for brands - send scheduled tweets and alert on empty queues"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode (no actual tweets sent)",
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
            task_name="send_brand_tweets",
            description="Process tweet queue - send scheduled tweets and alert on empty queues",
            details={
                "dry_run": options["dry_run"],
                "limit": options["limit"],
                "verbose": options["verbose"],
            },
        )

        # Setup Sentry cron monitoring
        monitor_slug = "cron-every-minute"
        self.setup_sentry_cron_monitor(monitor_slug)

        try:
            self.dry_run = options["dry_run"]
            self.limit = options["limit"]
            self.verbose = options["verbose"]
            self.web_log = web_log

            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS("Starting brand tweet processing...")
                )

            # Early exit if no brands with Twitter configuration exist
            from website.models import Brand

            brands_with_twitter = Brand.objects.filter(
                twitter_api_key__isnull=False,
                twitter_api_secret__isnull=False,
                twitter_access_token__isnull=False,
                twitter_access_token_secret__isnull=False,
            ).exclude(
                twitter_api_key="",
                twitter_api_secret="",
                twitter_access_token="",
                twitter_access_token_secret="",
            )

            if not brands_with_twitter.exists():
                if self.verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            "No brands with Twitter configuration found - exiting early"
                        )
                    )
                web_log.mark_completed(
                    items_succeeded=0,
                    items_failed=0,
                    details={"message": "No brands with Twitter configuration found"},
                )
                return

            # Get brands ready to tweet
            ready_brands = self.get_ready_brands()

            if not ready_brands:
                self.stdout.write(
                    self.style.WARNING("No brands have scheduled tweets ready to post")
                )
                # Mark as completed with no processing
                web_log.mark_completed(
                    items_succeeded=0,
                    items_failed=0,
                    details={
                        "message": "No brands have scheduled tweets ready to post"
                    },
                )
                return

            # Process each brand
            processed_count = 0
            success_count = 0
            failed_count = 0

            for brand in ready_brands[: self.limit]:
                try:
                    if self.process_brand_tweets(brand):
                        success_count += 1
                    else:
                        failed_count += 1
                    processed_count += 1

                    # Update progress
                    web_log.update_progress(
                        items_processed=processed_count,
                        items_succeeded=success_count,
                        items_failed=failed_count,
                        details={
                            "current_brand": brand.name,
                            "brands_remaining": len(ready_brands) - processed_count,
                        },
                    )
                except Exception as e:
                    failed_count += 1
                    processed_count += 1
                    logger.error(f"Error processing brand {brand.name}: {str(e)}")
                    if self.verbose:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error processing brand {brand.name}: {str(e)}"
                            )
                        )

            # Report results
            self.stdout.write(
                self.style.SUCCESS(
                    f"Processed {processed_count} brands, "
                    f"{success_count} successful, {failed_count} failed"
                )
            )

            # Mark as completed
            web_log.mark_completed(
                items_succeeded=success_count,
                items_failed=failed_count,
                details={
                    "total_brands": len(ready_brands),
                    "processed_brands": processed_count,
                    "success_rate": (
                        (success_count / processed_count * 100)
                        if processed_count > 0
                        else 0
                    ),
                    "message": f"Processed {processed_count} brand tweet queues successfully",
                },
            )

        except Exception as e:
            error_message = str(e)
            error_traceback = traceback.format_exc()

            logger.error(f"Critical error in send_brand_tweets: {error_message}")
            logger.error(error_traceback)

            # Mark as failed
            web_log.mark_failed(
                error_message=error_message,
                error_traceback=error_traceback,
                details={"command_args": options, "error_type": type(e).__name__},
            )

            self.report_sentry_cron_failure(monitor_slug, error_message)
            raise

    def get_ready_brands(self):
        """Get brands that have tweets ready to post"""
        from django.utils import timezone
        from website.models import BrandTweet

        # First check if there are any brands with Twitter configuration
        brands_with_twitter = Brand.objects.filter(
            twitter_api_key__isnull=False,
            twitter_api_secret__isnull=False,
            twitter_access_token__isnull=False,
            twitter_access_token_secret__isnull=False,
        ).exclude(
            twitter_api_key="",
            twitter_api_secret="",
            twitter_access_token="",
            twitter_access_token_secret="",
        )

        if not brands_with_twitter.exists():
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING("No brands with Twitter configuration found")
                )
            return []

        # Check if there are any tweets ready to post
        ready_tweets = BrandTweet.objects.filter(
            status="approved",
            scheduled_for__lte=timezone.now(),
            brand__in=brands_with_twitter,
        )

        if not ready_tweets.exists():
            if self.verbose:
                self.stdout.write(self.style.WARNING("No tweets ready to post"))
            return []

        # Get unique brands that have ready tweets
        ready_brand_ids = ready_tweets.values_list("brand_id", flat=True).distinct()
        ready_brands = brands_with_twitter.filter(id__in=ready_brand_ids)

        if self.verbose:
            self.stdout.write(
                f"Found {ready_brands.count()} brands with tweets ready to post"
            )

        return list(ready_brands)

    def process_brand_tweets(self, brand):
        """Process tweets for a specific brand"""
        if self.verbose:
            self.stdout.write(
                f"Processing brand: {brand.name} (owner: {brand.owner.username})"
            )

        success = False

        # Process BrandTweet objects from the queue
        try:
            if self.process_brand_tweet_objects(brand):
                success = True
        except Exception as e:
            logger.error(
                f"Error processing BrandTweet objects for brand {brand.name}: {str(e)}"
            )
            if self.verbose:
                self.stdout.write(
                    self.style.ERROR(f"Error processing BrandTweet objects: {str(e)}")
                )

        return success

    def process_brand_tweet_objects(self, brand):
        """Process BrandTweet objects for a specific brand"""
        from django.utils import timezone
        from website.models import BrandTweet

        if self.verbose:
            self.stdout.write(f"\nProcessing tweets for brand: {brand.name}")

        # Get approved tweets that are scheduled for now or earlier
        ready_tweets = BrandTweet.objects.filter(
            brand=brand,
            status="approved",
            scheduled_for__lte=timezone.now(),
        ).order_by("scheduled_for")

        if not ready_tweets.exists():
            if self.verbose:
                self.stdout.write(f"No tweets ready to post for brand {brand.name}")
            return 0

        posted_count = 0
        failed_count = 0

        for brand_tweet in ready_tweets:
            try:
                if self.dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Would post tweet: {brand_tweet.content[:50]}..."
                    )
                    posted_count += 1
                    continue

                success, error = self.post_with_brand_credentials(brand_tweet)

                if success:
                    posted_count += 1
                    if self.verbose:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Posted tweet for {brand.name}: {brand_tweet.content[:50]}..."
                            )
                        )
                else:
                    failed_count += 1
                    if self.verbose:
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Failed to post tweet for {brand.name}: {error}"
                            )
                        )

            except Exception as e:
                failed_count += 1
                error_msg = f"Unexpected error: {str(e)}"
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Error processing tweet: {error_msg}")
                    )

        if self.verbose:
            self.stdout.write(
                f"Brand {brand.name}: {posted_count} posted, {failed_count} failed"
            )

        return posted_count

    def check_and_notify_empty_queue(self, brand, posted_count):
        """Check if brand has empty tweet queue and send Slack notification"""
        from datetime import timedelta

        now = timezone.now()
        next_24_hours = now + timedelta(hours=24)
        next_3_days = now + timedelta(days=3)
        next_week = now + timedelta(days=7)

        # Check for tweets in different time periods
        tweets_next_24h = brand.brand_tweets.filter(
            status__in=["approved", "draft"], scheduled_for__range=[now, next_24_hours]
        ).count()

        tweets_next_3_days = brand.brand_tweets.filter(
            status__in=["approved", "draft"], scheduled_for__range=[now, next_3_days]
        ).count()

        tweets_next_week = brand.brand_tweets.filter(
            status__in=["approved", "draft"], scheduled_for__range=[now, next_week]
        ).count()

        # Total pending tweets (regardless of schedule)
        total_pending = brand.brand_tweets.filter(
            status__in=["approved", "draft"]
        ).count()

        # Send notification if completely empty or running low
        should_notify = False
        message = ""

        if total_pending == 0:
            # Completely empty queue
            should_notify = True
            message = (
                f"🚨 *URGENT: Tweet Queue Completely Empty* for {brand.name}\n\n"
                f"❌ No tweets are scheduled at all!\n"
                f"Your Twitter automation will stop working until new tweets are added.\n\n"
                f"🔗 **Action Required:** Log in to Gemnar immediately to schedule tweets."
            )
        elif tweets_next_24h == 0:
            # No tweets in next 24 hours
            should_notify = True
            message = (
                f"⚠️ *Tweet Queue Running Low* for {brand.name}\n\n"
                f"❌ No tweets scheduled for the next 24 hours\n"
                f"📊 **Status:**\n"
                f"   • Next 3 days: {tweets_next_3_days} tweets\n"
                f"   • Next 7 days: {tweets_next_week} tweets\n"
                f"   • Total pending: {total_pending} tweets\n\n"
                f"🔗 Consider adding more tweets to maintain consistent posting."
            )
        elif tweets_next_3_days <= 2:
            # Low on tweets for next 3 days
            should_notify = True
            message = (
                f"⚠️ *Tweet Queue Low* for {brand.name}\n\n"
                f"📊 **Status:**\n"
                f"   • Next 24 hours: {tweets_next_24h} tweets\n"
                f"   • Next 3 days: {tweets_next_3_days} tweets\n"
                f"   • Next 7 days: {tweets_next_week} tweets\n"
                f"   • Total pending: {total_pending} tweets\n\n"
                f"💡 Consider scheduling more tweets to maintain engagement."
            )

        # Send notification if conditions are met and brand has Slack configured
        if should_notify and hasattr(brand, "send_slack_notification"):
            try:
                brand.send_slack_notification(message, urgent=True)
                if self.verbose:
                    self.stdout.write(
                        f"Sent queue status notification to Slack for {brand.name}"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to send Slack notification for {brand.name}: {str(e)}"
                )
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to send Slack notification: {str(e)}")
                    )

        # Always log queue status in verbose mode
        if self.verbose:
            self.stdout.write(f"Queue status for {brand.name}:")
            self.stdout.write(f"  - Posted this run: {posted_count}")
            self.stdout.write(f"  - Next 24h: {tweets_next_24h}")
            self.stdout.write(f"  - Next 3 days: {tweets_next_3_days}")
            self.stdout.write(f"  - Next 7 days: {tweets_next_week}")
            self.stdout.write(f"  - Total pending: {total_pending}")

    def post_brand_tweet(self, brand_tweet):
        """Post a BrandTweet object to Twitter using brand credentials"""
        if self.dry_run:
            self.stdout.write(
                f"DRY RUN: Would post BrandTweet: {brand_tweet.content[:50]}..."
            )
            return True

        try:
            if self.verbose:
                self.stdout.write(
                    f"Checking if tweet {brand_tweet.id} can be posted..."
                )
                self.stdout.write(f"  Status: {brand_tweet.status}")
                self.stdout.write(f"  Content length: {len(brand_tweet.content)}")
                self.stdout.write(
                    f"  Brand has Twitter config: {brand_tweet.brand.has_twitter_config}"
                )

            # Use brand credentials to post the tweet
            success, error = self.post_with_brand_credentials(brand_tweet)

            if success:
                # Refresh to get updated status and tweet_id
                brand_tweet.refresh_from_db()
                if self.verbose:
                    tweet_url = brand_tweet.get_twitter_url()
                    success_msg = (
                        f"Successfully posted BrandTweet: "
                        f"{brand_tweet.content[:50]}... "
                        f"(Status: {brand_tweet.status}, Tweet ID: {brand_tweet.tweet_id})"
                    )
                    if tweet_url:
                        success_msg += f"\nTweet URL: {tweet_url}"
                    self.stdout.write(self.style.SUCCESS(success_msg))
                return True
            else:
                brand_tweet.refresh_from_db()
                logger.error(f"Failed to post BrandTweet {brand_tweet.id}: {error}")
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to post: {error} (Status: {brand_tweet.status})"
                        )
                    )
                return False

        except Exception as e:
            logger.error(f"Error posting BrandTweet {brand_tweet.id}: {str(e)}")
            if self.verbose:
                self.stdout.write(self.style.ERROR(f"Exception occurred: {str(e)}"))
            return False

    def post_with_brand_credentials(self, brand_tweet):
        """Post tweet using brand's Twitter credentials with proper error handling"""
        try:
            import tweepy
            from django.utils import timezone

            brand = brand_tweet.brand

            # Validate brand has complete Twitter configuration
            if not all(
                [
                    brand.twitter_api_key,
                    brand.twitter_api_secret,
                    brand.twitter_access_token,
                    brand.twitter_access_token_secret,
                    brand.twitter_bearer_token,
                ]
            ):
                error_msg = f"Brand {brand.name} missing Twitter API credentials"
                brand_tweet.status = "failed"
                brand_tweet.error_message = error_msg
                brand_tweet.save()
                return False, error_msg

            # Create Twitter API v2 client using brand credentials
            client = tweepy.Client(
                bearer_token=brand.twitter_bearer_token,
                consumer_key=brand.twitter_api_key,
                consumer_secret=brand.twitter_api_secret,
                access_token=brand.twitter_access_token,
                access_token_secret=brand.twitter_access_token_secret,
                wait_on_rate_limit=True,
            )

            if self.verbose:
                self.stdout.write(
                    f"Posting tweet with brand {brand.name} credentials..."
                )

            # Post tweet using API v2
            response = client.create_tweet(text=brand_tweet.content)

            if response.data:
                # Update tweet record
                brand_tweet.tweet_id = response.data["id"]
                brand_tweet.status = "posted"
                brand_tweet.posted_at = timezone.now()
                brand_tweet.save()

                # Send Slack notification if brand has Slack configured
                self.send_success_notification(brand_tweet, response.data["id"])

                return True, None
            else:
                error_msg = "Twitter API returned no data"
                brand_tweet.status = "failed"
                brand_tweet.error_message = error_msg
                brand_tweet.save()
                return False, error_msg

        except tweepy.Forbidden as e:
            error_msg = f"Twitter API access forbidden: {str(e)}"
            brand_tweet.status = "failed"
            brand_tweet.error_message = error_msg
            brand_tweet.save()
            return False, error_msg
        except tweepy.TooManyRequests as e:
            error_msg = f"Twitter API rate limit exceeded: {str(e)}"
            brand_tweet.status = "failed"
            brand_tweet.error_message = error_msg
            brand_tweet.save()
            return False, error_msg
        except Exception as e:
            error_msg = f"Error posting to Twitter: {str(e)}"
            brand_tweet.status = "failed"
            brand_tweet.error_message = error_msg
            brand_tweet.save()
            return False, error_msg

    def send_success_notification(self, brand_tweet, tweet_id):
        """Send Slack notification when tweet is successfully posted"""
        brand = brand_tweet.brand

        # Only send if brand has Slack configured
        if not hasattr(brand, "send_slack_notification"):
            return

        try:
            # Construct tweet URL
            tweet_url = f"https://twitter.com/i/status/{tweet_id}"

            # Create notification message
            message = (
                f"🐦 *Tweet Posted Successfully for {brand.name}*\n\n"
                f"📝 **Content:** {brand_tweet.content[:200]}{'...' if len(brand_tweet.content) > 200 else ''}\n\n"
                f"🔗 **Tweet URL:** {tweet_url}\n"
                f"📅 **Posted:** {brand_tweet.posted_at.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"🤖 **Posted by:** Automated Queue System"
            )

            # Send to Slack
            brand.send_slack_notification(message, urgent=False)

            if self.verbose:
                self.stdout.write(
                    f"Sent success notification to Slack for {brand.name}"
                )

        except Exception as e:
            # Don't fail tweet posting if Slack notification fails
            logger.warning(
                f"Failed to send Slack notification for {brand.name}: {str(e)}"
            )
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING(f"Slack notification failed: {str(e)}")
                )

    def should_post_according_to_config(self, brand, current_time):
        """Check if current time aligns with any active TweetConfiguration schedules"""
        try:
            # Get active tweet configurations for the brand owner
            configs = brand.owner.tweet_configs.filter(is_active=True)

            if not configs.exists():
                # No active configurations, allow posting anytime
                return True

            # Check if any active configuration allows posting at current time
            for config in configs:
                if self.is_time_allowed_by_config(config, current_time):
                    if self.verbose:
                        self.stdout.write(
                            f"Posting allowed by config '{config.name}' for {brand.name}"
                        )
                    return True

            # If we have active configs but none allow current time, don't post
            if self.verbose:
                config_names = [c.name for c in configs]
                self.stdout.write(
                    f"Current time not allowed by any active configs for {brand.name}: {config_names}"
                )
            return False

        except Exception as e:
            logger.warning(
                f"Error checking TweetConfiguration for {brand.name}: {str(e)}"
            )
            # If there's an error checking configs, allow posting (fail open)
            return True

    def is_time_allowed_by_config(self, config, current_time):
        """Check if current time is allowed by a specific TweetConfiguration"""
        schedule = config.schedule
        if not schedule:
            return True

        frequency = schedule.get("frequency", "daily")

        if frequency == "daily":
            # For daily tweets, check if we're within the allowed time window
            allowed_time = schedule.get("time", "09:00")
            try:
                hour, minute = map(int, allowed_time.split(":"))
                # Allow posting within a 1-hour window of the scheduled time
                scheduled_datetime = current_time.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                time_diff = abs((current_time - scheduled_datetime).total_seconds())
                return time_diff <= 3600  # Within 1 hour
            except (ValueError, AttributeError):
                return True  # If time parsing fails, allow posting

        elif frequency == "weekly":
            # For weekly tweets, check both day and time
            current_day = current_time.strftime("%a")
            scheduled_days = schedule.get("days", [])

            if current_day not in scheduled_days:
                return False

            # Check time window for weekly posts too
            allowed_time = schedule.get("time", "09:00")
            try:
                hour, minute = map(int, allowed_time.split(":"))
                scheduled_datetime = current_time.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                time_diff = abs((current_time - scheduled_datetime).total_seconds())
                return time_diff <= 3600  # Within 1 hour
            except (ValueError, AttributeError):
                return True

        # For any other frequency or if schedule is malformed, allow posting
        return True

    def setup_sentry_cron_monitor(self, monitor_slug):
        """Setup Sentry cron monitoring"""
        try:
            import sentry_sdk
            from sentry_sdk.crons import monitor

            # Check if Sentry is configured
            if not hasattr(settings, "SENTRY_DSN") or not settings.SENTRY_DSN:
                return

            # Setup cron monitor
            @monitor(monitor_slug=monitor_slug)
            def monitored_job():
                pass

            # Start monitor
            with sentry_sdk.start_transaction(name="send_brand_tweets"):
                monitored_job()

        except ImportError:
            # Sentry not installed, skip monitoring
            pass
        except Exception as e:
            logger.error(f"Error setting up Sentry cron monitor: {str(e)}")

    def report_sentry_cron_failure(self, monitor_slug, error_message):
        """Report failure to Sentry"""
        try:
            import sentry_sdk

            if not hasattr(settings, "SENTRY_DSN") or not settings.SENTRY_DSN:
                return

            # Report failure with proper SDK v2 syntax
            with sentry_sdk.configure_scope() as scope:
                scope.set_extra("monitor_slug", monitor_slug)
                sentry_sdk.capture_exception(
                    Exception(f"Brand tweets failed: {error_message}"),
                )

        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error reporting Sentry failure: {str(e)}")
