from django.core.management.base import BaseCommand
from website.models import SystemStats


class Command(BaseCommand):
    help = "Collect current system statistics and store in database"

    def handle(self, *args, **options):
        try:
            stats = SystemStats.capture_current_stats()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Stats collected: CPU {stats.cpu_percent:.1f}%, "
                    f"Memory {stats.memory_percent:.1f}%, "
                    f"Disk {stats.disk_percent:.1f}%"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to collect stats: {e}"))
            raise
