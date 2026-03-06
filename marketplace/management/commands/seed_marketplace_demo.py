from decimal import Decimal

from django.core.management.base import BaseCommand

from marketplace.models import Accessory, AvailabilityChoices, Car, Phone, RealEstate, RealEstateType


class Command(BaseCommand):
    help = "Seed demo marketplace data for Lubumbashi-focused storefront"

    def handle(self, *args, **options):
        car_count = self._seed_cars()
        phone_count = self._seed_phones()
        accessory_count = self._seed_accessories()
        estate_count = self._seed_real_estate()

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: cars={car_count}, phones={phone_count}, accessories={accessory_count}, real_estate={estate_count}"
        ))

    def _seed_cars(self):
        cars = [
            {
                "brand": "Toyota",
                "model": "Land Cruiser Prado",
                "vehicle_type": Car.VehicleType.SUV,
                "year": 2021,
                "mileage": 42000,
                "transmission": Car.TransmissionType.AUTOMATIC,
                "fuel_type": Car.FuelType.DIESEL,
                "price": Decimal("56000"),
                "description": "SUV robuste ideal pour Lubumbashi et trajets longue distance.",
                "seller_phone": "+243970000001",
                "is_commission": False,
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 184,
            },
            {
                "brand": "Nissan",
                "model": "X-Trail",
                "vehicle_type": Car.VehicleType.SUV,
                "year": 2020,
                "mileage": 55000,
                "transmission": Car.TransmissionType.AUTOMATIC,
                "fuel_type": Car.FuelType.PETROL,
                "price": Decimal("24500"),
                "description": "SUV familial confortable et economique.",
                "seller_phone": "+243970000002",
                "is_commission": True,
                "availability": AvailabilityChoices.RESERVED,
                "view_count": 233,
            },
            {
                "brand": "Mercedes",
                "model": "GLE 350",
                "vehicle_type": Car.VehicleType.SUV,
                "year": 2022,
                "mileage": 29800,
                "transmission": Car.TransmissionType.AUTOMATIC,
                "fuel_type": Car.FuelType.DIESEL,
                "price": Decimal("67000"),
                "description": "SUV premium avec interieur cuir et assistance complete.",
                "seller_phone": "+243970000003",
                "is_commission": False,
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 311,
            },
            {
                "brand": "Honda",
                "model": "CR-V",
                "vehicle_type": Car.VehicleType.SUV,
                "year": 2019,
                "mileage": 71000,
                "transmission": Car.TransmissionType.AUTOMATIC,
                "fuel_type": Car.FuelType.PETROL,
                "price": Decimal("22800"),
                "description": "SUV fiable et bien entretenu, ideal usage quotidien.",
                "seller_phone": "+243970000004",
                "is_commission": False,
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 149,
            },
            {
                "brand": "Hyundai",
                "model": "Santa Fe",
                "vehicle_type": Car.VehicleType.SUV,
                "year": 2021,
                "mileage": 46200,
                "transmission": Car.TransmissionType.AUTOMATIC,
                "fuel_type": Car.FuelType.DIESEL,
                "price": Decimal("31800"),
                "description": "SUV 7 places, excellent rapport qualite-prix.",
                "seller_phone": "+243970000005",
                "is_commission": True,
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 192,
            },
            {
                "brand": "Kia",
                "model": "Sportage",
                "vehicle_type": Car.VehicleType.SUV,
                "year": 2020,
                "mileage": 59000,
                "transmission": Car.TransmissionType.AUTOMATIC,
                "fuel_type": Car.FuelType.PETROL,
                "price": Decimal("23900"),
                "description": "SUV compact moderne avec consommation optimisee.",
                "seller_phone": "+243970000006",
                "is_commission": False,
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 163,
            },
            {
                "brand": "Mitsubishi",
                "model": "Pajero",
                "vehicle_type": Car.VehicleType.SUV,
                "year": 2018,
                "mileage": 86000,
                "transmission": Car.TransmissionType.AUTOMATIC,
                "fuel_type": Car.FuelType.DIESEL,
                "price": Decimal("26500"),
                "description": "4x4 solide adapte aux routes mixtes de la region.",
                "seller_phone": "+243970000007",
                "is_commission": False,
                "availability": AvailabilityChoices.RESERVED,
                "view_count": 278,
            },
        ]

        for payload in cars:
            Car.objects.update_or_create(
                brand=payload["brand"],
                model=payload["model"],
                year=payload["year"],
                defaults=payload,
            )
        return len(cars)

    def _seed_phones(self):
        phones = [
            {
                "brand": "Samsung",
                "model": "Galaxy S24 Ultra",
                "storage": "512 Go",
                "price": Decimal("1170"),
                "description": "Flagship photo/video pour createurs et professionnels.",
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 404,
            },
            {
                "brand": "iPhone",
                "model": "15 Pro",
                "storage": "256 Go",
                "price": Decimal("1240"),
                "description": "Performance premium et ecosysteme Apple complet.",
                "availability": AvailabilityChoices.RESERVED,
                "view_count": 451,
            },
            {
                "brand": "Tecno",
                "model": "Camon 30",
                "storage": "256 Go",
                "price": Decimal("295"),
                "description": "Excellent smartphone milieu de gamme tres populaire en RDC.",
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 339,
            },
            {
                "brand": "Infinix",
                "model": "Note 40",
                "storage": "256 Go",
                "price": Decimal("260"),
                "description": "Autonomie solide et grand ecran pour multitache.",
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 287,
            },
            {
                "brand": "Xiaomi",
                "model": "Redmi Note 13 Pro",
                "storage": "256 Go",
                "price": Decimal("330"),
                "description": "Tres bon rapport qualite-prix avec appareil photo detaille.",
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 315,
            },
            {
                "brand": "Oppo",
                "model": "Reno 11",
                "storage": "256 Go",
                "price": Decimal("420"),
                "description": "Design premium et recharge rapide.",
                "availability": AvailabilityChoices.SOLD,
                "view_count": 244,
            },
        ]

        for payload in phones:
            Phone.objects.update_or_create(
                brand=payload["brand"],
                model=payload["model"],
                storage=payload["storage"],
                defaults=payload,
            )
        return len(phones)

    def _seed_accessories(self):
        accessories = [
            {
                "name": "Chargeur rapide 65W",
                "price": Decimal("28"),
                "description": "Chargeur universel type C pour smartphone et tablette.",
                "availability": AvailabilityChoices.AVAILABLE,
            },
            {
                "name": "Ecouteurs Bluetooth Pro",
                "price": Decimal("34"),
                "description": "Autonomie longue duree avec reduction de bruit.",
                "availability": AvailabilityChoices.AVAILABLE,
            },
            {
                "name": "Coque antichoc premium",
                "price": Decimal("15"),
                "description": "Protection renforcee pour iPhone, Samsung, Tecno et Infinix.",
                "availability": AvailabilityChoices.RESERVED,
            },
            {
                "name": "Power bank 20000 mAh",
                "price": Decimal("39"),
                "description": "Batterie externe fiable pour deplacements frequents.",
                "availability": AvailabilityChoices.AVAILABLE,
            },
        ]

        for payload in accessories:
            Accessory.objects.update_or_create(name=payload["name"], defaults=payload)
        return len(accessories)

    def _seed_real_estate(self):
        estates = [
            {
                "real_estate_type": RealEstateType.HOUSE,
                "location": "Golf",
                "price": Decimal("185000"),
                "description": "Maison moderne 4 chambres avec parking securise.",
                "is_commission": True,
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 196,
            },
            {
                "real_estate_type": RealEstateType.LAND,
                "location": "Ruashi",
                "price": Decimal("52000"),
                "description": "Parcelle bien situee, documents en regle.",
                "is_commission": False,
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 241,
            },
            {
                "real_estate_type": RealEstateType.HOUSE,
                "location": "Bel-Air",
                "price": Decimal("132000"),
                "description": "Maison familiale proche des ecoles et commerces.",
                "is_commission": True,
                "availability": AvailabilityChoices.RESERVED,
                "view_count": 167,
            },
            {
                "real_estate_type": RealEstateType.LAND,
                "location": "Kamalondo",
                "price": Decimal("47000"),
                "description": "Parcelle residentielle dans quartier recherche.",
                "is_commission": False,
                "availability": AvailabilityChoices.AVAILABLE,
                "view_count": 215,
            },
        ]

        for payload in estates:
            RealEstate.objects.update_or_create(
                real_estate_type=payload["real_estate_type"],
                location=payload["location"],
                defaults=payload,
            )
        return len(estates)
