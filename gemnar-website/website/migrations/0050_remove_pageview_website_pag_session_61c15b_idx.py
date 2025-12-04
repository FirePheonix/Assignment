"""Safely remove orphaned PageView session index if it exists.

Replaces a brittle RemoveIndex that fails on SQLite when the index
doesn't exist (e.g., on fresh test databases).
"""

from django.db import migrations


def safe_drop_pageview_session_index(apps, schema_editor):
    index_name = "website_pag_session_61c15b_idx"
    vendor = getattr(schema_editor.connection, "vendor", "")

    try:
        with schema_editor.connection.cursor() as cursor:
            if vendor == "postgresql":
                cursor.execute(f'DROP INDEX IF EXISTS "{index_name}";')
            elif vendor == "sqlite":
                # Check existence first; then drop
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name=?
                    """,
                    [index_name],
                )
                if cursor.fetchone():
                    cursor.execute(f"DROP INDEX {index_name};")
            else:
                # Generic attempt with IF EXISTS
                try:
                    cursor.execute(f'DROP INDEX IF EXISTS "{index_name}";')
                except Exception:
                    # Last resort without quotes/IF EXISTS
                    cursor.execute(f"DROP INDEX {index_name};")
    except Exception:
        # Swallow errors; index may not exist in new DBs
        pass


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0049_add_instagram_metrics"),
    ]

    operations = [
        migrations.RunPython(safe_drop_pageview_session_index, noop_reverse),
    ]
