from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import models
from website.models import Brand


class Command(BaseCommand):
    help = "Fix brands with empty or null slugs by regenerating them"

    def handle(self, *args, **options):
        # Find brands with empty or null slugs
        brands_without_slugs = Brand.objects.filter(
            models.Q(slug__isnull=True) | models.Q(slug="")
        )

        count = brands_without_slugs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No brands with empty slugs found."))
            return

        self.stdout.write(f"Found {count} brands with empty slugs. Fixing...")

        fixed_count = 0
        for brand in brands_without_slugs:
            if brand.name:
                # Generate slug from name
                base_slug = slugify(brand.name)
                if base_slug:  # Make sure we got a valid slug
                    # Check for uniqueness
                    counter = 1
                    slug = base_slug
                    while Brand.objects.filter(slug=slug).exclude(pk=brand.pk).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    brand.slug = slug
                    brand.save()
                    fixed_count += 1
                    self.stdout.write(f'Fixed brand "{brand.name}" -> slug: "{slug}"')
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Could not generate slug for brand "{brand.name}"'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Brand with ID {brand.id} has no name to generate slug from"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully fixed {fixed_count} out of {count} brands."
            )
        )
