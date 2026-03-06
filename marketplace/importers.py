import csv
import io
import os
import zipfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen
import unicodedata

from django.core.files.base import ContentFile
from django.db import transaction

from .models import AvailabilityChoices, Car, CarImage


@dataclass
class CarImportResult:
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped_duplicates: int = 0
    images_added: int = 0
    errors: list[str] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CarCSVImporter:
    REQUIRED_COLUMNS = {"brand", "model", "year", "mileage", "price", "description", "image"}

    HEADER_ALIASES = {
        "marque": "brand",
        "brand": "brand",
        "modele": "model",
        "model": "model",
        "annee": "year",
        "year": "year",
        "kilometrage": "mileage",
        "mileage": "mileage",
        "prix": "price",
        "price": "price",
        "description": "description",
        "image": "image",
        "images": "image",
        "vehicle_type": "vehicle_type",
        "type_vehicule": "vehicle_type",
        "transmission": "transmission",
        "fuel_type": "fuel_type",
        "carburant": "fuel_type",
        "availability": "availability",
        "disponibilite": "availability",
        "seller_phone": "seller_phone",
        "telephone_vendeur": "seller_phone",
        "is_commission": "is_commission",
        "commission": "is_commission",
    }

    def __init__(self, duplicate_strategy="skip"):
        self.duplicate_strategy = duplicate_strategy

    def import_file(self, csv_file, images_zip_file=None):
        result = CarImportResult()
        image_archive = self._load_zip(images_zip_file, result)

        csv_file.seek(0)
        wrapper = io.TextIOWrapper(csv_file, encoding="utf-8-sig", errors="replace")
        reader = csv.DictReader(wrapper)

        if not reader.fieldnames:
            result.errors.append("Le fichier CSV est vide.")
            return result

        header_map = self._map_headers(reader.fieldnames)
        missing = [column for column in self.REQUIRED_COLUMNS if column not in header_map.values()]
        if missing:
            result.errors.append(
                "Colonnes obligatoires manquantes: " + ", ".join(sorted(missing))
            )
            return result

        with transaction.atomic():
            for index, row in enumerate(reader, start=2):
                result.processed += 1
                try:
                    self._import_row(row, header_map, image_archive, result)
                except Exception as exc:  # noqa: BLE001
                    result.errors.append(f"Ligne {index}: {exc}")

        return result

    def _load_zip(self, images_zip_file, result):
        if not images_zip_file:
            return None
        try:
            images_zip_file.seek(0)
            return zipfile.ZipFile(images_zip_file)
        except zipfile.BadZipFile:
            result.errors.append("Le fichier d'images n'est pas un ZIP valide.")
            return None

    def _import_row(self, row, header_map, image_archive, result):
        values = self._normalize_row(row, header_map)
        brand = self._required_text(values, "brand")
        model = self._required_text(values, "model")
        year = self._to_int(values.get("year"), "year")
        mileage = self._to_int(values.get("mileage"), "mileage")
        price = self._to_decimal(values.get("price"), "price")

        lookup = {
            "brand__iexact": brand,
            "model__iexact": model,
            "year": year,
            "mileage": mileage,
            "price": price,
        }
        existing = Car.objects.filter(**lookup).first()

        payload = {
            "brand": brand,
            "model": model,
            "year": year,
            "mileage": mileage,
            "price": price,
            "description": values.get("description", "").strip(),
            "vehicle_type": self._choice(
                values.get("vehicle_type"),
                {choice for choice, _ in Car.VehicleType.choices},
                Car.VehicleType.OTHER,
            ),
            "transmission": self._choice(
                values.get("transmission"),
                {choice for choice, _ in Car.TransmissionType.choices},
                Car.TransmissionType.AUTOMATIC,
            ),
            "fuel_type": self._choice(
                values.get("fuel_type"),
                {choice for choice, _ in Car.FuelType.choices},
                Car.FuelType.PETROL,
            ),
            "availability": self._choice(
                values.get("availability"),
                {choice for choice, _ in AvailabilityChoices.choices},
                AvailabilityChoices.AVAILABLE,
            ),
            "seller_phone": values.get("seller_phone", "").strip(),
            "is_commission": self._to_bool(values.get("is_commission")),
        }

        if existing:
            if self.duplicate_strategy == "skip":
                result.skipped_duplicates += 1
                return
            for field, value in payload.items():
                setattr(existing, field, value)
            existing.save()
            car = existing
            result.updated += 1
        else:
            car = Car.objects.create(**payload)
            result.created += 1

        image_refs = self._parse_image_refs(values.get("image", ""))
        if image_refs:
            result.images_added += self._attach_images(car, image_refs, image_archive)

    def _map_headers(self, fieldnames):
        mapped = {}
        for raw_header in fieldnames:
            if raw_header is None:
                continue
            key = self._slug(raw_header)
            canonical = self.HEADER_ALIASES.get(key)
            if canonical:
                mapped[raw_header] = canonical
        return mapped

    def _normalize_row(self, row, header_map):
        normalized = {}
        for raw_key, value in row.items():
            canonical = header_map.get(raw_key)
            if canonical:
                normalized[canonical] = value or ""
        return normalized

    def _required_text(self, values, field):
        text = (values.get(field) or "").strip()
        if not text:
            raise ValueError(f"Le champ '{field}' est obligatoire")
        return text

    def _to_int(self, raw, field):
        value = (raw or "").strip()
        if not value:
            raise ValueError(f"Le champ '{field}' est obligatoire")
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"Le champ '{field}' doit etre un entier") from exc

    def _to_decimal(self, raw, field):
        value = (raw or "").strip().replace(" ", "").replace(",", ".")
        if not value:
            raise ValueError(f"Le champ '{field}' est obligatoire")
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"Le champ '{field}' doit etre un decimal valide") from exc

    def _to_bool(self, raw):
        value = (raw or "").strip().lower()
        return value in {"1", "true", "oui", "yes", "y"}

    def _choice(self, raw, allowed_values, default):
        value = (raw or "").strip().lower()
        if value in allowed_values:
            return value
        return default

    def _parse_image_refs(self, raw):
        if not raw:
            return []
        splitters = ["|", ";", ","]
        refs = [raw]
        for splitter in splitters:
            if splitter in raw:
                refs = [piece for chunk in refs for piece in chunk.split(splitter)]
        return [item.strip() for item in refs if item.strip()]

    def _attach_images(self, car, image_refs, image_archive):
        existing_names = {
            os.path.basename(image.image.name).lower()
            for image in car.images.only("image")
            if image.image and image.image.name
        }
        created_count = 0
        for ref in image_refs:
            basename = os.path.basename(ref).lower()
            if basename and basename in existing_names:
                continue

            content = self._resolve_image_content(ref, image_archive)
            if content is None:
                continue

            filename, file_bytes = content
            CarImage.objects.create(
                car=car,
                image=ContentFile(file_bytes, name=filename),
            )
            existing_names.add(os.path.basename(filename).lower())
            created_count += 1
        return created_count

    def _resolve_image_content(self, ref, image_archive):
        if ref.startswith("http://") or ref.startswith("https://"):
            return self._download_image(ref)

        if image_archive is None:
            return None

        normalized_ref = ref.replace("\\", "/").lstrip("./")
        for zip_name in image_archive.namelist():
            normalized_zip = zip_name.replace("\\", "/").lstrip("./")
            if normalized_zip.lower() == normalized_ref.lower() or os.path.basename(normalized_zip).lower() == os.path.basename(normalized_ref).lower():
                with image_archive.open(zip_name) as file_obj:
                    data = file_obj.read()
                return os.path.basename(zip_name), data
        return None

    def _download_image(self, url):
        try:
            with urlopen(url, timeout=15) as response:  # nosec B310
                data = response.read()
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or "image.jpg"
            return filename, data
        except (URLError, OSError):
            return None

    def _slug(self, value):
        normalized = unicodedata.normalize("NFKD", value)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        return ascii_text.strip().lower().replace(" ", "_")
