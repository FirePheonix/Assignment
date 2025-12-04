# Generated manually for adding tweet_url field to BrandTweet model

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0024_aiservicelimit_aiserviceusage_weblog"),
    ]

    operations = [
        migrations.AddField(
            model_name="brandtweet",
            name="tweet_url",
            field=models.URLField(
                blank=True, help_text="Direct URL to the tweet on Twitter", null=True
            ),
        ),
    ]
