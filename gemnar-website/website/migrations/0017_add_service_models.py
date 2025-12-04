# Generated manually for agency service models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0016_add_encrypted_variable"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServicePrompt",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "service",
                    models.CharField(
                        choices=[
                            ("twitter", "Twitter"),
                            ("instagram", "Instagram"),
                            ("reddit", "Reddit"),
                            ("blog", "Blog"),
                            ("gemnar_feed", "Gemnar Feed"),
                        ],
                        max_length=20,
                    ),
                ),
                ("prompt", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("scheduled", "Scheduled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("generated_content", models.TextField(blank=True, null=True)),
                (
                    "generated_image",
                    models.ImageField(
                        blank=True, null=True, upload_to="generated_images/"
                    ),
                ),
                ("posted_at", models.DateTimeField(blank=True, null=True)),
                ("external_url", models.URLField(blank=True, null=True)),
                (
                    "external_id",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("likes", models.IntegerField(default=0)),
                ("shares", models.IntegerField(default=0)),
                ("comments", models.IntegerField(default=0)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="website.user"
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ServiceStats",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "service",
                    models.CharField(
                        choices=[
                            ("twitter", "Twitter"),
                            ("instagram", "Instagram"),
                            ("reddit", "Reddit"),
                            ("blog", "Blog"),
                            ("gemnar_feed", "Gemnar Feed"),
                        ],
                        max_length=20,
                    ),
                ),
                ("total_prompts", models.IntegerField(default=0)),
                ("successful_posts", models.IntegerField(default=0)),
                ("failed_posts", models.IntegerField(default=0)),
                ("pending_posts", models.IntegerField(default=0)),
                ("total_likes", models.IntegerField(default=0)),
                ("total_shares", models.IntegerField(default=0)),
                ("total_comments", models.IntegerField(default=0)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="website.user"
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "service")},
            },
        ),
        migrations.CreateModel(
            name="ServiceConnection",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "service",
                    models.CharField(
                        choices=[
                            ("twitter", "Twitter"),
                            ("instagram", "Instagram"),
                            ("reddit", "Reddit"),
                            ("blog", "Blog"),
                            ("gemnar_feed", "Gemnar Feed"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_connected", models.BooleanField(default=False)),
                ("access_token", models.TextField(blank=True, null=True)),
                ("refresh_token", models.TextField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("username", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "service_user_id",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="website.user"
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "service")},
            },
        ),
    ]
