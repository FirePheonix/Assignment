"""
Management command to set up the credit system
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from website.models import Brand, CreditPackage
from website.utils.credit_manager import CreditManager


class Command(BaseCommand):
    help = "Set up the AI credit system with initial packages and free credits for existing brands"

    def add_arguments(self, parser):
        parser.add_argument(
            "--free-credits",
            type=float,
            default=5.0,
            help="Amount of free credits to give to existing brands (default: 5.0)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        free_credits = Decimal(str(options["free_credits"]))
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        self.stdout.write("Setting up AI credit system...")

        # Check existing credit packages
        existing_packages = CreditPackage.objects.all()
        self.stdout.write(f"Found {existing_packages.count()} existing credit packages")

        if existing_packages.count() == 0:
            self.stdout.write(
                "No credit packages found. Run migration 0053 to create initial packages."
            )
        else:
            for package in existing_packages:
                self.stdout.write(
                    f"  - {package.name}: {package.total_credits} credits for ${package.price_usd}"
                )

        # Get brands that don't have credits yet
        brands_without_credits = Brand.objects.filter(credits_balance=0)
        self.stdout.write(
            f"\nFound {brands_without_credits.count()} brands with 0 credits"
        )

        if brands_without_credits.count() > 0 and free_credits > 0:
            if not dry_run:
                with transaction.atomic():
                    credits_given = 0
                    for brand in brands_without_credits:
                        success, message = CreditManager.add_credits(
                            brand=brand,
                            amount=free_credits,
                            description=f"Welcome bonus: {free_credits} free AI credits",
                            transaction_type="bonus",
                        )

                        if success:
                            credits_given += 1
                            self.stdout.write(
                                f"  ✓ Gave {free_credits} credits to {brand.name}"
                            )
                        else:
                            self.stdout.write(
                                f"  ✗ Failed to give credits to {brand.name}: {message}"
                            )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\nSuccessfully gave free credits to {credits_given} brands"
                        )
                    )
            else:
                for brand in brands_without_credits:
                    self.stdout.write(
                        f"  Would give {free_credits} credits to {brand.name}"
                    )

        # Show credit statistics
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("CREDIT SYSTEM STATISTICS")
        self.stdout.write("=" * 50)

        total_brands = Brand.objects.count()
        brands_with_credits = Brand.objects.filter(credits_balance__gt=0).count()
        total_credits = sum(b.credits_balance for b in Brand.objects.all())

        self.stdout.write(f"Total brands: {total_brands}")
        self.stdout.write(f"Brands with credits: {brands_with_credits}")
        self.stdout.write(f"Total credits in system: ${total_credits:.2f}")

        if total_brands > 0:
            avg_credits = total_credits / total_brands
            self.stdout.write(f"Average credits per brand: ${avg_credits:.2f}")

        # Show packages info
        if existing_packages.count() > 0:
            self.stdout.write(
                f"\nCredit packages available: {existing_packages.count()}"
            )
            for package in existing_packages.filter(is_active=True):
                ratio = package.credits_per_dollar
                self.stdout.write(
                    f"  - {package.name}: {package.total_credits} credits "
                    f"for ${package.price_usd} ({ratio:.2f} credits/$)"
                )

        self.stdout.write(self.style.SUCCESS("\nCredit system setup complete!"))

        # Show next steps
        self.stdout.write("\nNext steps:")
        self.stdout.write(
            "1. Configure Stripe price IDs for credit packages in Django admin"
        )
        self.stdout.write("2. Add credit purchase functionality to the frontend")
        self.stdout.write("3. Set up webhook handlers for payment processing")
        self.stdout.write("4. Test the Runware integration with credit deduction")
