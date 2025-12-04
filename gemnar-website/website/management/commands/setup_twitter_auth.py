import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = "Set up Twitter OAuth 2.0 application for social authentication"

    def add_arguments(self, parser):
        parser.add_argument(
            "--client-id",
            type=str,
            help="Twitter OAuth 2.0 Client ID",
            default=os.environ.get("TWITTER_CLIENT_ID"),
        )
        parser.add_argument(
            "--client-secret",
            type=str,
            help="Twitter OAuth 2.0 Client Secret",
            default=os.environ.get("TWITTER_CLIENT_SECRET"),
        )
        parser.add_argument(
            "--name", type=str, help="Application name", default="Twitter"
        )

    def handle(self, *args, **options):
        client_id = options["client_id"]
        client_secret = options["client_secret"]
        app_name = options["name"]

        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR(
                    "Twitter OAuth credentials are required. "
                    "Set TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET "
                    "environment variables or use --client-id and "
                    "--client-secret arguments."
                )
            )
            return

        # Get or create the current site
        try:
            site = Site.objects.get_current()
        except Site.DoesNotExist:
            site = Site.objects.create(domain="gemnar.com", name="Gemnar")
            self.stdout.write(self.style.SUCCESS(f"Created site: {site.domain}"))

        # Create or update Twitter OAuth 2.0 social application
        social_app, created = SocialApp.objects.get_or_create(
            provider="twitter_oauth2",
            name=app_name,
            defaults={
                "client_id": client_id,
                "secret": client_secret,
            },
        )

        if not created:
            # Update existing app
            social_app.client_id = client_id
            social_app.secret = client_secret
            social_app.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated existing Twitter OAuth 2.0 app: {app_name}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Created new Twitter OAuth 2.0 app: {app_name}")
            )

        # Add the current site to the social app
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f"Added site {site.domain} to Twitter app")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Twitter OAuth 2.0 setup complete!\n"
                f"App Name: {social_app.name}\n"
                f"Provider: {social_app.provider}\n"
                f"Client ID: {social_app.client_id[:8]}...\n"
                f"Sites: {', '.join([s.domain for s in social_app.sites.all()])}\n"
                f"\nUsers can now log in with Twitter at: "
                f"/accounts/twitter_oauth2/login/"
            )
        )

        # Display callback URL information
        self.stdout.write(
            self.style.WARNING(
                f"\n📝 Important: Configure this callback URL in your "
                f"Twitter app:\n"
                f"https://{site.domain}/accounts/twitter_oauth2/login/callback/\n"
                f"\nFor development, also add:\n"
                f"http://localhost:8000/accounts/twitter_oauth2/login/callback/"
            )
        )
