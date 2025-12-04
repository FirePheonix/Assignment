"""
Fix workspace slugs to remove dashes
"""
import os
import sys
import django

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gemnar.settings')
django.setup()

from website.workspace_models import FlowWorkspace

def fix_slugs():
    """Update all workspace slugs to remove dashes"""
    workspaces = FlowWorkspace.objects.all()
    updated_count = 0
    
    for workspace in workspaces:
        old_slug = workspace.slug
        # Generate new slug without dashes
        new_slug = str(workspace.id).replace('-', '')[:12]
        
        if old_slug != new_slug:
            workspace.slug = new_slug
            workspace.save(update_fields=['slug'])
            print(f"Updated: {old_slug} -> {new_slug}")
            updated_count += 1
        else:
            print(f"Skipped: {old_slug} (already correct)")
    
    print(f"\n✅ Updated {updated_count} workspace slugs")

if __name__ == '__main__':
    fix_slugs()
