# Generated manually to remove orphaned index
from django.db import migrations


def remove_orphaned_index(apps, schema_editor):
    """Remove the orphaned session index if it exists"""
    # Try to remove the index, ignore if it doesn't exist
    try:
        with schema_editor.connection.cursor() as cursor:
            # Check if we're using PostgreSQL or SQLite
            if schema_editor.connection.vendor == "postgresql":
                cursor.execute("DROP INDEX IF EXISTS website_pag_session_61c15b_idx;")
            elif schema_editor.connection.vendor == "sqlite":
                # SQLite doesn't support IF EXISTS for DROP INDEX, so we check first
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name='website_pag_session_61c15b_idx';
                """
                )
                if cursor.fetchone():
                    cursor.execute("DROP INDEX website_pag_session_61c15b_idx;")
            else:
                # For other databases, try the generic approach
                cursor.execute("DROP INDEX IF EXISTS website_pag_session_61c15b_idx;")
    except Exception:
        # If the index doesn't exist or there's an error, that's fine
        # We just want to make sure it's gone
        pass


def reverse_remove_orphaned_index(apps, schema_editor):
    """Cannot recreate the index without the session field"""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0045_remove_pageview_website_pag_session_61c15b_idx_and_more"),
    ]

    operations = [
        # Remove the orphaned session index if it exists
        migrations.RunPython(
            remove_orphaned_index,
            reverse_remove_orphaned_index,
        ),
    ]
