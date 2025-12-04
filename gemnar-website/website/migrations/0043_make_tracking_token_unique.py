from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0042_add_tweet_tracking_fields"),
    ]

    def clean_tracking_tokens(apps, schema_editor):
        import uuid

        BrandTweet = apps.get_model("website", "BrandTweet")
        seen = set()
        for obj in BrandTweet.objects.all():
            token = obj.tracking_token
            # If blank or duplicate, assign a new unique token
            if not token or token in seen:
                new_token = str(uuid.uuid4())[:32]
                while BrandTweet.objects.filter(tracking_token=new_token).exists():
                    new_token = str(uuid.uuid4())[:32]
                obj.tracking_token = new_token
                obj.save(update_fields=["tracking_token"])
            seen.add(obj.tracking_token)

    operations = [
        migrations.RunPython(clean_tracking_tokens),
        migrations.AlterField(
            model_name="brandtweet",
            name="tracking_token",
            field=models.CharField(
                blank=True,
                help_text="Unique token for tracking link clicks",
                max_length=32,
                unique=True,
            ),
        ),
    ]
