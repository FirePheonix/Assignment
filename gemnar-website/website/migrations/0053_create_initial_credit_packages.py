"""
Data migration to create initial credit packages
"""

from django.db import migrations
from decimal import Decimal


def create_initial_credit_packages(apps, schema_editor):
    """Create some initial credit packages"""
    CreditPackage = apps.get_model("website", "CreditPackage")

    packages = [
        {
            "name": "Starter Pack",
            "description": "Perfect for trying out AI features. Generate about 100 images.",
            "credits_amount": Decimal("2.00"),
            "price_usd": Decimal("5.00"),
            "bonus_credits": Decimal("0.00"),
            "sort_order": 1,
            "is_active": True,
            "is_featured": False,
        },
        {
            "name": "Creator Pack",
            "description": "Great for regular content creation. Generate about 500 images.",
            "credits_amount": Decimal("10.00"),
            "price_usd": Decimal("20.00"),
            "bonus_credits": Decimal("2.00"),  # 20% bonus
            "sort_order": 2,
            "is_active": True,
            "is_featured": True,
        },
        {
            "name": "Professional Pack",
            "description": "For heavy users and agencies. Generate about 1250 images.",
            "credits_amount": Decimal("25.00"),
            "price_usd": Decimal("45.00"),
            "bonus_credits": Decimal("5.00"),  # 20% bonus
            "sort_order": 3,
            "is_active": True,
            "is_featured": True,
        },
        {
            "name": "Enterprise Pack",
            "description": "Maximum value for high-volume usage. Generate about 2500 images.",
            "credits_amount": Decimal("50.00"),
            "price_usd": Decimal("80.00"),
            "bonus_credits": Decimal("15.00"),  # 30% bonus
            "sort_order": 4,
            "is_active": True,
            "is_featured": False,
        },
    ]

    for package_data in packages:
        CreditPackage.objects.get_or_create(
            name=package_data["name"], defaults=package_data
        )


def remove_initial_credit_packages(apps, schema_editor):
    """Remove the initial credit packages"""
    CreditPackage = apps.get_model("website", "CreditPackage")

    package_names = [
        "Starter Pack",
        "Creator Pack",
        "Professional Pack",
        "Enterprise Pack",
    ]
    CreditPackage.objects.filter(name__in=package_names).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("website", "0052_creditpackage_brand_credits_balance_and_more"),
    ]

    operations = [
        migrations.RunPython(
            create_initial_credit_packages, remove_initial_credit_packages
        ),
    ]
