# Generated manually to add missing FlowWorkspace fields
# These were supposed to be added in 0064 but that migration was converted to no-op

import django.db.models.deletion
import uuid
import website.workspace_models
from django.db import migrations, models, connection


def get_db_vendor():
    """Get the database vendor (sqlite, postgresql, etc.)"""
    return connection.vendor


def column_exists(table_name, column_name):
    """Check if a column exists in a table (supports SQLite and PostgreSQL)"""
    vendor = get_db_vendor()
    with connection.cursor() as cursor:
        if vendor == 'sqlite':
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return column_name in columns
        else:  # PostgreSQL
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, [table_name, column_name])
            return cursor.fetchone() is not None


def table_exists(table_name):
    """Check if a table exists (supports SQLite and PostgreSQL)"""
    vendor = get_db_vendor()
    with connection.cursor() as cursor:
        if vendor == 'sqlite':
            # Use string formatting for SQLite to avoid parameter issues
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
        else:  # PostgreSQL
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = %s
            """, [table_name])
        return cursor.fetchone() is not None


def index_exists(index_name):
    """Check if an index exists (supports SQLite and PostgreSQL)"""
    vendor = get_db_vendor()
    with connection.cursor() as cursor:
        if vendor == 'sqlite':
            # Use string formatting for SQLite to avoid parameter issues
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"
            )
        else:  # PostgreSQL
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE indexname = %s
            """, [index_name])
        return cursor.fetchone() is not None


def add_fields_if_missing(apps, schema_editor):
    """Add missing fields to FlowWorkspace table"""
    table_name = 'website_flow_workspace'
    vendor = get_db_vendor()
    
    with connection.cursor() as cursor:
        # Add clone_count if missing
        if not column_exists(table_name, 'clone_count'):
            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN clone_count INTEGER DEFAULT 0 NOT NULL')
            print(f"Added clone_count to {table_name}")
        
        # Add description if missing
        if not column_exists(table_name, 'description'):
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN description TEXT DEFAULT '' NOT NULL")
            print(f"Added description to {table_name}")
        
        # Add is_public if missing
        if not column_exists(table_name, 'is_public'):
            if vendor == 'sqlite':
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN is_public INTEGER DEFAULT 0 NOT NULL')
            else:
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN is_public BOOLEAN DEFAULT FALSE NOT NULL')
            print(f"Added is_public to {table_name}")
        
        # Add published_at if missing
        if not column_exists(table_name, 'published_at'):
            if vendor == 'sqlite':
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN published_at DATETIME NULL')
            else:
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN published_at TIMESTAMP WITH TIME ZONE NULL')
            print(f"Added published_at to {table_name}")
        
        # Add view_count if missing
        if not column_exists(table_name, 'view_count'):
            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN view_count INTEGER DEFAULT 0 NOT NULL')
            print(f"Added view_count to {table_name}")
        
        # Add indexes if missing
        if not index_exists('website_flo_is_publ_c7a8a7_idx'):
            if vendor == 'sqlite':
                cursor.execute(f'CREATE INDEX website_flo_is_publ_c7a8a7_idx ON {table_name} (is_public, published_at DESC)')
            else:
                cursor.execute(f'CREATE INDEX website_flo_is_publ_c7a8a7_idx ON {table_name} (is_public, published_at DESC NULLS LAST)')
            print("Added index website_flo_is_publ_c7a8a7_idx")
        
        if not index_exists('website_flo_is_publ_cc1f27_idx'):
            cursor.execute(f'CREATE INDEX website_flo_is_publ_cc1f27_idx ON {table_name} (is_public, view_count DESC)')
            print("Added index website_flo_is_publ_cc1f27_idx")


def create_workspace_media_if_missing(apps, schema_editor):
    """Create WorkspaceMedia table if it doesn't exist"""
    vendor = get_db_vendor()
    
    if not table_exists('website_workspace_media'):
        with connection.cursor() as cursor:
            if vendor == 'sqlite':
                # SQLite version
                cursor.execute('''
                    CREATE TABLE website_workspace_media (
                        id VARCHAR(36) PRIMARY KEY,
                        media_type VARCHAR(10) NOT NULL,
                        file VARCHAR(255) NOT NULL,
                        thumbnail VARCHAR(255) NULL,
                        title VARCHAR(255) DEFAULT '' NOT NULL,
                        "order" INTEGER DEFAULT 0 NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        workspace_id VARCHAR(36) NOT NULL REFERENCES website_flow_workspace(id) ON DELETE CASCADE
                    )
                ''')
            else:
                # PostgreSQL version
                cursor.execute('''
                    CREATE TABLE website_workspace_media (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        media_type VARCHAR(10) NOT NULL,
                        file VARCHAR(255) NOT NULL,
                        thumbnail VARCHAR(255) NULL,
                        title VARCHAR(255) DEFAULT '' NOT NULL,
                        "order" INTEGER DEFAULT 0 NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        workspace_id UUID NOT NULL REFERENCES website_flow_workspace(id) ON DELETE CASCADE
                    )
                ''')
            cursor.execute('CREATE INDEX workspace_media_workspace_idx ON website_workspace_media (workspace_id)')
            cursor.execute('CREATE INDEX workspace_media_order_idx ON website_workspace_media ("order", created_at DESC)')
            print("Created website_workspace_media table with indexes")
    else:
        print("website_workspace_media table already exists")


class Migration(migrations.Migration):
    """
    Add missing fields to FlowWorkspace and create WorkspaceMedia table.
    These fields were supposed to be added in migration 0064 but that was converted to no-op.
    Uses RunPython to safely check if fields/tables exist before creating them.
    """

    dependencies = [
        ("website", "0070_safe_remove_pageview_index"),
    ]

    operations = [
        migrations.RunPython(add_fields_if_missing, migrations.RunPython.noop),
        migrations.RunPython(create_workspace_media_if_missing, migrations.RunPython.noop),
    ]

