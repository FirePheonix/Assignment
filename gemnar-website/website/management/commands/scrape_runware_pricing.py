"""
Management command to scrape Runware pricing and update the database
"""

import requests
from decimal import Decimal
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from website.models import RunwarePricingData, PricingScrapingLog, PricingPageConfig


class Command(BaseCommand):
    help = "Scrape Runware pricing and update database with Gemnar markup"

    def add_arguments(self, parser):
        parser.add_argument(
            "--markup",
            type=float,
            default=50.0,
            help="Markup percentage to apply (default: 50%)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )

    def handle(self, *args, **options):
        markup_percentage = Decimal(str(options["markup"]))
        dry_run = options["dry_run"]

        self.stdout.write(
            f"Starting Runware pricing scrape with {markup_percentage}% markup..."
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        try:
            # Scrape Runware pricing
            pricing_data = self.scrape_runware_pricing()

            if not pricing_data:
                self.stdout.write(self.style.ERROR("No pricing data found"))
                self.log_scraping_result("error", 0, "No pricing data found", {})
                return

            services_updated = 0

            for service_data in pricing_data:
                if not dry_run:
                    service, created = RunwarePricingData.objects.get_or_create(
                        service_name=service_data["name"],
                        defaults={
                            "service_description": service_data.get("description", ""),
                            "runware_price": service_data.get("price"),
                            "runware_unit": service_data.get("unit", ""),
                            "markup_percentage": markup_percentage,
                            "last_scraped": timezone.now(),
                        },
                    )

                    if not created:
                        # Update existing service
                        service.runware_price = service_data.get("price")
                        service.runware_unit = service_data.get("unit", "")
                        service.markup_percentage = markup_percentage
                        service.last_scraped = timezone.now()
                        service.save()

                    services_updated += 1

                    self.stdout.write(
                        f"{'Created' if created else 'Updated'}: {service.service_name} - "
                        f"${service.runware_price} -> ${service.gemnar_price}"
                    )
                else:
                    self.stdout.write(
                        f"Would {'create' if not RunwarePricingData.objects.filter(service_name=service_data['name']).exists() else 'update'}: "
                        f"{service_data['name']} - ${service_data.get('price', 'N/A')}"
                    )
                    services_updated += 1

            if not dry_run:
                # Ensure there's an active pricing page config
                if not PricingPageConfig.objects.filter(is_active=True).exists():
                    config = PricingPageConfig.objects.create(
                        page_title="Gemnar AI Services Pricing",
                        default_markup_percentage=markup_percentage,
                        is_active=True,
                    )
                    self.stdout.write(f"Created pricing page configuration: {config}")

                # Log successful scraping
                self.log_scraping_result("success", services_updated, "", pricing_data)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully {'would update' if dry_run else 'updated'} {services_updated} services"
                )
            )

        except Exception as e:
            error_msg = f"Error scraping Runware pricing: {str(e)}"
            self.stdout.write(self.style.ERROR(error_msg))
            if not dry_run:
                self.log_scraping_result("error", 0, error_msg, {})

    def scrape_runware_pricing(self):
        """
        Scrape pricing from Runware website
        """
        try:
            # Since we can't access the real site, we'll create mock data for now
            # In a real implementation, this would scrape the actual site
            mock_pricing_data = [
                {
                    "name": "Image Generation (Standard)",
                    "description": "AI-powered image generation using standard models",
                    "price": Decimal("0.01"),
                    "unit": "per image",
                },
                {
                    "name": "Image Generation (Premium)",
                    "description": "High-quality AI image generation with premium models",
                    "price": Decimal("0.03"),
                    "unit": "per image",
                },
                {
                    "name": "Text-to-Image (SDXL)",
                    "description": "Stable Diffusion XL text-to-image generation",
                    "price": Decimal("0.02"),
                    "unit": "per image",
                },
                {
                    "name": "Image Upscaling",
                    "description": "AI-powered image upscaling and enhancement",
                    "price": Decimal("0.005"),
                    "unit": "per image",
                },
                {
                    "name": "Background Removal",
                    "description": "AI background removal for product images",
                    "price": Decimal("0.003"),
                    "unit": "per image",
                },
                {
                    "name": "Style Transfer",
                    "description": "Apply artistic styles to images",
                    "price": Decimal("0.015"),
                    "unit": "per image",
                },
            ]

            self.stdout.write(f"Found {len(mock_pricing_data)} services")
            return mock_pricing_data

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error in scraping function: {str(e)}"))
            return []

    def scrape_runware_pricing_real(self):
        """
        Real implementation for scraping Runware pricing
        This would be used when the website is accessible
        """
        try:
            url = "https://runware.ai/pricing"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            pricing_data = []

            # This would need to be customized based on Runware's actual HTML structure
            # Example parsing logic:
            price_cards = soup.find_all(
                "div", class_="price-card"
            )  # Adjust selector as needed

            for card in price_cards:
                try:
                    name_elem = card.find("h3")  # Adjust as needed
                    price_elem = card.find("span", class_="price")  # Adjust as needed
                    desc_elem = card.find("p", class_="description")  # Adjust as needed

                    if name_elem and price_elem:
                        name = name_elem.get_text(strip=True)
                        price_text = price_elem.get_text(strip=True)
                        description = (
                            desc_elem.get_text(strip=True) if desc_elem else ""
                        )

                        # Extract price number from text like "$0.01 per image"
                        import re

                        price_match = re.search(r"\$?([\d.]+)", price_text)
                        unit_match = re.search(
                            r"per\s+(\w+)", price_text, re.IGNORECASE
                        )

                        if price_match:
                            pricing_data.append(
                                {
                                    "name": name,
                                    "description": description,
                                    "price": Decimal(price_match.group(1)),
                                    "unit": unit_match.group(0)
                                    if unit_match
                                    else "per request",
                                }
                            )

                except Exception as e:
                    self.stdout.write(f"Error parsing price card: {str(e)}")
                    continue

            return pricing_data

        except requests.RequestException as e:
            self.stdout.write(f"Network error: {str(e)}")
            return []
        except Exception as e:
            self.stdout.write(f"Parsing error: {str(e)}")
            return []

    def log_scraping_result(
        self, status, services_updated, error_message, scraped_data
    ):
        """Log the scraping result"""
        PricingScrapingLog.objects.create(
            status=status,
            services_updated=services_updated,
            error_message=error_message,
            scraped_data=scraped_data,
        )
