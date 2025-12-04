from django.core.management.base import BaseCommand
from website.models import BrandInstagramPost


class Command(BaseCommand):
    help = "Fix Instagram post images with malformed URLs or local file paths"

    def handle(self, *args, **options):
        posts = BrandInstagramPost.objects.all()
        fixed_count = 0

        for post in posts:
            if post.image:
                image_url = str(post.image)

                # Check if the image has a malformed URL or local path
                if (
                    image_url.startswith("file://")
                    or "http%3A" in image_url
                    or "image_picker_" in image_url
                    or image_url.startswith(
                        "/media/brand_instagram_posts/image_picker_"
                    )
                ):
                    self.stdout.write(f"Fixing post {post.id}: {image_url}")

                    # Clear the malformed image
                    post.image = None
                    post.save()

                    fixed_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully fixed {fixed_count} Instagram posts")
        )
