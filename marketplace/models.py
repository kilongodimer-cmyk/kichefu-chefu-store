from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone


def upload_car_image(instance, filename):
	return f"marketplace/cars/{instance.car_id}/{filename}"


def upload_phone_image(instance, filename):
	return f"marketplace/phones/{instance.phone_id}/{filename}"


def upload_accessory_image(instance, filename):
	return f"marketplace/accessories/{instance.pk}/{filename}"


def upload_real_estate_image(instance, filename):
	return f"marketplace/real_estate/{instance.real_estate_id}/{filename}"


def upload_proposal_image(instance, filename):
	return f"marketplace/proposals/{instance.proposal_id}/{filename}"


def upload_sell_car_image(instance, filename):
	return f"marketplace/sell_car/{instance.sell_request_id}/{filename}"


def _build_unique_slug(model_class, raw_text, current_pk=None):
	base_slug = slugify(raw_text)[:170] or "item"
	candidate = base_slug
	counter = 2

	while True:
		queryset = model_class.objects.filter(slug=candidate)
		if current_pk:
			queryset = queryset.exclude(pk=current_pk)
		if not queryset.exists():
			return candidate
		suffix = f"-{counter}"
		candidate = f"{base_slug[:170 - len(suffix)]}{suffix}"
		counter += 1


class AvailabilityChoices(models.TextChoices):
	AVAILABLE = "available", "Disponible"
	RESERVED = "reserved", "Reserve"
	SOLD = "sold", "Vendu"


class Car(models.Model):
	class VehicleType(models.TextChoices):
		SEDAN = "sedan", "Berline"
		SUV = "suv", "SUV"
		PICKUP = "pickup", "Pickup"
		HATCHBACK = "hatchback", "Hatchback"
		COUPE = "coupe", "Coupe"
		VAN = "van", "Van"
		OTHER = "other", "Autre"

	class TransmissionType(models.TextChoices):
		MANUAL = "manual", "Manuelle"
		AUTOMATIC = "automatic", "Automatique"

	class FuelType(models.TextChoices):
		PETROL = "petrol", "Essence"
		DIESEL = "diesel", "Diesel"
		HYBRID = "hybrid", "Hybride"
		ELECTRIC = "electric", "Electrique"
		GAS = "gas", "Gaz"

	brand = models.CharField(max_length=60, db_index=True)
	model = models.CharField(max_length=60, db_index=True)
	slug = models.SlugField(max_length=180, unique=True, blank=True, null=True, db_index=True)
	vehicle_type = models.CharField(
		max_length=20,
		choices=VehicleType.choices,
		default=VehicleType.OTHER,
		db_index=True,
	)
	year = models.PositiveIntegerField(
		validators=[MinValueValidator(1950), MaxValueValidator(timezone.now().year + 1)]
	)
	mileage = models.PositiveIntegerField(validators=[MinValueValidator(0)])
	stock = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)], help_text="Quantité disponible en stock.")
	transmission = models.CharField(
		max_length=12,
		choices=TransmissionType.choices,
		default=TransmissionType.AUTOMATIC,
	)
	fuel_type = models.CharField(
		max_length=12,
		choices=FuelType.choices,
		default=FuelType.PETROL,
	)
	price = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)
	city = models.CharField(max_length=80, blank=True, db_index=True)
	description = models.TextField(blank=True)
	seller_phone = models.CharField(max_length=30, blank=True)
	is_commission = models.BooleanField(default=False, db_index=True)
	view_count = models.PositiveIntegerField(default=0, db_index=True)
	availability = models.CharField(
		max_length=12,
		choices=AvailabilityChoices.choices,
		default=AvailabilityChoices.AVAILABLE,
		db_index=True,
	)
	date_added = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-date_added"]
		indexes = [
			models.Index(fields=["brand", "model"]),
			models.Index(fields=["vehicle_type", "availability"]),
			models.Index(fields=["availability", "price"]),
			models.Index(fields=["city", "availability"]),
			models.Index(fields=["year", "mileage"]),
		]

	def __str__(self):
		return f"{self.brand} {self.model} ({self.year})"

	def get_absolute_url(self):
		return reverse("marketplace:car_detail", kwargs={"slug": self.slug or str(self.pk)})

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = _build_unique_slug(Car, f"{self.brand} {self.model} {self.year}", self.pk)
		# Gestion automatique du statut rupture de stock
		if hasattr(self, 'stock') and self.stock == 0:
			self.availability = AvailabilityChoices.RESERVED
		elif hasattr(self, 'stock') and self.stock > 0 and self.availability != AvailabilityChoices.SOLD:
			self.availability = AvailabilityChoices.AVAILABLE
		super().save(*args, **kwargs)


class CarImage(models.Model):
	car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to=upload_car_image)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"Image Car #{self.car_id}"


class Phone(models.Model):
	brand = models.CharField(max_length=60, db_index=True)
	model = models.CharField(max_length=60, db_index=True)
	slug = models.SlugField(max_length=180, unique=True, blank=True, null=True, db_index=True)
	storage = models.CharField(max_length=40)
	price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
	description = models.TextField(blank=True)
	view_count = models.PositiveIntegerField(default=0, db_index=True)
	stock = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)], help_text="Quantité disponible en stock.")
	availability = models.CharField(
		max_length=12,
		choices=AvailabilityChoices.choices,
		default=AvailabilityChoices.AVAILABLE,
		db_index=True,
	)
	date_added = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-date_added"]
		indexes = [
			models.Index(fields=["brand", "model"]),
			models.Index(fields=["availability", "price"]),
		]

	def __str__(self):
		return f"{self.brand} {self.model}"

	def get_absolute_url(self):
		return reverse("marketplace:phone_detail", kwargs={"slug": self.slug or str(self.pk)})

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = _build_unique_slug(Phone, f"{self.brand} {self.model}", self.pk)
		# Gestion automatique du statut rupture de stock
		if hasattr(self, 'stock') and self.stock == 0:
			self.availability = AvailabilityChoices.RESERVED
		elif hasattr(self, 'stock') and self.stock > 0 and self.availability != AvailabilityChoices.SOLD:
			self.availability = AvailabilityChoices.AVAILABLE
		super().save(*args, **kwargs)


class PhoneImage(models.Model):
	phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to=upload_phone_image)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"Image Phone #{self.phone_id}"


class Accessory(models.Model):
	name = models.CharField(max_length=120)
	price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
	description = models.TextField(blank=True)
	image = models.ImageField(upload_to=upload_accessory_image, blank=True, null=True)
	stock = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)], help_text="Quantité disponible en stock.")
	availability = models.CharField(
		max_length=12,
		choices=AvailabilityChoices.choices,
		default=AvailabilityChoices.AVAILABLE,
		db_index=True,
	)
	date_added = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-date_added"]
		indexes = [models.Index(fields=["availability", "price"])]

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse("marketplace:accessory_detail", kwargs={"pk": self.pk})

	def save(self, *args, **kwargs):
		# Gestion automatique du statut rupture de stock
		if hasattr(self, 'stock') and self.stock == 0:
			self.availability = AvailabilityChoices.RESERVED
		elif hasattr(self, 'stock') and self.stock > 0 and self.availability != AvailabilityChoices.SOLD:
			self.availability = AvailabilityChoices.AVAILABLE
		super().save(*args, **kwargs)


class RealEstateType(models.TextChoices):
	HOUSE = "house", "Maison"
	LAND = "land", "Parcelle"


class RealEstate(models.Model):
	real_estate_type = models.CharField(max_length=10, choices=RealEstateType.choices)
	location = models.CharField(max_length=140, db_index=True)
	slug = models.SlugField(max_length=180, unique=True, blank=True, null=True, db_index=True)
	price = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)
	description = models.TextField(blank=True)
	is_commission = models.BooleanField(default=False, db_index=True)
	view_count = models.PositiveIntegerField(default=0, db_index=True)
	stock = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)], help_text="Quantité disponible en stock.")
	availability = models.CharField(
		max_length=12,
		choices=AvailabilityChoices.choices,
		default=AvailabilityChoices.AVAILABLE,
		db_index=True,
	)
	date_added = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-date_added"]
		indexes = [
			models.Index(fields=["real_estate_type", "location"]),
			models.Index(fields=["availability", "price"]),
		]

	def __str__(self):
		return f"{self.get_real_estate_type_display()} - {self.location}"

	def get_absolute_url(self):
		return reverse("marketplace:land_detail", kwargs={"slug": self.slug or str(self.pk)})

	def save(self, *args, **kwargs):
		if not self.slug:
			type_label = self.get_real_estate_type_display() if self.real_estate_type else "parcelle"
			self.slug = _build_unique_slug(RealEstate, f"{type_label} {self.location}", self.pk)
		# Gestion automatique du statut rupture de stock
		if hasattr(self, 'stock') and self.stock == 0:
			self.availability = AvailabilityChoices.RESERVED
		elif hasattr(self, 'stock') and self.stock > 0 and self.availability != AvailabilityChoices.SOLD:
			self.availability = AvailabilityChoices.AVAILABLE
		super().save(*args, **kwargs)


class RealEstateImage(models.Model):
	real_estate = models.ForeignKey(RealEstate, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to=upload_real_estate_image)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"Image RealEstate #{self.real_estate_id}"


class ProposalAssetType(models.TextChoices):
	CAR = "car", "Voiture"
	HOUSE = "house", "Maison"
	LAND = "land", "Parcelle"
	ACCESSORY = "accessory", "Accessoire"
	PHONE = "phone", "Telephone"


class ProposalConditionChoices(models.TextChoices):
	NEW = "new", "Neuf"
	USED = "used", "Occasion"
	REFURBISHED = "refurbished", "Reconditionne"


class ProposalTransmissionChoices(models.TextChoices):
	MANUAL = "manual", "Manuelle"
	AUTOMATIC = "automatic", "Automatique"
	OTHER = "other", "Autre"


class ProposalFuelChoices(models.TextChoices):
	PETROL = "petrol", "Essence"
	DIESEL = "diesel", "Diesel"
	HYBRID = "hybrid", "Hybride"
	ELECTRIC = "electric", "Electrique"
	OTHER = "other", "Autre"


class Proposal(models.Model):
	name = models.CharField(max_length=120)
	phone_number = models.CharField(max_length=30)
	asset_type = models.CharField(max_length=10, choices=ProposalAssetType.choices)
	brand = models.CharField(max_length=80, blank=True)
	model_name = models.CharField(max_length=80, blank=True)
	year = models.PositiveIntegerField(
		null=True,
		blank=True,
		validators=[MinValueValidator(1950), MaxValueValidator(timezone.now().year + 1)],
	)
	mileage = models.PositiveIntegerField(null=True, blank=True)
	storage = models.CharField(max_length=40, blank=True)
	transmission = models.CharField(max_length=12, choices=ProposalTransmissionChoices.choices, blank=True)
	fuel_type = models.CharField(max_length=12, choices=ProposalFuelChoices.choices, blank=True)
	city = models.CharField(max_length=120, blank=True)
	location_details = models.CharField(max_length=180, blank=True)
	surface_area = models.CharField(max_length=80, blank=True)
	item_condition = models.CharField(max_length=12, choices=ProposalConditionChoices.choices, blank=True)
	description = models.TextField(blank=True)
	desired_price = models.DecimalField(max_digits=12, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.name} - {self.get_asset_type_display()}"


class ProposalImage(models.Model):
	proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to=upload_proposal_image)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"Image Proposal #{self.proposal_id}"


class CarSellRequest(models.Model):
	name = models.CharField(max_length=120)
	phone_number = models.CharField(max_length=30)
	model = models.CharField(max_length=120)
	year = models.PositiveIntegerField(
		validators=[MinValueValidator(1950), MaxValueValidator(timezone.now().year + 1)]
	)
	desired_price = models.DecimalField(max_digits=12, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.name} - {self.model} ({self.year})"


class CarSellRequestImage(models.Model):
	sell_request = models.ForeignKey(
		CarSellRequest,
		on_delete=models.CASCADE,
		related_name="photos",
	)
	image = models.ImageField(upload_to=upload_sell_car_image)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"Photo SellCar #{self.sell_request_id}"


class Favorite(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.PositiveIntegerField()
	content_object = GenericForeignKey("content_type", "object_id")
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="unique_user_favorite")
		]
		indexes = [models.Index(fields=["content_type", "object_id"])]

	def __str__(self):
		return f"Favorite #{self.pk} by {self.user_id}"


class UserMarketplaceProfile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="marketplace_profile")
	city = models.CharField(max_length=80, blank=True, db_index=True)
	notify_new_listings = models.BooleanField(default=True, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Profile {self.user_id}"


class PriceDropAlert(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="price_alerts")
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.PositiveIntegerField()
	content_object = GenericForeignKey("content_type", "object_id")
	target_price = models.DecimalField(max_digits=12, decimal_places=2, db_index=True)
	is_active = models.BooleanField(default=True, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.UniqueConstraint(
				fields=["user", "content_type", "object_id"],
				name="unique_user_price_alert",
			)
		]
		indexes = [
			models.Index(fields=["content_type", "object_id", "is_active"]),
		]

	def __str__(self):
		return f"PriceAlert #{self.pk} by {self.user_id}"


class UserNotification(models.Model):
	class NotificationType(models.TextChoices):
		PRICE_DROP = "price_drop", "Baisse de prix"
		NEW_LISTING = "new_listing", "Nouvelle annonce"

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="marketplace_notifications")
	notification_type = models.CharField(max_length=20, choices=NotificationType.choices, db_index=True)
	title = models.CharField(max_length=180)
	message = models.TextField(blank=True)
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
	object_id = models.PositiveIntegerField(null=True, blank=True)
	content_object = GenericForeignKey("content_type", "object_id")
	is_read = models.BooleanField(default=False, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["user", "is_read", "created_at"]),
		]

	def __str__(self):
		return f"Notification #{self.pk} -> {self.user_id}"

# Create your models here.
