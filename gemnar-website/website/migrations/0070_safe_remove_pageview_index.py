# Safe removal of pageview session index
from django.db import migrations


def safe_remove_pageview_index(apps, schema_editor):
    """
    Safely remove the pageview session index if it exists.
    Handles both SQLite and PostgreSQL databases.
    """
    index_name = "website_pag_session_61c15b_idx"
    vendor = schema_editor.connection.vendor
    
    try:
        with schema_editor.connection.cursor() as cursor:
            if vendor == "postgresql":
                # PostgreSQL: Drop if exists
                cursor.execute(f'DROP INDEX IF EXISTS "{index_name}";')
            elif vendor == "sqlite":
                # SQLite: Check first, then drop
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name=?
                    """,
                    [index_name],
                )
                if cursor.fetchone():
                    cursor.execute(f"DROP INDEX IF EXISTS {index_name};")
            else:
                # MySQL or other: Try generic DROP IF EXISTS
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS {index_name};")
                except Exception:
                    pass
    except Exception as e:
        # Silently ignore errors - index may not exist
        print(f"Note: Could not remove index {index_name} (may not exist): {e}")


class Migration(migrations.Migration):
    """
    Safely removes the pageview session index that was causing migration conflicts.
    Replaced the RemoveIndex operation from migration 0059 with this safe version.
    """

    dependencies = [
        ('website', '0069_alter_queuedtweet_options_and_more'),
    ]

    operations = [
        migrations.RunPython(
            safe_remove_pageview_index,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
