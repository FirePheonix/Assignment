from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Fix socialaccount_socialapp_sites integrity issues"

    def handle(self, *args, **options):
        """
        Fix the socialaccount_socialapp_sites table integrity issues.
        This handles both missing tables and sequence synchronization problems.
        """
        check_only = options.get("check_only", False)
        verbose = options.get("verbose", False)

        if check_only:
            self.stdout.write("Checking for integrity issues...")
            self._check_integrity_issues(verbose)
        else:
            self.stdout.write(
                "Fixing socialaccount_socialapp_sites integrity issues..."
            )
            self._fix_integrity_issues(verbose)

    def _check_integrity_issues(self, verbose):
        """Check for integrity issues without fixing them"""
        with connection.cursor() as cursor:
            issues_found = False

            # Check if table exists
            if not self._check_table_exists(cursor):
                self.stdout.write(
                    self.style.WARNING("❌ socialaccount_socialapp_sites table missing")
                )
                issues_found = True
            else:
                self.stdout.write("✓ socialaccount_socialapp_sites table exists")

            # Check for sequence issues (PostgreSQL only)
            if connection.vendor == "postgresql":
                try:
                    cursor.execute(
                        "SELECT nextval(pg_get_serial_sequence('socialaccount_socialapp_sites', 'id'))"
                    )
                    next_id = cursor.fetchone()[0]

                    cursor.execute(
                        "SELECT COALESCE(MAX(id), 0) FROM socialaccount_socialapp_sites"
                    )
                    max_id = cursor.fetchone()[0]

                    if next_id <= max_id:
                        self.stdout.write(
                            self.style.WARNING(
                                f"❌ Sequence issue: next_id={next_id}, max_id={max_id}"
                            )
                        )
                        issues_found = True
                    else:
                        self.stdout.write("✓ Sequence is synchronized")
                except Exception as e:
                    if verbose:
                        self.stdout.write(f"Could not check sequence: {e}")

            if issues_found:
                self.stdout.write(
                    self.style.ERROR(
                        "Issues found! Run without --check-only to fix them."
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS("No integrity issues found!"))

    def _fix_integrity_issues(self, verbose):
        """Fix all integrity issues"""
        with transaction.atomic():
            with connection.cursor() as cursor:
                # First, ensure the Site table exists and has a default site
                self._ensure_site_exists(cursor)

                # Check if socialaccount_socialapp_sites table exists
                table_exists = self._check_table_exists(cursor)

                if not table_exists:
                    self.stdout.write(
                        "Creating missing socialaccount_socialapp_sites table..."
                    )
                    self._create_socialapp_sites_table(cursor)
                else:
                    if verbose:
                        self.stdout.write(
                            "Table exists, checking for integrity issues..."
                        )
                    self._fix_table_integrity(cursor)

                # Fix sequence issues
                self._fix_sequence_issues(cursor)

                # Ensure all social apps have site associations
                self._ensure_social_apps_have_sites(cursor)

        self.stdout.write(self.style.SUCCESS("Integrity issues fixed!"))
        self.stdout.write("You can now use the admin interface for social apps.")

    def _ensure_site_exists(self, cursor):
        """Ensure the Site table exists and has a default site"""
        if connection.vendor == "sqlite":
            cursor.execute(
                """
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='django_site'
            """
            )
        else:  # PostgreSQL
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'django_site'
            """
            )

        site_table_exists = cursor.fetchone()[0] > 0

        if not site_table_exists:
            if connection.vendor == "sqlite":
                cursor.execute(
                    """
                    CREATE TABLE django_site (
                        id INTEGER PRIMARY KEY,
                        domain VARCHAR(100) NOT NULL UNIQUE,
                        name VARCHAR(50) NOT NULL
                    )
                """
                )
            else:  # PostgreSQL
                cursor.execute(
                    """
                    CREATE TABLE django_site (
                        id SERIAL PRIMARY KEY,
                        domain VARCHAR(100) NOT NULL UNIQUE,
                        name VARCHAR(50) NOT NULL
                    )
                """
                )
            self.stdout.write("✓ Created django_site table")

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

        self.stdout.write("✓ Ensured default site exists")

    def _check_table_exists(self, cursor):
        """Check if socialaccount_socialapp_sites table exists"""
        if connection.vendor == "sqlite":
            cursor.execute(
                """
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='socialaccount_socialapp_sites'
            """
            )
        else:  # PostgreSQL
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'socialaccount_socialapp_sites'
            """
            )

        return cursor.fetchone()[0] > 0

    def _create_socialapp_sites_table(self, cursor):
        """Create the socialaccount_socialapp_sites table"""
        if connection.vendor == "sqlite":
            cursor.execute(
                """
                CREATE TABLE socialaccount_socialapp_sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    socialapp_id INTEGER NOT NULL,
                    site_id INTEGER NOT NULL,
                    FOREIGN KEY (socialapp_id) 
                        REFERENCES socialaccount_socialapp (id) DEFERRABLE INITIALLY DEFERRED,
                    FOREIGN KEY (site_id) 
                        REFERENCES django_site (id) DEFERRABLE INITIALLY DEFERRED,
                    UNIQUE(socialapp_id, site_id)
                )
            """
            )
        else:  # PostgreSQL
            cursor.execute(
                """
                CREATE TABLE socialaccount_socialapp_sites (
                    id SERIAL PRIMARY KEY,
                    socialapp_id INTEGER NOT NULL,
                    site_id INTEGER NOT NULL,
                    FOREIGN KEY (socialapp_id) 
                        REFERENCES socialaccount_socialapp (id) DEFERRABLE INITIALLY DEFERRED,
                    FOREIGN KEY (site_id) 
                        REFERENCES django_site (id) DEFERRABLE INITIALLY DEFERRED,
                    UNIQUE(socialapp_id, site_id)
                )
            """
            )

        self.stdout.write("✓ Created socialaccount_socialapp_sites table")

    def _fix_table_integrity(self, cursor):
        """Fix integrity issues in existing table"""
        # Check for any orphaned records
        cursor.execute(
            """
            SELECT COUNT(*) FROM socialaccount_socialapp_sites 
            WHERE socialapp_id NOT IN (
                SELECT id FROM socialaccount_socialapp
            )
        """
        )

        orphaned_socialapp_count = cursor.fetchone()[0]
        if orphaned_socialapp_count > 0:
            self.stdout.write(
                f"Found {orphaned_socialapp_count} orphaned socialapp records"
            )
            cursor.execute(
                """
                DELETE FROM socialaccount_socialapp_sites 
                WHERE socialapp_id NOT IN (
                    SELECT id FROM socialaccount_socialapp
                )
            """
            )
            self.stdout.write("✓ Removed orphaned socialapp records")

        # Check for orphaned site records
        cursor.execute(
            """
            SELECT COUNT(*) FROM socialaccount_socialapp_sites 
            WHERE site_id NOT IN (
                SELECT id FROM django_site
            )
        """
        )

        orphaned_site_count = cursor.fetchone()[0]
        if orphaned_site_count > 0:
            self.stdout.write(f"Found {orphaned_site_count} orphaned site records")
            cursor.execute(
                """
                DELETE FROM socialaccount_socialapp_sites 
                WHERE site_id NOT IN (
                    SELECT id FROM django_site
                )
            """
            )
            self.stdout.write("✓ Removed orphaned site records")

    def _fix_sequence_issues(self, cursor):
        """Fix sequence synchronization issues"""
        if connection.vendor == "postgresql":
            # Get the maximum ID from the table
            cursor.execute(
                """
                SELECT COALESCE(MAX(id), 0) FROM socialaccount_socialapp_sites
            """
            )
            max_id = cursor.fetchone()[0]

            # Reset the sequence to the correct value
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

            self.stdout.write(f"✓ Reset sequence to {max_id}")

        # For SQLite, this is handled automatically by AUTOINCREMENT

    def _ensure_social_apps_have_sites(self, cursor):
        """Ensure all social apps have at least one site association"""
        # Get all social apps without site associations
        cursor.execute(
            """
            SELECT id FROM socialaccount_socialapp 
            WHERE id NOT IN (
                SELECT DISTINCT socialapp_id 
                FROM socialaccount_socialapp_sites
            )
        """
        )

        apps_without_sites = cursor.fetchall()

        if apps_without_sites:
            self.stdout.write(
                f"Found {len(apps_without_sites)} social apps without sites"
            )

            # Associate them with the default site (id=1)
            for app_id_tuple in apps_without_sites:
                app_id = app_id_tuple[0]

                if connection.vendor == "sqlite":
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO socialaccount_socialapp_sites 
                        (socialapp_id, site_id) VALUES (?, 1)
                    """,
                        [app_id],
                    )
                else:  # PostgreSQL
                    cursor.execute(
                        """
                        INSERT INTO socialaccount_socialapp_sites 
                        (socialapp_id, site_id) VALUES (%s, 1)
                        ON CONFLICT (socialapp_id, site_id) DO NOTHING
                    """,
                        [app_id],
                    )

            self.stdout.write("✓ Associated social apps with default site")

    def add_arguments(self, parser):
        parser.add_argument(
            "--check-only",
            action="store_true",
            help="Only check for issues without fixing them",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output",
        )
