#!/usr/bin/env python
"""
Script to fix sites framework migration dependency issue.
Run this before normal migrations on production.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)


def fix_migration_dependencies():
    """
    Fix migration dependency issues by marking missing dependencies as applied.
    """
    print("Checking for migration dependency issues...")

    with connection.cursor() as cursor:
        # Check if website.0022_fix_sites_dependency exists but isn't marked
        # as applied
        cursor.execute(
            """
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'website' AND name = '0022_fix_sites_dependency'
        """
        )
        sites_dependency_applied = cursor.fetchone()[0] > 0

        # Check if website.0023_ensure_sites_first exists but isn't marked
        # as applied
        cursor.execute(
            """
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'website' AND name = '0023_ensure_sites_first'
        """
        )
        sites_migration_applied = cursor.fetchone()[0] > 0

        # Check if account.0001_initial is applied
        cursor.execute(
            """
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'account' AND name = '0001_initial'
        """
        )
        account_migration_applied = cursor.fetchone()[0] > 0

        # Fix website.0022_fix_sites_dependency dependency issue
        if sites_migration_applied and not sites_dependency_applied:
            print(
                "Found dependency issue: website.0023_ensure_sites_first applied before "
                "website.0022_fix_sites_dependency"
            )
            print("Marking website.0022_fix_sites_dependency as applied...")

            # Mark the dependency migration as applied
            cursor.execute(
                """
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('website', '0022_fix_sites_dependency', NOW())
            """
            )

            print("Website dependency issue fixed")

        # Fix account.0001_initial dependency issue
        if account_migration_applied and not sites_migration_applied:
            print(
                "Found dependency issue: account.0001_initial applied before "
                "website.0023_ensure_sites_first"
            )
            print("Marking website.0023_ensure_sites_first as applied...")

            # Mark the dependency migration as applied
            cursor.execute(
                """
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('website', '0023_ensure_sites_first', NOW())
            """
            )

            print("Account dependency issue fixed")

        if (
            not sites_migration_applied
            and not sites_dependency_applied
            and not account_migration_applied
        ):
            print("No dependency issues found")


def fix_sites_migration():
    """
    Fix the sites migration dependency issue by ensuring sites is migrated first.
    """
    print("Fixing sites framework migration dependency...")

    # Check if sites migrations have been applied
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'sites' AND name = '0001_initial'
        """
        )
        sites_migrated = cursor.fetchone()[0] > 0

        # Check if socialaccount migrations have been applied
        cursor.execute(
            """
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'socialaccount' AND name = '0001_initial'
        """
        )
        socialaccount_migrated = cursor.fetchone()[0] > 0

        if socialaccount_migrated and not sites_migrated:
            print("Found dependency issue: socialaccount migrated before sites")
            print("Applying sites migration manually...")

            # Mark sites migration as applied without running it
            cursor.execute(
                """
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('sites', '0001_initial', NOW())
            """
            )

            # Create the sites table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS django_site (
                    id SERIAL PRIMARY KEY,
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

            print("Sites framework fixed successfully")
        else:
            print("No sites dependency issue found")

    # Fix migration dependencies
    fix_migration_dependencies()

    print("Running remaining migrations...")
    execute_from_command_line(["manage.py", "migrate"])


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gemnar.settings")
    django.setup()
    fix_sites_migration()
