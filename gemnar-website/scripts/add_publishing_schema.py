#!/usr/bin/env python
"""
Add publishing schema to workspace table
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gemnar.settings')
django.setup()

from django.db import connection

def add_publishing_fields():
    """Add publishing fields to workspace table"""
    cursor = connection.cursor()
    
    try:
        # Add description field
        cursor.execute('ALTER TABLE website_flow_workspace ADD COLUMN description TEXT DEFAULT ""')
        print("✓ Added description field")
    except Exception as e:
        print(f"  description field already exists or error: {e}")
    
    try:
        # Add is_public field
        cursor.execute('ALTER TABLE website_flow_workspace ADD COLUMN is_public INTEGER DEFAULT 0')
        print("✓ Added is_public field")
    except Exception as e:
        print(f"  is_public field already exists or error: {e}")
    
    try:
        # Add published_at field
        cursor.execute('ALTER TABLE website_flow_workspace ADD COLUMN published_at DATETIME NULL')
        print("✓ Added published_at field")
    except Exception as e:
        print(f"  published_at field already exists or error: {e}")
    
    try:
        # Add view_count field
        cursor.execute('ALTER TABLE website_flow_workspace ADD COLUMN view_count INTEGER DEFAULT 0')
        print("✓ Added view_count field")
    except Exception as e:
        print(f"  view_count field already exists or error: {e}")
    
    try:
        # Add clone_count field
        cursor.execute('ALTER TABLE website_flow_workspace ADD COLUMN clone_count INTEGER DEFAULT 0')
        print("✓ Added clone_count field")
    except Exception as e:
        print(f"  clone_count field already exists or error: {e}")
    
    try:
        # Create index on public + published_at
        cursor.execute('CREATE INDEX idx_public_published ON website_flow_workspace(is_public, published_at DESC)')
        print("✓ Created idx_public_published index")
    except Exception as e:
        print(f"  idx_public_published index already exists or error: {e}")
    
    try:
        # Create index on public + view_count
        cursor.execute('CREATE INDEX idx_public_views ON website_flow_workspace(is_public, view_count DESC)')
        print("✓ Created idx_public_views index")
    except Exception as e:
        print(f"  idx_public_views index already exists or error: {e}")
    
    connection.commit()
    print("\n✅ Schema update complete!")

def create_media_table():
    """Create workspace_media table"""
    cursor = connection.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE website_workspace_media (
                id CHAR(32) PRIMARY KEY,
                workspace_id CHAR(32) NOT NULL,
                media_type VARCHAR(10) NOT NULL,
                file VARCHAR(100) NOT NULL,
                thumbnail VARCHAR(100) NULL,
                title VARCHAR(255) DEFAULT '',
                "order" INTEGER DEFAULT 0,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES website_flow_workspace(id) ON DELETE CASCADE
            )
        ''')
        print("✓ Created website_workspace_media table")
        
        cursor.execute('CREATE INDEX idx_media_workspace ON website_workspace_media(workspace_id, "order")')
        print("✓ Created idx_media_workspace index")
        
        connection.commit()
        print("\n✅ Media table created!")
    except Exception as e:
        print(f"  Media table already exists or error: {e}")

if __name__ == '__main__':
    print("Adding publishing schema to workspace table...\n")
    add_publishing_fields()
    print("\nCreating workspace media table...\n")
    create_media_table()
