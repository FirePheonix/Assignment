from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Fix sites/socialaccount migration dependency issue"

    def handle(self, *args, **options):
        """
        Fix the migration dependency issue where socialaccount migrations
        were applied before sites migrations.
        """
        self.stdout.write("Fixing sites/socialaccount migration dependency issue...")

        with connection.cursor() as cursor:
            # Check if sites migrations are already marked as applied
            cursor.execute(
                """
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = 'sites' AND name = '0001_initial'
            """
            )
            sites_initial_applied = cursor.fetchone()[0] > 0

            cursor.execute(
                """
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = 'sites' AND name = '0002_alter_domain_unique'
            """
            )
            sites_alter_domain_applied = cursor.fetchone()[0] > 0

            # Check if socialaccount migrations are applied
            cursor.execute(
                """
                SELECT COUNT(*) FROM django_migrations 
                WHERE app = 'socialaccount' AND name = '0001_initial'
            """
            )
            socialaccount_applied = cursor.fetchone()[0] > 0

            if socialaccount_applied and not sites_initial_applied:
                self.stdout.write(
                    "Found dependency issue: socialaccount applied before sites"
                )

                # Create sites table if it doesn't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS django_site (
                        id INTEGER PRIMARY KEY,
                        domain VARCHAR(100) NOT NULL UNIQUE,
                        name VARCHAR(50) NOT NULL
                    )
                """
                )

                # Insert default site if it doesn't exist
                cursor.execute(
                    """
                    INSERT INTO django_site (id, domain, name) 
                    VALUES (1, 'example.com', 'example.com')
                    ON CONFLICT (id) DO NOTHING
                """
                )

                # Mark sites migrations as applied
                cursor.execute(
                    """
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES ('sites', '0001_initial', datetime('now'))
                """
                )

                self.stdout.write("✓ Marked sites.0001_initial as applied")

            if socialaccount_applied and not sites_alter_domain_applied:
                # Mark the second sites migration as applied
                cursor.execute(
                    """
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES ('sites', '0002_alter_domain_unique', 
                            datetime('now'))
                """
                )

                self.stdout.write("✓ Marked sites.0002_alter_domain_unique as applied")

            # Check if we need to create the missing table
            # Use database-specific syntax for checking table existence
            if connection.vendor == "sqlite":
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name='socialaccount_socialapp_sites'
                """
                )
            else:  # PostgreSQL and other databases
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'socialaccount_socialapp_sites'
                """
                )
            socialapp_sites_exists = cursor.fetchone()[0] > 0

            if not socialapp_sites_exists:
                self.stdout.write(
                    "Creating missing socialaccount_socialapp_sites table..."
                )

                # Create the missing many-to-many table
                cursor.execute(
                    """
                    CREATE TABLE socialaccount_socialapp_sites (
                        id INTEGER PRIMARY KEY,
                        socialapp_id INTEGER NOT NULL,
                        site_id INTEGER NOT NULL,
                        FOREIGN KEY (socialapp_id) 
                            REFERENCES socialaccount_socialapp (id),
                        FOREIGN KEY (site_id) REFERENCES django_site (id),
                        UNIQUE(socialapp_id, site_id)
                    )
                """
                )

                self.stdout.write("✓ Created socialaccount_socialapp_sites table")

        self.stdout.write(self.style.SUCCESS("Migration dependency issue fixed!"))
        self.stdout.write("You can now run: python manage.py migrate")
