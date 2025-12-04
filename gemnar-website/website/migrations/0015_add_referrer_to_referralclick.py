# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0014_task_taskapplication"),
    ]

    operations = [
        migrations.AddField(
            model_name="referralclick",
            name="referrer",
            field=models.URLField(
                blank=True, help_text="URL where the click originated from", null=True
            ),
        ),
    ]
