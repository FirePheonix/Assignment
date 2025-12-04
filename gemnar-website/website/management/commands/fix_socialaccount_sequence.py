from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Fix socialaccount_socialapp_sites sequence and null ID issues"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output",
        )

    def _diagnose_issue(self, cursor):
        """Diagnose the current state"""
        self.stdout.write("Diagnosing current state...")

        # Check table structure (database-specific)
        if connection.vendor == "sqlite":
            cursor.execute("PRAGMA table_info(socialaccount_socialapp_sites)")
            columns = cursor.fetchall()
            self.stdout.write("Table structure:")
            for col in columns:
                # SQLite PRAGMA returns: cid, name, type, notnull, dflt_value, pk
                self.stdout.write(f"  {col[1]}: {col[2]} (default: {col[4]})")
        else:  # PostgreSQL
            cursor.execute(
                """
                SELECT column_name, data_type, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'socialaccount_socialapp_sites'
                ORDER BY ordinal_position
            """
            )
            columns = cursor.fetchall()
            self.stdout.write("Table structure:")
            for col in columns:
                self.stdout.write(f"  {col[0]}: {col[1]} (default: {col[2]})")

        # Check current max ID
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM socialaccount_socialapp_sites")
        max_id = cursor.fetchone()[0]
        self.stdout.write(f"Current max ID: {max_id}")

        # Check sequence current value (PostgreSQL only)
        if connection.vendor == "postgresql":
            try:
                cursor.execute(
                    """
                    SELECT currval(pg_get_serial_sequence('socialaccount_socialapp_sites', 'id'))
                """
                )
                current_val = cursor.fetchone()[0]
                self.stdout.write(f"Current sequence value: {current_val}")
            except Exception as e:
                self.stdout.write(f"Could not get sequence value: {e}")
        else:
            self.stdout.write("SQLite uses AUTOINCREMENT (no sequence to check)")

        # Check for orphaned social apps
        cursor.execute(
            """
            SELECT id FROM socialaccount_socialapp 
            WHERE id NOT IN (
                SELECT DISTINCT socialapp_id 
                FROM socialaccount_socialapp_sites
                WHERE socialapp_id IS NOT NULL
            )
        """
        )
        orphaned_apps = cursor.fetchall()
        self.stdout.write(
            f"Social apps without site associations: {len(orphaned_apps)}"
        )

    def _fix_sequence_issue(self, cursor):
        """Fix the sequence synchronization"""
        if connection.vendor == "sqlite":
            self.stdout.write("SQLite uses AUTOINCREMENT - no sequence to fix")
            return

        self.stdout.write("Fixing sequence synchronization...")

        # Get the actual max ID from the table
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM socialaccount_socialapp_sites")
        max_id = cursor.fetchone()[0]

        # Set the sequence to max_id so next insert gets max_id + 1
        # Use 'true' to indicate this value has been returned by nextval()
        cursor.execute(
            """
            SELECT setval(
                pg_get_serial_sequence('socialaccount_socialapp_sites', 'id'),
                %s,
                true
            )
        """,
            [max_id],
        )

        self.stdout.write(f"✓ Set sequence current value to {max_id}")

        # Verify the sequence is working by checking last_value
        cursor.execute(
            """
            SELECT last_value FROM socialaccount_socialapp_sites_id_seq
        """
        )
        current_val = cursor.fetchone()[0]

        self.stdout.write(
            f"✓ Sequence last_value is {current_val}, next insert will get {current_val + 1}"
        )

    def _fix_missing_site_associations(self, cursor):
        """Fix missing site associations with proper ID generation"""
        self.stdout.write("Fixing missing site associations...")

        # Get social apps without site associations
        cursor.execute(
            """
            SELECT sa.id, sa.name 
            FROM socialaccount_socialapp sa
            WHERE sa.id NOT IN (
                SELECT DISTINCT socialapp_id 
                FROM socialaccount_socialapp_sites
                WHERE socialapp_id IS NOT NULL
            )
        """
        )

        orphaned_apps = cursor.fetchall()

        if not orphaned_apps:
            self.stdout.write("✓ All social apps already have site associations")
            return

        self.stdout.write(
            f"Found {len(orphaned_apps)} social apps needing site associations"
        )

        # Ensure default site exists
        if connection.vendor == "sqlite":
            cursor.execute(
                """
                INSERT OR IGNORE INTO django_site (id, domain, name) 
                VALUES (1, 'gemnar.com', 'Gemnar')
            """
            )
        else:  # PostgreSQL
            cursor.execute(
                """
                INSERT INTO django_site (id, domain, name) 
                VALUES (1, 'gemnar.com', 'Gemnar')
                ON CONFLICT (id) DO NOTHING
            """
            )

        # Insert associations one by one with proper database handling
        for app_id, app_name in orphaned_apps:
            try:
                if connection.vendor == "sqlite":
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO socialaccount_socialapp_sites (socialapp_id, site_id) 
                        VALUES (?, 1)
                    """,
                        [app_id],
                    )
                else:  # PostgreSQL
                    cursor.execute(
                        """
                        INSERT INTO socialaccount_socialapp_sites (socialapp_id, site_id) 
                        VALUES (%s, 1)
                        ON CONFLICT (socialapp_id, site_id) DO NOTHING
                    """,
                        [app_id],
                    )

                self.stdout.write(
                    f"✓ Associated app '{app_name}' (ID: {app_id}) with default site"
                )

            except Exception as e:
                self.stdout.write(
                    f"✗ Failed to associate app '{app_name}' (ID: {app_id}): {e}"
                )

    def handle(self, *args, **options):
        """Handle the command with options"""
        dry_run = options.get("dry_run", False)
        verbose = options.get("verbose", False)

        if dry_run:
            self.stdout.write("DRY RUN MODE - No changes will be made")

        self.stdout.write("Fixing socialaccount_socialapp_sites sequence issues...")

        if dry_run:
            self._diagnose_issue_only()
        else:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    if verbose:
                        self._diagnose_issue(cursor)

                    self._fix_sequence_issue(cursor)
                    self._fix_missing_site_associations(cursor)

            self.stdout.write(self.style.SUCCESS("Sequence issues fixed!"))

    def _diagnose_issue_only(self):
        """Diagnose without making changes"""
        with connection.cursor() as cursor:
            self._diagnose_issue(cursor)

            # Check if we can predict what would happen
            cursor.execute(
                "SELECT COALESCE(MAX(id), 0) FROM socialaccount_socialapp_sites"
            )
            max_id = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT id FROM socialaccount_socialapp 
                WHERE id NOT IN (
                    SELECT DISTINCT socialapp_id 
                    FROM socialaccount_socialapp_sites
                    WHERE socialapp_id IS NOT NULL
                )
            """
            )
            orphaned_apps = cursor.fetchall()

            self.stdout.write("\nProposed changes:")
            self.stdout.write(f"- Would set sequence to start at {max_id + 1}")
            self.stdout.write(
                f"- Would create {len(orphaned_apps)} new site associations"
            )
            for app_id_tuple in orphaned_apps:
                self.stdout.write(f"  - Social app ID {app_id_tuple[0]} → Site ID 1")
