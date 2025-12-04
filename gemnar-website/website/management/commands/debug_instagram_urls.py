from django.core.management.base import BaseCommand
from website.models import BrandInstagramPost
from django.conf import settings


class Command(BaseCommand):
    help = "Debug Instagram post URLs for specific post IDs"

    def add_arguments(self, parser):
        parser.add_argument("post_ids", nargs="+", type=int, help="Post IDs to debug")

    def handle(self, *args, **options):
        post_ids = options["post_ids"]

        self.stdout.write("=" * 60)
        self.stdout.write("INSTAGRAM POST URL DEBUG")
        self.stdout.write("=" * 60)

        for post_id in post_ids:
            self.stdout.write(f"\n--- Post {post_id} ---")

            try:
                post = BrandInstagramPost.objects.get(id=post_id)

                self.stdout.write(f"Post ID: {post.id}")
                self.stdout.write(f"Content: {post.content[:100]}...")
                self.stdout.write(f"Status: {post.status}")

                # Print image field (relative URL)
                if post.image:
                    self.stdout.write(f"Image field (relative): {post.image.url}")
                else:
                    self.stdout.write("Image field: None")

                # Print thumbnail URL
                thumbnail_url = post.get_thumbnail_url()
                if thumbnail_url:
                    self.stdout.write(f"Thumbnail URL: {thumbnail_url}")
                else:
                    self.stdout.write("Thumbnail URL: None")

                # Print media URL
                media_url = post.get_media_url()
                if media_url:
                    self.stdout.write(f"Media URL: {media_url}")
                else:
                    self.stdout.write("Media URL: None")

                # Construct absolute URLs
                if post.image:
                    from django.contrib.sites.models import Site

                    try:
                        current_site = Site.objects.get_current()
                        protocol = (
                            "https" if getattr(settings, "USE_TLS", True) else "http"
                        )
                        absolute_image_url = (
                            f"{protocol}://{current_site.domain}{post.image.url}"
                        )
                        self.stdout.write(f"Absolute Image URL: {absolute_image_url}")
                    except Exception as e:
                        self.stdout.write(f"Could not construct absolute URL: {e}")

            except BrandInstagramPost.DoesNotExist:
                self.stdout.write(f"Post {post_id} does not exist")
            except Exception as e:
                self.stdout.write(f"Error processing post {post_id}: {e}")

        self.stdout.write("\n" + "=" * 60)
