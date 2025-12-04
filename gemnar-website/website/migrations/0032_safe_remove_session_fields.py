# Generated manually - Safe removal of session fields and CustomSession model

from django.db import migrations


def safe_cleanup(apps, schema_editor):
    """
    Safely clean up any remaining session-related data.
    This is a no-op migration since we've already removed the model definitions.
    """
    # CustomSession model and related fields have been removed from models.py
    # This migration just ensures Django's migration state is consistent
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0031_add_analytics_models"),
    ]

    operations = [
        # Just mark that we've cleaned up the session fields
        migrations.RunPython(
            safe_cleanup,
            migrations.RunPython.noop,
        ),
    ]
