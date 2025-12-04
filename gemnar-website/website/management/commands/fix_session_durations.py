from django.core.management.base import BaseCommand
from website.analytics_models import AnalyticsSession


class Command(BaseCommand):
    help = "Fix session durations for analytics sessions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Get sessions with zero or null duration
        sessions_to_fix = AnalyticsSession.objects.filter(duration_seconds__lte=0)

        total_sessions = sessions_to_fix.count()
        self.stdout.write(f"Found {total_sessions} sessions with zero/null duration")

        updated_count = 0

        for session in sessions_to_fix:
            if session.last_activity and session.started_at:
                # Calculate duration from timestamps
                time_diff = session.last_activity - session.started_at
                duration = time_diff.total_seconds()

                if duration > 0:
                    if not dry_run:
                        session.duration_seconds = duration
                        session.save()
                    updated_count += 1

                    if updated_count % 100 == 0:
                        msg = f"Processed {updated_count} sessions..."
                        self.stdout.write(msg)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would update {updated_count} sessions")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully updated {updated_count} sessions")
            )
