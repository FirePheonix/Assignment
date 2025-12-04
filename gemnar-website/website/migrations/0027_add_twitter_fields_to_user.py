# Generated manually to add Twitter fields to User model

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "website",
            "0026_brand_instagram_access_token_brand_instagram_app_id_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="twitter_bearer_token",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=255,
                help_text="Twitter Bearer Token (required for API v2)",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="twitter_username",
            field=models.CharField(
                blank=True, null=True, max_length=100, help_text="Twitter username"
            ),
        ),
    ]
