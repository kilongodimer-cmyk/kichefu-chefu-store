from django.core.management.base import BaseCommand

from marketplace.demo_seed import seed_marketplace_demo_data


class Command(BaseCommand):
    help = "Seed demo marketplace data for Lubumbashi-focused storefront"

    def handle(self, *args, **options):
        result = seed_marketplace_demo_data()

        self.stdout.write(self.style.SUCCESS(
            "Seed complete: "
            f"cars={result['cars']}, "
            f"phones={result['phones']}, "
            f"accessories={result['accessories']}, "
            f"real_estate={result['real_estate']}"
        ))
