# Generated migration for adding slug field to FlowWorkspace

from django.db import migrations, models
import uuid


def generate_slugs(apps, schema_editor):
    """Generate slugs for existing workspaces"""
    FlowWorkspace = apps.get_model('website', 'FlowWorkspace')
    for workspace in FlowWorkspace.objects.all():
        # Use first 12 characters of UUID for slug
        workspace.slug = str(workspace.id)[:12]
        workspace.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0062_cloudinary_nullable_user'),
    ]

    operations = [
        # Step 1: Add slug field as nullable first
        migrations.AddField(
            model_name='flowworkspace',
            name='slug',
            field=models.CharField(
                max_length=12,
                null=True,
                blank=True,
                help_text='Unique slug for workspace URL (auto-generated from UUID)'
            ),
        ),
        
        # Step 2: Generate slugs for existing records
        migrations.RunPython(generate_slugs, reverse_code=migrations.RunPython.noop),
        
        # Step 3: Make slug unique and non-nullable
        migrations.AlterField(
            model_name='flowworkspace',
            name='slug',
            field=models.CharField(
                max_length=12,
                unique=True,
                db_index=True,
                editable=False,
                help_text='Unique slug for workspace URL (auto-generated from UUID)'
            ),
        ),
        
        # Add index for slug
        migrations.AddIndex(
            model_name='flowworkspace',
            index=models.Index(fields=['slug'], name='website_flo_slug_idx'),
        ),
    ]
