from django.core.management.base import BaseCommand

from core.models import EmissionFactor


FACTORS = [
    ("diesel", "L", 2.68, "DEFRA 2024", 2024),
    ("petrol", "L", 2.31, "DEFRA 2024", 2024),
    ("lubricant", "KG", 3.18, "DEFRA 2024", 2024),
    ("cng", "KG", 2.54, "DEFRA 2024", 2024),
    ("grid_electricity_IN", "kWh", 0.82, "CEA India 2024", 2024),
    ("flight_economy", "km", 0.158, "DEFRA 2024", 2024),
    ("flight_business", "km", 0.434, "DEFRA 2024", 2024),
    ("hotel_IN", "night", 12.2, "DEFRA 2024", 2024),
    ("hotel_US", "night", 18.5, "DEFRA 2024", 2024),
    ("car_rental", "day", 5.0, "estimated", 2024),
    ("rail", "km", 0.035, "DEFRA 2024", 2024),
]


class Command(BaseCommand):
    help = "Populate EmissionFactor with the MVP set (idempotent)."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for category, unit, value, citation, year in FACTORS:
            _, was_created = EmissionFactor.objects.update_or_create(
                category=category,
                unit=unit,
                valid_year=year,
                defaults={"factor_value": value, "source_citation": citation},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_factors done — created={created}, updated={updated}, "
                f"total in table={EmissionFactor.objects.count()}"
            )
        )
